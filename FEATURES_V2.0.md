# Guide des nouvelles fonctionnalités - Version 2.0

## 🎉 7 nouvelles fonctionnalités ajoutées !

### 📋 Liste des fonctionnalités

1. **Filtres de sélection avancés** - Filtrer les photos à traiter
2. **Profiles de tagging sauvegardables** - Sauvegarder vos configurations
3. **Détection de tags similaires** - Fusionner les doublons
4. **Suggestions EXIF** - Tags automatiques depuis métadonnées
5. **Tags hiérarchiques** - Organisation en arborescence
6. **Support universel** - Adobe Bridge, Capture One, etc.
7. **Export CSV/JSON** - Exporter vos tags

---

## 1️⃣ Filtres de sélection avancés

### Utilisation

```python
from photo_filters import PhotoFilter

# Créer un filtre
filter = PhotoFilter()

# Photos sans tags uniquement
filter.set_filter('only_untagged', True)

# Période spécifique
filter.set_filter('date_from', '2024-01-01')
filter.set_filter('date_to', '2024-12-31')

# Note minimale
filter.set_filter('min_rating', 3)  # 3 étoiles minimum

# Collection spécifique
filter.set_filter('collection', 'Mes meilleures photos')

# Résumé
print(filter.get_active_filters_summary())
# → "Sans tags uniquement | Période : depuis 2024-01-01 jusqu'au 2024-12-31 | Note ≥ 3 étoiles"
```

### Cas d'usage

**Scénario 1** : Traiter uniquement les nouvelles photos
```python
filter.set_filter('only_untagged', True)
# → Ne traite que les photos qui n'ont aucun tag
```

**Scénario 2** : Photos d'une période
```python
filter.set_filter('date_from', '2024-07-01')
filter.set_filter('date_to', '2024-07-31')
# → Uniquement les photos de juillet 2024
```

**Scénario 3** : Meilleures photos uniquement
```python
filter.set_filter('min_rating', 4)
# → Uniquement les photos avec 4-5 étoiles
```

---

## 2️⃣ Profiles de tagging sauvegardables

### Utilisation

```python
from tagging_profiles import TaggingProfile

# Créer le gestionnaire
profiles = TaggingProfile()

# Sauvegarder une configuration
config = {
    'model': 'qwen2-vl',
    'temperature': 0.05,
    'write_to_catalog': True,
    'write_to_xmp': True,
    'tagging_mode': 'targeted',
    'mappings': [
        ['nébuleuse', 'Nebuleuse'],
        ['galaxie', 'Galaxie']
    ]
}
profiles.save_profile('Astronomie Deep Sky', config)

# Charger un profile
loaded_config = profiles.load_profile('Astronomie Deep Sky')

# Lister les profiles
all_profiles = profiles.list_profiles()
for profile in all_profiles:
    print(f"- {profile['name']} (créé le {profile['created']})")

# Exporter/Importer
profiles.export_profile('Astronomie Deep Sky', '/path/to/export.json')
profiles.import_profile('/path/to/received_profile.json')
```

### Profiles par défaut inclus

Le système crée automatiquement 3 profiles :

1. **Astronomie Deep Sky**
   - Température basse (0.05)
   - Mappings pour nébuleuses, galaxies, amas
   - Tags auto : Astrophoto, DeepSky

2. **Photos de voyage**
   - Mode automatique
   - Tag auto : Voyage

3. **Architecture**
   - Mappings pour styles architecturaux
   - Tag auto : Architecture

---

## 3️⃣ Détection de tags similaires

### Utilisation

```python
from similar_tags import SimilarTagDetector
import sqlite3

# Créer le détecteur
detector = SimilarTagDetector()

# Connexion au catalogue
conn = sqlite3.connect('/path/to/catalog.lrcat')

# Trouver les tags similaires
similar_groups = detector.find_similar_tags(conn)

for group in similar_groups:
    print(f"\nTags similaires détectés:")
    for tag_id, name, count in group['tags']:
        print(f"  - {name} ({count} photos)")

# Fusionner des tags
# Garder "Architecture" et fusionner "Bâtiment" et "Building"
source_ids = [id_batiment, id_building]
target_id = id_architecture
detector.merge_tags(conn, source_ids, target_id)

# Sauvegarder la décision
detector.save_decision(
    tag_names=['Architecture', 'Bâtiment', 'Building'],
    chosen_tag='Architecture',
    action='merge'
)
```

### Fichier de décisions

Les décisions sont sauvegardées dans `tag_merge_decisions.json` :

```json
{
  "Architecture||Bâtiment||Building": {
    "tags": ["Architecture", "Bâtiment", "Building"],
    "chosen": "Architecture",
    "action": "merge",
    "timestamp": "2024-11-28T16:30:00"
  }
}
```

**Avantage** : La prochaine fois, le système ne redemandera pas !

---

## 4️⃣ Suggestions EXIF

### Utilisation

```python
from exif_suggester import EXIFTagSuggester

# Créer le suggesteur
suggester = EXIFTagSuggester()

# Suggérer des tags depuis EXIF
tags = suggester.suggest_tags_from_exif('/path/to/photo.jpg')
print(f"Tags suggérés: {tags}")
# → ['Canon', 'Canon EOS R', 'Longue exposition', 'ISO élevé', 'Coucher du soleil']

# Informations détaillées
exif_info = suggester.get_detailed_exif_info('/path/to/photo.jpg')
print(suggester.format_exif_display(exif_info))
# → 📷 Appareil : Canon EOS R
#   🔭 Objectif : RF 24-105mm F4 L IS USM
#   ⚙️ Paramètres : 1/125s • f/8.0 • ISO 400 • 50mm
#   📅 Date : 2024:07:15 19:30:00
```

### Tags automatiques générés

Basés sur :
- **Appareil** : Canon, Nikon, Sony, etc.
- **ISO** : ISO élevé (≥3200), ISO moyen (≥1600)
- **Exposition** : Longue exposition (≥1s), Pose longue (≥30s)
- **Ouverture** : Grande ouverture (≤f/2.8), Petite ouverture (≥f/11)
- **Focale** : Grand angle (≤35mm), Téléobjectif (≥200mm), Portrait (50-85mm)
- **Flash** : Avec/Sans flash
- **Heure** : Lever du soleil, Coucher du soleil, Nuit
- **Saison** : Hiver, Printemps, Été, Automne

---

## 5️⃣ Tags hiérarchiques

### Utilisation

```python
from hierarchical_tags import HierarchicalTagger

# Créer le gestionnaire
htagger = HierarchicalTagger()

# Développer un tag avec ses parents
full_path = htagger.expand_tag_with_parents('Nébuleuse')
print(full_path)
# → ['Astronomie', 'Deep Sky', 'Nébuleuse']

# Suggérer des enfants
children = htagger.suggest_child_tags('Nébuleuse')
print(children)
# → ['Emission', 'Réflexion', 'Obscure']

# Ajouter un tag personnalisé
htagger.add_tag_to_hierarchy('IC434', parent='Nébuleuse')

# Exporter l'arbre
tree = htagger.export_as_tree()
print(tree)
# → Nature
#   ├── Paysage
#   │   ├── Montagne
#   │   ├── Mer
#   │   └── Forêt
#   ├── Animaux
#   │   ├── Oiseaux
#   │   └── Mammifères
#   └── Végétation
```

### Hiérarchie par défaut

```
Nature
  ├─ Paysage (Montagne, Mer, Forêt, Désert)
  ├─ Animaux (Oiseaux, Mammifères, Insectes, Reptiles)
  ├─ Végétation (Arbres, Fleurs, Plantes)
  └─ Ciel (Nuages, Coucher de soleil, Arc-en-ciel)

Architecture
  ├─ Bâtiments (Moderne, Ancien, Religieux)
  ├─ Monuments
  └─ Ponts

Astronomie
  ├─ Deep Sky
  │   ├─ Nébuleuse (Emission, Réflexion, Obscure)
  │   ├─ Galaxie (Spirale, Elliptique)
  │   └─ Amas (Ouvert, Globulaire)
  └─ Système solaire (Lune, Planètes, Soleil)
```

---

## 6️⃣ Support universel (Bridge, Capture One, etc.)

### Applications supportées

- Adobe Bridge
- Adobe Lightroom Classic
- Capture One
- Darktable
- DigiKam
- ACDSee
- ON1 Photo RAW
- Luminar
- **XMP uniquement** (universel)

### Utilisation

```python
from universal_manager import UniversalPhotoManager

# Mode XMP universel
manager = UniversalPhotoManager(app_type='xmp_only')

# Trouver les photos
photos = manager.find_photos_in_folder('/path/to/photos', recursive=True)
print(f"{len(photos)} photos trouvées")

# Écrire des tags (universel via XMP)
manager.write_tags_universal('/path/to/photo.jpg', ['Nature', 'Montagne', 'Été'])

# Lire des tags
tags = manager.read_tags_universal('/path/to/photo.jpg')
print(f"Tags : {tags}")

# Traitement batch
def my_tag_function(photo_path):
    # Votre logique de génération de tags
    return ['Tag1', 'Tag2']

stats = manager.batch_process_folder('/path/to/photos', my_tag_function)
print(stats)
# → {'total': 100, 'processed': 95, 'success': 90, 'failed': 5, 'skipped': 5}

# Notes spécifiques à l'application
notes = manager.get_app_specific_notes('bridge')
print(notes)
```

### Notes Adobe Bridge

```
Adobe Bridge - Notes d'utilisation:
- Bridge lit automatiquement les fichiers XMP sidecars
- Les tags apparaissent dans le panneau Mots-clés
- Pour synchroniser: Fichier → Lire les métadonnées
- Compatible avec tous les formats RAW
```

---

## 7️⃣ Export CSV/JSON

### Utilisation

```python
from tag_exporter import TagExporter
import sqlite3

exporter = TagExporter()
conn = sqlite3.connect('/path/to/catalog.lrcat')

# Export vers CSV
exporter.export_from_catalog_to_csv(conn, 'export_tags.csv')

# Export vers JSON
exporter.export_from_catalog_to_json(conn, 'export_tags.json', pretty=True)

# Export statistiques
exporter.export_tag_statistics_to_csv(conn, 'stats_tags.csv')

# Export XMP d'un dossier vers CSV
exporter.export_xmp_folder_to_csv('/path/to/photos', 'xmp_tags.csv')

# Export Markdown (rapport)
exporter.export_to_markdown(conn, 'rapport_tags.md')
```

### Formats de sortie

**CSV (export_tags.csv)** :
```csv
Photo ID,Chemin,Nom de fichier,Tags,Date de capture,Note
1234,/Volumes/Photos/IMG_1234.jpg,IMG_1234.jpg,"Tour, Mer, Architecture",2024-07-15 19:30:00,4
1235,/Volumes/Photos/IMG_1235.jpg,IMG_1235.jpg,"Montagne, Neige",2024-01-10 14:20:00,5
```

**JSON (export_tags.json)** :
```json
{
  "export_date": "2024-11-28T16:30:00",
  "total_photos": 1547,
  "photos": [
    {
      "id": 1234,
      "path": "/Volumes/Photos/IMG_1234.jpg",
      "filename": "IMG_1234.jpg",
      "tags": ["Tour", "Mer", "Architecture"],
      "capture_time": "2024-07-15 19:30:00",
      "rating": 4
    }
  ]
}
```

**Markdown (rapport_tags.md)** :
```markdown
# Rapport de tags

**Date** : 2024-11-28 16:30:00

## 📊 Statistiques globales

- Total de photos : **1547**
- Photos taguées : **1520** (98.3%)
- Total de tags : **245**

## 🏆 Top 20 des tags

| Rang | Tag | Nombre de photos |
|------|-----|------------------|
| 1 | Nébuleuse | 345 |
| 2 | IC434 | 234 |
| 3 | Narrowband | 198 |
```

---

## 🎯 Workflows recommandés

### Workflow 1 : Premier traitement complet

```python
# 1. Créer un profile
profiles = TaggingProfile()
config = {...}  # Votre config
profiles.save_profile('Mon workflow', config)

# 2. Appliquer des filtres
filter = PhotoFilter()
filter.set_filter('only_untagged', True)

# 3. Traiter
# → Utilisez photo_tagger_gui.py avec le profile chargé

# 4. Exporter
exporter = TagExporter()
exporter.export_from_catalog_to_csv(conn, 'backup_tags.csv')
```

### Workflow 2 : Nettoyage des tags

```python
# 1. Détecter les similaires
detector = SimilarTagDetector()
similar = detector.find_similar_tags(conn)

# 2. Fusionner
for group in similar:
    # Demander à l'utilisateur quel tag garder
    # Fusionner avec detector.merge_tags()
    pass

# 3. Exporter les stats
exporter.export_tag_statistics_to_csv(conn, 'stats_after_cleanup.csv')
```

### Workflow 3 : Migration vers Bridge

```python
# 1. Export depuis Lightroom
exporter = TagExporter()
exporter.export_from_catalog_to_json(conn, 'lightroom_tags.json')

# 2. Créer XMP universels
manager = UniversalPhotoManager('xmp_only')
manager.create_xmp_for_folder('/path/to/photos')

# 3. Ouvrir dans Bridge
# → Les tags apparaissent automatiquement !
```

---

## 📚 Documentation des modules

- `photo_filters.py` - Filtrage avancé
- `tagging_profiles.py` - Gestion profiles
- `similar_tags.py` - Détection doublons
- `exif_suggester.py` - Suggestions EXIF
- `hierarchical_tags.py` - Tags hiérarchiques
- `universal_manager.py` - Support multi-apps
- `tag_exporter.py` - Export CSV/JSON/MD

---

**Version** : 2.0  
**Date** : 2024-11-28  
**Nouvelles fonctionnalités** : 7  
**Modules ajoutés** : 7
