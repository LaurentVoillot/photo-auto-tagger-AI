"""
Module utilitaire pour la gestion des suffixes de tags.
Permet d'ajouter un suffixe aux tags générés automatiquement.
"""

import logging
from typing import List
import config

logger = logging.getLogger(__name__)


class TagSuffixManager:
    """Gestion des suffixes de tags."""
    
    def __init__(self, 
                 suffix: str = None, 
                 enabled: bool = None,
                 separator: str = None):
        """
        Initialise le gestionnaire de suffixes.
        
        Args:
            suffix: Suffixe à ajouter (défaut: config.TAG_SUFFIX)
            enabled: Activer/désactiver (défaut: config.TAG_SUFFIX_ENABLED)
            separator: Séparateur (défaut: config.TAG_SUFFIX_SEPARATOR)
        """
        self.suffix = suffix if suffix is not None else config.TAG_SUFFIX
        self.enabled = enabled if enabled is not None else config.TAG_SUFFIX_ENABLED
        self.separator = separator if separator is not None else config.TAG_SUFFIX_SEPARATOR
        
        logger.info(f"TagSuffixManager initialisé: suffix='{self.suffix}', enabled={self.enabled}")
    
    def add_suffix(self, tag: str) -> str:
        """
        Ajoute le suffixe à un tag.
        
        Args:
            tag: Tag original
            
        Returns:
            Tag avec suffixe si activé
        """
        if not self.enabled or not tag:
            return tag
        
        # Ne pas ajouter si déjà présent
        full_suffix = f"{self.separator}{self.suffix}"
        if tag.endswith(full_suffix):
            return tag
        
        return f"{tag}{full_suffix}"
    
    def add_suffix_to_list(self, tags: List[str]) -> List[str]:
        """
        Ajoute le suffixe à une liste de tags.
        
        Args:
            tags: Liste de tags
            
        Returns:
            Liste de tags avec suffixes
        """
        if not self.enabled:
            return tags
        
        suffixed_tags = [self.add_suffix(tag) for tag in tags]
        
        logger.debug(f"Tags originaux: {tags}")
        logger.debug(f"Tags avec suffixe: {suffixed_tags}")
        
        return suffixed_tags
    
    def remove_suffix(self, tag: str) -> str:
        """
        Retire le suffixe d'un tag.
        
        Args:
            tag: Tag avec suffixe
            
        Returns:
            Tag sans suffixe
        """
        if not tag:
            return tag
        
        full_suffix = f"{self.separator}{self.suffix}"
        if tag.endswith(full_suffix):
            return tag[:-len(full_suffix)]
        
        return tag
    
    def remove_suffix_from_list(self, tags: List[str]) -> List[str]:
        """
        Retire le suffixe d'une liste de tags.
        
        Args:
            tags: Liste de tags avec suffixes
            
        Returns:
            Liste de tags sans suffixes
        """
        return [self.remove_suffix(tag) for tag in tags]
    
    def has_suffix(self, tag: str) -> bool:
        """
        Vérifie si un tag a le suffixe.
        
        Args:
            tag: Tag à vérifier
            
        Returns:
            True si le tag a le suffixe
        """
        if not tag:
            return False
        
        full_suffix = f"{self.separator}{self.suffix}"
        return tag.endswith(full_suffix)
    
    def filter_auto_tags(self, tags: List[str]) -> List[str]:
        """
        Filtre uniquement les tags automatiques (avec suffixe).
        
        Args:
            tags: Liste de tous les tags
            
        Returns:
            Liste des tags avec suffixe uniquement
        """
        return [tag for tag in tags if self.has_suffix(tag)]
    
    def filter_manual_tags(self, tags: List[str]) -> List[str]:
        """
        Filtre uniquement les tags manuels (sans suffixe).
        
        Args:
            tags: Liste de tous les tags
            
        Returns:
            Liste des tags sans suffixe uniquement
        """
        return [tag for tag in tags if not self.has_suffix(tag)]
    
    def get_stats(self, tags: List[str]) -> dict:
        """
        Retourne des statistiques sur les tags.
        
        Args:
            tags: Liste de tags
            
        Returns:
            Dictionnaire de statistiques
        """
        auto_tags = self.filter_auto_tags(tags)
        manual_tags = self.filter_manual_tags(tags)
        
        return {
            'total': len(tags),
            'auto': len(auto_tags),
            'manual': len(manual_tags),
            'auto_tags': auto_tags,
            'manual_tags': manual_tags
        }


def apply_suffix_to_tags(tags: List[str], 
                         suffix: str = None,
                         enabled: bool = None) -> List[str]:
    """
    Fonction utilitaire pour ajouter un suffixe à une liste de tags.
    
    Args:
        tags: Liste de tags
        suffix: Suffixe (défaut: config.TAG_SUFFIX)
        enabled: Activer (défaut: config.TAG_SUFFIX_ENABLED)
        
    Returns:
        Liste de tags avec suffixes
    """
    manager = TagSuffixManager(suffix=suffix, enabled=enabled)
    return manager.add_suffix_to_list(tags)


def remove_suffix_from_tags(tags: List[str],
                            suffix: str = None) -> List[str]:
    """
    Fonction utilitaire pour retirer un suffixe d'une liste de tags.
    
    Args:
        tags: Liste de tags
        suffix: Suffixe (défaut: config.TAG_SUFFIX)
        
    Returns:
        Liste de tags sans suffixes
    """
    manager = TagSuffixManager(suffix=suffix)
    return manager.remove_suffix_from_list(tags)
