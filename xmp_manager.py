"""
Module de gestion des fichiers XMP pour le tagging de photos.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from lxml import etree

logger = logging.getLogger(__name__)


class XMPManager:
    """Gestionnaire de fichiers XMP pour les métadonnées photo."""
    
    # Namespaces XMP
    NAMESPACES = {
        'x': 'adobe:ns:meta/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'lr': 'http://ns.adobe.com/lightroom/1.0/',
        'xmp': 'http://ns.adobe.com/xap/1.0/'
    }
    
    def __init__(self):
        """Initialise le gestionnaire XMP."""
        # Enregistrer les namespaces pour lxml
        for prefix, uri in self.NAMESPACES.items():
            etree.register_namespace(prefix, uri)
    
    def get_xmp_path(self, image_path: str) -> str:
        """
        Détermine le chemin du fichier XMP pour une image.
        Le XMP doit avoir le même nom que l'image mais avec l'extension .xmp
        Exemple: photo.jpg → photo.xmp (et NON photo.jpg.xmp)
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Chemin du fichier XMP correspondant
        """
        path = Path(image_path)
        # Enlever l'extension originale et ajouter .xmp
        xmp_name = path.stem + '.xmp'
        xmp_path = path.parent / xmp_name
        return str(xmp_path)
    
    def xmp_exists(self, image_path: str) -> bool:
        """
        Vérifie si un fichier XMP existe pour une image.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            True si le XMP existe, False sinon
        """
        xmp_path = self.get_xmp_path(image_path)
        return os.path.exists(xmp_path)
    
    def read_tags(self, image_path: str) -> List[str]:
        """
        Lit les tags existants d'un fichier XMP.
        
        Args:
            image_path: Chemin de l'image
            
        Returns:
            Liste des tags existants (vide si pas de XMP ou pas de tags)
        """
        xmp_path = self.get_xmp_path(image_path)
        
        if not os.path.exists(xmp_path):
            logger.debug(f"Pas de XMP existant: {xmp_path}")
            return []
        
        try:
            tree = etree.parse(xmp_path)
            root = tree.getroot()
            
            # Chercher les tags dans dc:subject
            tags = []
            
            # XPath pour trouver les éléments rdf:li dans dc:subject/rdf:Bag
            xpath = './/dc:subject/rdf:Bag/rdf:li'
            elements = root.xpath(xpath, namespaces=self.NAMESPACES)
            
            for elem in elements:
                if elem.text:
                    tags.append(elem.text.strip())
            
            logger.debug(f"Tags existants lus: {tags}")
            return tags
            
        except Exception as e:
            logger.error(f"Erreur lecture XMP {xmp_path}: {e}")
            return []
    
    def write_tags(self, image_path: str, new_tags: List[str]) -> bool:
        """
        Écrit des tags dans le fichier XMP (ajout aux existants).
        
        Args:
            image_path: Chemin de l'image
            new_tags: Liste des nouveaux tags à ajouter
            
        Returns:
            True si succès, False sinon
        """
        if not new_tags:
            logger.warning("Aucun tag à écrire")
            return True
        
        xmp_path = self.get_xmp_path(image_path)
        
        # Lire les tags existants
        existing_tags = self.read_tags(image_path)
        
        # Combiner et dédupliquer
        all_tags = list(existing_tags)
        for tag in new_tags:
            if tag not in all_tags:
                all_tags.append(tag)
        
        try:
            if os.path.exists(xmp_path):
                logger.debug(f"Mise à jour XMP existant: {xmp_path}")
                return self._update_xmp(xmp_path, all_tags)
            else:
                logger.debug(f"Création nouveau XMP: {xmp_path}")
                return self._create_xmp(xmp_path, all_tags)
                
        except Exception as e:
            logger.error(f"Erreur écriture XMP {xmp_path}: {e}")
            return False
    
    def _create_xmp(self, xmp_path: str, tags: List[str]) -> bool:
        """
        Crée un nouveau fichier XMP.
        
        Args:
            xmp_path: Chemin du fichier XMP à créer
            tags: Liste des tags
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Créer la structure XMP de base
            xmpmeta = etree.Element(
                '{adobe:ns:meta/}xmpmeta',
                attrib={'{adobe:ns:meta/}xmptk': 'Photo Auto Tagger 1.0'}
            )
            
            rdf_rdf = etree.SubElement(
                xmpmeta,
                '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF'
            )
            
            rdf_description = etree.SubElement(
                rdf_rdf,
                '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description',
                attrib={'{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about': ''}
            )
            
            # Ajouter les tags dans dc:subject
            dc_subject = etree.SubElement(
                rdf_description,
                '{http://purl.org/dc/elements/1.1/}subject'
            )
            
            rdf_bag = etree.SubElement(
                dc_subject,
                '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag'
            )
            
            for tag in tags:
                rdf_li = etree.SubElement(
                    rdf_bag,
                    '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li'
                )
                rdf_li.text = tag
            
            # Écrire le fichier
            tree = etree.ElementTree(xmpmeta)
            tree.write(
                xmp_path,
                encoding='UTF-8',
                xml_declaration=True,
                pretty_print=True
            )
            
            logger.info(f"XMP créé avec {len(tags)} tags: {xmp_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur création XMP {xmp_path}: {e}")
            return False
    
    def _update_xmp(self, xmp_path: str, tags: List[str]) -> bool:
        """
        Met à jour un fichier XMP existant.
        
        Args:
            xmp_path: Chemin du fichier XMP
            tags: Liste complète des tags (existants + nouveaux)
            
        Returns:
            True si succès, False sinon
        """
        try:
            tree = etree.parse(xmp_path)
            root = tree.getroot()
            
            # Trouver ou créer dc:subject
            xpath_desc = './/rdf:Description'
            descriptions = root.xpath(xpath_desc, namespaces=self.NAMESPACES)
            
            if not descriptions:
                logger.error("Structure XMP invalide: pas de rdf:Description")
                return False
            
            description = descriptions[0]
            
            # Chercher dc:subject existant
            xpath_subject = './/dc:subject'
            subjects = description.xpath(xpath_subject, namespaces=self.NAMESPACES)
            
            if subjects:
                # Supprimer l'ancien dc:subject
                for subject in subjects:
                    subject.getparent().remove(subject)
            
            # Créer nouveau dc:subject avec tous les tags
            dc_subject = etree.SubElement(
                description,
                '{http://purl.org/dc/elements/1.1/}subject'
            )
            
            rdf_bag = etree.SubElement(
                dc_subject,
                '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag'
            )
            
            for tag in tags:
                rdf_li = etree.SubElement(
                    rdf_bag,
                    '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li'
                )
                rdf_li.text = tag
            
            # Écrire le fichier mis à jour
            tree.write(
                xmp_path,
                encoding='UTF-8',
                xml_declaration=True,
                pretty_print=True
            )
            
            logger.info(f"XMP mis à jour avec {len(tags)} tags: {xmp_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour XMP {xmp_path}: {e}")
            return False


if __name__ == "__main__":
    # Test du module
    logging.basicConfig(level=logging.DEBUG)
    
    manager = XMPManager()
    
    # Test avec un fichier fictif
    test_image = "/tmp/test_photo.jpg"
    
    print(f"Chemin XMP: {manager.get_xmp_path(test_image)}")
    print(f"XMP existe: {manager.xmp_exists(test_image)}")
    
    # Test création
    if manager.write_tags(test_image, ["Paris", "Tour Eiffel", "Monument"]):
        print("✓ Tags écrits")
        
        # Test lecture
        tags = manager.read_tags(test_image)
        print(f"Tags lus: {tags}")
        
        # Test ajout
        if manager.write_tags(test_image, ["Nuit", "Lumières"]):
            print("✓ Tags ajoutés")
            tags = manager.read_tags(test_image)
            print(f"Tags finaux: {tags}")
