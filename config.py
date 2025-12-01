"""
Configuration pour Photo Auto Tagger
Modifiez ces paramètres selon vos besoins
"""

# ===== Paramètres Ollama =====

# Timeout pour les requêtes Ollama (en secondes)
# Augmentez si vous avez des timeouts fréquents
# Valeur par défaut: 300 (5 minutes)
OLLAMA_TIMEOUT = 300

# Nombre de tentatives en cas d'échec
# Valeur par défaut: 2
OLLAMA_MAX_RETRIES = 2

# URL du serveur Ollama
# Valeur par défaut: "http://localhost:11434"
OLLAMA_BASE_URL = "http://localhost:11434"

# ===== Paramètres d'image =====

# Taille maximale des images envoyées à Ollama (en pixels)
# Plus petit = plus rapide mais moins précis
# Plus grand = plus lent mais plus précis
# Valeur par défaut: 1024
IMAGE_MAX_SIZE = 1024

# Qualité JPEG pour l'encodage (1-100)
# Plus bas = plus rapide mais moins précis
# Plus haut = plus lent mais plus précis
# Valeur par défaut: 70
JPEG_QUALITY = 70

# ===== Paramètres de prompt =====

# Langue des tags générés
# Options: "français", "english", "español", "deutsch", "italiano", etc.
# Valeur par défaut: "français"
TAG_LANGUAGE = "français"

# Prompt pour le mode automatique
AUTO_PROMPT = """Décris cette photo sous forme de tags pour un logiciel photo.
Retourne uniquement une liste de mots-clés séparés par des virgules, sans numérotation ni formatage.
Exemple de réponse attendue: Paris, Tour Eiffel, Monument, Architecture, Nuit

Règles:
- Mots-clés en {language}
- Entre 5 et 15 tags
- Précis et descriptifs
- Sans articles (le, la, les, un, une, des)
"""

# Template de prompt pour le mode ciblé
# {criteria} sera remplacé par le critère de recherche
TARGETED_PROMPT_TEMPLATE = """Analyse cette photo et réponds uniquement par OUI ou NON.

Question: Cette photo contient-elle {criteria} ?

Réponds UNIQUEMENT par:
- OUI si tu détectes clairement {criteria} dans l'image
- NON sinon

Ne donne aucune explication, juste OUI ou NON.
"""

# ===== Paramètres de génération =====

# Température pour la génération (0.0 - 1.0)
# 0.0 = très déterministe
# 1.0 = très créatif/aléatoire
# Valeur par défaut: 0.1
TEMPERATURE = 0.1

# Nombre maximum de tokens à générer
# Valeur par défaut: 100
MAX_TOKENS = 100

# ===== Paramètres de logging =====

# Niveau de log (DEBUG, INFO, WARNING, ERROR)
# DEBUG = tous les détails
# INFO = informations importantes
# WARNING = avertissements uniquement
# ERROR = erreurs uniquement
# Valeur par défaut: INFO
LOG_LEVEL = "INFO"

# Fichier de log
# Valeur par défaut: "photo_tagger.log"
LOG_FILE = "photo_tagger.log"

# ===== Paramètres de traitement =====

# Nombre maximum de tags à générer par photo
# Valeur par défaut: 15
MAX_TAGS_PER_PHOTO = 15

# Ignorer les photos si échec de chargement
# True = continuer avec les autres photos
# False = arrêter le traitement
# Valeur par défaut: True
SKIP_ON_ERROR = True

# ===== Formats d'image supportés =====

# Extensions de fichiers supportées (en minuscules)
SUPPORTED_IMAGE_FORMATS = [
    '.jpg', '.jpeg', '.png', '.tif', '.tiff',
    '.cr2', '.nef', '.arw', '.dng', '.raf',
    '.orf', '.rw2', '.pef', '.srw'
]

# ===== Configuration XMP =====

# Créer automatiquement les XMP s'ils n'existent pas
# Valeur par défaut: True
XMP_AUTO_CREATE = True

# Préfixe pour les namespaces XMP personnalisés (si besoin)
# Valeur par défaut: None (utilise les standards Adobe)
XMP_CUSTOM_NAMESPACE = None


# ===== Configuration des tags =====

# Suffixe à ajouter aux tags générés automatiquement
# Permet de différencier les tags IA des tags manuels
# Exemple: "Montagne" devient "Montagne_ai"
# Valeur par défaut: "_ai"
TAG_SUFFIX = "_ai"

# Activer/désactiver le suffixe automatique
# True = ajoute le suffixe (ex: "Montagne_ai")
# False = pas de suffixe (ex: "Montagne")
# Valeur par défaut: True
TAG_SUFFIX_ENABLED = True

# Séparateur avant le suffixe
# Valeur par défaut: "_"
TAG_SUFFIX_SEPARATOR = "_"


# ===== Fonctions utilitaires =====

def get_config():
    """Retourne un dictionnaire avec toute la configuration."""
    return {
        'ollama': {
            'timeout': OLLAMA_TIMEOUT,
            'max_retries': OLLAMA_MAX_RETRIES,
            'base_url': OLLAMA_BASE_URL,
            'temperature': TEMPERATURE,
            'max_tokens': MAX_TOKENS
        },
        'image': {
            'max_size': IMAGE_MAX_SIZE,
            'jpeg_quality': JPEG_QUALITY
        },
        'prompts': {
            'auto': AUTO_PROMPT,
            'targeted_template': TARGETED_PROMPT_TEMPLATE,
            'tag_language': TAG_LANGUAGE
        },
        'logging': {
            'level': LOG_LEVEL,
            'file': LOG_FILE
        },
        'processing': {
            'max_tags': MAX_TAGS_PER_PHOTO,
            'skip_on_error': SKIP_ON_ERROR,
            'supported_formats': SUPPORTED_IMAGE_FORMATS
        },
        'xmp': {
            'auto_create': XMP_AUTO_CREATE,
            'custom_namespace': XMP_CUSTOM_NAMESPACE
        },
        'tags': {
            'suffix': TAG_SUFFIX,
            'suffix_enabled': TAG_SUFFIX_ENABLED,
            'suffix_separator': TAG_SUFFIX_SEPARATOR
        }
    }


def print_config():
    """Affiche la configuration actuelle."""
    config = get_config()
    
    print("\n" + "="*60)
    print("Configuration Photo Auto Tagger")
    print("="*60 + "\n")
    
    for section, params in config.items():
        print(f"[{section.upper()}]")
        for key, value in params.items():
            print(f"  {key}: {value}")
        print()


if __name__ == "__main__":
    print_config()
