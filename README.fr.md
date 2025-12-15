# Photo Auto Tagger - Lightroom & Ollama

Application Python pour le tagging automatique de photos dans Adobe Lightroom Classic en utilisant des modèles de vision locaux via Ollama.

## 📋 Vue d'ensemble

Cette application permet d'analyser automatiquement vos photos et d'y appliquer des tags (mots-clés) en utilisant des modèles d'IA locaux. Les tags peuvent être écrits directement dans le catalogue Lightroom et/ou dans les fichiers XMP pour assurer la portabilité.

### Fonctionnalités principales

- ✅ **Analyse locale** : utilise Ollama avec des modèles de vision (qwen2-vl, qwen2.5-vl, etc.)
- ✅ **Deux modes de tagging** :
  - Mode automatique : génération de tags descriptifs généraux
  - Mode ciblé : recherche de critères spécifiques avec mapping personnalisé
- ✅ **Double écriture** : catalogue Lightroom (.lrcat) et/ou fichiers XMP
- ✅ **Deux sources** : catalogue Lightroom (Smart Previews) ou répertoire de photos
- ✅ **Interface graphique** : application GUI complète avec suivi de progression
- ✅ **Tags additifs** : les nouveaux tags s'ajoutent aux existants

## 🔧 Prérequis

### Logiciels requis

1. **Python 3.8+**
2. **Ollama** installé et en cours d'exécution
   - Installation : https://ollama.ai/
   - Au moins un modèle de vision installé (ex: `ollama pull qwen2-vl`)
3. **Adobe Lightroom Classic** (si utilisation du catalogue)

### Dépendances Python

```bash
pip install -r requirements.txt
```

Dépendances principales :
- `tkinter` (généralement inclus avec Python)
- `Pillow` : manipulation d'images
- `requests` : communication avec Ollama
- `sqlite3` : accès au catalogue Lightroom (module standard)

## 🚀 Installation

1. Cloner ou télécharger ce dépôt

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Vérifier qu'Ollama est en cours d'exécution :
```bash
ollama list
```

4. Si nécessaire, télécharger un modèle de vision :
```bash
ollama pull qwen2-vl
```

## 📖 Utilisation

### Lancement de l'application

```bash
python photo_tagger_gui.py
```

### Guide d'utilisation pas à pas

#### 1. Configuration du modèle
- Sélectionnez le modèle Ollama à utiliser dans la liste déroulante
- Les modèles disponibles sont automatiquement détectés

#### 2. Source des photos
Choisissez l'une des deux options :

**Option A : Catalogue Lightroom**
- Sélectionnez votre fichier catalogue (.lrcat)
- L'application analysera les Smart Previews (plus rapide)

**Option B : Répertoire de photos**
- Sélectionnez un dossier contenant vos photos
- ⚠️ Plus lent car analyse directe des fichiers originaux
- Les options catalogue seront automatiquement désactivées

#### 3. Destination des tags
Cochez au moins une option :
- ☑️ **Catalogue Lightroom** : écrit dans la base SQLite du catalogue
- ☑️ **Fichiers XMP** : crée/met à jour les fichiers XMP sidecar

> **Note** : En mode répertoire, seule l'option XMP est disponible

#### 4. Mode de tagging

**Mode automatique**
- Génère des tags descriptifs généraux pour chaque photo
- Prompt utilisé : "Décris cette photo sous forme de tags pour un logiciel photo"

**Mode ciblé**
- Définissez des critères de recherche avec les tags correspondants
- Exemple : "la tour eiffel" → "TourEiffel"
- Chaque photo est analysée pour tous les critères
- Si un critère est détecté, le tag correspondant est appliqué
- Une photo peut recevoir plusieurs tags si elle correspond à plusieurs critères

**Gestion du mapping :**
- Cliquez sur "➕ Ajouter un mapping" pour ajouter une ligne
- Cliquez sur 🗑️ pour supprimer une ligne
- Les cellules sont éditables directement

#### 5. Lancement du traitement
- Cliquez sur **▶️ START** pour démarrer
- Suivez la progression via :
  - Barre de progression visuelle
  - Compteur de photos traitées
  - Log en temps réel dans la console
- Cliquez sur **⏹️ STOP** pour arrêter à tout moment

## 🗂️ Structure du projet

```
photo-auto-tagger/
├── README.md                    # Ce fichier
├── TECHNICAL_DOC.md            # Documentation technique détaillée
├── requirements.txt            # Dépendances Python
├── photo_tagger_gui.py         # Application GUI principale
├── lightroom_manager.py        # Gestion du catalogue Lightroom
├── ollama_client.py            # Client pour l'API Ollama
├── xmp_manager.py              # Gestion des fichiers XMP
└── photo_tagger_interface.drawio  # Maquette de l'interface
```

## ⚠️ Avertissements et limitations

### Sauvegardes
- **IMPORTANT** : Faites toujours une sauvegarde de votre catalogue Lightroom avant traitement
- Les modifications dans le catalogue sont irréversibles sans sauvegarde

### Performances
- **Catalogue Lightroom** : rapide (utilise les Smart Previews)
- **Répertoire de photos** : plus lent (charge les images complètes)
- La vitesse dépend de :
  - La puissance de votre machine (RAM, GPU)
  - Le modèle Ollama utilisé
  - Le nombre de photos à traiter

### Compatibilité
- Testé avec Lightroom Classic 12.x et 13.x
- Fonctionne uniquement avec les catalogues locaux (pas Cloud)
- Les Smart Previews doivent être générés dans Lightroom

### Fichiers XMP
- Les XMP sont créés automatiquement s'ils n'existent pas
- Format compatible avec : Lightroom, Bridge, Photoshop, etc.
- Les tags existants sont préservés (ajout, pas remplacement)

## ⚡ Optimisation des performances

### Importance de l'optimisation du LLM

**Les performances dépendent fortement de votre configuration matérielle !** Un modèle mal adapté à votre machine peut être 10x plus lent.

#### 🖥️ Configuration matérielle

| Composant | Minimum | Recommandé | Optimal |
|-----------|---------|------------|---------|
| **RAM** | 16 Go | 32 Go | 64 Go+ |
| **GPU VRAM** | 6 Go | 8 Go | 12 Go+ |
| **CPU** | 4 cœurs | 8 cœurs | 16 cœurs+ |
| **Stockage** | HDD | SSD | NVMe SSD |

#### 🎯 Choix du modèle selon votre matériel

```bash
# Pour systèmes avec 32 Go+ RAM et bon GPU (RTX 3060+)
ollama pull qwen2-vl:7b       # Meilleur compromis qualité/vitesse

# Pour systèmes avec 16-32 Go RAM
ollama pull qwen2-vl:3b       # Plus léger, plus rapide

# Pour matériel limité/ancien
ollama pull llava:7b          # Plus compatible
```

#### 🚀 Création de modèles optimisés personnalisés

**Exemple** : Créer une variante rapide optimisée pour votre matériel

```bash
# Créer un Modelfile
cat > qwen-fast << EOF
FROM qwen2-vl:7b

# Optimiser pour la vitesse
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 2048
PARAMETER num_predict 100

# Prompt système pour tags concis
SYSTEM Tu es un expert en tagging de photos. Génère uniquement des mots-clés précis et concis.
EOF

# Construire le modèle personnalisé
ollama create qwen-fast -f qwen-fast

# Utiliser dans l'application
# Sélectionner "qwen-fast" dans le menu déroulant
```

#### 💡 Conseils de performance

1. **Utiliser les Smart Previews** (10-100x plus rapide)
   ```
   Lightroom → Tout sélectionner → Bibliothèque → Previews → Créer Smart Previews
   ```

2. **Ajuster la taille d'image** dans `config.py`:
   ```python
   IMAGE_MAX_SIZE = 1024  # Plus bas = plus rapide (512, 768, 1024, 2048)
   JPEG_QUALITY = 70      # Plus bas = plus rapide (50-90)
   ```

3. **Accélération GPU** (si disponible):
   ```bash
   # Vérifier l'utilisation GPU
   nvidia-smi  # NVIDIA
   rocm-smi    # AMD
   
   # Ollama utilise le GPU automatiquement s'il est détecté
   ```

#### 📊 Performances attendues

Avec **32 Go RAM** + **RTX 3060** + **qwen2-vl:7b** + **Smart Previews** :

| Taille catalogue | Temps traitement | Vitesse |
|------------------|------------------|---------|
| 1 000 photos | ~15 minutes | ~4 photos/min |
| 10 000 photos | ~2,5 heures | ~66 photos/min |
| 100 000 photos | ~1 jour | ~70 photos/min |
| 214 129 photos | ~2 jours | ~75 photos/min |

**Sans Smart Previews** : 5-10x plus lent (surtout sur disques externes)

#### 🔍 Surveiller les performances

```bash
# Terminal 1 : Surveiller Ollama
ollama logs

# Terminal 2 : Surveiller les ressources système
# macOS
top -o cpu

# Linux
htop

# Vérifier si le GPU est utilisé
nvidia-smi -l 1  # Mise à jour chaque seconde
```

#### 🐌 Résolution des problèmes de lenteur

**Problème** : Tags prenant 10+ secondes par photo

**Solutions** :
1. ✅ Créer des Smart Previews dans Lightroom
2. ✅ Utiliser un modèle plus petit/rapide (`qwen2-vl:3b` au lieu de `7b`)
3. ✅ Réduire `IMAGE_MAX_SIZE` à 512 ou 768
4. ✅ Fermer les autres applications
5. ✅ Vérifier que le GPU est détecté : `ollama run qwen2-vl "test"`
6. ✅ Augmenter la RAM si swap constant

## 🔍 Exemples de mapping critère/tag

| Critère de recherche | Tag à appliquer |
|---------------------|-----------------|
| la tour eiffel | TourEiffel |
| des bâtiments | Architecture |
| un coucher de soleil | Sunset |
| des montagnes | Montagne |
| la mer ou l'océan | Mer |
| des personnes | Personnes |
| un animal | Animaux |
| de la nourriture | Gastronomie |

## 🐛 Dépannage

### Ollama ne répond pas
```bash
# Vérifier qu'Ollama est lancé
ollama list

# Relancer Ollama si nécessaire
ollama serve
```

### Erreur "Catalogue verrouillé"
- Fermez Lightroom avant de lancer le traitement
- Vérifiez qu'aucun autre processus n'accède au catalogue

### Modèle introuvable
```bash
# Lister les modèles disponibles
ollama list

# Télécharger un modèle de vision
ollama pull qwen2-vl
```

### Tags non visibles dans Lightroom
- Synchronisez les métadonnées : Métadonnées > Lire les métadonnées
- Vérifiez que les fichiers XMP sont bien créés à côté des photos

## 📝 Changelog

### Version 1.0.0 (2024-11-28)
- Première version fonctionnelle
- Support catalogue Lightroom et répertoire
- Modes automatique et ciblé
- Écriture catalogue et XMP
- Interface graphique complète

## 📄 Licence

Ce projet est fourni tel quel, sans garantie. Utilisez-le à vos propres risques.

## 👤 Auteur

Laurent - Workflow photographique automatisé

## 🔗 Liens utiles

- [Ollama](https://ollama.ai/)
- [Adobe Lightroom Classic](https://www.adobe.com/products/photoshop-lightroom-classic.html)
- [Format XMP](https://www.adobe.com/products/xmp.html)
