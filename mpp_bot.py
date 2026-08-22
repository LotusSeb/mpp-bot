"""
MPP Bot - ÉTAPE 1: Connexion à MPP
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 1: Connexion à MPP")

# Config Chromium
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.binary_location = '/usr/bin/chromium-browser'

service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Accès à MPP
    print("   🌐 Accès à https://mpp.football/...")
    driver.get('https://mpp.football/')
    time.sleep(10)
    print("   ✅ Page chargée")
    
    # Clic sur "Se connecter"
    print("   🔍 Recherche bouton 'Se connecter'...")
    connect_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Se connecter')]")
    connect_button.click()
    time.sleep(2)
    print("   ✅ Cliqué")
    
    # Connexion
    print("   📝 Saisie identifiants...")
    login = os.environ.get('MPP_LOGIN', 'sebsdp@yahoo.fr')
    password = os.environ.get('MPP_PASSWORD', 'Football99@')
    
    username_field = driver.find_element(By.ID, "username")
    username_field.send_keys(login)
    
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)
    
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()
    
    time.sleep(3)
    print("   ✅ Connecté")
    
    # Attendre l'affichage
    time.sleep(5)
    
    # Chercher les inputs (matchs)
    print("   🔍 Recherche des matchs...")
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    score_inputs = [i for i in all_inputs if i.is_displayed()]
    
    nb_matchs = len(score_inputs) // 2
    print(f"   ✅ {nb_matchs} matchs trouvés ({len(score_inputs)} inputs)")
    
    print("\n✅ ÉTAPE 1 RÉUSSIE!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
