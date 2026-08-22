"""
MPP Ligue 1 Bot - Automatisation des pronostics de score
Version simplifiée et optimisée
"""

import os
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
MPP_URL = 'https://mpp.football'

class LiguePredictor:
    """Récupère les stats Ligue 1 et génère les prédictions"""
    
    def __init__(self):
        self.api_url = 'https://api.football-data.org/v4'
        self.api_token = os.environ.get('FOOTBALL_API_TOKEN', '')
        self.matchs = []
        self.team_stats = {}
    
    def get_next_7_days_matchs(self):
        """Récupère les matchs Ligue 1 des 7 prochains jours"""
        try:
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
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
            params = {'status': 'FINISHED', 'limit': 7}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('matches', [])
            else:
                return []
        except:
            return []
    
    def calculate_team_stats(self, team_id, team_name):
        """Calcule les stats d'une équipe basées sur ses 7 derniers matchs"""
        if team_name in self.team_stats:
            return self.team_stats[team_name]
        
        matches = self.get_team_last_7_matches(team_id)
        
        if not matches:
            return {'goals_for': 1.5, 'goals_against': 1.2, 'matches_played': 0}
        
        total_goals_for = 0
        total_goals_against = 0
        
        for match in matches:
            if match['homeTeam']['id'] == team_id:
                total_goals_for += match['score']['fullTime']['home']
                total_goals_against += match['score']['fullTime']['away']
            else:
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
        """Génère une prédiction de score"""
        try:
            home_team = match_data['homeTeam']['name']
            away_team = match_data['awayTeam']['name']
            home_team_id = match_data['homeTeam']['id']
            away_team_id = match_data['awayTeam']['id']
            
            home_stats = self.calculate_team_stats(home_team_id, home_team)
            away_stats = self.calculate_team_stats(away_team_id, away_team)
            
            home_goals = (home_stats['goals_for'] + away_stats['goals_against']) / 2
            away_goals = (away_stats['goals_for'] + home_stats['goals_against']) / 2
            
            home_goals = round(max(0, home_goals))
            away_goals = round(max(0, away_goals))
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'away_goals': away_goals,
            }
        except Exception as e:
            print(f"❌ Erreur prédiction: {e}")
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
    
    def close_ads(self):
        """Ferme les pop-ups publicitaires"""
        try:
            ad_close_selectors = [
                'button[aria-label="Close"]',
                'button[class*="close"]',
                'button[class*="ad-close"]',
                '.ad-close-btn',
                '[id*="ad-close"]',
            ]
            
            for selector in ad_close_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(0.5)
                except:
                    pass
            
            # Supprime les iframes pub
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    if 'ad' in (iframe.get_attribute('id') or '').lower():
                        self.driver.execute_script("arguments[0].remove();", iframe)
            except:
                pass
        except:
            pass
    
    def setup_driver(self):
        """Configure le navigateur Chromium"""
        chrome_options = Options()
        
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        prefs = {"profile.default_content_settings.popups": 0}
        chrome_options.add_experimental_option("prefs", prefs)
        
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        service = Service('/usr/bin/chromedriver')
        
        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
            print("✅ Navigateur configuré")
        except Exception as e:
            print(f"❌ Erreur navigateur: {e}")
            raise
    
    def login_mpp(self):
        """Se connecte à MPP"""
        try:
            print("🔄 Accès à MPP...")
            self.driver.get(f'{MPP_URL}/')
            time.sleep(3)
            
            # Ferme les pubs
            self.close_ads()
            time.sleep(1)
            
            print("🔄 Recherche du bouton 'Se connecter'...")
            # Essaie plusieurs façons de trouver le bouton
            connect_btn = None
            selectors = [
                (By.XPATH, "//button[contains(text(), 'Se connecter')]"),
                (By.XPATH, "//*[text()='Se connecter']"),
                (By.XPATH, "//button[contains(., 'Se connecter')]"),
            ]
            
            for selector in selectors:
                try:
                    connect_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    print(f"✅ Trouvé avec: {selector}")
                    break
                except:
                    continue
            
            if not connect_btn:
                print("❌ Bouton 'Se connecter' non trouvé")
                # Affiche tous les boutons
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                print(f"Boutons trouvés: {len(buttons)}")
                for btn in buttons[:5]:
                    print(f"  - '{btn.text}'")
                raise Exception("Bouton 'Se connecter' introuvable")
            
            print("🔄 Clic sur 'Se connecter'...")
            connect_btn.click()
            print("🔄 Attente de l'ouverture du formulaire...")
            time.sleep(5)
            
            print("🔄 Saisie identifiants...")
            # Cherche le champ username (Auth0)
            username_field = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            username_field.send_keys(self.login)
            
            # Cherche le champ password
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)
            
            # Cherche le bouton submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_btn.click()
            
            print("🔄 Attente de la connexion...")
            time.sleep(5)
            
            print("✅ Connecté à MPP")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    def fill_predictions(self, predictions):
        """Remplit les pronostics"""
        try:
            self.close_ads()
            time.sleep(1)

            print("🔄 Recherche des champs de score...")
            
            # Trouve tous les inputs sur la page
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            
            # Filtre les inputs de type nombre/texte visibles
            score_inputs = []
            for inp in all_inputs:
                try:
                    if inp.is_displayed():
                        score_inputs.append(inp)
                except:
                    pass
            
            print(f"📊 {len(score_inputs)} champs trouvés")
            
            # Remplit par paires (home, away)
            for idx, pred in enumerate(predictions):
                input_idx = idx * 2
                
                if input_idx + 1 < len(score_inputs):
                    print(f"📝 {pred['home_team']} {pred['home_goals']}-{pred['away_goals']} {pred['away_team']}")
                    
                    try:
                        score_inputs[input_idx].clear()
                        score_inputs[input_idx].send_keys(str(pred['home_goals']))
                        time.sleep(0.3)
                        
                        score_inputs[input_idx + 1].clear()
                        score_inputs[input_idx + 1].send_keys(str(pred['away_goals']))
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"⚠️ Erreur: {e}")
            
            # Cherche le bouton de soumission
            print("🔄 Soumission...")
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Valider')]")
            except:
                try:
                    submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Soumettre')]")
                except:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            
            submit_btn.click()
            time.sleep(2)
            print("✅ Pronostics soumis!")
            return True
        except Exception as e:
            print(f"❌ Erreur remplissage: {e}")
            return False
    
    def close(self):
        """Ferme le navigateur"""
        if self.driver:
            self.driver.quit()


def main():
    """Fonction principale"""
    print("=" * 50)
    print("🚀 MPP Bot Ligue 1")
    print("=" * 50)
    
    # Récupère les matchs
    predictor = LiguePredictor()
    if not predictor.get_next_7_days_matchs():
        return False
    
    # Génère les prédictions
    predictions = predictor.generate_predictions()
    if not predictions:
        print("❌ Aucune prédiction")
        return False
    
    print(f"\n📊 Prédictions générées:")
    for pred in predictions:
        print(f"  • {pred['home_team']} {pred['home_goals']}-{pred['away_goals']} {pred['away_team']}")
    
    # Se connecte et remplit
    bot = MPPBot(LOGIN, PASSWORD)
    try:
        bot.setup_driver()
        if bot.login_mpp():
            bot.fill_predictions(predictions)
        else:
            return False
    finally:
        bot.close()
    
    print("\n" + "=" * 50)
    print("✅ Succès!")
    print("=" * 50)
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
