"""
Module de filtrage des photos pour sélection avancée.
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PhotoFilter:
    """Gestion des filtres de sélection de photos."""
    
    def __init__(self):
        """Initialise le filtre."""
        self.filters = {
            'only_untagged': False,
            'date_from': None,
            'date_to': None,
            'min_rating': None,
            'collection': None,
            'exclude_already_processed': False
        }
    
    def set_filter(self, filter_name: str, value):
        """
        Définit un filtre.
        
        Args:
            filter_name: Nom du filtre
            value: Valeur du filtre
        """
        if filter_name in self.filters:
            self.filters[filter_name] = value
            logger.debug(f"Filtre '{filter_name}' défini à: {value}")
    
    def apply_filters_catalog(self, conn: sqlite3.Connection, base_query: str) -> tuple:
        """
        Applique les filtres à une requête de catalogue Lightroom.
        
        Args:
            conn: Connexion au catalogue
            base_query: Requête SQL de base
            
        Returns:
            Tuple (query modifiée, paramètres)
        """
        conditions = []
        params = []
        
        # Filtre : uniquement photos sans tags
        if self.filters['only_untagged']:
            conditions.append("""
                ai.id_local NOT IN (
                    SELECT image FROM AgLibraryKeywordImage
                )
            """)
        
        # Filtre : période de dates
        if self.filters['date_from']:
            conditions.append("ai.captureTime >= ?")
            params.append(self.filters['date_from'])
        
        if self.filters['date_to']:
            # Ajouter 23:59:59 pour inclure toute la journée
            end_date = f"{self.filters['date_to']} 23:59:59"
            conditions.append("ai.captureTime <= ?")
            params.append(end_date)
        
        # Filtre : note minimale (rating)
        if self.filters['min_rating'] is not None:
            conditions.append("ai.rating >= ?")
            params.append(self.filters['min_rating'])
        
        # Filtre : collection spécifique
        if self.filters['collection']:
            conditions.append("""
                ai.id_local IN (
                    SELECT image FROM AgLibraryCollectionImage aci
                    INNER JOIN AgLibraryCollection ac ON aci.collection = ac.id_local
                    WHERE ac.name LIKE ?
                )
            """)
            params.append(f"%{self.filters['collection']}%")
        
        # Construire la requête finale
        if conditions:
            where_clause = " AND " + " AND ".join(conditions)
            modified_query = base_query.replace("WHERE ai.id_local IS NOT NULL", 
                                               f"WHERE ai.id_local IS NOT NULL {where_clause}")
        else:
            modified_query = base_query
        
        logger.info(f"Filtres appliqués: {sum(1 for v in self.filters.values() if v)}")
        return modified_query, tuple(params)
    
    def apply_filters_folder(self, photos: List[Dict]) -> List[Dict]:
        """
        Applique les filtres à une liste de photos d'un dossier.
        
        Args:
            photos: Liste de photos
            
        Returns:
            Liste filtrée
        """
        filtered = photos
        
        # Filtre : période de dates (si EXIF disponible)
        if self.filters['date_from'] or self.filters['date_to']:
            from PIL import Image
            from PIL.ExifTags import TAGS
            
            def get_capture_time(photo_path: str) -> Optional[datetime]:
                """Extrait la date de capture depuis EXIF."""
                try:
                    img = Image.open(photo_path)
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if tag == 'DateTimeOriginal':
                                return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                except:
                    pass
                return None
            
            date_filtered = []
            for photo in filtered:
                capture_time = get_capture_time(photo['full_path'])
                if capture_time:
                    if self.filters['date_from']:
                        from_dt = datetime.strptime(self.filters['date_from'], '%Y-%m-%d')
                        if capture_time < from_dt:
                            continue
                    
                    if self.filters['date_to']:
                        to_dt = datetime.strptime(self.filters['date_to'], '%Y-%m-%d')
                        to_dt = to_dt.replace(hour=23, minute=59, second=59)
                        if capture_time > to_dt:
                            continue
                
                date_filtered.append(photo)
            
            filtered = date_filtered
        
        logger.info(f"Photos après filtrage: {len(filtered)}/{len(photos)}")
        return filtered
    
    def get_active_filters_summary(self) -> str:
        """
        Retourne un résumé des filtres actifs.
        
        Returns:
            Texte descriptif
        """
        active = []
        
        if self.filters['only_untagged']:
            active.append("Sans tags uniquement")
        
        if self.filters['date_from'] or self.filters['date_to']:
            date_range = "Période : "
            if self.filters['date_from']:
                date_range += f"depuis {self.filters['date_from']}"
            if self.filters['date_to']:
                if self.filters['date_from']:
                    date_range += f" jusqu'au {self.filters['date_to']}"
                else:
                    date_range += f"jusqu'au {self.filters['date_to']}"
            active.append(date_range)
        
        if self.filters['min_rating'] is not None:
            active.append(f"Note ≥ {self.filters['min_rating']} étoiles")
        
        if self.filters['collection']:
            active.append(f"Collection : {self.filters['collection']}")
        
        if self.filters['exclude_already_processed']:
            active.append("Exclure photos déjà traitées")
        
        if not active:
            return "Aucun filtre actif"
        
        return " | ".join(active)
    
    def reset_filters(self):
        """Réinitialise tous les filtres."""
        for key in self.filters:
            if isinstance(self.filters[key], bool):
                self.filters[key] = False
            else:
                self.filters[key] = None
        
        logger.info("Filtres réinitialisés")
