"""
Module de gestion des profiles de tagging.
Permet de sauvegarder et charger des configurations complètes.
"""

import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TaggingProfile:
    """Gestion des profiles de tagging."""
    
    def __init__(self, profiles_dir: str = "profiles"):
        """
        Initialise le gestionnaire de profiles.
        
        Args:
            profiles_dir: Dossier contenant les profiles
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.current_profile = None
    
    def save_profile(self, name: str, config: Dict) -> bool:
        """
        Sauvegarde un profile de configuration.
        
        Args:
            name: Nom du profile
            config: Configuration à sauvegarder
            
        Returns:
            True si succès
        """
        try:
            profile_data = {
                'name': name,
                'version': '1.4',
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'config': config
            }
            
            # Nom de fichier sécurisé
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            filename = self.profiles_dir / f"{safe_name}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Profile '{name}' sauvegardé: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde profile '{name}': {e}")
            return False
    
    def load_profile(self, name: str) -> Optional[Dict]:
        """
        Charge un profile de configuration.
        
        Args:
            name: Nom du profile
            
        Returns:
            Configuration ou None si erreur
        """
        try:
            # Chercher le fichier
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            filename = self.profiles_dir / f"{safe_name}.json"
            
            if not filename.exists():
                logger.error(f"Profile '{name}' introuvable")
                return None
            
            with open(filename, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            self.current_profile = profile_data
            logger.info(f"Profile '{name}' chargé")
            
            return profile_data['config']
            
        except Exception as e:
            logger.error(f"Erreur chargement profile '{name}': {e}")
            return None
    
    def list_profiles(self) -> List[Dict]:
        """
        Liste tous les profiles disponibles.
        
        Returns:
            Liste de profiles avec métadonnées
        """
        profiles = []
        
        try:
            for filepath in self.profiles_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    
                    profiles.append({
                        'name': profile_data['name'],
                        'created': profile_data.get('created', 'inconnu'),
                        'modified': profile_data.get('modified', 'inconnu'),
                        'filepath': str(filepath)
                    })
                except:
                    logger.warning(f"Impossible de lire {filepath}")
            
            profiles.sort(key=lambda x: x['name'])
            logger.info(f"{len(profiles)} profile(s) trouvé(s)")
            
        except Exception as e:
            logger.error(f"Erreur liste profiles: {e}")
        
        return profiles
    
    def delete_profile(self, name: str) -> bool:
        """
        Supprime un profile.
        
        Args:
            name: Nom du profile
            
        Returns:
            True si succès
        """
        try:
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            filename = self.profiles_dir / f"{safe_name}.json"
            
            if filename.exists():
                filename.unlink()
                logger.info(f"Profile '{name}' supprimé")
                return True
            else:
                logger.warning(f"Profile '{name}' introuvable")
                return False
                
        except Exception as e:
            logger.error(f"Erreur suppression profile '{name}': {e}")
            return False
    
    def export_profile(self, name: str, export_path: str) -> bool:
        """
        Exporte un profile vers un fichier.
        
        Args:
            name: Nom du profile
            export_path: Chemin de destination
            
        Returns:
            True si succès
        """
        try:
            config = self.load_profile(name)
            if not config:
                return False
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_profile, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Profile '{name}' exporté vers: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export profile '{name}': {e}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[str]:
        """
        Importe un profile depuis un fichier.
        
        Args:
            import_path: Chemin du fichier à importer
            
        Returns:
            Nom du profile importé ou None si erreur
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            name = profile_data['name']
            
            # Sauvegarder dans le dossier profiles
            self.save_profile(name, profile_data['config'])
            
            logger.info(f"Profile '{name}' importé depuis: {import_path}")
            return name
            
        except Exception as e:
            logger.error(f"Erreur import profile: {e}")
            return None
    
    def get_default_profiles(self) -> List[Dict]:
        """
        Retourne des profiles par défaut prédéfinis.
        
        Returns:
            Liste de profiles par défaut
        """
        defaults = [
            {
                'name': 'Astronomie Deep Sky',
                'config': {
                    'model': 'qwen2-vl',
                    'temperature': 0.05,
                    'write_to_catalog': True,
                    'write_to_xmp': True,
                    'tagging_mode': 'targeted',
                    'mappings': [
                        ['une nébuleuse en émission', 'Emission'],
                        ['une nébuleuse obscure', 'Obscure'],
                        ['une galaxie', 'Galaxie'],
                        ['un amas d\'étoiles', 'Amas'],
                        ['objet IC', 'IC'],
                        ['objet NGC', 'NGC'],
                        ['objet Messier', 'Messier'],
                        ['technique narrowband', 'Narrowband'],
                        ['filtre Ha', 'Ha'],
                        ['filtre SII', 'SII'],
                        ['filtre OIII', 'OIII']
                    ],
                    'auto_tags': ['Astrophoto', 'DeepSky']
                }
            },
            {
                'name': 'Photos de voyage',
                'config': {
                    'model': 'qwen2-vl',
                    'temperature': 0.1,
                    'write_to_catalog': True,
                    'write_to_xmp': True,
                    'tagging_mode': 'auto',
                    'mappings': [],
                    'auto_tags': ['Voyage']
                }
            },
            {
                'name': 'Architecture',
                'config': {
                    'model': 'qwen2-vl',
                    'temperature': 0.1,
                    'write_to_catalog': True,
                    'write_to_xmp': True,
                    'tagging_mode': 'targeted',
                    'mappings': [
                        ['un bâtiment', 'Bâtiment'],
                        ['style moderne', 'Moderne'],
                        ['style ancien', 'Ancien'],
                        ['en pierre', 'Pierre'],
                        ['en verre', 'Verre'],
                        ['en béton', 'Béton']
                    ],
                    'auto_tags': ['Architecture']
                }
            }
        ]
        
        return defaults
    
    def create_default_profiles(self) -> int:
        """
        Crée les profiles par défaut s'ils n'existent pas.
        
        Returns:
            Nombre de profiles créés
        """
        created = 0
        
        for default in self.get_default_profiles():
            name = default['name']
            
            # Vérifier si existe déjà
            safe_name = name.replace(' ', '_')
            filename = self.profiles_dir / f"{safe_name}.json"
            
            if not filename.exists():
                if self.save_profile(name, default['config']):
                    created += 1
        
        if created > 0:
            logger.info(f"{created} profile(s) par défaut créé(s)")
        
        return created
