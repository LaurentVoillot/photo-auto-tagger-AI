# Guide de dépannage - Problèmes courants

## 🔴 Problème : Timeout Ollama (Read timed out)

### Symptôme
```
HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=120)
```

### Causes possibles
1. **Images trop grandes** : Les photos haute résolution (ex: 6000x4000) prennent beaucoup de temps à analyser
2. **Modèle trop lent** : Certains modèles sont plus lents que d'autres
3. **RAM insuffisante** : Le modèle swap sur disque
4. **CPU/GPU surchargé** : Autres processus consomment les ressources

### Solutions

#### Solution 1 : Augmenter le timeout (RECOMMANDÉ)

Éditez `config.py` :
```python
OLLAMA_TIMEOUT = 600  # 10 minutes au lieu de 5
```

Ou modifiez directement dans `ollama_client.py` ligne 21 :
```python
def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 600):
```

#### Solution 2 : Réduire la taille des images (TRÈS EFFICACE)

Éditez `config.py` :
```python
IMAGE_MAX_SIZE = 768   # Au lieu de 1024
JPEG_QUALITY = 60      # Au lieu de 70
```

**Impact** :
- Taille 1920 → 1024 : gain ~50% de temps
- Taille 1024 → 768 : gain ~30% de temps supplémentaire
- Qualité 70 → 60 : gain ~10% de temps

#### Solution 3 : Utiliser un modèle plus rapide

```bash
# Essayez ces modèles (du plus rapide au plus lent) :
ollama pull llava:7b          # Le plus rapide
ollama pull llava:13b         # Bon équilibre
ollama pull qwen2-vl:7b       # Qualité supérieure
ollama pull qwen2.5-vl:7b     # Meilleure qualité, plus lent
```

#### Solution 4 : Vérifier les ressources

```bash
# Voir la mémoire utilisée par Ollama
ps aux | grep ollama

# Sur macOS, vérifier l'activité
Activity Monitor > chercher "ollama"

# Fermer les applications gourmandes en RAM/CPU
```

#### Solution 5 : Pré-charger le modèle

```bash
# Garder le modèle en mémoire avant de lancer l'application
ollama run qwen2-vl
# Tapez "exit" pour sortir mais laisser le modèle en mémoire
```

## 🔴 Problème : Fichiers XMP non créés

### Symptôme
```
WARNING - Aucun tag généré pour: {'full_path': '...', 'filename': '...'}
```
Aucun fichier `.xmp` n'apparaît à côté des photos.

### Causes
1. **Timeout Ollama** → Aucun tag généré → Aucun XMP créé
2. **Erreur de parsing** → Tags mal extraits de la réponse
3. **Permissions fichiers** → Impossible d'écrire le XMP
4. **Chemin incorrect** → XMP créé au mauvais endroit

### Solutions

#### Solution 1 : Résoudre d'abord les timeouts (voir ci-dessus)

Si vous avez des timeouts, **aucun XMP ne sera créé**. Résolvez d'abord les timeouts.

#### Solution 2 : Vérifier les logs détaillés

Activez le mode DEBUG dans `config.py` :
```python
LOG_LEVEL = "DEBUG"
```

Relancez et vérifiez `photo_tagger.log` :
```bash
tail -f photo_tagger.log
```

Recherchez :
- "Réponse brute Ollama:" → Vérifiez ce que répond le modèle
- "Tags générés:" → Vérifiez que des tags sont extraits
- "XMP créé" ou "XMP mis à jour" → Vérifiez l'écriture XMP

#### Solution 3 : Test manuel de l'écriture XMP

Créez un fichier `test_xmp.py` :
```python
from xmp_manager import XMPManager
import logging

logging.basicConfig(level=logging.DEBUG)

manager = XMPManager()

# Remplacez par le chemin d'une de vos photos
test_photo = "/chemin/vers/votre/photo.jpg"
test_tags = ["Test1", "Test2", "Test3"]

print(f"Test écriture XMP pour: {test_photo}")
success = manager.write_tags(test_photo, test_tags)

if success:
    print("✅ XMP créé avec succès !")
    xmp_path = manager.get_xmp_path(test_photo)
    print(f"Fichier créé: {xmp_path}")
    
    # Vérifier lecture
    tags = manager.read_tags(test_photo)
    print(f"Tags lus: {tags}")
else:
    print("❌ Échec création XMP")
```

Lancez :
```bash
python test_xmp.py
```

#### Solution 4 : Vérifier les permissions

```bash
# Sur macOS/Linux, vérifier les permissions du dossier
ls -la /chemin/vers/vos/photos/

# Vérifier que vous pouvez créer des fichiers
touch /chemin/vers/vos/photos/test.txt
rm /chemin/vers/vos/photos/test.txt
```

#### Solution 5 : Forcer la création XMP même sans tags (DEBUG)

Modifiez temporairement `photo_tagger_gui.py`, méthode `_process_single_photo`, ligne ~670 :

```python
if not tags:
    logger.warning(f"Aucun tag généré pour: {photo.get('filename', photo)}")
    # MODE DEBUG : Créer XMP avec tag de test
    tags = ["DEBUG_NoTagsGenerated"]  # Ajoutez cette ligne
    # return  # Commentez cette ligne
```

Cela créera un XMP avec un tag "DEBUG_NoTagsGenerated" pour voir si le problème vient de la génération de tags ou de l'écriture XMP.

## 🔴 Problème : Images d'astronomie (ex: IC 434)

Vos photos sont des images astronomiques empilées. Ces images ont des caractéristiques particulières :

### Spécificités
- **Très haute résolution** : Souvent 10000+ pixels
- **Contenu inhabituel** : Nébuleuses, étoiles (peu présent dans les données d'entraînement)
- **Post-traitement lourd** : DxO, empilage (_mosaic_, _Stacked_)
- **Fichiers volumineux** : Plusieurs Mo par image

### Recommandations

#### 1. Réduire drastiquement la taille

Pour l'astronomie, éditez `config.py` :
```python
IMAGE_MAX_SIZE = 512    # Très petit mais suffisant
JPEG_QUALITY = 50       # Qualité basse acceptable
```

#### 2. Augmenter significativement le timeout

```python
OLLAMA_TIMEOUT = 900    # 15 minutes pour images complexes
```

#### 3. Utiliser un prompt adapté à l'astronomie

Pour le mode automatique, éditez `config.py` :
```python
AUTO_PROMPT = """Décris cette image astronomique avec des mots-clés.
Retourne uniquement une liste séparée par des virgules.

Exemples de mots-clés valides:
- Type d'objet: Nébuleuse, Galaxie, Amas, Étoile, Planète
- Nom d'objet: IC 434, M31, NGC 7000, Orion
- Caractéristiques: Emission, Réflexion, Sombre, Coloré
- Technique: Empilage, Mosaique, Longue pose, Narrowband

Règles:
- 5 à 10 mots-clés
- Français ou codes catalogue (IC, NGC, M)
- Sans articles
"""
```

#### 4. Mode ciblé pour l'astronomie

Exemples de mappings :
```
Critère                           | Tag
----------------------------------|------------------
une nébuleuse                     | Nebuleuse
la nébuleuse IC 434               | IC434
une nébuleuse en émission         | Emission
des étoiles                       | Etoiles
un objet du catalogue Messier     | Messier
un objet du catalogue NGC         | NGC
un objet du catalogue IC          | IC
une image en narrowband           | Narrowband
une image en SHO                  | SHO
une image RGB                     | RGB
```

#### 5. Traiter par petits lots

Pour les images astro :
1. **Testez avec 1 image** d'abord
2. Si ça marche, traitez **5-10 images**
3. Puis augmentez progressivement

## 🔧 Configuration optimale pour vos photos d'astronomie

Créez un fichier `config_astro.py` :

```python
# Configuration spéciale pour photos d'astronomie

OLLAMA_TIMEOUT = 900  # 15 minutes
OLLAMA_MAX_RETRIES = 3
IMAGE_MAX_SIZE = 512
JPEG_QUALITY = 50
MAX_TOKENS = 150

AUTO_PROMPT = """Décris cette image astronomique avec des mots-clés séparés par des virgules.

Types: Nébuleuse, Galaxie, Amas, Étoile, Planète
Noms: IC, NGC, M (codes catalogue)
Caractéristiques: Emission, Réflexion, Sombre, Coloré, Narrowband
Techniques: Empilage, Mosaique, Longue pose

Réponds uniquement avec la liste de mots-clés, sans numéros ni formatage.
"""
```

Puis modifiez `ollama_client.py` pour importer cette config :
```python
try:
    from config_astro import *
except ImportError:
    from config import *
```

## 📊 Tableau récapitulatif des solutions

| Problème | Solution rapide | Solution optimale |
|----------|----------------|-------------------|
| Timeout | Augmenter à 600s | Réduire taille à 768px + timeout 600s |
| XMP non créé | Résoudre timeout | Activer DEBUG et vérifier logs |
| Images astro | Taille 512px, timeout 900s | Config dédiée + prompt adapté |
| Lenteur générale | Modèle llava:7b | Pré-charger modèle + fermer apps |

## 🎯 Checklist avant de relancer

- [ ] Augmenter timeout à 600s minimum (900s pour astro)
- [ ] Réduire IMAGE_MAX_SIZE à 768 (512 pour astro)
- [ ] Activer LOG_LEVEL = "DEBUG"
- [ ] Pré-charger le modèle : `ollama run qwen2-vl`
- [ ] Fermer les applications gourmandes
- [ ] Tester avec UNE seule image d'abord
- [ ] Vérifier les logs : `tail -f photo_tagger.log`
- [ ] Vérifier création XMP : `ls -la /chemin/vers/photos/*.xmp`

## 📞 Si rien ne fonctionne

1. **Testez le script de test XMP** (voir Solution 3)
2. **Vérifiez que Ollama répond** : `ollama run qwen2-vl "décris cette image"`
3. **Essayez un modèle plus simple** : `ollama pull llava:7b`
4. **Vérifiez les logs complets** : `cat photo_tagger.log`
5. **Testez avec une image simple** (pas d'astronomie) pour isoler le problème
