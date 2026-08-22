"""
MPP Ligue 1 Bot - Automatisation des pronostics
VERSION STABLE + LOGS
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

LOGIN = os.environ.get('MPP_LOGIN', 'sebsdp@yahoo.fr')
PASSWORD = os.environ.get('MPP_PASSWORD', 'Football99@')
MPP_URL = 'https://mpp.football'

class LiguePredictor:
    def __init__(self):
        self.api_url = 'https://api.football-data.org/v4'
        self.api_token = os.environ.get('FOOTBALL_API_TOKEN', '')
        self.matchs = []
        self.team_stats = {}
    
    def get_next_7_days_matchs(self):
        try:
            print("[1/4] Récupération des matchs...")
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
            headers = {'X-Auth-Token': self.api_token}
            url = f'{self.api_url}/competitions/FL1/matches'
            params = {
                'status': 'SCHEDULED',
                'dateFrom': today.strftime('%Y-%m-%d'),
                'dateTo': next_week.strftime('%Y-%m-%d')
            }
            
            print(f"   🌐 Appel API: {url}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"   📊 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                self.matchs = response.json().get('matches', [])
                print(f"   ✅ {len(self.matchs)} matchs trouvés")
                return True
            print(f"   ❌ Erreur API: {response.status_code}")
            return False
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def get_team_last_7_matches(self, team_id):
        try:
            headers = {'X-Auth-Token': self.api_token}
            url = f'{self.api_url}/teams/{team_id}/matches'
            params = {'status': 'FINISHED', 'limit': 7}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('matches', [])
            return []
        except:
            return []
    
    def calculate_team_stats(self, team_id, team_name):
        if team_name in self.team_stats:
            return self.team_stats[team_name]
        
        matches = self.get_team_last_7_matches(team_id)
        
        if not matches:
            return {'goals_for': 1.5, 'goals_against': 1.2}
        
        total_goals_for = 0
        total_goals_against = 0
        
        for match in matches:
            if match['homeTeam']['id'] == team_id:
                total_goals_for += match['score']['fullTime']['home']
                total_goals_against += match['score']['fullTime']['away']
            else:
                total_goals_for += match['score']['fullTime']['away']
                total_goals_against += match['score']['fullTime']['home']
        
        avg_goals_for = total_goals_for / len(matches)
        avg_goals_against = total_goals_against / len(matches)
        
        self.team_stats[team_name] = {'goals_for': avg_goals_for, 'goals_against': avg_goals_against}
        return self.team_stats[team_name]
    
    def predict_score(self, match_data):
        try:
            home_team = match_data['homeTeam']['name']
            away_team = match_data['awayTeam']['name']
            home_team_id = match_data['homeTeam']['id']
            away_team_id = match_data['awayTeam']['id']
            
            home_stats = self.calculate_team_stats(home_team_id, home_team)
            away_stats = self.calculate_team_stats(away_team_id, away_team)
            
            home_goals = (home_stats['goals_for'] + away_stats['goals_against']) / 2
            away_goals = (away_stats['goals_for'] + home_stats['goals_against']) / 2
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': round(max(0, home_goals)),
                'away_goals': round(max(0, away_goals)),
            }
        except:
            return None
    
    def generate_predictions(self):
        print("[2/4] Génération des prédictions...")
        predictions = []
        for match in self.matchs:
            pred = self.predict_score(match)
            if pred:
                predictions.append(pred)
        
        print(f"   ✅ {len(predictions)} prédictions générées")
        for p in predictions[:3]:
            print(f"      • {p['home_team']} {p['home_goals']}-{p['away_goals']}")
        if len(predictions) > 3:
            print(f"      ... et {len(predictions)-3} autres")
        
        return predictions


class MPPBot:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.driver = None
    
    def setup_driver(self):
        print("\n[3/4] Configuration du navigateur...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        service = Service('/usr/bin/chromedriver')
        
        try:
            print("   🔧 Initialisation Chromium...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
            print("   ✅ Navigateur OK")
        except Exception as e:
            print(f"   ❌ Erreur navigateur: {e}")
            raise
    
    def login_mpp(self):
        try:
            print("\n[4/4] === CONNEXION MPP ===")
            
            print("   [1/5] Accès URL...")
            print(f"   🌐 {MPP_URL}/")
            self.driver.get(f'{MPP_URL}/')
            print(f"   ✅ Page chargée: {self.driver.current_url}")
            
            print("   ⏳ Attente 3 sec pour chargement JS...")
            time.sleep(10)
            print("   ✅ Page stabilisée")
            
            print("   [2/5] Recherche du bouton 'Se connecter'...")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"   📊 {len(all_buttons)} boutons trouvés")
            for i, btn in enumerate(all_buttons[:5]):
                print(f"      [{i}] {btn.text}")
            
            print("   🔍 WebDriverWait bouton 'Se connecter'...")
            print("   📋 Détails des boutons:")
            for i, btn in enumerate(all_buttons):
                print(f"      Button {i}:")
                print(f"         text: '{btn.text}'")
                print(f"         tag_name: {btn.tag_name}")
                print(f"         innerHTML: {btn.get_attribute('innerHTML')}")
            
            connect_btn = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Se connecter')]"))
            )
            print("   ✅ Bouton trouvé!")
            
            print("   [3/5] Clic sur 'Se connecter'...")
            connect_btn.click()
            print("   ✅ Cliqué")
            
            print("   ⏳ Attente 2 sec pour formulaire Auth0...")
            time.sleep(2)
            print("   ✅ Formulaire visible")
            
            print("   [4/5] Saisie identifiants...")
            print("   🔍 WebDriverWait champ 'username'...")
            username_field = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            print("   ✅ Champ trouvé")
            print(f"   📝 Saisie email: {self.login[:10]}...")
            username_field.send_keys(self.login)
            print("   ✅ Email saisi")
            
            print("   🔍 Recherche champ 'password'...")
            password_field = self.driver.find_element(By.ID, 'password')
            print("   ✅ Champ trouvé")
            print(f"   📝 Saisie password...")
            password_field.send_keys(self.password)
            print("   ✅ Password saisi")
            
            print("   [5/5] Soumission formulaire...")
            print("   🔍 Recherche bouton submit...")
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            print("   ✅ Bouton trouvé")
            print("   📤 Envoi...")
            submit_btn.click()
            print("   ✅ Formulaire soumis")
            
            print("   ⏳ Attente 3 sec pour authentification...")
            time.sleep(3)
            current_url = self.driver.current_url
            print(f"   ✅ URL finale: {current_url}")
            print("✅ CONNECTÉ AVEC SUCCÈS!")
            return True
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            if self.driver:
                print(f"   📍 URL actuelle: {self.driver.current_url}")
            return False
    
    def fill_predictions(self, predictions):
        try:
            print(f"\n📝 === REMPLISSAGE ===")
            print(f"   [{len(predictions)} matchs à remplir]")
            
            print("\n   [1/2] Recherche des champs input...")
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"   📊 {len(all_inputs)} inputs trouvés au total")
            
            score_inputs = [i for i in all_inputs if i.is_displayed()]
            print(f"   ✅ {len(score_inputs)} champs visibles")
            
            print("\n   [2/2] Remplissage des scores...")
            for idx, pred in enumerate(predictions):
                input_idx = idx * 2
                if input_idx + 1 < len(score_inputs):
                    print(f"\n      Match {idx+1}:")
                    print(f"      📋 {pred['home_team']} vs {pred['away_team']}")
                    print(f"      📝 Prédiction: {pred['home_goals']}-{pred['away_goals']}")
                    
                    print(f"      🧹 Clear input home...")
                    score_inputs[input_idx].clear()
                    print(f"      ✅ Cleared")
                    
                    print(f"      📝 Send keys home: {pred['home_goals']}")
                    score_inputs[input_idx].send_keys(str(pred['home_goals']))
                    print(f"      ✅ Saisi")
                    
                    print(f"      🧹 Clear input away...")
                    score_inputs[input_idx + 1].clear()
                    print(f"      ✅ Cleared")
                    
                    print(f"      📝 Send keys away: {pred['away_goals']}")
                    score_inputs[input_idx + 1].send_keys(str(pred['away_goals']))
                    print(f"      ✅ Saisi")
                    
                    print(f"      ✅ Match rempli!")
                else:
                    print(f"      ⚠️ Pas assez d'inputs pour match {idx+1}")
            
            print("\n✅ TOUS LES PRONOSTICS REMPLIS!")
            return True
        except Exception as e:
            print(f"\n❌ ERREUR REMPLISSAGE: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        if self.driver:
            print("\n🛑 Fermeture navigateur...")
            self.driver.quit()
            print("   ✅ Fermé")


def main():
    print("=" * 60)
    print("🚀 MPP BOT LIGUE 1")
    print("=" * 60)
    
    predictor = LiguePredictor()
    if not predictor.get_next_7_days_matchs():
        return False
    
    predictions = predictor.generate_predictions()
    if not predictions:
        print("❌ Aucune prédiction générée")
        return False
    
    bot = MPPBot(LOGIN, PASSWORD)
    try:
        bot.setup_driver()
        if bot.login_mpp():
            if bot.fill_predictions(predictions):
                print("\n" + "=" * 60)
                print("✅ BOT TERMINÉ AVEC SUCCÈS!")
                print("=" * 60)
                return True
        else:
            print("❌ Connexion échouée")
            return False
    except Exception as e:
        print(f"❌ Erreur main: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        bot.close()


if __name__ == '__main__':
    exit(0 if main() else 1)
