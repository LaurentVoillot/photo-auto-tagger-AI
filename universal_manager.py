"""
Module de support pour Adobe Bridge et autres logiciels photo.
Utilise les fichiers XMP comme format universel.
"""

import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from xmp_manager import XMPManager

logger = logging.getLogger(__name__)


class UniversalPhotoManager:
    """
    Gestionnaire universel pour différents logiciels photo.
    Utilise XMP comme format d'échange.
    """
    
    SUPPORTED_APPS = {
        'lightroom': 'Adobe Lightroom Classic',
        'bridge': 'Adobe Bridge',
        'capture_one': 'Capture One',
        'darktable': 'Darktable',
        'digikam': 'DigiKam',
        'acdsee': 'ACDSee',
        'on1': 'ON1 Photo RAW',
        'luminar': 'Luminar',
        'xmp_only': 'XMP uniquement (universel)'
    }
    
    def __init__(self, app_type: str = 'xmp_only'):
        """
        Initialise le gestionnaire.
        
        Args:
            app_type: Type d'application (voir SUPPORTED_APPS)
        """
        self.app_type = app_type
        self.xmp_manager = XMPManager()
        logger.info(f"Gestionnaire initialisé pour: {self.SUPPORTED_APPS.get(app_type, 'Inconnu')}")
    
    def find_photos_in_folder(self, folder_path: str, recursive: bool = True) -> List[Dict]:
        """
        Trouve toutes les photos dans un dossier.
        
        Args:
            folder_path: Chemin du dossier
            recursive: Recherche récursive
            
        Returns:
            Liste de photos
        """
        supported_extensions = {
            '.jpg', '.jpeg', '.png', '.tif', '.tiff',
            '.cr2', '.cr3', '.nef', '.arw', '.dng', '.raf',
            '.orf', '.rw2', '.pef', '.srw'
        }
        
        photos = []
        folder = Path(folder_path)
        
        if not folder.exists():
            logger.error(f"Dossier introuvable: {folder_path}")
            return photos
        
        # Chercher les fichiers
        pattern = "**/*" if recursive else "*"
        
        for file_path in folder.glob(pattern):
            if file_path.suffix.lower() in supported_extensions:
                photos.append({
                    'full_path': str(file_path),
                    'filename': file_path.name,
                    'folder': str(file_path.parent),
                    'extension': file_path.suffix.lower()
                })
        
        logger.info(f"{len(photos)} photo(s) trouvée(s) dans {folder_path}")
        return photos
    
    def write_tags_universal(self, photo_path: str, tags: List[str]) -> bool:
        """
        Écrit des tags de manière universelle (XMP).
        Compatible avec tous les logiciels.
        
        Args:
            photo_path: Chemin de la photo
            tags: Liste de tags
            
        Returns:
            True si succès
        """
        try:
            # Écrire dans XMP (universel)
            success = self.xmp_manager.write_tags(photo_path, tags)
            
            if success:
                logger.info(f"Tags universels écrits pour: {photo_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur écriture tags universels: {e}")
            return False
    
    def read_tags_universal(self, photo_path: str) -> List[str]:
        """
        Lit des tags de manière universelle (XMP).
        
        Args:
            photo_path: Chemin de la photo
            
        Returns:
            Liste de tags
        """
        try:
            tags = self.xmp_manager.read_tags(photo_path)
            logger.debug(f"{len(tags)} tag(s) lu(s) depuis: {photo_path}")
            return tags
            
        except Exception as e:
            logger.error(f"Erreur lecture tags universels: {e}")
            return []
    
    def batch_process_folder(self, folder_path: str, tag_function, recursive: bool = True) -> Dict:
        """
        Traite un dossier complet en batch.
        
        Args:
            folder_path: Dossier à traiter
            tag_function: Fonction de génération de tags
            recursive: Recherche récursive
            
        Returns:
            Statistiques du traitement
        """
        photos = self.find_photos_in_folder(folder_path, recursive)
        
        stats = {
            'total': len(photos),
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for photo in photos:
            try:
                # Vérifier si déjà traité
                existing_tags = self.read_tags_universal(photo['full_path'])
                if existing_tags:
                    logger.debug(f"Photo déjà taguée, ignorée: {photo['filename']}")
                    stats['skipped'] += 1
                    continue
                
                # Générer les tags
                new_tags = tag_function(photo['full_path'])
                
                if new_tags:
                    # Écrire les tags
                    if self.write_tags_universal(photo['full_path'], new_tags):
                        stats['success'] += 1
                    else:
                        stats['failed'] += 1
                else:
                    stats['skipped'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                logger.error(f"Erreur traitement {photo['filename']}: {e}")
                stats['failed'] += 1
        
        logger.info(f"Traitement terminé: {stats}")
        return stats
    
    def verify_xmp_sidecar(self, photo_path: str) -> Dict:
        """
        Vérifie l'existence et la validité du fichier XMP sidecar.
        
        Args:
            photo_path: Chemin de la photo
            
        Returns:
            Informations sur le XMP
        """
        xmp_path = self.xmp_manager.get_xmp_path(photo_path)
        
        info = {
            'photo': photo_path,
            'xmp_path': xmp_path,
            'exists': os.path.exists(xmp_path),
            'valid': False,
            'tags': []
        }
        
        if info['exists']:
            try:
                tags = self.xmp_manager.read_tags(photo_path)
                info['valid'] = True
                info['tags'] = tags
            except:
                info['valid'] = False
        
        return info
    
    def create_xmp_for_folder(self, folder_path: str, force: bool = False) -> int:
        """
        Crée des fichiers XMP pour toutes les photos d'un dossier.
        
        Args:
            folder_path: Dossier à traiter
            force: Écraser les XMP existants
            
        Returns:
            Nombre de XMP créés
        """
        photos = self.find_photos_in_folder(folder_path, recursive=False)
        created = 0
        
        for photo in photos:
            xmp_path = self.xmp_manager.get_xmp_path(photo['full_path'])
            
            if os.path.exists(xmp_path) and not force:
                logger.debug(f"XMP existe déjà: {xmp_path}")
                continue
            
            # Créer un XMP vide ou avec tags existants
            existing_tags = self.read_tags_universal(photo['full_path'])
            
            if self.write_tags_universal(photo['full_path'], existing_tags or []):
                created += 1
        
        logger.info(f"{created} fichier(s) XMP créé(s) dans {folder_path}")
        return created
    
    def get_app_specific_notes(self, app_type: str) -> str:
        """
        Retourne des notes spécifiques à l'application.
        
        Args:
            app_type: Type d'application
            
        Returns:
            Notes d'utilisation
        """
        notes = {
            'bridge': """
Adobe Bridge - Notes d'utilisation:
- Bridge lit automatiquement les fichiers XMP sidecars
- Les tags apparaissent dans le panneau Mots-clés
- Pour synchroniser: Fichier → Lire les métadonnées
- Compatible avec tous les formats RAW
            """,
            'capture_one': """
Capture One - Notes d'utilisation:
- Importer les photos dans le catalogue
- Outils → Lire les métadonnées depuis les fichiers
- Les tags apparaissent dans l'inspecteur de métadonnées
- Supporte XMP pour RAW et JPEG
            """,
            'darktable': """
Darktable - Notes d'utilisation:
- Importer le dossier dans la table lumineuse
- Darktable lit automatiquement les XMP
- Tags visibles dans le module "tagging"
- Open source et gratuit
            """,
            'digikam': """
DigiKam - Notes d'utilisation:
- Ajouter le dossier aux collections
- Paramètres → Configurer DigiKam → Métadonnées → Lire depuis XMP
- Tags intégrés à la base de données DigiKam
- Support excellent des XMP
            """
        }
        
        return notes.get(app_type, "Application supportée via XMP sidecars standard")
