# 🤖 MPP Bot - Pronostics Ligue 1 Automatisés

Bot d'automatisation qui génère et soumet automatiquement vos pronostics Ligue 1 sur **chaque lundi à 9h du matin** via GitHub Actions.

## 📋 Fonctionnalités

✅ Récupère les **7 prochains jours de matchs** Ligue 1  
✅ Génère des **prédictions intelligentes** basées sur les **7 derniers matchs** de chaque équipe  
✅ Remplit automatiquement les **scores** sur MPP  
✅ Exécution automatique **chaque lundi à 9h**  
✅ Zéro maintenance - tout en cloud GitHub

## 🔧 Installation (5 minutes)

### Étape 1: Créer un repo GitHub

1. Va sur [GitHub.com](https://github.com)
2. Clique sur **"New repository"**
3. Nomme-le: `mpp-bot` (ou ce que tu veux)
4. Clique **"Create repository"**

### Étape 2: Ajouter les fichiers

Clone le repo en local (ou crée les fichiers via l'interface web):

```bash
git clone https://github.com/[TON_USERNAME]/mpp-bot.git
cd mpp-bot
```

Ajoute ces fichiers:
- `mpp_bot.py` (le script principal)
- `.github/workflows/schedule.yml` (le workflow GitHub Actions)

### Étape 3: Obtenir une clé API (gratuit)

1. Va sur [football-data.org](https://www.football-data.org/)
2. Crée un compte gratuit
3. Clique sur **"Account"** → copie ton **API Token**

### Étape 4: Configurer les Secrets GitHub

⚠️ **Ne partage JAMAIS tes identifiants en dur dans le code!**

1. Va dans ton repo GitHub
2. Clique sur **Settings** → **Secrets and variables** → **Actions**
3. Clique sur **"New repository secret"** et ajoute:

| Nom | Valeur |
|-----|--------|
| `MPP_LOGIN` | `sebsdp@yahoo.fr` |
| `MPP_PASSWORD` | `Football99@` |
| `FOOTBALL_API_TOKEN` | (Ta clé API football-data.org) |

### Étape 5: Créer le Workflow GitHub Actions

1. Dans ton repo, crée le dossier: `.github/workflows/`
2. Crée le fichier: `.github/workflows/schedule.yml`
3. Copie le contenu du fichier `github_workflow.yml` fourni

### Étape 6: Push et c'est bon!

```bash
git add .
git commit -m "Initial commit - MPP Bot"
git push origin main
```

## 🚀 Test avant le lundi

Pour tester le bot maintenant (sans attendre lundi 9h):

1. Va dans ton repo GitHub
2. Clique sur l'onglet **"Actions"**
3. Sélectionne le workflow **"MPP Bot - Pronostics Ligue 1"**
4. Clique sur **"Run workflow"** → **"Run workflow"**

GitHub va exécuter le bot immédiatement! Regarde les logs pour voir si ça fonctionne.

## 📊 Comment fonctionne l'algorithme?

Le bot calcule une prédiction intelligente combinant:

### 📈 **80% - Forme récente (7 derniers matchs)**
- Moyenne des buts marqués par une équipe
- Moyenne des buts encaissés par une équipe
- Reflète la **forme actuelle**

**Formule:**
```
Pred_Recent = (Buts_marqués_7j + Buts_encaissés_adversaire_7j) / 2
```

### 🏆 **20% - Historique H2H (5 dernières années)**
- Moyenne des buts marqués dans les confrontations directes
- Moyenne des buts encaissés dans les confrontations directes
- Capture la **tendance historique** entre les deux équipes

**Formule:**
```
Pred_H2H = Moyenne_buts_H2H_5ans
```

### 🎯 **Prédiction finale (fusion pondérée):**
```
Buts_Final = (0.80 × Pred_Recent) + (0.20 × Pred_H2H)
```

**Exemple:**
```
OM vs Strasbourg

Données 7 derniers matchs OM:
  - OM: 1.5 buts/match en moyenne
  - Strasbourg: 1.0 but encaissé/match en moyenne
  → Pred_Recent = (1.5 + 1.0) / 2 = 1.25

Données H2H OM vs Strasbourg (5 dernières années):
  - OM: 1.8 buts/match en moyenne (vs Strasbourg)
  → Pred_H2H = 1.8

Prédiction finale OM:
  = (0.80 × 1.25) + (0.20 × 1.8)
  = 1.0 + 0.36
  = 1.36 → arrondi à 1 but pour OM
```

### 💡 Avantages de cette approche:
✅ **Équilibre** entre forme récente et historique  
✅ **Fiabilité** - pas trop dépendant d'une mauvaise semaine  
✅ **Tendances** - capture les dynamiques anciennes des équipes  
✅ **Flexibilité** - 80/20 peut être ajusté facilement

## 📝 Logs et Monitoring

Après chaque exécution (chaque lundi 9h):

1. Va dans **"Actions"** de ton repo GitHub
2. Clique sur la dernière exécution
3. Vois les logs détaillés:
   - ✅ Matchs trouvés
   - 📊 Prédictions générées
   - ✅ Pronostics soumis

## ⚙️ Ajustements possibles

### Changer l'heure d'exécution

Edit `.github/workflows/schedule.yml` et change la ligne:
```yaml
- cron: '0 9 * * 1'  # Actuellement: Lundi à 9h UTC
```

**Exemples:**
- `'0 10 * * 1'` = Lundi 10h UTC
- `'0 7 * * 1'` = Lundi 7h UTC

### Améliorer l'algorithme

Le fichier `mpp_bot.py` contient la classe `LiguePredictor`.  
Tu peux modifier la formule de prédiction.

**Changer les poids (actuellement 80% récent / 20% H2H):**

Dans la méthode `predict_score()`, modifie cette ligne:
```python
home_goals = (0.80 * pred_home_7d) + (0.20 * pred_home_h2h)
away_goals = (0.80 * pred_away_7d) + (0.20 * pred_away_h2h)
```

Exemples:
- `(0.90 * recent) + (0.10 * h2h)` = Plus de poids à la forme récente
- `(0.70 * recent) + (0.30 * h2h)` = Plus de poids à l'historique
- `(0.85 * recent) + (0.15 * h2h)` = Équilibre entre les deux

### Ajouter des sélecteurs pour nouvelles pubs

Si le bot ne ferme pas une pub spécifique:

1. **Inspecte le HTML de la pub** (F12 sur MPP)
2. **Cherche le bouton de fermeture** ou l'ID/classe de la pub
3. **Ajoute le sélecteur** dans `mpp_bot.py`, méthode `close_ads()`:

```python
ad_close_selectors = [
    # Sélecteurs existants...
    'ton-nouveau-selecteur-ici',  # ← Ajoute ici
]
```

**Exemples de sélecteurs:**
```python
'button.ma-pub-close'           # Classe
'button#ad-close-123'           # ID
'div[data-ad-id="banner"]'      # Attribut
'a[href*="close-ad"]'           # Contient du texte
```

## 🐛 Troubleshooting

### ❌ "API token invalide"
- Vérifie que tu as bien copié ton token football-data.org
- Revérifie dans GitHub Secrets

### ❌ "Erreur connexion MPP"
- Vérifie que le login/mdp sont corrects
- MPP a peut-être changé la structure HTML (rare mais possible)
- En cas de changement, met à jour les sélecteurs CSS/XPath dans `mpp_bot.py`

### ❌ "Les pubs bloquent l'accès"
✅ Le bot ferme automatiquement les pubs avec la méthode `close_ads()`.

**Stratégies utilisées:**
- Détecte et clique les boutons "Fermer"
- Supprime les iframes publicitaires
- Scroll vers les éléments (évite les overlays)
- Attend que les pubs disparaissent avant de continuer

**Si les pubs persistent:**
1. Vérifie dans les logs GitHub Actions quelles pubs sont détectées
2. Ajoute les sélecteurs CSS/XPath des pubs dans la liste `ad_close_selectors`
3. Relance le test avec "Run workflow"

### ❌ "Timeout"
- Les APIs peuvent être lentes
- Le bot réessaiera à la prochaine exécution (lundi prochain)

### ❌ "Erreur: impossible de trouver les champs de pronostic"
- MPP a peut-être changé la structure des inputs
- Vérifiez les sélecteurs XPath/CSS dans `fill_predictions()`
- Inspectez la page MPP (F12) pour trouver les bons sélecteurs

## 📞 Support

Si tu as des soucis:
1. Regarde les logs GitHub Actions (Settings → Actions)
2. Vérifie que tous les Secrets sont rentrés correctement
3. Teste manuellement le workflow via "Run workflow"

## 🔒 Sécurité

✅ Tes identifiants sont **jamais** en dur dans le code  
✅ Stockés en Secrets GitHub (chiffré)  
✅ Le script s'exécute sur les serveurs GitHub (pas ton PC)  
✅ Aucune donnée n'est loggée ou partagée

## 📅 Horaire d'exécution

**Rappel:** GitHub Actions utilise l'heure **UTC**

Actuellement configuré pour: **Lundi 9h UTC**

- En hiver (CET): = Lundi 10h votre heure
- En été (CEST): = Lundi 11h votre heure

Ajuste le `cron` si besoin!

---

**Bon pronostiquage! 🎯⚽**
