"""
MPP Bot - ÉTAPE 4: Remplissage via JavaScript
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 4: Remplissage via JavaScript")

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
    
    scores = [
        {"match": "Angers SCO vs LOSC", "home": 0, "away": 2},
        {"match": "Havre AC vs AS Monaco", "home": 0, "away": 1},
        {"match": "Rennes vs Paris SG", "home": 0, "away": 1}
    ]
    
    print("\n📝 Remplissage des scores...")
    for idx, score in enumerate(scores):
        input_idx = idx * 2
        
        if input_idx + 1 < len(score_inputs):
            print(f"\n   Match {idx+1}: {score['match']}")
            
            # Remplir home via JavaScript
            js_home = f"""
            const inputs = document.querySelectorAll('input');
            inputs[{input_idx}].value = '{score['home']}';
            inputs[{input_idx}].dispatchEvent(new Event('input', {{ bubbles: true }}));
            inputs[{input_idx}].dispatchEvent(new Event('change', {{ bubbles: true }}));
            """
            driver.execute_script(js_home)
            print(f"      ✅ Home: {score['home']}")
            
            # Remplir away via JavaScript
            js_away = f"""
            const inputs = document.querySelectorAll('input');
            inputs[{input_idx + 1}].value = '{score['away']}';
            inputs[{input_idx + 1}].dispatchEvent(new Event('input', {{ bubbles: true }}));
            inputs[{input_idx + 1}].dispatchEvent(new Event('change', {{ bubbles: true }}));
            """
            driver.execute_script(js_away)
            print(f"      ✅ Away: {score['away']}")
    
    print("\n✅ ÉTAPE 4 RÉUSSIE!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
