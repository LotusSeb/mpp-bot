"""
MPP Ligue 1 Bot - Automatisation des pronostics
VERSION STABLE QUI MARCHE
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
                self.matchs = response.json().get('matches', [])
                print(f"✅ {len(self.matchs)} matchs trouvés")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur API: {e}")
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
    
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        service = Service('/usr/bin/chromedriver')
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(15)
        self.driver.implicitly_wait(3)
        print("✅ Navigateur OK")
    
    def login_mpp(self):
        try:
            print("\n🔐 Connexion MPP...")
            self.driver.get(f'{MPP_URL}/')
            time.sleep(2)
            
            connect_btn = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Se connecter')]"))
            )
            connect_btn.click()
            time.sleep(2)
            
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, 'username'))
            ).send_keys(self.login)
            
            self.driver.find_element(By.ID, 'password').send_keys(self.password)
            self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
            
            time.sleep(3)
            print("✅ Connecté!")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False
    
    def fill_predictions(self, predictions):
        try:
            print(f"\n📝 Remplissage {len(predictions)} matchs...")
            
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            score_inputs = [i for i in all_inputs if i.is_displayed()]
            
            for idx, pred in enumerate(predictions):
                input_idx = idx * 2
                if input_idx + 1 < len(score_inputs):
                    score_inputs[input_idx].clear()
                    score_inputs[input_idx].send_keys(str(pred['home_goals']))
                    
                    score_inputs[input_idx + 1].clear()
                    score_inputs[input_idx + 1].send_keys(str(pred['away_goals']))
                    
                    print(f"   ✅ {pred['home_team']} {pred['home_goals']}-{pred['away_goals']}")
            
            print("✅ Tous les pronostics remplis!")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def close(self):
        if self.driver:
            self.driver.quit()


def main():
    print("=" * 50)
    print("🚀 MPP BOT LIGUE 1")
    print("=" * 50)
    
    predictor = LiguePredictor()
    if not predictor.get_next_7_days_matchs():
        return False
    
    predictions = predictor.generate_predictions()
    if not predictions:
        return False
    
    print(f"📊 {len(predictions)} prédictions")
    
    bot = MPPBot(LOGIN, PASSWORD)
    try:
        bot.setup_driver()
        if bot.login_mpp():
            bot.fill_predictions(predictions)
    finally:
        bot.close()
    
    print("\n" + "=" * 50)
    print("✅ SUCCÈS!")
    print("=" * 50)
    return True


if __name__ == '__main__':
    exit(0 if main() else 1)
