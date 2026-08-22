"""
MPP Ligue 1 Bot - Automatisation des pronostics
VERSION AVEC BEAUCOUP DE LOGS POUR DÉBOGUER
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
                print(f"✅ {len(self.matchs)} matchs trouvés")
                return True
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur matchs: {e}")
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
        except Exception as e:
            print(f"❌ Erreur prédiction: {e}")
            return None
    
    def generate_predictions(self):
        predictions = []
        for match in self.matchs:
            pred = self.predict_score(match)
            if pred:
                predictions.append(pred)
        return predictions


class MPPBot:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.driver = None
    
    def close_ads(self):
        """Ferme les pubs avec logs"""
        try:
            ad_close_selectors = [
                'button[aria-label="Close"]',
                'button[class*="close"]',
                'button[class*="ad-close"]',
                '.ad-close-btn',
                '[id*="ad-close"]',
            ]
            
            ads_found = 0
            for selector in ad_close_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            print(f"   🔴 Pub fermée")
                            element.click()
                            ads_found += 1
                            time.sleep(0.5)
                except:
                    pass
            
            if ads_found > 0:
                print(f"   ✅ {ads_found} pub(s)")
        except Exception as e:
            print(f"   ⚠️ Erreur pubs: {e}")
    
    def setup_driver(self):
        """Configure le navigateur"""
        print("\n🔧 === CONFIGURATION ===")
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
            print("   Initialisation Chromium...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
            print("✅ Navigateur OK")
        except Exception as e:
            print(f"❌ Erreur: {e}")
            raise
    
    def login_mpp(self):
        """Se connecte à MPP avec beaucoup de logs"""
        try:
            print("\n📱 === CONNEXION ===")
            
            print("\n[1/6] Page d'accueil...")
            self.driver.get(f'{MPP_URL}/')
            print(f"   ✅ {self.driver.current_url}")
            time.sleep(3)
            
            print("\n[2/6] Fermeture pubs...")
            self.close_ads()
            time.sleep(1)
            
            print("\n[3/6] Recherche bouton 'Se connecter'...")
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"   {len(all_buttons)} boutons trouvés")
            
            connect_btn = None
            for selector in [(By.XPATH, "//button[contains(text(), 'Se connecter')]"),
                             (By.XPATH, "//*[contains(text(), 'Se connecter')]")]:
                try:
                    connect_btn = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(selector)
                    )
                    print(f"   ✅ Trouvé!")
                    break
                except:
                    pass
            
            if not connect_btn:
                raise Exception("Bouton introuvable")
            
            print("\n[4/6] Clic...")
            self.close_ads()
            time.sleep(1)
            connect_btn.click()
            print("   ✅ OK")
            
            print("\n[5/6] Attente formulaire (5 sec)...")
            time.sleep(5)
            
            print("\n[6/6] Identifiants...")
            username_field = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            username_field.send_keys(self.login)
            print("   ✅ Email")
            
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(self.password)
            print("   ✅ Password")
            
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_btn.click()
            print("   ✅ Submit")
            
            print("\n   Attente (5 sec)...")
            time.sleep(5)
            print(f"✅ CONNECTÉ!")
            return True
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            return False
    
    def fill_predictions(self, predictions):
        """Remplit les pronostics"""
        try:
            print("\n📝 === REMPLISSAGE ===")
            
            print("\n[1/3] Recherche champs...")
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            score_inputs = [i for i in all_inputs if i.is_displayed()]
            print(f"   ✅ {len(score_inputs)} champs")
            
            print(f"\n[2/3] Scores ({len(predictions)} matchs)...")
            for idx, pred in enumerate(predictions):
                input_idx = idx * 2
                
                if input_idx + 1 < len(score_inputs):
                    try:
                        score_inputs[input_idx].clear()
                        score_inputs[input_idx].send_keys(str(pred['home_goals']))
                        time.sleep(0.2)
                        
                        score_inputs[input_idx + 1].clear()
                        score_inputs[input_idx + 1].send_keys(str(pred['away_goals']))
                        time.sleep(0.2)
                        
                        print(f"   ✅ [{idx+1}] {pred['home_team']} {pred['home_goals']}-{pred['away_goals']}")
                    except Exception as e:
                        print(f"   ❌ [{idx+1}] {e}")
            
            print(f"\n[3/3] Soumission...")
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Valider')]")
            submit_btn.click()
            time.sleep(2)
            print("✅ TERMINÉ!")
            return True
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()


def main():
    print("=" * 60)
    print("🚀 MPP BOT - LOGS DÉTAILLÉS")
    print("=" * 60)
    
    predictor = LiguePredictor()
    if not predictor.get_next_7_days_matchs():
        return False
    
    predictions = predictor.generate_predictions()
    if not predictions:
        print("❌ Aucune prédiction")
        return False
    
    print(f"\n📊 {len(predictions)} prédictions:")
    for i, p in enumerate(predictions[:3]):
        print(f"   • {p['home_team']} {p['home_goals']}-{p['away_goals']}")
    
    bot = MPPBot(LOGIN, PASSWORD)
    try:
        bot.setup_driver()
        if bot.login_mpp():
            bot.fill_predictions(predictions)
        else:
            return False
    finally:
        bot.close()
    
    print("\n" + "=" * 60)
    print("✅ SUCCÈS!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
