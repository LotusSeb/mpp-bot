"""
MPP Bot - Complet avec clic réel
"""

import os
import time
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from team_mapping import MPP_TO_API_ID

api_token = os.environ.get('FOOTBALL_API_TOKEN', '')
api_headers = {'X-Auth-Token': api_token}


def get_team_full_name(team_id):
    url = f'https://api.football-data.org/v4/teams/{team_id}'
    response = requests.get(url, headers=api_headers, timeout=10)
    return response.json().get('name', '')


def get_team_stats(team_id, team_full_name):
    """Recupere les 5 derniers matchs et calcule buts marques/encaisses en moyenne"""
    url = f'https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5'
    response = requests.get(url, headers=api_headers, timeout=10)
    
    if response.status_code != 200:
        return None
    
    matches = response.json().get('matches', [])
    if len(matches) == 0:
        return None
    
    goals_scored = []
    goals_conceded = []
    
    for m in matches:
        home_name = m['homeTeam']['name']
        home_score = m['score']['fullTime']['home']
        away_score = m['score']['fullTime']['away']
        
        if home_name == team_full_name:
            goals_scored.append(home_score)
            goals_conceded.append(away_score)
        else:
            goals_scored.append(away_score)
            goals_conceded.append(home_score)
    
    return {
        "avg_scored": sum(goals_scored) / len(goals_scored),
        "avg_conceded": sum(goals_conceded) / len(goals_conceded)
    }


def get_algo_prediction(team_home, team_away):
    """Calcule la prediction basee sur l'historique (formule domicile/exterieur).
    Retourne (1, 1) par defaut si les equipes ne sont pas trouvees ou pas de donnees."""
    if team_home not in MPP_TO_API_ID or team_away not in MPP_TO_API_ID:
        return (1, 1)
    
    id_home = MPP_TO_API_ID[team_home]
    id_away = MPP_TO_API_ID[team_away]
    
    name_home = get_team_full_name(id_home)
    time.sleep(6)
    name_away = get_team_full_name(id_away)
    time.sleep(6)
    
    stats_home = get_team_stats(id_home, name_home)
    time.sleep(6)
    stats_away = get_team_stats(id_away, name_away)
    time.sleep(6)
    
    if not stats_home or not stats_away:
        return (1, 1)
    
    buts_dom = round((stats_home['avg_scored'] + stats_away['avg_conceded']) / 2)
    buts_ext = round((stats_away['avg_scored'] + stats_home['avg_conceded']) / 2)
    
    return (buts_dom, buts_ext)

print("🚀 MPP BOT COMPLET")

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.binary_location = '/usr/bin/chromium-browser'

service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print("   🌐 Connexion...")
    driver.get('https://mpp.football/')
    time.sleep(10)
    
    connect_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Se connecter')]")
    connect_button.click()
    time.sleep(2)
    
    login = os.environ.get('MPP_LOGIN', 'sebsdp@yahoo.fr')
    password = os.environ.get('MPP_PASSWORD', 'Football99@')
    
    username_field = driver.find_element(By.ID, "username")
    username_field.send_keys(login)
    
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)
    
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    time.sleep(3)
    time.sleep(5)
    print("   ✅ Connecté")
    
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    score_inputs = [i for i in all_inputs if i.is_displayed()]
    print(f"   ✅ {len(score_inputs)} inputs trouvés")
    
    # Lire les noms et %
    js_all_text = """
    const inputs = document.querySelectorAll('input');
    const input = inputs[0];
    
    let parent = input;
    for (let i = 0; i < 20; i++) {
        parent = parent.parentElement;
        if (!parent) break;
    }
    
    const fullText = parent.innerText;
    const lines = fullText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
    
    return lines;
    """
    
    all_text = driver.execute_script(js_all_text)
    
    print("\n📊 Calcul des prédictions...")
    predictions = []
    match_count = 0
    
    for i in range(len(all_text)):
        if all_text[i].startswith('J.'):
            team_home = all_text[i-1]
            
            pct_count = 0
            pct1_idx = None
            pct2_idx = None
            pct3_idx = None
            
            for j in range(i, len(all_text)):
                if '%' in all_text[j]:
                    pct_count += 1
                    if pct_count == 1:
                        pct1_idx = j
                    elif pct_count == 2:
                        pct2_idx = j
                    elif pct_count == 3:
                        pct3_idx = j
                        break
            
            if pct3_idx and pct3_idx + 2 < len(all_text):
                team_away = all_text[pct3_idx + 2]
                
                pct1 = int(all_text[pct1_idx].rstrip('%'))
                pct2 = int(all_text[pct2_idx].rstrip('%'))
                pct3 = int(all_text[pct3_idx].rstrip('%'))
                pcts = [pct1, pct2, pct3]
                
                match_name = f"{team_home} vs {team_away}"
                
                our_home, our_away = get_algo_prediction(team_home, team_away)
                max_idx = pcts.index(max(pcts))
                
                if max_idx == 0:
                    consensus_pred = (1, 0)
                elif max_idx == 1:
                    consensus_pred = (1, 1)
                else:
                    consensus_pred = (0, 1)
                
                final_home = int(our_home * 0.20 + consensus_pred[0] * 0.80)
                final_away = int(our_away * 0.20 + consensus_pred[1] * 0.80)
                
                if max(pcts) > 80:
                    if max_idx == 0:
                        final_home += 1
                    elif max_idx == 1:
                        final_home += 1
                        final_away += 1
                    else:
                        final_away += 1
                
                predictions.append({
                    "match": match_name,
                    "home": final_home,
                    "away": final_away
                })
                
                print(f"   ✅ {match_name}: {final_home}-{final_away}")
                
                match_count += 1
                if match_count >= len(score_inputs) // 2:
                    break
    
    # Remplir les scores
    print("\n📝 Remplissage des scores...")
    for idx, pred in enumerate(predictions):
        input_idx = idx * 2
        
        if input_idx + 1 < len(score_inputs):
            print(f"   ✅ {pred['match']}: {pred['home']}-{pred['away']}")
            
            # Scroll + Clic JavaScript + Selenium sendKeys
            driver.execute_script(f"document.querySelectorAll('input')[{input_idx}].scrollIntoView({{block: 'center'}});")
            time.sleep(0.3)
            driver.execute_script(f"document.querySelectorAll('input')[{input_idx}].click();")
            time.sleep(0.1)
            score_inputs[input_idx].send_keys(Keys.BACKSPACE + Keys.BACKSPACE)
            score_inputs[input_idx].send_keys(str(pred['home']))
            
            driver.execute_script(f"document.querySelectorAll('input')[{input_idx + 1}].scrollIntoView({{block: 'center'}});")
            time.sleep(0.3)
            driver.execute_script(f"document.querySelectorAll('input')[{input_idx + 1}].click();")
            time.sleep(0.1)
            score_inputs[input_idx + 1].send_keys(Keys.BACKSPACE + Keys.BACKSPACE)
            score_inputs[input_idx + 1].send_keys(str(pred['away']))
    
    # Envoyer email
    print("\n📧 Envoi email...")
    sender_email = os.getenv('GMAIL_EMAIL')
    sender_password = os.getenv('GMAIL_PASSWORD')
    recipient_email = "sebsdp@yahoo.fr"
    
    if sender_email and sender_password:
        html_table = "<table style='border-collapse: collapse; width: 100%;'>\n"
        html_table += "<tr style='background-color: #4CAF50; color: white;'>"
        html_table += "<th style='border: 1px solid black; padding: 8px;'>Match</th>"
        html_table += "<th style='border: 1px solid black; padding: 8px;'>Prédiction</th>"
        html_table += "</tr>\n"
        
        for idx, pred in enumerate(predictions):
            score = f"{pred['home']}-{pred['away']}"
            color = "#f2f2f2" if idx % 2 == 0 else "white"
            html_table += f"<tr style='background-color: {color};'>"
            html_table += f"<td style='border: 1px solid black; padding: 8px;'>{pred['match']}</td>"
            html_table += f"<td style='border: 1px solid black; padding: 8px; text-align: center;'><strong>{score}</strong></td>"
            html_table += "</tr>\n"
        
        html_table += "</table>"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"🏆 Pronostics Ligue 1"
        
        body = f"""
        <html>
            <body style='font-family: Arial, sans-serif;'>
                <h2>📊 Pronostics Ligue 1</h2>
                <p>Voici les pronostics générés automatiquement:</p>
                {html_table}
                <p style='margin-top: 20px; font-size: 12px; color: #666;'>
                    <em>Pondération: 20% algorithme (historique 5 derniers matchs) + 80% consensus</em><br>
                    <em>Bonus: +1 but si consensus > 80%</em>
                </p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"   ✅ Email envoyé")
    else:
        print("   ⚠️ Credentials Gmail manquants")
    
    print("\n✅ BOT RÉUSSI!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
