"""
Module de gestion de tags hiérarchiques.
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HierarchicalTagger:
    """Gestion de tags hiérarchiques."""
    
    def __init__(self, hierarchy_file: str = "tag_hierarchy.json"):
        """
        Initialise le gestionnaire hiérarchique.
        
        Args:
            hierarchy_file: Fichier de hiérarchie
        """
        self.hierarchy_file = Path(hierarchy_file)
        self.hierarchy = self._load_hierarchy()
    
    def _load_hierarchy(self) -> Dict:
        """Charge la hiérarchie depuis le fichier."""
        if self.hierarchy_file.exists():
            try:
                with open(self.hierarchy_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erreur chargement hiérarchie: {e}")
        
        # Hiérarchie par défaut
        return self._get_default_hierarchy()
    
    def _get_default_hierarchy(self) -> Dict:
        """Retourne la hiérarchie par défaut."""
        return {
            'Nature': {
                'Paysage': {
                    'Montagne': {},
                    'Mer': {},
                    'Forêt': {},
                    'Désert': {}
                },
                'Animaux': {
                    'Oiseaux': {},
                    'Mammifères': {},
                    'Insectes': {},
                    'Reptiles': {}
                },
                'Végétation': {
                    'Arbres': {},
                    'Fleurs': {},
                    'Plantes': {}
                },
                'Ciel': {
                    'Nuages': {},
                    'Coucher de soleil': {},
                    'Lever de soleil': {},
                    'Arc-en-ciel': {}
                }
            },
            'Architecture': {
                'Bâtiments': {
                    'Moderne': {},
                    'Ancien': {},
                    'Religieux': {}
                },
                'Monuments': {},
                'Ponts': {},
                'Intérieur': {}
            },
            'Personnes': {
                'Portrait': {},
                'Groupe': {},
                'Famille': {},
                'Enfants': {}
            },
            'Astronomie': {
                'Deep Sky': {
                    'Nébuleuse': {
                        'Emission': {},
                        'Réflexion': {},
                        'Obscure': {}
                    },
                    'Galaxie': {
                        'Spirale': {},
                        'Elliptique': {},
                        'Irrégulière': {}
                    },
                    'Amas': {
                        'Ouvert': {},
                        'Globulaire': {}
                    }
                },
                'Système solaire': {
                    'Lune': {},
                    'Planètes': {},
                    'Soleil': {}
                }
            },
            'Événements': {
                'Voyage': {},
                'Mariage': {},
                'Fête': {},
                'Sport': {}
            }
        }
    
    def _save_hierarchy(self):
        """Sauvegarde la hiérarchie."""
        try:
            with open(self.hierarchy_file, 'w', encoding='utf-8') as f:
                json.dump(self.hierarchy, f, indent=2, ensure_ascii=False)
            logger.info(f"Hiérarchie sauvegardée: {self.hierarchy_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde hiérarchie: {e}")
    
    def expand_tag_with_parents(self, tag: str) -> List[str]:
        """
        Développe un tag avec tous ses parents.
        
        Args:
            tag: Tag à développer
            
        Returns:
            Liste [parent, sous-parent, ..., tag]
        """
        def find_path(hierarchy: Dict, target: str, path: List[str] = []) -> Optional[List[str]]:
            """Recherche récursive du chemin."""
            for key, children in hierarchy.items():
                if key == target:
                    return path + [key]
                if isinstance(children, dict) and children:
                    result = find_path(children, target, path + [key])
                    if result:
                        return result
            return None
        
        path = find_path(self.hierarchy, tag)
        return path if path else [tag]
    
    def suggest_child_tags(self, parent_tag: str) -> List[str]:
        """
        Suggère des tags enfants pour un tag parent.
        
        Args:
            parent_tag: Tag parent
            
        Returns:
            Liste des tags enfants
        """
        def find_children(hierarchy: Dict, target: str) -> Optional[List[str]]:
            """Recherche récursive des enfants."""
            for key, children in hierarchy.items():
                if key == target:
                    if isinstance(children, dict):
                        return list(children.keys())
                    return []
                if isinstance(children, dict) and children:
                    result = find_children(children, target)
                    if result is not None:
                        return result
            return None
        
        children = find_children(self.hierarchy, parent_tag)
        return children if children else []
    
    def add_tag_to_hierarchy(self, tag: str, parent: Optional[str] = None):
        """
        Ajoute un tag à la hiérarchie.
        
        Args:
            tag: Tag à ajouter
            parent: Tag parent (None = racine)
        """
        def add_to_dict(hierarchy: Dict, parent_name: str, child_name: str) -> bool:
            """Ajout récursif."""
            for key, children in hierarchy.items():
                if key == parent_name:
                    if isinstance(children, dict):
                        children[child_name] = {}
                        return True
                    return False
                if isinstance(children, dict) and children:
                    if add_to_dict(children, parent_name, child_name):
                        return True
            return False
        
        if parent is None:
            self.hierarchy[tag] = {}
        else:
            if not add_to_dict(self.hierarchy, parent, tag):
                logger.warning(f"Parent '{parent}' introuvable")
                return
        
        self._save_hierarchy()
        logger.info(f"Tag '{tag}' ajouté sous '{parent or 'racine'}'")
    
    def get_all_tags_flat(self) -> List[str]:
        """
        Retourne tous les tags à plat.
        
        Returns:
            Liste de tous les tags
        """
        def flatten(hierarchy: Dict) -> List[str]:
            """Aplatit récursivement."""
            tags = []
            for key, children in hierarchy.items():
                tags.append(key)
                if isinstance(children, dict) and children:
                    tags.extend(flatten(children))
            return tags
        
        return flatten(self.hierarchy)
    
    def export_as_tree(self) -> str:
        """
        Exporte la hiérarchie sous forme d'arbre ASCII.
        
        Returns:
            Représentation texte
        """
        def build_tree(hierarchy: Dict, prefix: str = "", is_last: bool = True) -> str:
            """Construction récursive."""
            lines = []
            items = list(hierarchy.items())
            
            for i, (key, children) in enumerate(items):
                is_last_item = (i == len(items) - 1)
                connector = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{connector}{key}")
                
                if isinstance(children, dict) and children:
                    extension = "    " if is_last_item else "│   "
                    lines.append(build_tree(children, prefix + extension, is_last_item))
            
            return "\n".join(lines)
        
        return build_tree(self.hierarchy)
