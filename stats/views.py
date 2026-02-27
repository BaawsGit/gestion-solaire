# stats/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
from django.utils import timezone
from datetime import timedelta
import json
from plotly.offline import plot
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from interventions.models import Intervention
from clients.models import Client
from techniciens.models import Technicien


@login_required
def statistics_dashboard(request):
    """
    Tableau de bord statistique
    """
    if hasattr(request.user, 'technicien'):
        return redirect('dashboard')

    # 1. Nombre d'interventions par mois (3D) - GARDÉ
    interventions_par_mois = get_interventions_par_mois()

    # 2. Répartition par type d'intervention (3D) - GARDÉ
    repartition_type = get_repartition_par_type()

    # 3. Techniciens les plus actifs (3D) - GARDÉ
    techniciens_actifs = get_techniciens_actifs_2d()

    # 4. Clients les plus sollicités (2D amélioré)
    clients_sollicites = get_clients_sollicites_ameliore()

    # 5. Évolution financière (2D amélioré)
    evolution_financiere = get_evolution_financiere_ameliore()

    # 6. Répartition par type d'installation (2D amélioré)
    repartition_installation = get_repartition_par_installation_par_mois()

    # 7. NOUVEAU: Répartition par type d'installation par mois
    repartition_installation_mois = get_repartition_par_installation_par_mois()

    # Statistiques globales
    total_interventions = Intervention.objects.count()
    total_clients = Client.objects.count()
    total_techniciens = Technicien.objects.count()
    revenu_total = Intervention.objects.filter(statut='terminee').aggregate(
        total=Sum('prix_intervention')
    )['total'] or 0

    context = {
        'page_title': '📊 Tableau de Bord Statistiques',
        'interventions_par_mois': interventions_par_mois,
        'repartition_type': repartition_type,
        'techniciens_actifs': techniciens_actifs,
        'clients_sollicites': clients_sollicites,
        'evolution_financiere': evolution_financiere,
        'repartition_installation': repartition_installation,
        'repartition_installation_mois': repartition_installation_mois,  # NOUVEAU
        'total_interventions': total_interventions,
        'total_clients': total_clients,
        'total_techniciens': total_techniciens,
        'revenu_total': revenu_total,
    }

    return render(request, 'stats/dashboard.html', context)


def get_interventions_par_mois():
    """Graphique 1 - Nombre d'interventions par mois (2D avec effet visuel original)"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)

    interventions = Intervention.objects.filter(
        date_intervention__gte=start_date
    ).annotate(
        year=ExtractYear('date_intervention'),
        month=ExtractMonth('date_intervention')
    ).values('year', 'month').annotate(
        count=Count('id')
    ).order_by('year', 'month')

    months = []
    counts = []

    for interv in interventions:
        month_name = f"{interv['month']:02d}/{interv['year']}"
        months.append(month_name)
        counts.append(interv['count'])

    if not counts:
        return None

    # Créer un graphique avec effet "waterfall" ou cascade
    fig = go.Figure()

    # Barres avec dégradé de couleur selon la valeur
    fig.add_trace(go.Bar(
        x=months,
        y=counts,
        name='Interventions',
        marker=dict(
            color=counts,
            colorscale='Viridis',
            line=dict(color='rgba(0,0,0,0.3)', width=1),
            showscale=True,
            colorbar=dict(title='Nombre', thickness=15)
        ),
        text=counts,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Interventions: %{y}<extra></extra>'
    ))

    # Ajouter une ligne de moyenne mobile
    if len(counts) >= 3:
        moving_avg = []
        for i in range(len(counts)):
            start_idx = max(0, i - 1)
            end_idx = min(len(counts), i + 2)
            avg = sum(counts[start_idx:end_idx]) / (end_idx - start_idx)
            moving_avg.append(avg)

        fig.add_trace(go.Scatter(
            x=months,
            y=moving_avg,
            name='Tendance (moyenne mobile)',
            mode='lines+markers',
            line=dict(
                color='#e74c3c',
                width=3,
                dash='dash'
            ),
            marker=dict(
                size=8,
                symbol='diamond',
                color='#e74c3c'
            ),
            hovertemplate='<b>%{x}</b><br>Tendance: %{y:.1f}<extra></extra>'
        ))

    # Ajouter une zone d'ombre pour la variabilité
    fig.add_trace(go.Scatter(
        x=months + months[::-1],
        y=counts + [0] * len(counts),
        fill='toself',
        fillcolor='rgba(52, 152, 219, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Zone d\'activité',
        showlegend=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        title=dict(
            text='<b>Évolution mensuelle des interventions</b>',
            font=dict(size=14),
        ),
        xaxis=dict(
            title='Mois',
            tickangle=-45,
            gridcolor='rgba(200,200,200,0.2)',
            showgrid=True,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title='Nombre d\'interventions',
            gridcolor='rgba(200,200,200,0.2)',
            showgrid=True,
            title_font=dict(size=10)
        ),
        height=400,
        # AUGMENTER la marge inférieure pour les légendes
        margin=dict(l=50, r=50, b=120, t=80),  # b=120 au lieu de b=100
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x unified',
        barmode='overlay',
        # REPOSITIONNER les légendes EN DESSOUS
        legend=dict(
            orientation="h",  # Horizontal
            yanchor="top",    # Ancre au top de la légende
            y=-0.25,          # Position NÉGATIVE = sous le graphique
            xanchor="center",
            x=0.5,
            #bgcolor='rgba(255, 255, 255, 0.8)',
            #bordercolor='#3498db',
            #borderwidth=1,
            font=dict(size=10)
        ),
        shapes=[
            # Ligne de séparation stylisée
            dict(
                type='line',
                x0=months[0] if months else 0,
                y0=0,
                x1=months[-1] if months else 1,
                y1=0,
                line=dict(color='#95a5a6', width=2, dash='dot')
            )
        ]
    )

    return plot(fig, output_type='div', include_plotlyjs=False)



def get_repartition_par_type():
    """Graphique 3D Pie - Répartition par type d'intervention"""
    repartition = Intervention.objects.values('type_intervention').annotate(
        count=Count('id')
    )
    # Vérifier s'il y a des données
    if not repartition or sum(r['count'] for r in repartition) == 0:
        return None

    labels = [dict(Intervention.TYPE_INTERVENTION_CHOICES).get(r['type_intervention'], r['type_intervention'])
              for r in repartition]
    values = [r['count'] for r in repartition]

    # Créer un graphique 3D Pie
    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(
                colors=px.colors.qualitative.Set3,
                line=dict(color='#000000', width=1)
            ),
            textinfo='percent+label',
            textposition='outside',
            pull=[0.1, 0, 0] if len(values) == 3 else None,
            hoverinfo='label+percent+value'
        )
    ])

    fig.update_layout(
        title=dict(
            text='<b>Répartition par type d\'intervention</b>',
            font=dict(size=14)
        ),
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    return plot(fig, output_type='div', include_plotlyjs=False)


# Dans stats/views.py - Fonction get_techniciens_actifs modifiée
# Dans stats/views.py - Modifier la fonction get_techniciens_actifs_2d

def get_techniciens_actifs_2d():
    """Graphique 3 - Camembert élégant : Répartition des interventions par technicien"""
    # Récupérer les techniciens avec leurs interventions terminées
    techniciens = Technicien.objects.annotate(
        # Total des interventions (tous statuts)
        intervention_count=Count('interventions'),
        # Interventions TERMINÉES seulement
        intervention_terminees_count=Count(
            'interventions',
            filter=Q(interventions__statut='terminee')
        ),
        # Revenu des interventions TERMINÉES seulement
        total_revenu_terminees=Sum(
            'interventions__prix_intervention',
            filter=Q(interventions__statut='terminee')
        ),
        # Ancien calcul (tous statuts) - pour comparaison
        total_revenu_tous=Sum('interventions__prix_intervention')
    ).filter(intervention_count__gt=0).order_by('-intervention_count')[:8]

    if not techniciens:
        return None

    names = [t.nom for t in techniciens]
    counts = [t.intervention_count for t in techniciens]
    revenus_terminees = [float(t.total_revenu_terminees or 0) for t in techniciens]
    revenus_tous = [float(t.total_revenu_tous or 0) for t in techniciens]
    terminees_counts = [t.intervention_terminees_count for t in techniciens]

    # Calculer les pourcentages
    total = sum(counts)
    percentages = [(c / total * 100) for c in counts]

    # Créer le texte pour le tooltip
    hover_texts = []
    for i, nom in enumerate(names):
        hover_text = (f"<b>{nom}</b><br>"
                     f"Interventions totales: {counts[i]}<br>"
                     f"Interventions terminées: {terminees_counts[i]}<br>"
                     f"Pourcentage: {percentages[i]:.1f}%<br>"
                     f"Revenu encaissé (terminées): {revenus_terminees[i]:,.0f} FCFA<br>"
                     f"Revenu total (tous statuts): {revenus_tous[i]:,.0f} FCFA")
        hover_texts.append(hover_text)

    # PALETTE DE COULEURS VARIEE ET HARMONIEUSE
    colors_palettes = [
        ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#d35400', '#34495e'],
        ['#6FA8DC', '#93C47D', '#E06666', '#FFD966', '#8E7CC3', '#76A5AF', '#F6B26B', '#999999'],
        ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#673AB7', '#FF9800', '#009688', '#795548'],
        ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    ]

    colors = colors_palettes[0][:len(names)]

    # Créer un camembert en anneau avec rotation
    fig = go.Figure(data=[
        go.Pie(
            labels=names,
            values=counts,
            hole=0.55,
            marker=dict(
                colors=colors,
                line=dict(color='white', width=3),
                pattern=dict(
                    shape="/",
                    size=4,
                    solidity=0.2
                )
            ),
            textinfo='percent+label',
            textposition='outside',
            textfont=dict(
                size=11,
                family="Arial, sans-serif",
                color=['white' if i < 2 else '#2c3e50' for i in range(len(names))]
            ),
            hoverinfo='text',
            hovertext=hover_texts,
            pull=[0.1 if i < 2 else 0.05 for i in range(len(names))],
            rotation=30,
            direction='clockwise',
            sort=False,
        )
    ])

    # Calculer les totaux
    total_interventions = sum(counts)
    total_interventions_terminees = sum(terminees_counts)
    total_revenu_terminees = sum(revenus_terminees)
    total_revenu_tous = sum(revenus_tous)

    fig.update_layout(
        title=dict(
            text='<b>Répartition par Technicien</b><br><span style="font-size:12px;color:#666"></span>',
            font=dict(size=14),
        ),
        height=420,
        margin=dict(l=20, r=20, b=100, t=100),
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="right",
            x=1.15,
            font=dict(size=11, family="Arial, sans-serif"),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#3498db',
            borderwidth=2,
            itemclick=False,
            itemdoubleclick=False
        ),
        annotations=[
            # Annotation principale - Interventions totales
            dict(
                text=f'Total interventions<br>'
                     f'<span style="font-size:20px;color:#2c3e50;font-weight:bold">{total_interventions}</span><br>'
                     f'<span style="font-size:14px;color:#27ae60">({total_interventions_terminees} terminées)</span>',
                x=0.5,
                y=0.6,
                font=dict(size=13, color='#7f8c8d', family="Arial, sans-serif"),
                showarrow=False,
                align='center'
            ),
            # Annotation secondaire - Revenu
            dict(
                text=f'Revenu encaissé<br>'
                     f'<span style="font-size:16px;color:#27ae60">{total_revenu_terminees:,.0f} FCFA</span><br>'
                     f'<span style="font-size:11px;color:#95a5a6">({total_revenu_tous:,.0f} FCFA total)</span>',
                x=0.5,
                y=0.35,
                font=dict(size=11, color='#7f8c8d', family="Arial, sans-serif"),
                showarrow=False,
                align='center'
            )
        ]
    )

    # Ajouter des effets visuels
    fig.update_traces(
        marker=dict(
            line=dict(color='white', width=2.5),
            pattern=dict(
                shape="/",
                size=5,
                solidity=0.15
            )
        ),
        texttemplate='%{label}<br>%{percent}'
    )

    return plot(fig, output_type='div', include_plotlyjs=False)


# Dans stats/views.py - Fonction get_clients_sollicites_ameliore modifiée
def get_clients_sollicites_ameliore():
    """Graphique 2D amélioré - Clients les plus sollicités avec deux lignes de revenus"""
    clients = Client.objects.annotate(
        intervention_count=Count('interventions'),
        total_revenu=Sum('interventions__prix_intervention'),
        # NOUVEAU : Revenu des interventions terminées seulement
        revenu_terminees=Sum(
            'interventions__prix_intervention',
            filter=Q(interventions__statut='terminee')
        )
    ).filter(intervention_count__gt=0).order_by('-intervention_count')[:10]

    if not clients:
        return None

    noms = [c.nom[:15] + '...' if len(c.nom) > 15 else c.nom for c in clients]
    counts = [c.intervention_count for c in clients]
    revenus_tous = [float(c.total_revenu or 0) for c in clients]
    revenus_terminees = [float(c.revenu_terminees or 0) for c in clients]  # NOUVEAU

    # Créer un bar chart avec triple axe Y (barres + 2 lignes)
    fig = go.Figure()

    # Barres pour le nombre d'interventions
    fig.add_trace(go.Bar(
        x=noms,
        y=counts,
        name='Nombre<br>d\'interventions',
        marker_color='#3498db',
        text=counts,
        textposition='auto',
        yaxis='y',
        opacity=0.8
    ))

    # Ligne 1 (orange) : revenus totaux (tous statuts)
    fig.add_trace(go.Scatter(
        x=noms,
        y=revenus_tous,
        name='Revenus totaux<br>(tous statuts)',
        mode='lines+markers',
        marker=dict(
            size=8,
            color='#e74c3c',  # Rouge orangé
            symbol='diamond'
        ),
        line=dict(
            width=3,
            color='#e74c3c'
        ),
        yaxis='y2'
    ))

    # Ligne 2 (jaune) : revenus des interventions terminées seulement - NOUVEAU
    fig.add_trace(go.Scatter(
        x=noms,
        y=revenus_terminees,
        name='Revenus réels<br>(interventions terminées)',
        mode='lines+markers',
        marker=dict(
            size=8,
            color='#f1c40f',  # Jaune vif
            symbol='star'
        ),
        line=dict(
            width=3,
            color='#f1c40f',
            dash='dash'  # Ligne en pointillés pour différenciation
        ),
        yaxis='y2'
    ))

    fig.update_layout(
        title=dict(
            text='<b>Top 10 Clients les plus sollicités</b>',
            font=dict(size=14),
        ),
        xaxis=dict(
            title='Clients',
            tickangle=-45,
            gridcolor='rgba(200,200,200,0.2)',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title='Nombre d\'interventions',
            side='left',
            gridcolor='rgba(200,200,200,0.2)',
            title_font=dict(size=11),
            showgrid=True
        ),
        yaxis2=dict(
            title='Revenus générés (FCFA)',
            side='right',
            overlaying='y',
            gridcolor='rgba(200,200,200,0.2)',
            title_font=dict(size=11),
            showgrid=True
        ),
        height=400,
        margin=dict(l=50, r=50, b=100, t=60),
        paper_bgcolor='white',
        plot_bgcolor='white',
        barmode='group',
        legend=dict(
            orientation="v",  # Vertical
            yanchor="top",
            y=0.98,  # En haut
            xanchor="right",
            x=0.98,  # À droite
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#3498db',
            borderwidth=1,
            font=dict(size=10)
        ),
        hovermode='x unified'
    )

    return plot(fig, output_type='div', include_plotlyjs=False)


def get_evolution_financiere_ameliore():
    """Graphique 2D amélioré - Évolution financière avec tendance"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)

    finances = Intervention.objects.filter(
        date_intervention__gte=start_date,
        statut='terminee'
    ).annotate(
        year=ExtractYear('date_intervention'),
        month=ExtractMonth('date_intervention')
    ).values('year', 'month').annotate(
        total=Sum('prix_intervention'),
        count=Count('id')
    ).order_by('year', 'month')

    months = []
    totals = []
    counts = []

    for f in finances:
        month_name = f"{f['month']:02d}/{f['year']}"
        months.append(month_name)
        totals.append(float(f['total'] or 0))
        counts.append(f['count'])

    if not totals:
        return None

    # Créer un graphique avec barres
    fig = go.Figure()

    # Barres pour les revenus mensuels
    fig.add_trace(go.Bar(
        x=months,
        y=totals,
        name='Revenus mensuels',
        marker_color='#2ecc71',
        text=[f"{t:,.0f}" for t in totals],
        textposition='auto',
        hoverinfo='text'
    ))

    fig.update_layout(
        title=dict(
            text='<b>Évolution financière (12 derniers mois)</b>',
            font=dict(size=14)
        ),
        xaxis=dict(
            title='Mois',
            tickangle=-45,
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            title='Revenus (FCFA)',
            gridcolor='lightgrey'
        ),
        height=400,
        margin=dict(l=50, r=30, b=40, t=40),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x unified'
    )

    return plot(fig, output_type='div', include_plotlyjs=False)



def get_repartition_par_installation_par_mois():
    """Graphique 6 - Répartition des interventions par type d'installation par mois"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=180)  # 6 derniers mois

    # Récupérer les interventions groupées par mois et type d'installation
    interventions = Intervention.objects.filter(
        date_intervention__gte=start_date
    ).annotate(
        month=TruncMonth('date_intervention')
    ).select_related('client')

    # Structurer les données par mois
    data_by_month = {}

    for intervention in interventions:
        month_key = intervention.month.strftime('%Y-%m')
        month_display = intervention.month.strftime('%b %Y')

        if month_key not in data_by_month:
            data_by_month[month_key] = {
                'display': month_display,
                'counts': {
                    '3KVA': 0,
                    '5KVA': 0,
                    '8KVA': 0,
                    '16KVA': 0,
                    '24KVA': 0,
                    'Autre': 0
                }
            }

        # Déterminer le type d'installation
        type_install = intervention.client.type_installation or 'Autre'
        normalized_type = 'Autre'

        for kva_type in ['3KVA', '5KVA', '8KVA', '16KVA', '24KVA']:
            if kva_type in type_install.upper():
                normalized_type = kva_type
                break

        data_by_month[month_key]['counts'][normalized_type] += 1

    # Trier les mois
    sorted_months = sorted(data_by_month.keys())
    month_labels = [data_by_month[m]['display'] for m in sorted_months]

    # Types d'installation
    installation_types = ['3KVA', '5KVA', '8KVA', '16KVA', '24KVA', 'Autre']

    # Préparer les données pour chaque type
    fig = go.Figure()

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

    for i, inst_type in enumerate(installation_types):
        values = [data_by_month[m]['counts'][inst_type] for m in sorted_months]

        # Ne montrer que les types qui ont des données
        if sum(values) > 0:
            fig.add_trace(go.Bar(
                name=inst_type,
                x=month_labels,
                y=values,
                marker_color=colors[i],
                hovertemplate=(
                    f"<b>{inst_type}</b><br>"
                    "Mois: %{x}<br>"
                    "Interventions: %{y}<br>"
                    "<extra></extra>"
                )
            ))

    # SOLUTION RADICALE : Utiliser exactement la même configuration que le graphique 1
    # Copiez toute la partie update_layout du graphique 1
    fig.update_layout(
        title=dict(
            text='<b>Répartition par type d\'installation par mois</b>',
            font=dict(size=14),
        ),
        xaxis=dict(
            title='Mois',
            tickangle=-45,
            gridcolor='rgba(200,200,200,0.2)',
            showgrid=True,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title='Nombre d\'interventions',
            gridcolor='rgba(200,200,200,0.2)',
            showgrid=True,
            title_font=dict(size=10)
        ),
        height=400,
        # Marge TRÈS grande en bas pour forcer l'espace
        margin=dict(l=50, r=50, b=150, t=80),  # Augmenté à b=150
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x unified',
        barmode='stack',
    )

    return plot(fig, output_type='div', include_plotlyjs=False)

# ==================== FONCTIONS D'EXPORT ====================

def get_interventions_data():
    """Données brutes pour les interventions par mois"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)

    interventions = Intervention.objects.filter(
        date_intervention__gte=start_date
    ).annotate(
        year=ExtractYear('date_intervention'),
        month=ExtractMonth('date_intervention')
    ).values('year', 'month').annotate(
        count=Count('id')
    ).order_by('year', 'month')

    data = []
    for interv in interventions:
        data.append({
            'year': interv['year'],
            'month': interv['month'],
            'count': interv['count']
        })

    return data


def get_type_data():
    """Données brutes pour la répartition par type"""
    repartition = Intervention.objects.values('type_intervention').annotate(
        count=Count('id')
    )

    data = []
    for r in repartition:
        data.append({
            'type': r['type_intervention'],
            'count': r['count']
        })

    return data


def get_techniciens_data():
    """Données brutes pour les techniciens actifs"""
    techniciens = Technicien.objects.annotate(
        intervention_count=Count('interventions')
    ).order_by('-intervention_count')[:10]

    data = []
    for t in techniciens:
        data.append({
            'id': t.id,
            'nom': t.nom,
            'intervention_count': t.intervention_count
        })

    return data


def get_clients_data():
    """Données brutes pour les clients sollicités"""
    clients = Client.objects.annotate(
        intervention_count=Count('interventions'),
        total_revenu=Sum('interventions__prix_intervention')
    ).order_by('-intervention_count')[:10]

    data = []
    for c in clients:
        data.append({
            'id': c.id,
            'nom': c.nom,
            'intervention_count': c.intervention_count,
            'total_revenu': float(c.total_revenu or 0)
        })

    return data


def get_financial_data():
    """Données brutes pour l'évolution financière"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)

    finances = Intervention.objects.filter(
        date_intervention__gte=start_date,
        statut='terminee'
    ).annotate(
        year=ExtractYear('date_intervention'),
        month=ExtractMonth('date_intervention')
    ).values('year', 'month').annotate(
        total=Sum('prix_intervention'),
        count=Count('id')
    ).order_by('year', 'month')

    data = []
    for f in finances:
        data.append({
            'year': f['year'],
            'month': f['month'],
            'total': float(f['total'] or 0),
            'count': f['count']
        })

    return data


def get_installation_data():
    """Données brutes pour la répartition par type d'installation"""
    interventions = Intervention.objects.select_related('client').all()

    counts = {
        '3KVA': 0,
        '5KVA': 0,
        '8KVA': 0,
        '16KVA': 0,
        '24KVA': 0,
        'Autre': 0
    }

    for intervention in interventions:
        type_install = intervention.client.type_installation or 'Autre'

        normalized_type = 'Autre'
        for kva_type in ['3KVA', '5KVA', '8KVA', '16KVA', '24KVA']:
            if kva_type in type_install.upper():
                normalized_type = kva_type
                break

        counts[normalized_type] += 1

    data = []
    for kva_type, count in counts.items():
        data.append({
            'type_installation': kva_type,
            'count': count
        })

    return data


def get_repartition_par_installation_par_mois():
    """Graphique 7 - Répartition des interventions par type d'installation par mois"""
    end_date = timezone.now()
    start_date = end_date - timedelta(days=180)  # 6 derniers mois

    # Récupérer les interventions groupées par mois et type d'installation
    interventions = Intervention.objects.filter(
        date_intervention__gte=start_date
    ).annotate(
        month=TruncMonth('date_intervention')
    ).select_related('client')

    # Structurer les données par mois
    data_by_month = {}

    for intervention in interventions:
        month_key = intervention.month.strftime('%Y-%m')
        month_display = intervention.month.strftime('%b %Y')

        if month_key not in data_by_month:
            data_by_month[month_key] = {
                'display': month_display,
                'counts': {
                    '3KVA': 0,
                    '5KVA': 0,
                    '8KVA': 0,
                    '16KVA': 0,
                    '24KVA': 0,
                    'Autre': 0
                }
            }

        # Déterminer le type d'installation
        type_install = intervention.client.type_installation or 'Autre'
        normalized_type = 'Autre'

        for kva_type in ['3KVA', '5KVA', '8KVA', '16KVA', '24KVA']:
            if kva_type in type_install.upper():
                normalized_type = kva_type
                break

        data_by_month[month_key]['counts'][normalized_type] += 1

    # Trier les mois
    sorted_months = sorted(data_by_month.keys())
    month_labels = [data_by_month[m]['display'] for m in sorted_months]

    # Types d'installation
    installation_types = ['3KVA', '5KVA', '8KVA', '16KVA', '24KVA', 'Autre']

    # Préparer les données pour chaque type
    fig = go.Figure()

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

    for i, inst_type in enumerate(installation_types):
        values = [data_by_month[m]['counts'][inst_type] for m in sorted_months]

        # Ne montrer que les types qui ont des données
        if sum(values) > 0:
            fig.add_trace(go.Bar(
                name=inst_type,
                x=month_labels,
                y=values,
                marker_color=colors[i],
                hovertemplate=(
                    f"<b>{inst_type}</b><br>"
                    "Mois: %{x}<br>"
                    "Interventions: %{y}<br>"
                    "<extra></extra>"
                )
            ))

    fig.update_layout(
        title=dict(
            text='<b>Répartition par type d\'installation par mois</b>',
            font=dict(size=14),
            y=0.95
        ),
        xaxis=dict(
            title='Mois',
            tickangle=-45,
            gridcolor='rgba(200,200,200,0.2)',
            showgrid=True
        ),
        yaxis=dict(
            title='Nombre d\'interventions',
            gridcolor='rgba(200,200,200,0.2)',
            showgrid=True
        ),
        barmode='stack',
        height=400,
        margin=dict(l=50, r=50, b=100, t=80),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#3498db',
            borderwidth=1,
            font=dict(size=10)
        )
    )

    return plot(fig, output_type='div', include_plotlyjs=False)






@login_required
def export_statistics(request):
    """Export des statistiques en JSON (téléchargement de fichier)"""
    if hasattr(request.user, 'technicien'):
        return redirect('dashboard')

    # Récupérer toutes les données
    data = {
        'interventions_par_mois': get_interventions_data(),
        'repartition_type': get_type_data(),
        'techniciens_actifs': get_techniciens_data(),
        'clients_sollicites': get_clients_data(),
        'evolution_financiere': get_financial_data(),
        'repartition_installation': get_installation_data(),
        'meta': {
            'date_export': timezone.now().isoformat(),
            'total_interventions': Intervention.objects.count(),
            'total_clients': Client.objects.count(),
            'total_techniciens': Technicien.objects.count(),
            'revenu_total': Intervention.objects.filter(statut='terminee').aggregate(
                total=Sum('prix_intervention')
            )['total'] or 0,
        }
    }

    # Créer une réponse JSON en tant que fichier à télécharger
    from django.http import JsonResponse
    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="statistiques_solar_{timezone.now().date()}.json"'
    return response


@login_required
def export_excel(request):
    """Export des statistiques en Excel"""
    if hasattr(request.user, 'technicien'):
        return redirect('dashboard')

    # Créer un DataFrame pandas avec toutes les données
    import pandas as pd
    from django.http import HttpResponse

    # Créer un writer Excel
    output = pd.ExcelWriter('statistiques_solar.xlsx', engine='xlsxwriter')

    # Feuille 1: Interventions par mois
    df_interventions = pd.DataFrame(get_interventions_data())
    if not df_interventions.empty:
        df_interventions.to_excel(output, sheet_name='Interventions par mois', index=False)

    # Feuille 2: Répartition par type
    df_type = pd.DataFrame(get_type_data())
    if not df_type.empty:
        df_type.to_excel(output, sheet_name='Répartition par type', index=False)

    # Feuille 3: Techniciens actifs
    df_techniciens = pd.DataFrame(get_techniciens_data())
    if not df_techniciens.empty:
        df_techniciens.to_excel(output, sheet_name='Techniciens actifs', index=False)

    # Feuille 4: Clients sollicités
    df_clients = pd.DataFrame(get_clients_data())
    if not df_clients.empty:
        df_clients.to_excel(output, sheet_name='Clients sollicités', index=False)

    # Feuille 5: Évolution financière
    df_finances = pd.DataFrame(get_financial_data())
    if not df_finances.empty:
        df_finances.to_excel(output, sheet_name='Évolution financière', index=False)

    # Feuille 6: Répartition par installation
    df_installation = pd.DataFrame(get_installation_data())
    if not df_installation.empty:
        df_installation.to_excel(output, sheet_name='Répartition installation', index=False)

    output.close()

    # Lire le fichier Excel généré
    with open('statistiques_solar.xlsx', 'rb') as f:
        excel_data = f.read()

    # Créer la réponse HTTP
    response = HttpResponse(
        excel_data,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="statistiques_solar_{timezone.now().date()}.xlsx"'

    return response