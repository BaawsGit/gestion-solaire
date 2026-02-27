import requests
import json
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from interventions.models import Intervention
from django.db.models import Count, Avg, Q


class OllamaService:
    """Service pour interagir avec l'API Ollama"""

    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "gemma3:4b"  # ou "gemma3:4b" selon votre configuration

    def check_connection(self):
        """Vérifie si Ollama est accessible et quels modèles sont disponibles"""
        try:
            # Essayer d'accéder à l'API
            response = requests.get(f"{self.base_url}/api/tags", timeout=20)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model.get("name") for model in models]

                # Vérifier si notre modèle est disponible
                model_available = any(self.model_name in name for name in available_models)

                return {
                    'success': True,
                    'available': True,
                    'message': "Ollama est connecté",
                    'models': available_models,
                    'model_available': model_available,
                    'url': self.base_url,
                    'model': self.model_name
                }
            else:
                return {
                    'success': False,
                    'available': False,
                    'message': f"Erreur API Ollama: {response.status_code}"
                }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'available': False,
                'message': "Impossible de se connecter à Ollama"
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'available': False,
                'message': "Timeout: Ollama ne répond pas"
            }
        except Exception as e:
            return {
                'success': False,
                'available': False,
                'message': f"Erreur inattendue: {str(e)}"
            }

    def test_model(self):
        """Teste si le modèle peut générer une réponse simple"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": "Bonjour, peux-tu me dire 'OK' en une seule ligne?",
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message': "Modèle fonctionnel",
                    'response': result.get('response', '')
                }
            else:
                return {
                    'success': False,
                    'message': f"Erreur lors du test du modèle: {response.status_code}"
                }

        except Exception as e:
            return {
                'success': False,
                'message': f"Erreur lors du test: {str(e)}"
            }

    def generate_report_analysis(self, month, year, stats):
        """Génère une analyse IA basée sur les données fournies"""
        try:
            # Préparer le prompt avec le contexte
            prompt = self._create_report_prompt(month, year, stats)

            print(f"🔍 Envoi du prompt à Ollama ({len(prompt)} caractères)...")

            # Appeler l'API Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 800,  # Réduire la longueur de réponse
                        "num_ctx": 2048  # Réduire le contexte
                    }
                },
                timeout=180
            )

            print("✅ Réponse reçue d'Ollama")

            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '')

                # Nettoyer et structurer la réponse
                return self._parse_ai_response(analysis, stats)
            else:
                return {
                    'success': False,
                    'error': f"Erreur API Ollama: {response.status_code}",
                    'analysis': "Impossible de générer l'analyse IA."
                }


        except requests.exceptions.Timeout:
            print("⏰ Timeout Ollama - La réponse prend trop de temps")
            return {
                'success': False,
                'error': "Ollama met trop de temps à répondre. Essayez avec un modèle plus léger ou réduisez la période d'analyse.",
                'analysis': "Timeout lors de la génération de l'analyse."
            }

        except Exception as e:
            print(f"❌ Erreur Ollama: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': "Erreur lors de la génération de l'analyse."
            }

    def _create_report_prompt(self, month, year, stats):
        """Crée le prompt pour l'analyse du rapport"""

        # Formater le mois
        from datetime import datetime
        month_name = datetime.strptime(str(month), "%m").strftime("%B")

        prompt = f"""Tu es un analyste expert en maintenance solaire. Analyse ces données du mois de {month_name} {year} et fournis un rapport structuré.

    ## STATISTIQUES DU MOIS:
    - Période: {month_name} {year}
    - Total interventions: {stats.get('total_interventions', 0)}
    - Interventions terminées: {stats.get('completed_interventions', 0)}
    - Interventions en cours: {stats.get('ongoing_interventions', 0)}
    - Taux de réussite: {stats.get('success_rate', 0):.1f}%
    - Indice de performance interne (basé sur le taux de réussite): {stats.get('performance_score', 0):.1f}/10
    - Durée moyenne: {stats.get('avg_duration', 'N/A')}
    - Chiffre d'affaires total: {stats.get('total_revenue', 0):,.0f} FCFA

    ## IMPORTANT:
    - L'indice de performance est un indicateur INTERNE de l'entreprise, calculé à partir du taux de réussite
    - Ce n'est PAS un score de satisfaction client
    - Il mesure l'efficacité opérationnelle de l'entreprise

    ## RÉPARTITION PAR TYPE:
    {self._format_type_stats(stats.get('interventions_by_type', []))}

    ## PERFORMANCE DES TECHNICIENS:
    {self._format_technician_stats(stats.get('top_technicians', []))}

    ## TÂCHE:
    Génère un rapport d'analyse complet avec les sections suivantes:

    1. **RÉSUMÉ EXÉCUTIF** (2-3 phrases maximum)
    2. **RECOMMANDATIONS CLÉS** (liste numérotée de 1-3 recommandations concrètes)
    3. **ANALYSE TECHNIQUE** (analyse détaillée des pannes, pièces remplacées, tendances)
    4. **MAINTENANCE PRÉDICTIVE** (prédictions pour les mois à venir basées sur les données)

    Ton: Professionnel, factuel, constructif.
    Format: Utilise des balises HTML simples <p>, <ul>, <li>, <strong>, <em>.
    Ne mets pas de code markdown (```), utilise uniquement du HTML."""

        return prompt

    def _format_type_stats(self, type_stats):
        """Formate les statistiques par type"""
        if not type_stats:
            return "Aucune donnée"

        lines = []
        for item in type_stats:
            lines.append(f"- {item['type_intervention']}: {item['count']} interventions")
        return "\n".join(lines)

    def _format_technician_stats(self, tech_stats):
        """Formate les statistiques des techniciens"""
        if not tech_stats:
            return "Aucune donnée"

        lines = []
        for item in tech_stats:
            lines.append(f"- {item['technicien__nom']}: {item['intervention_count']} interventions")
        return "\n".join(lines)

    def _parse_ai_response(self, response, stats):
        """Nettoie et structure la réponse de l'IA"""
        # Retirer les éventuels marqueurs de code
        response = response.replace("```html", "").replace("```", "").strip()

        # Séparer les sections
        sections = {
            'summary': '',
            'recommendations': '',
            'technical_analysis': '',
            'predictive_maintenance': ''
        }

        # Simple parsing par sections (améliorable)
        lines = response.split('\n')
        current_section = None

        for line in lines:
            line_lower = line.lower()
            if 'résumé' in line_lower or 'executif' in line_lower:
                current_section = 'summary'
            elif 'recommandation' in line_lower:
                current_section = 'recommendations'
            elif 'technique' in line_lower:
                current_section = 'technical_analysis'
            elif 'prédictive' in line_lower:
                current_section = 'predictive_maintenance'

            if current_section and line.strip():
                sections[current_section] += line + '\n'

        # Si le parsing a échoué, mettre tout dans le résumé
        if not any(sections.values()):
            sections['summary'] = response

        return {
            'success': True,
            'sections': sections,
            'raw_response': response,
            'timestamp': datetime.now().isoformat()
        }