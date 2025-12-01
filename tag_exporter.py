"""
Module d'export des tags vers différents formats (CSV, JSON, etc.).
"""

import csv
import json
import sqlite3
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class TagExporter:
    """Exportation des tags vers différents formats."""
    
    def __init__(self):
        """Initialise l'exporteur."""
        pass
    
    def export_from_catalog_to_csv(self, conn: sqlite3.Connection, output_file: str) -> bool:
        """
        Exporte les tags d'un catalogue Lightroom vers CSV.
        
        Args:
            conn: Connexion au catalogue
            output_file: Fichier CSV de sortie
            
        Returns:
            True si succès
        """
        try:
            cursor = conn.cursor()
            
            # Requête pour obtenir photos et leurs tags
            query = """
            SELECT 
                ai.id_local as photo_id,
                rf.absolutePath || alf.pathFromRoot || af.baseName || '.' || af.extension as photo_path,
                af.baseName || '.' || af.extension as filename,
                GROUP_CONCAT(k.name, '|') as tags,
                ai.captureTime,
                ai.rating
            FROM Adobe_images ai
            INNER JOIN AgLibraryFile af ON ai.rootFile = af.id_local
            INNER JOIN AgLibraryFolder alf ON af.folder = alf.id_local
            INNER JOIN AgLibraryRootFolder rf ON alf.rootFolder = rf.id_local
            LEFT JOIN AgLibraryKeywordImage ki ON ai.id_local = ki.image
            LEFT JOIN AgLibraryKeyword k ON ki.tag = k.id_local
            GROUP BY ai.id_local
            ORDER BY ai.captureTime DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Écrire le CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # En-têtes
                writer.writerow(['Photo ID', 'Chemin', 'Nom de fichier', 'Tags', 'Date de capture', 'Note'])
                
                # Données
                for row in rows:
                    photo_id, photo_path, filename, tags, capture_time, rating = row
                    
                    # Remplacer | par , pour les tags
                    tag_list = tags.replace('|', ', ') if tags else ''
                    
                    writer.writerow([
                        photo_id,
                        photo_path,
                        filename,
                        tag_list,
                        capture_time or '',
                        rating or ''
                    ])
            
            logger.info(f"Export CSV réussi: {output_file} ({len(rows)} photos)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export CSV: {e}")
            return False
    
    def export_from_catalog_to_json(self, conn: sqlite3.Connection, output_file: str, pretty: bool = True) -> bool:
        """
        Exporte les tags d'un catalogue Lightroom vers JSON.
        
        Args:
            conn: Connexion au catalogue
            output_file: Fichier JSON de sortie
            pretty: Formatage indenté
            
        Returns:
            True si succès
        """
        try:
            cursor = conn.cursor()
            
            # Requête détaillée
            query = """
            SELECT 
                ai.id_local as photo_id,
                rf.absolutePath || alf.pathFromRoot || af.baseName || '.' || af.extension as photo_path,
                af.baseName || '.' || af.extension as filename,
                af.baseName as basename,
                af.extension as extension,
                ai.captureTime,
                ai.rating,
                ai.fileFormat,
                ai.colorLabels
            FROM Adobe_images ai
            INNER JOIN AgLibraryFile af ON ai.rootFile = af.id_local
            INNER JOIN AgLibraryFolder alf ON af.folder = alf.id_local
            INNER JOIN AgLibraryRootFolder rf ON alf.rootFolder = rf.id_local
            ORDER BY ai.captureTime DESC
            """
            
            cursor.execute(query)
            photos = cursor.fetchall()
            
            # Construire le JSON
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_photos': len(photos),
                'photos': []
            }
            
            for photo in photos:
                photo_id, photo_path, filename, basename, extension, capture_time, rating, file_format, color_labels = photo
                
                # Récupérer les tags pour cette photo
                cursor.execute("""
                    SELECT k.name
                    FROM AgLibraryKeywordImage ki
                    INNER JOIN AgLibraryKeyword k ON ki.tag = k.id_local
                    WHERE ki.image = ?
                    ORDER BY k.name
                """, (photo_id,))
                
                tags = [row[0] for row in cursor.fetchall()]
                
                photo_data = {
                    'id': photo_id,
                    'path': photo_path,
                    'filename': filename,
                    'basename': basename,
                    'extension': extension,
                    'tags': tags,
                    'capture_time': capture_time,
                    'rating': rating,
                    'format': file_format,
                    'color_labels': color_labels
                }
                
                export_data['photos'].append(photo_data)
            
            # Écrire le JSON
            with open(output_file, 'w', encoding='utf-8') as jsonfile:
                if pretty:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, jsonfile, ensure_ascii=False)
            
            logger.info(f"Export JSON réussi: {output_file} ({len(photos)} photos)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export JSON: {e}")
            return False
    
    def export_tag_statistics_to_csv(self, conn: sqlite3.Connection, output_file: str) -> bool:
        """
        Exporte les statistiques des tags vers CSV.
        
        Args:
            conn: Connexion au catalogue
            output_file: Fichier CSV de sortie
            
        Returns:
            True si succès
        """
        try:
            cursor = conn.cursor()
            
            # Statistiques par tag
            query = """
            SELECT 
                k.name as tag_name,
                COUNT(ki.image) as photo_count,
                k.dateCreated
            FROM AgLibraryKeyword k
            LEFT JOIN AgLibraryKeywordImage ki ON k.id_local = ki.tag
            GROUP BY k.id_local, k.name
            ORDER BY photo_count DESC, k.name
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Écrire le CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # En-têtes
                writer.writerow(['Tag', 'Nombre de photos', 'Date de création'])
                
                # Données
                for tag_name, photo_count, date_created in rows:
                    writer.writerow([tag_name, photo_count, date_created or ''])
            
            logger.info(f"Export statistiques CSV réussi: {output_file} ({len(rows)} tags)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export statistiques CSV: {e}")
            return False
    
    def export_xmp_folder_to_csv(self, folder_path: str, output_file: str) -> bool:
        """
        Exporte les tags des fichiers XMP d'un dossier vers CSV.
        
        Args:
            folder_path: Dossier contenant les XMP
            output_file: Fichier CSV de sortie
            
        Returns:
            True si succès
        """
        try:
            from xmp_manager import XMPManager
            xmp_manager = XMPManager()
            
            folder = Path(folder_path)
            xmp_files = list(folder.glob("*.xmp"))
            
            # Écrire le CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # En-têtes
                writer.writerow(['Fichier XMP', 'Photo associée', 'Tags'])
                
                # Parcourir les XMP
                for xmp_file in xmp_files:
                    try:
                        # Déduire le nom de la photo
                        photo_name = xmp_file.stem  # Sans .xmp
                        
                        # Lire les tags
                        tags = xmp_manager.read_tags_from_xmp(str(xmp_file))
                        
                        writer.writerow([
                            xmp_file.name,
                            photo_name,
                            ', '.join(tags)
                        ])
                    except Exception as e:
                        logger.warning(f"Erreur lecture {xmp_file}: {e}")
            
            logger.info(f"Export XMP→CSV réussi: {output_file} ({len(xmp_files)} fichiers)")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export XMP→CSV: {e}")
            return False
    
    def export_to_markdown(self, conn: sqlite3.Connection, output_file: str) -> bool:
        """
        Exporte vers Markdown pour documentation.
        
        Args:
            conn: Connexion au catalogue
            output_file: Fichier Markdown de sortie
            
        Returns:
            True si succès
        """
        try:
            cursor = conn.cursor()
            
            # Statistiques globales
            cursor.execute("SELECT COUNT(*) FROM Adobe_images")
            total_photos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM AgLibraryKeyword")
            total_tags = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT image) FROM AgLibraryKeywordImage
            """)
            tagged_photos = cursor.fetchone()[0]
            
            # Tags les plus utilisés
            cursor.execute("""
                SELECT k.name, COUNT(ki.image) as count
                FROM AgLibraryKeyword k
                INNER JOIN AgLibraryKeywordImage ki ON k.id_local = ki.tag
                GROUP BY k.id_local
                ORDER BY count DESC
                LIMIT 20
            """)
            top_tags = cursor.fetchall()
            
            # Écrire le Markdown
            with open(output_file, 'w', encoding='utf-8') as md:
                md.write(f"# Rapport de tags\n\n")
                md.write(f"**Date** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                md.write(f"## 📊 Statistiques globales\n\n")
                md.write(f"- Total de photos : **{total_photos}**\n")
                md.write(f"- Photos taguées : **{tagged_photos}** ({tagged_photos/total_photos*100:.1f}%)\n")
                md.write(f"- Total de tags : **{total_tags}**\n\n")
                
                md.write(f"## 🏆 Top 20 des tags\n\n")
                md.write(f"| Rang | Tag | Nombre de photos |\n")
                md.write(f"|------|-----|------------------|\n")
                
                for i, (tag_name, count) in enumerate(top_tags, 1):
                    md.write(f"| {i} | {tag_name} | {count} |\n")
            
            logger.info(f"Export Markdown réussi: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export Markdown: {e}")
            return False
