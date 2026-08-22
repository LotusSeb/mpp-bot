"""
MPP Bot - ÉTAPE 5: Complet + Email
"""

import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 5: Complet + Email")

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
    
    # ÉTAPE 3: Lire les noms et %
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
                
                our_home = 1
                our_away = 1
                max_idx = pcts.index(max(pcts))
                
                if max_idx == 0:
                    consensus_pred = (1, 0)
                elif max_idx == 1:
                    consensus_pred = (1, 1)
                else:
                    consensus_pred = (0, 1)
                
                final_home = int(our_home * 0.25 + consensus_pred[0] * 0.75)
                final_away = int(our_away * 0.25 + consensus_pred[1] * 0.75)
                
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
                if match_count >= 3:
                    break
    
    # ÉTAPE 4: Remplir les scores
    print("\n📝 Remplissage des scores...")
    for idx, pred in enumerate(predictions):
        input_idx = idx * 2
        
        if input_idx + 1 < len(score_inputs):
            # Remplir home via JavaScript
            js_home = f"""
            const inputs = document.querySelectorAll('input');
            inputs[{input_idx}].value = '';
            inputs[{input_idx}].value = '{pred['home']}';
            inputs[{input_idx}].dispatchEvent(new Event('input', {{ bubbles: true }}));
            inputs[{input_idx}].dispatchEvent(new Event('change', {{ bubbles: true }}));
            """
            driver.execute_script(js_home)
            
            js_away = f"""
            const inputs = document.querySelectorAll('input');
            inputs[{input_idx + 1}].value = '';
            inputs[{input_idx + 1}].value = '{pred['away']}';
            inputs[{input_idx + 1}].dispatchEvent(new Event('input', {{ bubbles: true }}));
            inputs[{input_idx + 1}].dispatchEvent(new Event('change', {{ bubbles: true }}));
            """
            driver.execute_script(js_away)
            
            print(f"   ✅ {pred['match']}: {pred['home']}-{pred['away']}")
    
    # ÉTAPE 5: Envoyer email
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
                    <em>Pondération: 25% algorithme + 75% consensus</em><br>
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
    
    print("\n✅ BOT COMPLET - RÉUSSI!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
