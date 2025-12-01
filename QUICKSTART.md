# Guide de démarrage rapide - Photo Auto Tagger

## 🚀 Installation et premier lancement

### Étape 1 : Vérifier les prérequis

```bash
# Vérifier Python (3.8+ requis)
python --version

# Vérifier Ollama
ollama list

# Si Ollama n'est pas lancé
ollama serve
```

### Étape 2 : Installer les dépendances

```bash
# Se placer dans le dossier du projet
cd /chemin/vers/photo-auto-tagger

# Installer les dépendances Python
pip install -r requirements.txt
```

### Étape 3 : Télécharger un modèle de vision

```bash
# Modèle recommandé : Qwen2-VL
ollama pull qwen2-vl

# Alternative : Qwen2.5-VL (plus récent)
ollama pull qwen2.5-vl

# Vérifier l'installation
ollama list
```

### Étape 4 : Lancer l'application

```bash
python photo_tagger_gui.py
```

## 📋 Utilisation rapide

### Mode automatique (tags généraux)

1. **Sélectionner le modèle** : `qwen2-vl` dans la liste
2. **Choisir la source** :
   - Option 1 : Catalogue Lightroom (.lrcat)
   - Option 2 : Dossier de photos
3. **Destination** : Cocher "Catalogue" et/ou "XMP"
4. **Mode** : Laisser "Mode automatique"
5. **Cliquer sur START**

### Mode ciblé (recherche spécifique)

1. Suivre les étapes 1-3 ci-dessus
2. **Mode** : Sélectionner "Mode ciblé"
3. **Ajouter des mappings** :
   - Cliquer sur "➕ Ajouter un mapping"
   - Entrer le critère : "la tour eiffel"
   - Entrer le tag : "TourEiffel"
   - Cliquer sur OK
4. **Répéter** pour d'autres critères
5. **Cliquer sur START**

## ⚙️ Configuration recommandée

### Pour de meilleures performances

1. **Utiliser le catalogue Lightroom** si possible :
   - Plus rapide (Smart Previews)
   - Intégration native
   - Tags directement dans Lightroom

2. **Choisir le bon modèle** :
   - `qwen2-vl` : Bon équilibre vitesse/qualité
   - `qwen2.5-vl` : Meilleure qualité, un peu plus lent
   - Éviter les modèles trop gros si RAM limitée

3. **Traitement par lots** :
   - Ne pas traiter toutes les photos d'un coup
   - Commencer par un petit lot de test (10-20 photos)
   - Vérifier les résultats avant de continuer

### Paramètres Ollama recommandés

Les paramètres optimaux sont déjà configurés dans le code :
- `temperature: 0.1` (réponses déterministes)
- Timeout: 120 secondes
- Pas de streaming

## 🔧 Résolution des problèmes courants

### "Ollama non disponible"

```bash
# Vérifier qu'Ollama est lancé
ollama serve

# Dans un autre terminal, tester
ollama list
```

### "Catalogue verrouillé"

- Fermer Lightroom avant le traitement
- Le catalogue ne peut être ouvert que par un seul processus

### "Pas de Smart Preview"

- Dans Lightroom : Bibliothèque > Aperçus > Créer des aperçus 1:1
- Ou utiliser le mode "Répertoire de photos" (plus lent)

### Tags non visibles dans Lightroom

```
Lightroom > Métadonnées > Lire les métadonnées depuis les fichiers
```

### Erreur "Module not found"

```bash
# Réinstaller les dépendances
pip install -r requirements.txt --upgrade
```

## 📊 Exemples de mappings critère/tag

### Lieux et monuments

| Critère | Tag |
|---------|-----|
| la tour eiffel | TourEiffel |
| l'arc de triomphe | ArcDeTriomphe |
| la cathédrale Notre-Dame | NotreDame |
| la muraille de Chine | MurailleChine |

### Architecture

| Critère | Tag |
|---------|-----|
| des bâtiments | Architecture |
| un gratte-ciel | Gratteciel |
| une église | Eglise |
| un pont | Pont |

### Nature

| Critère | Tag |
|---------|-----|
| un coucher de soleil | Sunset |
| des montagnes | Montagne |
| la mer ou l'océan | Mer |
| une forêt | Foret |

### Sujets

| Critère | Tag |
|---------|-----|
| des personnes | Personnes |
| un animal | Animaux |
| un chat | Chat |
| un chien | Chien |
| de la nourriture | Gastronomie |

## 📈 Workflow recommandé

### 1. Préparation (une seule fois)

```bash
# Créer une sauvegarde du catalogue
cp MonCatalogue.lrcat MonCatalogue_backup.lrcat

# Générer les Smart Previews dans Lightroom
# Bibliothèque > Aperçus > Créer des aperçus dynamiques
```

### 2. Test initial (10-20 photos)

- Sélectionner un petit lot de test
- Lancer en mode automatique
- Vérifier la qualité des tags générés

### 3. Ajustement

- Si les tags sont trop généraux → passer en mode ciblé
- Si certains sujets manquent → ajouter des mappings
- Si trop de faux positifs → affiner les critères

### 4. Traitement complet

- Une fois satisfait, traiter tout le catalogue
- Surveiller la progression
- Vérifier régulièrement les résultats

### 5. Validation finale

```
Lightroom > Métadonnées > Lire les métadonnées depuis les fichiers
```

## 🎯 Conseils pour de meilleurs résultats

### Formulation des critères

✅ **Bon** :
- "la tour eiffel"
- "un coucher de soleil"
- "des montagnes enneigées"

❌ **Éviter** :
- "tour eiffel" (sans article)
- "sunset" (utiliser le français)
- "photo avec montagne" (trop verbeux)

### Nommage des tags

✅ **Bon** :
- "TourEiffel" (PascalCase)
- "CoucherSoleil"
- "Architecture"

❌ **Éviter** :
- "tour eiffel" (avec espaces)
- "TOUR_EIFFEL" (trop technique)
- "Tour Eiffel Monument Paris" (trop long)

### Stratégie de tagging

**Option 1 : Large puis précis**
1. Mode automatique pour tags généraux
2. Mode ciblé pour éléments spécifiques

**Option 2 : Ciblé uniquement**
- Créer une liste exhaustive de critères
- Tagging très précis dès le départ

## 📞 Support

En cas de problème :
1. Vérifier les logs : `photo_tagger.log`
2. Consulter la documentation : `TECHNICAL_DOC.md`
3. Vérifier qu'Ollama fonctionne : `ollama list`

## 🎓 Pour aller plus loin

- Tester différents modèles de vision
- Créer des scripts de traitement par lots
- Intégrer dans un workflow automatisé
- Explorer l'API REST d'Ollama pour des besoins avancés
