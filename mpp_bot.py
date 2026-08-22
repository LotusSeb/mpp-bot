"""
MPP Bot - ÉTAPE 3: Prédictions - Filtrer les VRAIS noms
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("🚀 ÉTAPE 3: Prédictions avec noms")

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
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    score_inputs = [i for i in all_inputs if i.is_displayed()]
    print(f"   ✅ {len(score_inputs)} inputs trouvés")
    
    # Récupère TOUS les textes
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
    
    # Filtre pour garder JUSTE les noms d'équipes
    # = textes avec des lettres, pas de %, pas d'horaire, pas de nombres seuls
    exclusions = ['Créer', 'Rejoindre', 'Importer', 'Afficher', 'stats', 'Dimanche', 'août', 'J.1', '-', 'Activer', 'bonus', 'McDo', 'Ligue', 'compétition', 'Nouvelle']
    
    team_names = []
    for text in all_text:
        # Vérifie que c'est un vrai nom
        if ('%' not in text and 
            ':' not in text and  # Pas d'horaire
            not text.replace('.', '').isdigit() and  # Pas de nombre
            any(c.isalpha() for c in text) and  # Au moins une lettre
            text not in exclusions and
            len(text) > 2):
            team_names.append(text)
    
    # Lire les % pour chaque match
    print("\n📊 Calcul des prédictions...")
    match_count = 0
    for i in range(0, len(all_text), 5):
        if match_count >= 3:
            break
        
        text = all_text[i]
        
        # Cherche les 3 %
        if '%' in text:
            try:
                pct1 = int(text.rstrip('%'))
                pct2 = int(all_text[i+2].rstrip('%'))
                pct3 = int(all_text[i+4].rstrip('%'))
                pcts = [pct1, pct2, pct3]
                
                # Prend les noms correspondants
                if match_count < len(team_names) - 1:
                    team_home = team_names[match_count * 2]
                    team_away = team_names[match_count * 2 + 1]
                    match_name = f"{team_home} vs {team_away}"
                    
                    # Prédiction de base: 1-1
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
            except:
                pass
    
    print("\n✅ ÉTAPE 3 RÉUSSIE!")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n🛑 Fermé")
