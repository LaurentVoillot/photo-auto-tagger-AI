# Fonctionnalité Pause/Resume

## 🎯 Vue d'ensemble

La fonctionnalité Pause/Resume permet de :
- ⏸️ **Mettre en pause** le traitement en cours
- 💾 **Sauvegarder** automatiquement l'état (configuration + progression)
- 🔄 **Reprendre** ultérieurement là où vous vous étiez arrêté
- 🚪 **Fermer l'application** pendant la pause

## 🎮 Boutons de contrôle

### ▶️ START
Lance un nouveau traitement depuis le début
- Réinitialise tous les compteurs
- Active les boutons Pause et Stop
- Désactive Resume

### ⏸️ PAUSE
Met en pause le traitement en cours
- Sauvegarde l'état actuel dans `photo_tagger_state.json`
- Arrête proprement le thread de traitement
- Permet de fermer l'application
- Active le bouton Resume

### ▶️ RESUME  
Reprend le traitement depuis l'état sauvegardé
- Charge la configuration sauvegardée
- Restaure la progression exacte
- Continue depuis la dernière photo traitée
- Préserve les statistiques

### ⏹️ STOP
Arrête définitivement le traitement
- Supprime l'état sauvegardé
- Impossible de reprendre
- Demande confirmation

## 📋 Cas d'usage

### Cas 1 : Pause longue (nuit, week-end)

```
Situation : Vous traitez 5000 photos, il est 23h

1. ▶️ START → Lancement du traitement
2. Traitement : 847 / 5000 photos (17%)
3. ⏸️ PAUSE → Sauvegarde automatique
4. Message : "Traitement mis en pause ! Progression : 847/5000"
5. Fermer l'application → Éteindre l'ordinateur

Le lendemain :
1. Lancer l'application
2. ▶️ RESUME → Reprend à la photo 848
3. Traitement continue automatiquement
```

### Cas 2 : Changement de priorité

```
Situation : Besoin urgent de libérer les ressources

1. Traitement en cours : 1234 / 3000 photos
2. ⏸️ PAUSE → État sauvegardé
3. Faire autre chose (montage vidéo, compilation, etc.)
4. Plus tard : ▶️ RESUME → Reprise automatique
```

### Cas 3 : Erreur de configuration

```
Situation : Vous réalisez qu'un mapping est incorrect

1. Traitement en cours : 234 / 1000 photos
2. ⏹️ STOP → Arrêt définitif (pas de sauvegarde)
3. Modifier les mappings
4. ▶️ START → Nouveau traitement depuis le début
```

### Cas 4 : Pannes / Plantages

```
Situation : L'application plante ou l'ordinateur s'éteint

1. Traitement en cours : 456 / 2000 photos
2. Crash / Coupure électrique
3. Relancer l'application
4. Si PAUSE avait été fait : ▶️ RESUME disponible
5. Sinon : Recommencer avec ▶️ START
```

## 💾 Fichier d'état sauvegardé

### Emplacement
```
photo_tagger_state.json
```
Dans le même dossier que l'application.

### Contenu

```json
{
  "version": "1.2",
  "timestamp": "2024-11-28 15:30:45.123456",
  "source_mode": "catalog",
  "catalog_path": "/Volumes/Photos/Catalog.lrcat",
  "folder_path": "",
  "selected_model": "qwen2-vl",
  "write_to_catalog": true,
  "write_to_xmp": true,
  "tagging_mode": "auto",
  "mappings": [
    ["la tour eiffel", "TourEiffel"],
    ["des bâtiments", "Architecture"]
  ],
  "current_photo": 847,
  "total_photos": 5000,
  "stats_tags_written_catalog": 820,
  "stats_tags_written_xmp": 815,
  "stats_xmp_skipped_no_file": 5
}
```

### Données sauvegardées

**Configuration** :
- Source (catalogue ou répertoire)
- Chemin du catalogue/dossier
- Modèle Ollama sélectionné
- Options d'écriture (catalogue/XMP)
- Mode de tagging (auto/ciblé)
- Liste des mappings

**Progression** :
- Photo courante (numéro)
- Total de photos
- Statistiques :
  - Tags écrits dans catalogue
  - XMP créés
  - XMP ignorés

## 🔄 Comportement détaillé

### Lors de PAUSE

```python
1. Utilisateur clique sur PAUSE
2. Confirmation : "Mettre en pause ?"
3. Flag should_pause = True
4. Fin de la photo en cours de traitement
5. Sauvegarde de l'état dans JSON
6. Arrêt du thread de traitement
7. Message : "Progression sauvegardée"
8. Boutons :
   - START : désactivé
   - PAUSE : désactivé  
   - RESUME : activé ✅
   - STOP : désactivé
```

### Lors de RESUME

```python
1. Utilisateur clique sur RESUME
2. Vérification existence de photo_tagger_state.json
3. Chargement du JSON
4. Restauration de tous les paramètres :
   - Interface : source, modèle, options
   - Mappings : remplissage de la table
   - Progression : current_photo, stats
5. Mise à jour de l'affichage
6. Lancement du thread
7. Boucle commence à current_photo + 1
8. Traitement continue normalement
```

### Lors de STOP

```python
1. Utilisateur clique sur STOP
2. Confirmation : "Arrêter ?"
3. Flag should_stop = True
4. Suppression de photo_tagger_state.json
5. Arrêt du thread
6. Message : "Traitement arrêté"
7. Boutons :
   - START : activé ✅
   - PAUSE : désactivé
   - RESUME : désactivé
   - STOP : désactivé
```

### Fin normale

```python
1. Dernière photo traitée
2. Suppression automatique de photo_tagger_state.json
3. Rapport final avec statistiques
4. Boutons :
   - START : activé ✅
   - PAUSE : désactivé
   - RESUME : désactivé
   - STOP : désactivé
```

## ⚠️ Limitations et précautions

### ❌ Ce qui n'est PAS sauvegardé

- **Connexions actives** : Ollama, catalogue Lightroom
- **Images en mémoire** : Les Smart Previews doivent être rechargés
- **Cache** : Pas de cache des réponses Ollama

### ⚡ Implications

**Lors de RESUME** :
- Reconnexion au catalogue nécessaire
- Rechargement de la liste des photos
- Les photos déjà traitées sont **ignorées** (pas retraitées)
- Statistiques **préservées** et continuées

### 🔒 Sécurité

**Le fichier d'état contient** :
- ✅ Chemins des fichiers (OK)
- ✅ Configuration (OK)
- ✅ Mappings (OK)
- ❌ Pas de données sensibles

**Peut être partagé** : Oui, mais inutile (chemins spécifiques à votre système)

### 🔍 Validité de l'état

**L'état sauvegardé est valide si** :
- Le catalogue existe toujours au même emplacement
- Le dossier de photos existe toujours
- Le modèle Ollama est toujours disponible
- La structure n'a pas changé (pas de photos ajoutées/supprimées)

**Sinon** :
- Message d'erreur approprié
- Suggestion de recommencer avec START

## 🧪 Tests recommandés

### Test 1 : Pause/Resume basique

```
1. START avec 100 photos
2. Attendre 10 photos traitées
3. PAUSE
4. Vérifier photo_tagger_state.json existe
5. RESUME
6. Vérifier reprise à photo 11
7. Laisser terminer
8. Vérifier photo_tagger_state.json supprimé
```

### Test 2 : Fermeture/réouverture

```
1. START avec 50 photos
2. Attendre 20 photos
3. PAUSE
4. Fermer l'application
5. Relancer l'application
6. Vérifier bouton RESUME actif
7. RESUME
8. Vérifier reprise à photo 21
```

### Test 3 : Statistiques préservées

```
1. START avec 30 photos
2. Attendre 15 photos (noter les stats)
3. PAUSE
4. RESUME
5. À la fin, vérifier :
   - Total = 30 photos traitées
   - Stats = somme correcte
```

### Test 4 : STOP vs PAUSE

```
1. START avec 20 photos
2. Attendre 10 photos
3. PAUSE
4. Vérifier état sauvegardé
5. STOP (au lieu de RESUME)
6. Vérifier état supprimé
7. RESUME désactivé
```

## 💡 Conseils d'utilisation

### ✅ Utilisez PAUSE quand

- Vous devez fermer l'ordinateur
- Traitement très long (>1h) et besoin de pause
- Libérer temporairement les ressources
- Vous voulez reprendre plus tard

### ✅ Utilisez STOP quand

- Vous avez fait une erreur de configuration
- Vous voulez recommencer depuis le début
- Le traitement ne donne pas les résultats attendus
- Vous ne prévoyez pas de reprendre

### ⚠️ Attention

- **Ne modifiez pas** le catalogue entre PAUSE et RESUME
- **Ne déplacez pas** les photos entre PAUSE et RESUME
- **Ne supprimez pas** `photo_tagger_state.json` manuellement
- **Fermez Lightroom** avant RESUME (comme avant START)

## 📊 Logs

```log
# Lors de PAUSE
INFO - Pause demandée par l'utilisateur
INFO - Traitement mis en pause
INFO - État sauvegardé: photo 847/5000

# Lors de RESUME
INFO - État chargé: photo 847/5000
INFO - Reprise du traitement à partir de la photo 847/5000
INFO - Connecté au catalogue: /Volumes/Photos/Catalog.lrcat
INFO - 5000 photos trouvées dans le catalogue
INFO - Traitement photo 848: IMG_0848.jpg
...

# Fin normale
INFO - État sauvegardé supprimé (traitement terminé)

# STOP
INFO - Arrêt demandé par l'utilisateur
INFO - État sauvegardé supprimé
```

## 🎓 Exemple complet

```
Scénario : Traiter 10000 photos d'astronomie

Lundi 18h - Session 1
  ▶️ START
  Progression : 0 → 2500 photos (3h)
  ⏸️ PAUSE → Dîner

Lundi 21h - Session 2
  ▶️ RESUME → 2500/10000
  Progression : 2500 → 5000 photos (3h)
  ⏸️ PAUSE → Sommeil
  Fermer l'application

Mardi 9h - Session 3
  Lancer l'application
  ▶️ RESUME → 5000/10000
  Progression : 5000 → 7500 photos (3h)
  ⏸️ PAUSE → Pause déjeuner

Mardi 14h - Session 4
  ▶️ RESUME → 7500/10000
  Progression : 7500 → 10000 photos (3h)
  ✅ Terminé !
  
Total : 10000 photos traitées
Temps : ~12h réparties sur 2 jours
```

---

**Version** : 1.3  
**Fonctionnalité** : Pause/Resume avec sauvegarde d'état  
**Fichier d'état** : `photo_tagger_state.json`
