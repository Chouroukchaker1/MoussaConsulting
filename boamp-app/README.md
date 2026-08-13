# MoussaConsulting · Extraction BOAMP

Application web pour extraire les annonces du BOAMP (Bulletin officiel des
annonces de marchés publics) et les formater pour appeloffres.net.

- **Backend** : Python (Flask), déployé comme fonction serverless Vercel (`api/index.py`)
- **Frontend** : React + Vite (`src/`)
- **Authentification** : identifiant / mot de passe (définis en variables d'environnement), jeton de session signé (JWT maison, sans dépendance)

## Fonctionnalités

- Page de connexion (identifiant + mot de passe)
- Extraction des annonces BOAMP sur une période donnée, filtrées par secteur
- Tableau de résultats avec export CSV / JSON
- Bouton de déconnexion

## Arborescence

```
api/index.py        → API Flask (login, secteurs, scrape)
src/                 → Frontend React
  App.jsx
  api.js             → client HTTP vers l'API
  pages/Login.jsx
  pages/Dashboard.jsx
vercel.json          → configuration de déploiement Vercel
requirements.txt      → dépendances Python
package.json          → dépendances frontend
```

## 1. Développement local

### Backend

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

export APP_USERNAME=admin
export APP_PASSWORD=motdepasse
export JWT_SECRET=une-chaine-aleatoire-longue

python api/index.py               # lance Flask sur http://127.0.0.1:5000

Alternative (Windows PowerShell helper):

```powershell
.\scripts\start-backend.ps1
```

Or use the npm script:

```powershell
npm run backend
```
```

### Frontend

Dans un autre terminal :

```bash
npm install
npm run dev                       # http://localhost:5173
```

Le frontend en dev proxie automatiquement `/api/*` vers `http://127.0.0.1:5000`
(voir `vite.config.js`). Connectez-vous avec `APP_USERNAME` / `APP_PASSWORD`.

## 2. Déploiement sur Vercel

### Option A — via l'interface Vercel

1. Poussez ce dossier sur un dépôt GitHub/GitLab/Bitbucket.
2. Sur [vercel.com](https://vercel.com), cliquez **Add New → Project**, puis
   importez le dépôt.
3. Vercel détecte automatiquement Vite pour le frontend et `api/index.py`
   comme fonction Python — aucune configuration supplémentaire n'est requise
   (tout est déjà décrit dans `vercel.json`).
4. Dans **Settings → Environment Variables**, ajoutez :
   - `APP_USERNAME`
   - `APP_PASSWORD`
   - `JWT_SECRET` (chaîne aléatoire longue, ex. générée avec `openssl rand -hex 32`)
   - `TOKEN_TTL_SECONDS` (optionnel, 28800 par défaut)
5. Cliquez **Deploy**.

### Option B — via la CLI Vercel

```bash
npm install -g vercel
vercel login
vercel                 # premier déploiement (suivre les invites)
vercel env add APP_USERNAME
vercel env add APP_PASSWORD
vercel env add JWT_SECRET
vercel --prod           # déploiement en production
```

## Sécurité — points à adapter avant mise en production

- Le mot de passe est comparé à une variable d'environnement en clair ; pour
  plusieurs utilisateurs ou une meilleure sécurité, remplacez cette logique
  par une vraie base d'utilisateurs avec mots de passe hashés (ex. `bcrypt`).
- `JWT_SECRET` doit être une valeur longue et aléatoire, différente entre
  environnements (preview / production).
- Le jeton est stocké côté client dans `sessionStorage` (effacé à la fermeture
  de l'onglet) — adaptez si vous avez besoin d'une session persistante.

## Filtrage par secteur

Le dataset BOAMP n'expose pas de champ "secteur" unique et fiable : le
filtrage se fait donc par mots-clés sur l'objet et les descripteurs de
chaque annonce (voir le dictionnaire `SECTEURS` dans `api/index.py`).
Vous pouvez librement ajouter, retirer ou affiner des secteurs et leurs
mots-clés à cet endroit.
