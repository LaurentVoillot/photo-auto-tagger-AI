"""
Module de suggestions de tags basées sur les métadonnées EXIF.
"""

import logging
from typing import List, Dict, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime

logger = logging.getLogger(__name__)


class EXIFTagSuggester:
    """Suggestions de tags basées sur EXIF."""
    
    def __init__(self):
        """Initialise le suggesteur."""
        self.camera_brands = {
            'Canon': ['Canon'],
            'Nikon': ['Nikon'],
            'Sony': ['Sony'],
            'Fujifilm': ['Fujifilm', 'Fuji'],
            'Olympus': ['Olympus'],
            'Panasonic': ['Panasonic'],
            'Leica': ['Leica'],
            'Pentax': ['Pentax'],
            'Hasselblad': ['Hasselblad']
        }
    
    def extract_exif(self, image_path: str) -> Dict:
        """
        Extrait les données EXIF d'une image.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Dictionnaire des données EXIF
        """
        exif_data = {}
        
        try:
            img = Image.open(image_path)
            exif = img._getexif()
            
            if not exif:
                return exif_data
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value
            
            # GPS si disponible
            if 'GPSInfo' in exif_data:
                gps_data = {}
                for key in exif_data['GPSInfo'].keys():
                    decode = GPSTAGS.get(key, key)
                    gps_data[decode] = exif_data['GPSInfo'][key]
                exif_data['GPSInfo'] = gps_data
            
        except Exception as e:
            logger.debug(f"Impossible d'extraire EXIF de {image_path}: {e}")
        
        return exif_data
    
    def suggest_tags_from_exif(self, image_path: str) -> List[str]:
        """
        Suggère des tags basés sur les données EXIF.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Liste de tags suggérés
        """
        suggestions = []
        exif = self.extract_exif(image_path)
        
        if not exif:
            return suggestions
        
        # Marque de l'appareil
        make = exif.get('Make', '')
        for brand, keywords in self.camera_brands.items():
            if any(keyword.lower() in make.lower() for keyword in keywords):
                suggestions.append(brand)
                break
        
        # Modèle d'appareil
        model = exif.get('Model', '')
        if model:
            # Nettoyer le nom du modèle
            clean_model = model.strip()
            if len(clean_model) > 3:
                suggestions.append(clean_model)
        
        # ISO
        iso = exif.get('ISOSpeedRatings')
        if iso:
            if iso >= 3200:
                suggestions.append('ISO élevé')
            elif iso >= 1600:
                suggestions.append('ISO moyen')
        
        # Exposition
        exposure = exif.get('ExposureTime')
        if exposure:
            # Convertir en secondes
            if isinstance(exposure, tuple):
                exp_seconds = exposure[0] / exposure[1]
            else:
                exp_seconds = float(exposure)
            
            if exp_seconds >= 1:
                suggestions.append('Longue exposition')
                if exp_seconds >= 30:
                    suggestions.append('Pose longue')
            elif exp_seconds < 1/1000:
                suggestions.append('Vitesse rapide')
        
        # Ouverture
        aperture = exif.get('FNumber')
        if aperture:
            if isinstance(aperture, tuple):
                f_value = aperture[0] / aperture[1]
            else:
                f_value = float(aperture)
            
            if f_value <= 2.8:
                suggestions.append('Grande ouverture')
            elif f_value >= 11:
                suggestions.append('Petite ouverture')
        
        # Focale
        focal_length = exif.get('FocalLength')
        if focal_length:
            if isinstance(focal_length, tuple):
                focal = focal_length[0] / focal_length[1]
            else:
                focal = float(focal_length)
            
            if focal <= 35:
                suggestions.append('Grand angle')
            elif focal >= 200:
                suggestions.append('Téléobjectif')
            elif 50 <= focal <= 85:
                suggestions.append('Portrait')
        
        # Flash
        flash = exif.get('Flash')
        if flash:
            if flash in [0, 16, 24, 32]:
                suggestions.append('Sans flash')
            else:
                suggestions.append('Avec flash')
        
        # Orientation
        orientation = exif.get('Orientation')
        if orientation:
            if orientation in [1, 2]:
                suggestions.append('Paysage')
            elif orientation in [6, 8]:
                suggestions.append('Portrait')
        
        # Date/Heure pour déterminer période
        date_time = exif.get('DateTimeOriginal')
        if date_time:
            try:
                dt = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
                hour = dt.hour
                
                if 5 <= hour < 9:
                    suggestions.append('Lever du soleil')
                elif 18 <= hour < 22:
                    suggestions.append('Coucher du soleil')
                elif 22 <= hour or hour < 5:
                    suggestions.append('Nuit')
                
                # Saison (hémisphère nord)
                month = dt.month
                if month in [12, 1, 2]:
                    suggestions.append('Hiver')
                elif month in [3, 4, 5]:
                    suggestions.append('Printemps')
                elif month in [6, 7, 8]:
                    suggestions.append('Été')
                elif month in [9, 10, 11]:
                    suggestions.append('Automne')
            except:
                pass
        
        # GPS pour localisation
        gps_info = exif.get('GPSInfo')
        if gps_info:
            suggestions.append('Géolocalisé')
        
        # Copyright
        copyright_info = exif.get('Copyright')
        if copyright_info:
            suggestions.append('Copyright')
        
        logger.debug(f"Suggestions EXIF pour {image_path}: {suggestions}")
        return suggestions
    
    def get_detailed_exif_info(self, image_path: str) -> Dict:
        """
        Retourne des informations EXIF détaillées et formatées.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Dictionnaire d'informations formatées
        """
        exif = self.extract_exif(image_path)
        info = {}
        
        if not exif:
            return info
        
        # Appareil
        make = exif.get('Make', '')
        model = exif.get('Model', '')
        if make or model:
            info['camera'] = f"{make} {model}".strip()
        
        # Objectif
        lens = exif.get('LensModel', exif.get('LensMake', ''))
        if lens:
            info['lens'] = lens
        
        # Paramètres d'exposition
        iso = exif.get('ISOSpeedRatings')
        if iso:
            info['iso'] = f"ISO {iso}"
        
        exposure = exif.get('ExposureTime')
        if exposure:
            if isinstance(exposure, tuple):
                if exposure[0] < exposure[1]:
                    info['shutter_speed'] = f"1/{exposure[1]//exposure[0]}s"
                else:
                    info['shutter_speed'] = f"{exposure[0]/exposure[1]:.1f}s"
            else:
                info['shutter_speed'] = f"{exposure}s"
        
        aperture = exif.get('FNumber')
        if aperture:
            if isinstance(aperture, tuple):
                f_value = aperture[0] / aperture[1]
            else:
                f_value = float(aperture)
            info['aperture'] = f"f/{f_value:.1f}"
        
        focal_length = exif.get('FocalLength')
        if focal_length:
            if isinstance(focal_length, tuple):
                focal = focal_length[0] / focal_length[1]
            else:
                focal = float(focal_length)
            info['focal_length'] = f"{focal:.0f}mm"
        
        # Date
        date_time = exif.get('DateTimeOriginal')
        if date_time:
            info['date'] = date_time
        
        # Dimensions
        width = exif.get('ExifImageWidth')
        height = exif.get('ExifImageHeight')
        if width and height:
            info['dimensions'] = f"{width}x{height}"
        
        return info
    
    def format_exif_display(self, exif_info: Dict) -> str:
        """
        Formate les informations EXIF pour affichage.
        
        Args:
            exif_info: Informations EXIF
            
        Returns:
            Texte formaté
        """
        lines = []
        
        if 'camera' in exif_info:
            lines.append(f"📷 Appareil : {exif_info['camera']}")
        
        if 'lens' in exif_info:
            lines.append(f"🔭 Objectif : {exif_info['lens']}")
        
        exposure_parts = []
        if 'shutter_speed' in exif_info:
            exposure_parts.append(exif_info['shutter_speed'])
        if 'aperture' in exif_info:
            exposure_parts.append(exif_info['aperture'])
        if 'iso' in exif_info:
            exposure_parts.append(exif_info['iso'])
        if 'focal_length' in exif_info:
            exposure_parts.append(exif_info['focal_length'])
        
        if exposure_parts:
            lines.append(f"⚙️ Paramètres : {' • '.join(exposure_parts)}")
        
        if 'date' in exif_info:
            lines.append(f"📅 Date : {exif_info['date']}")
        
        if 'dimensions' in exif_info:
            lines.append(f"📐 Taille : {exif_info['dimensions']}")
        
        return "\n".join(lines) if lines else "Aucune information EXIF"
