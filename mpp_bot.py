"""
MPP Bot - ÉTAPE 2: Lire les %
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 2: Lire les %")

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
    time.sleep(5)  # Attendre affichage des %
    print("   ✅ Connecté")
    
    # Chercher les inputs
    print("   🔍 Recherche des inputs...")
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    score_inputs = [i for i in all_inputs if i.is_displayed()]
    print(f"   ✅ {len(score_inputs)} inputs trouvés")
    
    # Lire les % pour chaque match
    print("\n📊 Lecture des %...")
    for idx in range(0, len(score_inputs), 2):
        match_idx = idx // 2
        
        # JavaScript pour lire les % du parent de cet input
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
        
        pcts = driver.execute_script(js_code)
        if len(pcts) >= 3:
            print(f"   ✅ Match {match_idx+1}: {pcts[0]}% {pcts[1]}% {pcts[2]}%")
        else:
            print(f"   ⚠️ Match {match_idx+1}: {len(pcts)} % trouvés")
    
    print("\n✅ ÉTAPE 2 RÉUSSIE!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
