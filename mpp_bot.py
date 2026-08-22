"""
MPP Ligue 1 Bot - VERSION STABLE SIMPLE
Pondération 25% algo + 75% consensus + bonus si consensus > 80%
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
from selenium.webdriver.common.keys import Keys
import time


class MPPBot:
    def __init__(self):
        self.api_url = 'https://api.football-data.org/v4'
        self.api_token = os.environ.get('FOOTBALL_API_TOKEN', '')
        self.mpp_login = os.environ.get('MPP_LOGIN', 'sebsdp@yahoo.fr')
        self.mpp_password = os.environ.get('MPP_PASSWORD', 'Football99@')
        self.driver = None

    def get_matches(self):
        """Récupère les matchs de Ligue 1"""
        try:
            print("\n[1/4] Récupération des matchs...")
            headers = {'X-Auth-Token': self.api_token}
            url = f'{self.api_url}/competitions/FL1/matches'
            
            print(f"   🌐 Appel API: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   📊 Réponse: {response.status_code}")
            
            if response.status_code == 200:
                matches = response.json().get('matches', [])
                print(f"   ✅ {len(matches)} matchs trouvés")
                return matches
            return []
        except Exception as e:
            print(f"   ❌ Erreur API: {e}")
            return []

    def generate_predictions(self, matches):
        """Génère les prédictions de base (1-1)"""
        print("\n[2/4] Génération des prédictions...")
        predictions = []
        
        for match in matches:
            pred = {
                'home_team': match['homeTeam']['name'],
                'away_team': match['awayTeam']['name'],
                'home_goals': 1,
                'away_goals': 1
            }
            predictions.append(pred)
        
        print(f"   ✅ {len(predictions)} prédictions générées")
        for idx, p in enumerate(predictions[:3]):
            print(f"      • {p['home_team']} {p['home_goals']}-{p['away_goals']}")
        if len(predictions) > 3:
            print(f"      ... et {len(predictions) - 3} autres")
        
        return predictions

    def init_driver(self):
        """Initialise Chromium"""
        print("\n[3/4] Configuration du navigateur...")
        print("   🔧 Initialisation Chromium...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        
        try:
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(3)
            print("   ✅ Navigateur OK")
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False

    def login_mpp(self):
        """Se connecte à MPP"""
        print("\n[4/4] === CONNEXION MPP ===")
        try:
            print("   [1/5] Accès URL...")
            print(f"   🌐 https://mpp.football/")
            self.driver.get('https://mpp.football/')
            print(f"   ✅ Page chargée: {self.driver.current_url}")
            
            print("   ⏳ Attente 10 sec pour chargement JS...")
            time.sleep(10)
            print("   ✅ Page stabilisée")
            
            print("   [2/5] Recherche du bouton 'Se connecter'...")
            print("   🔍 Cherche par XPath...")
            connect_button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Se connecter')]")
            print("   ✅ Élément trouvé: div")
            
            print("   [3/5] Clic sur 'Se connecter'...")
            connect_button.click()
            print("   ✅ Cliqué")
            
            print("   ⏳ Attente 2 sec pour formulaire Auth0...")
            time.sleep(2)
            print("   ✅ Formulaire visible")
            
            print("   [4/5] Saisie identifiants...")
            print("   🔍 WebDriverWait champ 'username'...")
            username_field = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            print("   ✅ Champ trouvé")
            print(f"   📝 Saisie email: {self.mpp_login[:7]}...")
            username_field.send_keys(self.mpp_login)
            print("   ✅ Email saisi")
            
            print("   🔍 Recherche champ 'password'...")
            password_field = self.driver.find_element(By.ID, "password")
            print("   ✅ Champ trouvé")
            print("   📝 Saisie password...")
            password_field.send_keys(self.mpp_password)
            print("   ✅ Password saisi")
            
            print("   [5/5] Soumission formulaire...")
            print("   🔍 Recherche bouton submit...")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            print("   ✅ Bouton trouvé")
            print("   📤 Envoi...")
            submit_button.click()
            print("   ✅ Formulaire soumis")
            
            print("   ⏳ Attente 3 sec pour authentification...")
            time.sleep(3)
            print(f"   ✅ URL finale: {self.driver.current_url}")
            
            print("✅ CONNECTÉ AVEC SUCCÈS!")
            print("   ⏳ Attente 5 sec pour affichage des %...")
            time.sleep(5)
            
            return True
        except Exception as e:
            print(f"   ❌ Erreur login: {e}")
            import traceback
            traceback.print_exc()
            return False

    def read_consensus_percentages_per_match(self, score_inputs):
        """Lit les % pour chaque match individuellement"""
        try:
            print("\n📊 Lecture du consensus par match...")
            print(f"   Analyse {len(score_inputs)} inputs...")
            
            consensus_by_match = {}
            
            for idx in range(0, len(score_inputs), 2):
                match_idx = idx // 2
                
                js_code = f"""
                const inputs = document.querySelectorAll('input');
                const input = inputs[{idx}];
                
                let parent = input;
                for (let i = 0; i < 15; i++) {{
                    parent = parent.parentElement;
                    if (!parent) break;
                    const text = parent.textContent;
                    if (text.includes('%') && text.length < 500) {{
                        break;
                    }}
                }}
                
                if (!parent) parent = input.parentElement;
                
                const elements = parent.querySelectorAll('*');
                const percentElements = [];
                
                elements.forEach(el => {{
                    try {{
                        const text = (el.innerText || el.textContent || '').trim();
                        if (/^\\d{{1,3}}%$/.test(text) && text.length <= 5) {{
                            percentElements.push(parseInt(text));
                        }}
                    }} catch (e) {{}}
                }});
                
                return percentElements.slice(0, 3);
                """
                
                try:
                    pcts = self.driver.execute_script(js_code)
                    if len(pcts) >= 3:
                        consensus_by_match[match_idx] = pcts[:3]
                        print(f"   ✅ Match {match_idx+1}: {pcts[0]}% {pcts[1]}% {pcts[2]}%")
                except Exception as e:
                    pass
            
            print(f"   ✅ {len(consensus_by_match)} matchs avec %")
            return consensus_by_match
        except Exception as e:
            return {}

    def blend_with_consensus(self, our_home, our_away, consensus_percentages_match):
        """Pondère 25% algo + 75% consensus, avec bonus si > 80%"""
        if not consensus_percentages_match or len(consensus_percentages_match) < 3:
            return our_home, our_away
        
        match_pcts = consensus_percentages_match
        
        print(f"      📊 Consensus: Dom={match_pcts[0]}% Nul={match_pcts[1]}% Ext={match_pcts[2]}%")
        
        max_idx = match_pcts.index(max(match_pcts))
        max_pct = match_pcts[max_idx]
        
        if max_idx == 0:
            consensus_pred = (1, 0)
            consensus_pred_str = "Victoire Dom"
        elif max_idx == 1:
            consensus_pred = (1, 1)
            consensus_pred_str = "Nul"
        else:
            consensus_pred = (0, 1)
            consensus_pred_str = "Victoire Ext"
        
        final_home = int(our_home * 0.25 + consensus_pred[0] * 0.75)
        final_away = int(our_away * 0.25 + consensus_pred[1] * 0.75)
        
        bonus_str = ""
        if max_pct > 80:
            bonus_str = " (+1 but bonus)"
            if max_idx == 0:
                final_home += 1
            elif max_idx == 1:
                final_home += 1
                final_away += 1
            else:
                final_away += 1
        
        print(f"      ⚖️  Pondération 25/75: {consensus_pred_str} → {final_home}-{final_away}{bonus_str}")
        
        return final_home, final_away

    def send_email_predictions(self, scores_in_order):
        """Envoie un email avec un tableau des pronostics"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            print("\n📧 Envoi de l'email...")
            
            sender_email = os.getenv('GMAIL_EMAIL')
            sender_password = os.getenv('GMAIL_PASSWORD')
            recipient_email = "sebsdp@yahoo.fr"
            
            if not sender_email or not sender_password:
                print("   ⚠️ Credentials Gmail manquants")
                return
            
            html_table = "<table style='border-collapse: collapse; width: 100%;'>\n"
            html_table += "<tr style='background-color: #4CAF50; color: white;'>"
            html_table += "<th style='border: 1px solid black; padding: 8px;'>Match</th>"
            html_table += "<th style='border: 1px solid black; padding: 8px;'>Prédiction</th>"
            html_table += "</tr>\n"
            
            for idx, item in enumerate(scores_in_order[:8]):
                match_name = item['match_name']
                score = f"{item['home_goals']}-{item['away_goals']}"
                color = "#f2f2f2" if idx % 2 == 0 else "white"
                html_table += f"<tr style='background-color: {color};'>"
                html_table += f"<td style='border: 1px solid black; padding: 8px;'>{match_name}</td>"
                html_table += f"<td style='border: 1px solid black; padding: 8px; text-align: center;'><strong>{score}</strong></td>"
                html_table += "</tr>\n"
            
            html_table += "</table>"
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"🏆 Pronostics Ligue 1 - {datetime.now().strftime('%d/%m/%Y')}"
            
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
        except Exception as e:
            print(f"   ❌ Erreur email: {e}")

    def fill_predictions(self, predictions):
        try:
            print(f"\n📝 === REMPLISSAGE ===")
            print(f"   [{len(predictions)} matchs à remplir]")
            
            print("\n   [1/2] Recherche des champs input...")
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"   📊 {len(all_inputs)} inputs trouvés")
            
            score_inputs = [i for i in all_inputs if i.is_displayed()]
            print(f"   ✅ {len(score_inputs)} champs visibles")
            
            consensus_by_match = self.read_consensus_percentages_per_match(score_inputs)
            scores_in_order = []
            
            print("\n   [2/2] Remplissage des scores...")
            for idx, pred in enumerate(predictions):
                input_idx = idx * 2
                if input_idx + 1 < len(score_inputs):
                    match_name = f"{pred['home_team']} vs {pred['away_team']}"
                    
                    print(f"\n      Match {idx+1}:")
                    print(f"      📋 {match_name}")
                    print(f"      📝 Prédiction algo: {pred['home_goals']}-{pred['away_goals']}")
                    
                    match_consensus = consensus_by_match.get(idx, [])
                    final_home, final_away = self.blend_with_consensus(
                        pred['home_goals'],
                        pred['away_goals'],
                        match_consensus
                    )
                    
                    scores_in_order.append({
                        'match_name': match_name,
                        'home_goals': final_home,
                        'away_goals': final_away
                    })
                    
                    # Retry logic simple
                    for retry in range(3):
                        try:
                            time.sleep(0.3)
                            score_inputs[input_idx].click()
                            time.sleep(0.1)
                            score_inputs[input_idx].send_keys(Keys.BACKSPACE + Keys.BACKSPACE)
                            score_inputs[input_idx].send_keys(str(final_home))
                            print(f"      ✅ Home: {final_home}")
                            break
                        except:
                            if retry < 2:
                                time.sleep(0.5)
                    
                    for retry in range(3):
                        try:
                            time.sleep(0.3)
                            score_inputs[input_idx + 1].click()
                            time.sleep(0.1)
                            score_inputs[input_idx + 1].send_keys(Keys.BACKSPACE + Keys.BACKSPACE)
                            score_inputs[input_idx + 1].send_keys(str(final_away))
                            print(f"      ✅ Away: {final_away}")
                            break
                        except:
                            if retry < 2:
                                time.sleep(0.5)
                    
                    print(f"      ✅ Match rempli!")
            
            print("\n✅ TOUS LES PRONOSTICS REMPLIS!")
            self.send_email_predictions(scores_in_order)
            
            return True
        except Exception as e:
            print(f"\n❌ ERREUR REMPLISSAGE: {e}")
            return False

    def close(self):
        if self.driver:
            print("\n🛑 Fermeture navigateur...")
            self.driver.quit()
            print("   ✅ Fermé")


def main():
    print("============================================================")
    print("🚀 MPP BOT LIGUE 1")
    print("============================================================")
    
    bot = None
    try:
        bot = MPPBot()
        
        matches = bot.get_matches()
        if not matches:
            return
        
        predictions = bot.generate_predictions(matches)
        
        if not bot.init_driver():
            return
        
        if not bot.login_mpp():
            return
        
        bot.fill_predictions(predictions)
        
        print("\n============================================================")
        print("✅ BOT TERMINÉ AVEC SUCCÈS!")
        print("============================================================")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        if bot:
            bot.close()


if __name__ == '__main__':
    main()
