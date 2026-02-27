# interventions/views_pdf.py
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from .models import Intervention
import io
from datetime import datetime
from django.conf import settings
import os
import qrcode
from django.urls import reverse
from io import BytesIO
import tempfile
# Ajoutez cet import en haut du fichier :
from reportlab.platypus import PageBreak


@login_required
def intervention_pdf(request, pk):
    """Génère un PDF pour les détails d'une intervention"""

    # Récupérer l'intervention
    intervention = get_object_or_404(Intervention, pk=pk)

    # Vérifier les permissions
    if hasattr(request.user, 'technicien'):
        if intervention.technicien != request.user.technicien:
            from django.contrib import messages
            messages.error(request, 'Accès non autorisé à cette intervention.')
            from django.shortcuts import redirect
            return redirect('interventions:list')

    # Créer un objet BytesIO pour stocker le PDF
    buffer = io.BytesIO()

    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=30,
        bottomMargin=50
    )

    # Styles
    styles = getSampleStyleSheet()

    # Style personnalisé pour le titre principal
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=5,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1
    )

    # Style pour le titre du rapport
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=15,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1
    )

    # Style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=20,
        textColor=colors.HexColor('#2FD1FA'),
        fontName='Helvetica-Bold'
    )

    # Contenu du PDF
    story = []

    # ==================== LOGO ====================
    # Essayer plusieurs chemins pour le logo
    logo_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'images', 'solar_logo.png'),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'solar_logo.png'),
        os.path.join(settings.STATIC_ROOT, 'images', 'solar_logo.png') if settings.STATIC_ROOT else None,
    ]

    # Chercher le logo dans les chemins statiques
    logo_found = False
    for path in logo_paths:
        if path and os.path.exists(path):
            try:
                logo = Image(path, width=2.5 * inch, height=1 * inch)
                story.append(logo)
                story.append(Spacer(1, 0.1 * inch))
                logo_found = True
                break
            except:
                continue

    if not logo_found:
        # Logo de secours (texte)
        story.append(Paragraph("SOLAR MAINTENANCE", main_title_style))
        story.append(Paragraph("Gestion des interventions solaires", ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6c757d'),
            alignment=1,
            spaceAfter=15
        )))

    # Titre du document
    story.append(Paragraph("RAPPORT D'INTERVENTION", report_title_style))
    story.append(Spacer(1, 0.3 * inch))

    # ==================== INFORMATIONS GÉNÉRALES ====================
    story.append(Paragraph("INFORMATIONS GÉNÉRALES", subtitle_style))

    data_general = [
        ['ID Intervention:', f"#{intervention.id}"],
        ['Date d\'intervention:', intervention.date_intervention.strftime('%d/%m/%Y')],
        ['Type d\'intervention:', intervention.get_type_intervention_display()],
        ['Statut:', intervention.get_statut_display()],
        ['Durée totale:', intervention.get_duree_formatee()],  # AJOUTER CETTE LIGNE
        ['Prix total:', f"{intervention.prix_intervention:,.0f} FCFA".replace(',', ' ')],
    ]

    table_general = Table(data_general, colWidths=[2 * inch, 3.5 * inch])
    table_general.setStyle(TableStyle([
        # Colonne gauche (labels) - fond gris clair, texte en gras
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#212529')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 10),

        # Colonne droite (valeurs) - fond blanc
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#212529')),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 10),

        # Bordures
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))

    story.append(table_general)
    story.append(Spacer(1, 0.4 * inch))

    # ==================== PERSONNES CONCERNÉES ====================
    story.append(Paragraph("PERSONNES CONCERNÉES", subtitle_style))

    data_personnes = [
        ['Client:', intervention.client.nom],
        ['Téléphone:', intervention.client.telephone if intervention.client.telephone else 'Non renseigné'],
        ['Email:', intervention.client.email if intervention.client.email else 'Non renseigné'],
        ['Adresse:', intervention.client.adresse if intervention.client.adresse else 'Non renseignée'],
        ['Type installation:', intervention.client.type_installation],
    ]

    if intervention.technicien:
        data_personnes.append(['Technicien assigné:', intervention.technicien.nom])
        if intervention.technicien.telephone:
            data_personnes.append(['Tel technicien:', intervention.technicien.telephone])

    if intervention.fournisseur:
        data_personnes.append(['Fournisseur:', intervention.fournisseur.nom])

    # KVA
    try:
        kva = intervention.client.extraire_kva()
        if kva:
            data_personnes.append(['Puissance (KVA):', f"{kva} KVA"])
    except:
        pass

    table_personnes = Table(data_personnes, colWidths=[2 * inch, 3.5 * inch])
    table_personnes.setStyle(TableStyle([
        # Colonne gauche (labels) - fond gris clair, texte en gras
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#212529')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 10),

        # Colonne droite (valeurs) - fond blanc
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#212529')),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 0), (1, -1), 10),

        # Bordures
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))

    story.append(table_personnes)
    story.append(Spacer(1, 0.4 * inch))
    # Dans le code, avant "Détails Techniques" :
    story.append(PageBreak())  # Force une nouvelle page

    # ==================== DÉTAILS TECHNIQUES ====================
    story.append(Paragraph("DÉTAILS TECHNIQUES", subtitle_style))

    details_content = []

    # Panne constatée
    if intervention.panne_constatee:
        details_content.append(Paragraph("<b>Panne constatée:</b>", styles['Normal']))
        details_content.append(Paragraph(intervention.panne_constatee, ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            leftIndent=15,
            spaceAfter=10
        )))

    # Pièces remplacées
    if intervention.pieces_remplacees:
        details_content.append(Paragraph("<b>Pièces remplacées:</b>", styles['Normal']))
        details_content.append(Paragraph(intervention.pieces_remplacees, ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            leftIndent=15,
            spaceAfter=10
        )))

    # Notes
    if intervention.notes:
        details_content.append(Paragraph("<b>Notes:</b>", styles['Normal']))
        details_content.append(Paragraph(intervention.notes, ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            leftIndent=15,
            spaceAfter=10
        )))

    if details_content:
        for item in details_content:
            story.append(item)
    else:
        story.append(Paragraph("Aucun détail technique renseigné.", styles['Normal']))

    story.append(Spacer(1, 0.6 * inch))

    # ==================== SIGNATURE ====================
    # Signature numérique (image)
    signature_found = False
    signature_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'images', 'signature.png'),
        os.path.join(settings.BASE_DIR, 'static', 'images', 'signature_admin.png'),
    ]

    for sig_path in signature_paths:
        if sig_path and os.path.exists(sig_path):
            try:
                signature_img = Image(sig_path, width=1.5 * inch, height=1.5 * inch)
                # Aligner à droite
                signature_table = Table([[signature_img]], colWidths=[7.5 * inch])
                signature_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
                ]))
                story.append(signature_table)
                story.append(Spacer(1, 0.05 * inch))
                signature_found = True
                break
            except:
                continue

    if not signature_found:
        # Ligne de signature textuelle
        story.append(Paragraph(
            "_____________________________",
            ParagraphStyle('SignatureLine', parent=styles['Normal'], fontSize=12, alignment=2)
        ))
        story.append(Spacer(1, 0.05 * inch))

    # Nom de l'admin
    admin_name = request.user.get_full_name() or request.user.username
    signature_text = Paragraph(
        f"<b>{admin_name}</b><br/>Administrateur Solar Maintenance",
        ParagraphStyle(
            'Signature',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            alignment=2,
            spaceBefore=2
        )
    )
    story.append(signature_text)
    story.append(Spacer(1, 0.1 * inch))

    # Date de génération
    date_emission = datetime.now().strftime("%d/%m/%Y à %H:%M")
    date_text = Paragraph(
        f"Document généré le {date_emission}",
        ParagraphStyle(
            'Date',
            parent=styles['Italic'],
            fontSize=8,
            textColor=colors.grey,
            alignment=2
        )
    )
    story.append(date_text)

    story.append(Spacer(1, 0.4 * inch))

    # ==================== QR CODE - CORRIGÉ ====================
    # Variable pour stocker le chemin du fichier temporaire
    qr_temp_file = None

    try:
        # Construire l'URL absolue vers l'intervention
        if request.is_secure():
            protocol = 'https://'
        else:
            protocol = 'http://'

        host = request.get_host()
        intervention_url = f"{protocol}{host}{reverse('interventions:detail', args=[intervention.pk])}"

        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=3,
        )
        qr.add_data(intervention_url)
        qr.make(fit=True)

        # Créer une image du QR code
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Créer un fichier temporaire pour le QR code
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            qr_img.save(tmp_file.name)
            qr_temp_file = tmp_file.name

        # Ajouter le QR code au PDF à partir du fichier
        qr_image = Image(qr_temp_file, width=1 * inch, height=1 * inch)

        # Créer un tableau pour aligner QR code et texte
        qr_data = [
            [qr_image, Paragraph(
                f"<b>Scanner pour voir les détails</b><br/>ID: #{intervention.id}<br/>{intervention.date_intervention.strftime('%d/%m/%Y')}",
                ParagraphStyle('QRText', parent=styles['Normal'], fontSize=8)
            )]
        ]

        qr_table = Table(qr_data, colWidths=[1 * inch, 5.5 * inch])
        qr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ]))

        story.append(qr_table)

    except Exception as e:
        # Si le QR code échoue, ignorer silencieusement
        print(f"Erreur QR code: {e}")
        # Optionnel: ajouter un message texte à la place
        story.append(Paragraph(
            f"<i>URL de l'intervention:</i><br/>{intervention_url}",
            ParagraphStyle('URL', parent=styles['Normal'], fontSize=8)
        ))

    # Construire le PDF
    doc.build(story)

    # Nettoyer le fichier temporaire du QR code APRÈS la construction du PDF
    if qr_temp_file and os.path.exists(qr_temp_file):
        try:
            os.unlink(qr_temp_file)
        except:
            pass  # Ignorer les erreurs de suppression

    # Récupérer la valeur du buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_intervention_{intervention.id}.pdf"'
    response.write(pdf)

    return response