"""
MPP Bot - ÉTAPE 3: Prédictions et pondération + NOMS
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 3: Prédictions avec noms des matchs")

# Config Chromium
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.binary_location = '/usr/bin/chromium-browser'

service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Connexion à MPP
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
    
    # Chercher les inputs
    print("   🔍 Recherche des inputs...")
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    score_inputs = [i for i in all_inputs if i.is_displayed()]
    print(f"   ✅ {len(score_inputs)} inputs trouvés")
    
    # Lire les % et noms pour chaque match
    print("\n📊 Calcul des prédictions...")
    for idx in range(0, len(score_inputs), 2):
        match_idx = idx // 2
        
        # Lire le NOM du match
        js_name = f"""
        const inputs = document.querySelectorAll('input');
        const input = inputs[{idx}];
        
        let parent = input;
        for (let i = 0; i < 15; i++) {{
            parent = parent.parentElement;
            if (!parent) break;
        }}
        
        const text = parent.textContent;
        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
        
        return lines.slice(0, 3);
        """
        
        # Lire les %
        js_pcts = f"""
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
            lines = driver.execute_script(js_name)
            pcts = driver.execute_script(js_pcts)
            
            # Afficher le nom du match
            match_name = f"{lines[0]} vs {lines[1]}" if len(lines) >= 2 else "Match inconnu"
            
            if len(pcts) >= 3:
                dom_pct = pcts[0]
                nul_pct = pcts[1]
                ext_pct = pcts[2]
                
                # Prédiction de base: 1-1
                our_home = 1
                our_away = 1
                
                # Pondération 25% algo + 75% consensus
                max_idx = pcts.index(max(pcts))
                
                if max_idx == 0:
                    consensus_pred = (1, 0)
                    pred_str = "Victoire Dom"
                elif max_idx == 1:
                    consensus_pred = (1, 1)
                    pred_str = "Nul"
                else:
                    consensus_pred = (0, 1)
                    pred_str = "Victoire Ext"
                
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
                
                print(f"   ✅ Match {match_idx+1}: {match_name}")
                print(f"      Consensus: {dom_pct}% {nul_pct}% {ext_pct}%")
                print(f"      Pondéré: {final_home}-{final_away}{bonus_str}")
        except Exception as e:
            print(f"   ⚠️ Match {match_idx+1}: erreur {e}")
    
    print("\n✅ ÉTAPE 3 RÉUSSIE!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
