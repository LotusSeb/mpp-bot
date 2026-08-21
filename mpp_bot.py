"""
MPP Ligue 1 Bot - Automatisation des pronostics de score
Exécution : Chaque lundi à 9h (via GitHub Actions)
"""

import os
import json
from datetime import datetime, timedelta
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

# Configuration
LOGIN = os.environ.get('MPP_LOGIN', 'sebsdp@yahoo.fr')
PASSWORD = os.environ.get('MPP_PASSWORD', 'Football99@')
MPP_URL = 'https://www.mpp.fr'
print(f"🔗 URL MPP configurée: {MPP_URL}")

class LiguePredictor:
    """Récupère les stats Ligue 1 et génère les prédictions"""
    
    def __init__(self):
        self.api_url = 'https://api.football-data.org/v4'
        self.api_token = os.environ.get('FOOTBALL_API_TOKEN', '')
        self.matchs = []
        self.team_stats = {}  # Stats des 7 derniers matchs par équipe
    
    def get_next_7_days_matchs(self):
        """Récupère les matchs Ligue 1 des 7 prochains jours"""
        try:
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
            # Appel API football-data.org (gratuit et fiable)
            headers = {'X-Auth-Token': self.api_token}
            url = f'{self.api_url}/competitions/FL1/matches'
            params = {
                'status': 'SCHEDULED',
                'dateFrom': today.strftime('%Y-%m-%d'),
                'dateTo': next_week.strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.matchs = data.get('matches', [])
                print(f"✅ {len(self.matchs)} matchs trouvés pour la semaine")
                return True
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur récupération matchs: {e}")
            return False
    
    def get_team_last_7_matches(self, team_id):
        """Récupère les 7 derniers matchs d'une équipe"""
        try:
            headers = {'X-Auth-Token': self.api_token}
            url = f'{self.api_url}/teams/{team_id}/matches'
            params = {
                'status': 'FINISHED',
                'limit': 7
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('matches', [])
            else:
                print(f"⚠️ Impossible de récupérer les matchs pour équipe {team_id}")
                return []
        except Exception as e:
            print(f"⚠️ Erreur récupération matchs équipe: {e}")
            return []
    
    def calculate_team_stats(self, team_id, team_name):
        """Calcule les stats d'une équipe basées sur ses 7 derniers matchs"""
        if team_name in self.team_stats:
            return self.team_stats[team_name]
        
        matches = self.get_team_last_7_matches(team_id)
        
        if not matches:
            # Valeurs par défaut si pas d'historique
            return {
                'goals_for': 1.5,
                'goals_against': 1.2,
                'matches_played': 0
            }
        
        total_goals_for = 0
        total_goals_against = 0
        
        for match in matches:
            if match['homeTeam']['id'] == team_id:
                # Match à domicile
                total_goals_for += match['score']['fullTime']['home']
                total_goals_against += match['score']['fullTime']['away']
            else:
                # Match à l'extérieur
                total_goals_for += match['score']['fullTime']['away']
                total_goals_against += match['score']['fullTime']['home']
        
        avg_goals_for = total_goals_for / len(matches) if matches else 1.5
        avg_goals_against = total_goals_against / len(matches) if matches else 1.2
        
        stats = {
            'goals_for': avg_goals_for,
            'goals_against': avg_goals_against,
            'matches_played': len(matches)
        }
        
        self.team_stats[team_name] = stats
        return stats
    
    def predict_score(self, match_data):
        """Génère une prédiction de score basée sur:
        - 80% les 7 derniers matchs
        - 20% l'historique H2H des 5 dernières années
        """
        try:
            home_team = match_data['homeTeam']['name']
            away_team = match_data['awayTeam']['name']
            home_team_id = match_data['homeTeam']['id']
            away_team_id = match_data['awayTeam']['id']
            
            # === PART 1: Stats des 7 derniers matchs (80% du poids) ===
            home_stats = self.calculate_team_stats(home_team_id, home_team)
            away_stats = self.calculate_team_stats(away_team_id, away_team)
            
            # Prédiction basée sur les 7 derniers matchs
            pred_home_7d = (home_stats['goals_for'] + away_stats['goals_against']) / 2
            pred_away_7d = (away_stats['goals_for'] + home_stats['goals_against']) / 2
            
            # === PART 2: Stats H2H des 5 dernières années (20% du poids) ===
            h2h_stats = self.get_head_to_head_stats(home_team_id, away_team_id, home_team, away_team)
            
            if h2h_stats and h2h_stats['matches_played'] > 0:
                # Utilise les stats H2H
                pred_home_h2h = h2h_stats['home_goals']
                pred_away_h2h = h2h_stats['away_goals']
                
                # Fusion: 80% récent + 20% historique
                home_goals = (0.80 * pred_home_7d) + (0.20 * pred_home_h2h)
                away_goals = (0.80 * pred_away_7d) + (0.20 * pred_away_h2h)
                
                h2h_info = f" (H2H: {h2h_stats['matches_played']} matchs)"
            else:
                # Pas de H2H trouvé, utilise juste les 7 derniers matchs
                home_goals = pred_home_7d
                away_goals = pred_away_7d
                h2h_info = " (pas de H2H)"
            
            # Arrondit à l'entier le plus proche
            home_goals = round(home_goals)
            away_goals = round(away_goals)
            
            # Minimum 0 buts
            home_goals = max(0, home_goals)
            away_goals = max(0, away_goals)
            
            return {
                'match_id': match_data['id'],
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'kickoff': match_data['utcDate'],
                'home_stats': home_stats,
                'away_stats': away_stats,
                'h2h_stats': h2h_stats,
                'h2h_info': h2h_info
            }
        except Exception as e:
            print(f"❌ Erreur prédiction: {e}")
            return None
    
    def get_head_to_head_stats(self, home_team_id, away_team_id, home_team_name, away_team_name):
        """Récupère les stats H2H sur les 5 dernières années"""
        try:
            headers = {'X-Auth-Token': self.api_token}
            url = f'{self.api_url}/teams/{home_team_id}/matches'
            params = {
                'status': 'FINISHED',
                'limit': 100  # Récupère beaucoup de matchs pour trouver les H2H
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                return None
            
            matches = response.json().get('matches', [])
            h2h_matches = []
            
            # Filtre les matchs H2H (home_team vs away_team)
            for match in matches:
                # Vérifier que c'est un match entre les deux équipes
                is_h2h = (
                    (match['homeTeam']['id'] == home_team_id and match['awayTeam']['id'] == away_team_id) or
                    (match['homeTeam']['id'] == away_team_id and match['awayTeam']['id'] == home_team_id)
                )
                
                if is_h2h:
                    h2h_matches.append(match)
            
            if not h2h_matches:
                return None
            
            # Calcule les stats du home_team dans les matchs H2H
            home_goals_h2h = 0
            away_goals_h2h = 0
            
            for match in h2h_matches:
                if match['homeTeam']['id'] == home_team_id:
                    # home_team joue à domicile
                    home_goals_h2h += match['score']['fullTime']['home']
                    away_goals_h2h += match['score']['fullTime']['away']
                else:
                    # home_team joue en extérieur
                    home_goals_h2h += match['score']['fullTime']['away']
                    away_goals_h2h += match['score']['fullTime']['home']
            
            avg_home_goals_h2h = home_goals_h2h / len(h2h_matches)
            avg_away_goals_h2h = away_goals_h2h / len(h2h_matches)
            
            stats = {
                'home_goals': avg_home_goals_h2h,
                'away_goals': avg_away_goals_h2h,
                'matches_played': len(h2h_matches)
            }
            
            return stats
        except Exception as e:
            print(f"⚠️ Erreur récupération H2H {home_team_name} vs {away_team_name}: {e}")
            return None
    
    def generate_predictions(self):
        """Génère les prédictions pour tous les matchs"""
        predictions = []
        for match in self.matchs:
            pred = self.predict_score(match)
            if pred:
                predictions.append(pred)
        return predictions


class MPPBot:
    """Bot Selenium pour remplir les pronostics sur MPP"""
    
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.driver = None
    
    def setup_driver(self):
        """Configure le navigateur Chromium pour GitHub Actions"""
        chrome_options = Options()
        
        # Pour GitHub Actions (headless, pas d'affichage)
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Désactiver les notifications et popups
        prefs = {"profile.default_content_settings.popups": 0}
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Utilise Chromium du système (installé via apt-get)
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        
        # Utilise le chromedriver du système
        service = Service('/usr/bin/chromedriver')
        
        try:
            print("🔄 Initialisation du navigateur Chromium...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            # Important: définir les timeouts globaux
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            print("✅ Navigateur Chromium configuré")
        except Exception as e:
            print(f"❌ Erreur Chromium: {e}")
            raise
    
    def close_ads(self):
        """Ferme les pop-ups publicitaires et overlays"""
        try:
            # Liste des sélecteurs courants pour fermer les pubs
            ad_close_selectors = [
                # Boutons de fermeture standards
                'button[aria-label="Close"]',
                'button[class*="close"]',
                'button[class*="ad-close"]',
                'button[class*="modal-close"]',
                'button[title="Close"]',
                'button[title="Fermer"]',
                'a[class*="close"]',
                'a[class*="ad-close"]',
                '.ad-close-btn',
                '.close-ad',
                '.modal-close',
                '[class*="advertisement"] button',
                '[id*="ad-close"]',
                'svg[class*="close-icon"]',
            ]
            
            for selector in ad_close_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            print(f"🔴 Fermeture pub: {selector}")
                            element.click()
                            time.sleep(1)
                except:
                    pass
            
            # Attendre que les overlays disparaissent
            time.sleep(2)
            
            # Fermer les iframes publicitaires
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    if 'ad' in iframe.get_attribute('id').lower() or 'ad' in iframe.get_attribute('class').lower():
                        self.driver.execute_script("arguments[0].remove();", iframe)
                        print("🔴 iframe pub supprimée")
            except:
                pass
            
            print("✅ Pubs fermées")
            return True
        except Exception as e:
            print(f"⚠️ Erreur lors de la fermeture des pubs: {e}")
            return True  # Continue malgré tout
    
    def login_mpp(self):
        """Se connecte à MPP"""
        try:
            print("🔄 Accès à la page de login MPP...")
            self.driver.get(f'{MPP_URL}/login')
            time.sleep(5)  # Attendre le chargement
            
            # Ferme les pubs avant de se connecter
            self.close_ads()
            time.sleep(2)
            
            print("🔄 Recherche du champ email...")
            # À adapter selon la structure HTML réelle de MPP
            email_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, 'email'))
            )
            time.sleep(1)
            email_field.send_keys(self.login)
            print("✅ Email saisi")
            
            # Ferme les pubs qui pourraient apparaître
            self.close_ads()
            time.sleep(2)
            
            print("🔄 Recherche du champ password...")
            password_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, 'password'))
            )
            time.sleep(1)
            password_field.send_keys(self.password)
            print("✅ Password saisi")
            
            print("🔄 Clic sur le bouton login...")
            login_btn = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            login_btn.click()
            time.sleep(7)  # Attendre la redirection après login
            
            # Ferme les pubs après connexion
            self.close_ads()
            time.sleep(2)
            
            print("✅ Connecté à MPP")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion MPP: {e}")
            return False
    
    def fill_predictions(self, predictions):
        """Remplit les pronostics sur MPP"""
        try:
            # Accès à la page des pronostics
            print("🔄 Accès à la page des pronostics...")
            self.driver.get(f'{MPP_URL}/pronostics')
            time.sleep(5)
            
            # Ferme les pubs au chargement
            self.close_ads()
            time.sleep(2)
            
            for pred in predictions:
                print(f"📝 Remplissage: {pred['home_team']} {pred['home_goals']}-{pred['away_goals']} {pred['away_team']}")
                
                # À adapter selon la structure réelle de MPP
                # Cherche les champs de score pour ce match
                try:
                    # Ferme les pubs avant chaque remplissage
                    self.close_ads()
                    time.sleep(1)
                    
                    # Exemple: trouver les inputs par le nom du match
                    home_input = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, f"//input[@data-team='{pred['home_team']}'][@data-type='home']"))
                    )
                    away_input = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, f"//input[@data-team='{pred['away_team']}'][@data-type='away']"))
                    )
                    
                    # Scroll jusqu'aux inputs pour éviter les overlays
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", home_input)
                    time.sleep(2)
                    
                    home_input.clear()
                    home_input.send_keys(str(pred['home_goals']))
                    
                    away_input.clear()
                    away_input.send_keys(str(pred['away_goals']))
                    
                    time.sleep(1)
                except Exception as e:
                    print(f"⚠️ Erreur remplissage {pred['home_team']}: {e}")
            
            # Ferme les pubs avant de soumettre
            self.close_ads()
            time.sleep(2)
            
            # Soumet les pronostics
            print("🔄 Soumission des pronostics...")
            submit_btn = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[class*="submit"]'))
            )
            submit_btn.click()
            time.sleep(5)
            print("✅ Pronostics soumis!")
            return True
        except Exception as e:
            print(f"❌ Erreur remplissage pronostics: {e}")
            return False
    
    def close(self):
        """Ferme le navigateur"""
        if self.driver:
            self.driver.quit()


def main():
    """Fonction principale"""
    print("=" * 50)
    print("🚀 MPP Bot Ligue 1 - Exécution", datetime.now())
    print("=" * 50)
    
    # Test de connectivité
    print("🔍 Test de connectivité au site MPP...")
    try:
        response = requests.get(MPP_URL, timeout=10)
        print(f"✅ MPP accessible (status: {response.status_code})")
    except Exception as e:
        print(f"⚠️ Attention: MPP peut être inaccessible: {e}")
    
    # Étape 1: Récupérer les matchs
    predictor = LiguePredictor()
    if not predictor.get_next_7_days_matchs():
        print("❌ Impossible de récupérer les matchs")
        return False
    
    # Étape 2: Générer les prédictions
    predictions = predictor.generate_predictions()
    if not predictions:
        print("❌ Aucune prédiction générée")
        return False
    
    print(f"\n📊 {len(predictions)} prédictions générées:")
    for pred in predictions:
        home_avg = pred['home_stats']['goals_for']
        away_avg = pred['away_stats']['goals_for']
        h2h_info = pred.get('h2h_info', '')
        print(f"  • {pred['home_team']} ({home_avg:.1f}g) {pred['home_goals']}-{pred['away_goals']} ({away_avg:.1f}g) {pred['away_team']}{h2h_info}")
    
    # Étape 3: Se connecter à MPP et remplir
    bot = MPPBot(LOGIN, PASSWORD)
    try:
        bot.setup_driver()
        if bot.login_mpp():
            bot.fill_predictions(predictions)
        else:
            print("❌ Impossible de se connecter à MPP")
            return False
    finally:
        bot.close()
    
    print("\n" + "=" * 50)
    print("✅ Exécution terminée avec succès!")
    print("=" * 50)
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
