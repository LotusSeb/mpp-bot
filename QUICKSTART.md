# ⚡ Quick Start - Démarrer en 5 minutes

## 1️⃣ Créer un repo GitHub

```bash
# Option A: CLI (si tu as git)
gh repo create mpp-bot --public

# Option B: Via le site GitHub
# https://github.com/new → Nomme-le "mpp-bot"
```

## 2️⃣ Ajouter les fichiers

Clone/télécharge et ajoute ces fichiers au repo:

```
mpp-bot/
├── mpp_bot.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── .github/workflows/
    └── schedule.yml
```

**Via Git:**
```bash
git clone https://github.com/[TON_USERNAME]/mpp-bot.git
cd mpp-bot

# Copie les fichiers depuis le ZIP
cp [CHEMIN_DU_ZIP]/*.py .
cp [CHEMIN_DU_ZIP]/requirements.txt .
# etc...

git add .
git commit -m "Initial commit"
git push
```

**Via GitHub Web:**
1. Va sur ton repo
2. Clique "Add file" → "Upload files"
3. Drag-and-drop tous les fichiers

## 3️⃣ Obtenir ta clé API (2 min)

1. Va sur: https://www.football-data.org/
2. "Register" → crée un compte
3. Va dans ton email et confirme
4. Login et va dans "Account"
5. **Copie ton API Token**

## 4️⃣ Ajouter les Secrets GitHub (2 min)

**Dans ton repo GitHub:**
1. Settings → Secrets and variables → Actions
2. "New repository secret" et ajoute:

| Name | Value |
|------|-------|
| `MPP_LOGIN` | `sebsdp@yahoo.fr` |
| `MPP_PASSWORD` | `Football99@` |
| `FOOTBALL_API_TOKEN` | (ta clé du step 3) |

## 5️⃣ C'est bon! 🎉

Le bot s'exécutera automatiquement **chaque lundi à 9h UTC**.

### Test rapide:
1. Va dans **Actions**
2. Clique le workflow
3. "Run workflow" → "Run workflow"

Les logs vont montrer si ça marche!

---

## ⚠️ Checklist avant lundi:

- [ ] Repo créé
- [ ] Fichiers uploadés
- [ ] 3 Secrets GitHub configurés
- [ ] Test lancé manuellement (log vert ✅)

C'est tout! Ton bot sera prêt lundi matin! 🚀⚽
