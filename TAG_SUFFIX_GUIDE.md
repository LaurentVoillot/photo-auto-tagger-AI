# Suffixe de tags automatiques - Guide d'utilisation

## 🎯 Objectif

Le suffixe permet de **différencier les tags générés automatiquement par l'IA des tags ajoutés manuellement** dans Lightroom.

## ✨ Fonctionnement

### Exemple

**Sans suffixe** :
```
Tags générés : Montagne, Mer, Ciel
→ Écrits dans Lightroom : Montagne, Mer, Ciel
```

**Avec suffixe `_ai`** (par défaut) :
```
Tags générés : Montagne, Mer, Ciel
→ Écrits dans Lightroom : Montagne_ai, Mer_ai, Ciel_ai
```

**Avec suffixe personnalisé `_auto`** :
```
Tags générés : Montagne, Mer, Ciel
→ Écrits dans Lightroom : Montagne_auto, Mer_auto, Ciel_auto
```

---

## 🖥️ Configuration dans l'interface

### Option 1 : Interface graphique

1. Lancer `photo_tagger_gui.py`
2. Section **"3. Destination des tags"**
3. Cocher **"Ajouter un suffixe aux tags automatiques"**
4. Modifier le suffixe dans le champ (défaut : `_ai`)

```
┌─────────────────────────────────────────────────┐
│ 3. Destination des tags                         │
├─────────────────────────────────────────────────┤
│ ☑ Écrire dans le catalogue Lightroom            │
│ ☑ Écrire dans les fichiers XMP                  │
│                                                 │
│ ☑ Ajouter un suffixe aux tags automatiques     │
│   Suffixe: [_ai    ]  (ex: Montagne → Montagne_ai)│
└─────────────────────────────────────────────────┘
```

### Option 2 : Fichier de configuration

Modifier `config.py` :

```python
# Suffixe à ajouter aux tags générés automatiquement
TAG_SUFFIX = "_ai"  # Modifier ici

# Activer/désactiver
TAG_SUFFIX_ENABLED = True  # True ou False

# Séparateur
TAG_SUFFIX_SEPARATOR = "_"  # "_" ou "-" ou autre
```

**Exemples de suffixes** :
- `_ai` → Montagne_ai
- `_auto` → Montagne_auto
- `-ia` → Montagne-ia
- `_generated` → Montagne_generated

---

## 💡 Cas d'usage

### 1. Vérifier les tags IA

Dans Lightroom, rechercher tous les tags IA :
```
Filtre mots-clés : *_ai
→ Affiche tous les tags automatiques
```

### 2. Nettoyer les tags IA

Supprimer tous les tags automatiques d'un coup :
```python
from tag_suffix import TagSuffixManager
import sqlite3

conn = sqlite3.connect('catalog.lrcat')
manager = TagSuffixManager()

# Trouver tous les tags avec suffixe
cursor = conn.cursor()
cursor.execute("SELECT id_local, name FROM AgLibraryKeyword WHERE name LIKE '%_ai'")
tags = cursor.fetchall()

for tag_id, tag_name in tags:
    # Supprimer le tag
    cursor.execute("DELETE FROM AgLibraryKeyword WHERE id_local = ?", (tag_id,))

conn.commit()
```

### 3. Convertir tags IA en tags manuels

Retirer le suffixe d'un tag :
```python
from tag_suffix import TagSuffixManager

manager = TagSuffixManager()

# Tag avec suffixe
tag = "Montagne_ai"

# Retirer le suffixe
clean_tag = manager.remove_suffix(tag)
print(clean_tag)  # → Montagne
```

### 4. Filtrer par type de tag

```python
from tag_suffix import TagSuffixManager

manager = TagSuffixManager()

all_tags = ["Montagne_ai", "Voyage", "Mer_ai", "France", "Été_ai"]

# Seulement les tags IA
auto_tags = manager.filter_auto_tags(all_tags)
print(auto_tags)  # → ['Montagne_ai', 'Mer_ai', 'Été_ai']

# Seulement les tags manuels
manual_tags = manager.filter_manual_tags(all_tags)
print(manual_tags)  # → ['Voyage', 'France']

# Statistiques
stats = manager.get_stats(all_tags)
print(stats)
# → {
#     'total': 5,
#     'auto': 3,
#     'manual': 2,
#     'auto_tags': ['Montagne_ai', 'Mer_ai', 'Été_ai'],
#     'manual_tags': ['Voyage', 'France']
# }
```

---

## 📊 Exemples dans Lightroom

### Avant traitement

```
Photo : IMG_1234.jpg
Tags manuels : Voyage, France, 2024
Tags IA : (aucun)
```

### Après traitement (suffixe activé)

```
Photo : IMG_1234.jpg
Tags manuels : Voyage, France, 2024
Tags IA : Montagne_ai, Mer_ai, Côte_ai, Paysage_ai
```

**Avantages** :
- ✅ On voit immédiatement quels tags sont automatiques
- ✅ On peut filtrer uniquement les tags IA
- ✅ On peut supprimer tous les tags IA d'un coup
- ✅ On peut affiner manuellement les tags IA

---

## 🔧 API Python

### Ajouter un suffixe

```python
from tag_suffix import apply_suffix_to_tags

tags = ["Montagne", "Mer", "Ciel"]
tags_with_suffix = apply_suffix_to_tags(tags, suffix="_ai", enabled=True)
print(tags_with_suffix)
# → ['Montagne_ai', 'Mer_ai', 'Ciel_ai']
```

### Retirer un suffixe

```python
from tag_suffix import remove_suffix_from_tags

tags = ["Montagne_ai", "Mer_ai", "Ciel_ai"]
tags_without_suffix = remove_suffix_from_tags(tags, suffix="_ai")
print(tags_without_suffix)
# → ['Montagne', 'Mer', 'Ciel']
```

### Utilisation avancée

```python
from tag_suffix import TagSuffixManager

# Créer un gestionnaire personnalisé
manager = TagSuffixManager(
    suffix="_custom",
    enabled=True,
    separator="-"
)

# Ajouter
tag = manager.add_suffix("Montagne")
print(tag)  # → Montagne-_custom

# Vérifier
has_it = manager.has_suffix("Montagne-_custom")
print(has_it)  # → True

# Retirer
clean = manager.remove_suffix("Montagne-_custom")
print(clean)  # → Montagne
```

---

## 🎯 Recommandations

### Pour débuter

**Activé avec `_ai`** (recommandé)
- ✅ Permet de tester l'IA sans polluer vos tags manuels
- ✅ Facile à supprimer si pas satisfait
- ✅ Permet de comparer IA vs manuel

### Pour production

**Deux approches** :

1. **Garder le suffixe** :
   - Pro : Traçabilité complète
   - Con : Tags plus longs dans l'interface

2. **Désactiver après validation** :
   - Pro : Tags propres
   - Con : Impossible de différencier après coup

### Workflow recommandé

```
Phase 1 - Test (suffixe activé)
  → Traiter 100 photos test
  → Vérifier qualité des tags IA
  → Ajuster les paramètres si besoin
  
Phase 2 - Validation (suffixe activé)
  → Traiter 500 photos
  → Comparer tags IA vs tags manuels
  → Affiner les mappings
  
Phase 3 - Production (décision)
  Option A : Garder le suffixe
    → Traiter toutes les photos
    → Tags clairement identifiés
  
  Option B : Désactiver le suffixe
    → Traiter toutes les photos
    → Tags propres mais non différenciables
```

---

## ❓ FAQ

### Q : Puis-je changer le suffixe en cours de route ?

**R :** Oui, mais les anciens tags garderont l'ancien suffixe.

```
Traitement 1 avec "_ai" : Montagne_ai
Traitement 2 avec "_auto" : Mer_auto
→ Les deux coexistent dans le catalogue
```

### Q : Le suffixe est-il écrit dans les XMP ?

**R :** Oui ! Le suffixe fait partie du tag.

```xml
<dc:subject>
  <rdf:Bag>
    <rdf:li>Montagne_ai</rdf:li>
    <rdf:li>Mer_ai</rdf:li>
  </rdf:Bag>
</dc:subject>
```

### Q : Que se passe-t-il si je désactive puis réactive ?

**R :** Rien ! Les tags déjà créés conservent leur forme.

```
Traitement 1 (activé) : Montagne_ai
Traitement 2 (désactivé) : Mer
Traitement 3 (réactivé) : Ciel_ai
→ Catalogue final : Montagne_ai, Mer, Ciel_ai
```

### Q : Peut-on avoir plusieurs suffixes ?

**R :** Non, un seul à la fois. Mais vous pouvez changer entre les traitements.

---

## 🔍 Débogage

### Vérifier si le suffixe est actif

```bash
python
>>> import config
>>> print(f"Enabled: {config.TAG_SUFFIX_ENABLED}")
>>> print(f"Suffix: {config.TAG_SUFFIX}")
```

### Tester le module

```bash
python
>>> from tag_suffix import TagSuffixManager
>>> m = TagSuffixManager()
>>> m.add_suffix("Test")
'Test_ai'
>>> m.has_suffix("Test_ai")
True
>>> m.remove_suffix("Test_ai")
'Test'
```

---

**Version** : 2.1  
**Module** : `tag_suffix.py`  
**Configuration** : `config.py`  
**Interface** : Section "3. Destination des tags"
