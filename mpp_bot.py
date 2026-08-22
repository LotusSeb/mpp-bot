"""
MPP Bot - ÉTAPE 3: Prédictions - Noms CORRECTS
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 3: Prédictions avec noms CORRECTS")

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
    match_count = 0
    
    for i in range(len(all_text)):
        # Cherche "J." pour trouver le 1er club
        if all_text[i].startswith('J.'):
            # Le club est juste avant
            team_home = all_text[i-1]
            
            # Cherche le 3e % (vient après)
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
                # Le 2e mot après le 3e % 
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
                
                bonus_str = ""
                if max(pcts) > 80:
                    bonus_str = " (+1 bonus)"
                    if max_idx == 0:
                        final_home += 1
                    elif max_idx == 1:
                        final_home += 1
                        final_away += 1
                    else:
                        final_away += 1
                
                print(f"   ✅ {match_name}")
                print(f"      Consensus: {pct1}% {pct2}% {pct3}%")
                print(f"      Pondéré: {final_home}-{final_away}{bonus_str}")
                
                match_count += 1
                if match_count >= 3:
                    break
    
    print("\n✅ ÉTAPE 3 RÉUSSIE!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
