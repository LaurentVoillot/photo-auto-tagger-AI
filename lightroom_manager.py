"""
Module de gestion du catalogue Adobe Lightroom Classic.
"""

import sqlite3
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class LightroomManager:
    """Gestionnaire du catalogue Lightroom Classic."""
    
    def __init__(self):
        """Initialise le gestionnaire Lightroom."""
        self.conn: Optional[sqlite3.Connection] = None
        self.catalog_path: Optional[str] = None
        self.pyramid_table: Optional[str] = None
        self.preview_table: Optional[str] = None
    
    def connect(self, catalog_path: str) -> bool:
        """
        Se connecte à un catalogue Lightroom.
        
        Args:
            catalog_path: Chemin du fichier .lrcat
            
        Returns:
            True si connexion réussie, False sinon
        """
        if not os.path.exists(catalog_path):
            logger.error(f"Catalogue introuvable: {catalog_path}")
            return False
        
        try:
            self.conn = sqlite3.connect(catalog_path)
            self.catalog_path = catalog_path
            logger.info(f"Connecté au catalogue: {catalog_path}")
            
            # Détecter les tables de previews disponibles
            self._detect_preview_tables()
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Erreur connexion au catalogue: {e}")
            return False
    
    def _detect_preview_tables(self):
        """Détecte les noms des tables de previews disponibles dans le catalogue."""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Liste toutes les tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Chercher la table des Smart Previews (pyramide)
            pyramid_candidates = [
                'Adobe_previewCachePyramid',
                'Adobe_imageDevelopBeforeSettings',
                'Adobe_variablesTable'
            ]
            
            for candidate in pyramid_candidates:
                if candidate in tables:
                    # Vérifier que la table a une colonne 'data'
                    try:
                        cursor.execute(f"PRAGMA table_info({candidate})")
                        columns = [row[1] for row in cursor.fetchall()]
                        if 'data' in columns:
                            self.pyramid_table = candidate
                            logger.info(f"Table Smart Preview détectée: {candidate}")
                            break
                    except:
                        continue
            
            # Chercher la table des Previews standards
            preview_candidates = [
                'Adobe_previewCache',
                'Adobe_libraryImageDevelopHistoryStep'
            ]
            
            for candidate in preview_candidates:
                if candidate in tables:
                    try:
                        cursor.execute(f"PRAGMA table_info({candidate})")
                        columns = [row[1] for row in cursor.fetchall()]
                        if 'data' in columns:
                            self.preview_table = candidate
                            logger.info(f"Table Preview standard détectée: {candidate}")
                            break
                    except:
                        continue
            
            # Log si aucune table trouvée
            if not self.pyramid_table:
                logger.warning("Aucune table Smart Preview trouvée dans le catalogue")
                logger.info(f"Tables disponibles: {', '.join(sorted(tables))}")
            
            if not self.preview_table:
                logger.warning("Aucune table Preview standard trouvée dans le catalogue")
            
        except sqlite3.Error as e:
            logger.error(f"Erreur détection tables previews: {e}")
    
    def close(self):
        """Ferme la connexion au catalogue."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Connexion catalogue fermée")
    
    def get_photos_list(self) -> List[Dict]:
        """
        Récupère la liste des photos du catalogue avec Smart Previews.
        Compatible avec Lightroom Classic v12 à v15.
        
        Returns:
            Liste de dictionnaires contenant les infos des photos
        """
        if not self.conn:
            logger.error("Pas de connexion au catalogue")
            return []
        
        try:
            cursor = self.conn.cursor()
            
            # Nouvelle requête compatible avec Lightroom Classic v15
            # Utilise AgLibraryFile directement au lieu de pathFromRoot
            query = """
            SELECT DISTINCT
                ai.id_local as photo_id,
                rf.absolutePath || alf.pathFromRoot || af.baseName || '.' || af.extension as full_path,
                af.baseName || '.' || af.extension as filename,
                ai.fileFormat as format
            FROM Adobe_images ai
            INNER JOIN AgLibraryFile af ON ai.rootFile = af.id_local
            INNER JOIN AgLibraryFolder alf ON af.folder = alf.id_local
            INNER JOIN AgLibraryRootFolder rf ON alf.rootFolder = rf.id_local
            WHERE ai.id_local IS NOT NULL
            ORDER BY ai.id_local
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            photos = []
            for row in rows:
                photo_id, full_path, filename, file_format = row
                
                # Extraire le dossier du chemin complet
                if full_path:
                    folder_path = str(Path(full_path).parent)
                else:
                    folder_path = None
                
                photos.append({
                    'photo_id': photo_id,
                    'folder_path': folder_path,
                    'filename': filename,
                    'format': file_format,
                    'full_path': full_path
                })
            
            logger.info(f"{len(photos)} photos trouvées dans le catalogue")
            return photos
            
        except sqlite3.Error as e:
            logger.error(f"Erreur récupération liste photos: {e}")
            # Essayer une requête alternative pour versions plus anciennes
            return self._get_photos_list_fallback()
    
    def _get_photos_list_fallback(self) -> List[Dict]:
        """
        Méthode alternative pour récupérer les photos (versions anciennes de Lightroom).
        
        Returns:
            Liste de dictionnaires contenant les infos des photos
        """
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            # Requête simplifiée compatible avec toutes les versions
            query = """
            SELECT DISTINCT
                ai.id_local as photo_id,
                ai.idx_filename as filename
            FROM Adobe_images ai
            WHERE ai.id_local IS NOT NULL
            ORDER BY ai.id_local
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            photos = []
            for row in rows:
                photo_id, filename = row
                
                photos.append({
                    'photo_id': photo_id,
                    'folder_path': None,
                    'filename': filename,
                    'format': None,
                    'full_path': None  # Sera déterminé plus tard si nécessaire
                })
            
            logger.info(f"{len(photos)} photos trouvées dans le catalogue (mode fallback)")
            return photos
            
        except sqlite3.Error as e:
            logger.error(f"Erreur récupération liste photos (fallback): {e}")
            return []
    
    def get_smart_preview(self, photo_id: int) -> Optional[Image.Image]:
        """
        Récupère le Smart Preview d'une photo depuis le catalogue.
        Si aucun Smart Preview n'est disponible, essaie de récupérer le Preview standard.
        
        Args:
            photo_id: ID de la photo
            
        Returns:
            Image PIL ou None si ni Smart Preview ni Preview standard disponible
        """
        if not self.conn:
            logger.error("Pas de connexion au catalogue")
            return None
        
        # Essayer d'abord le Smart Preview
        image = self._get_smart_preview_pyramid(photo_id)
        if image:
            logger.debug(f"Smart Preview trouvé pour photo {photo_id}")
            return image
        
        # Si pas de Smart Preview, essayer le Preview standard
        logger.debug(f"Pas de Smart Preview pour photo {photo_id}, essai avec Preview standard")
        image = self._get_standard_preview(photo_id)
        if image:
            logger.debug(f"Preview standard trouvé pour photo {photo_id}")
            return image
        
        logger.warning(f"Aucun preview disponible pour photo {photo_id}")
        return None
    
    def _get_smart_preview_pyramid(self, photo_id: int) -> Optional[Image.Image]:
        """
        Récupère le Smart Preview (pyramide) d'une photo.
        Essaie d'abord la table SQL, puis cherche dans les fichiers .lrdata
        
        Args:
            photo_id: ID de la photo
            
        Returns:
            Image PIL ou None
        """
        logger.debug(f"=== DÉBUT _get_smart_preview_pyramid pour photo {photo_id} ===")
        
        # Méthode 1 : Essayer la table SQL (si détectée)
        if self.pyramid_table:
            try:
                cursor = self.conn.cursor()
                
                query = f"""
                SELECT data
                FROM {self.pyramid_table}
                WHERE image = ?
                AND data IS NOT NULL
                LIMIT 1
                """
                
                cursor.execute(query, (photo_id,))
                row = cursor.fetchone()
                
                if row and row[0]:
                    blob_data = row[0]
                    try:
                        image = Image.open(BytesIO(blob_data))
                        logger.debug(f"Smart Preview SQL chargé pour photo {photo_id}: {image.size}")
                        return image
                    except Exception as e:
                        logger.debug(f"Erreur décodage Smart Preview SQL photo {photo_id}: {e}")
                        
            except sqlite3.Error as e:
                logger.debug(f"Erreur récupération Smart Preview SQL photo {photo_id}: {e}")
        
        # Méthode 2 : Chercher dans le fichier .lrdata
        if self.catalog_path:
            # Détecter le bon dossier Smart Previews
            catalog_dir = os.path.dirname(self.catalog_path)
            catalog_base = os.path.splitext(os.path.basename(self.catalog_path))[0]
            
            # Essayer différents patterns de nommage
            lrdata_patterns = [
                os.path.join(catalog_dir, f"{catalog_base} Smart Previews.lrdata"),  # "catalog Smart Previews.lrdata"
                os.path.join(catalog_dir, f"{catalog_base} Smart Previews.lrdata"),  # Avec espace
                os.path.join(catalog_dir, "Smart Previews.lrdata"),                   # Sans nom de catalogue
            ]
            
            lrdata_path = None
            for pattern in lrdata_patterns:
                if os.path.exists(pattern):
                    lrdata_path = pattern
                    logger.debug(f"Dossier Smart Previews trouvé: {lrdata_path}")
                    break
            
            if lrdata_path:
                logger.debug(f"Recherche Smart Preview dans {lrdata_path}")
                # Les Smart Previews sont stockés comme des fichiers DNG
                # Le nom du fichier est basé sur le fileUUID de AgDNGProxyInfo
                # IMPORTANT: La relation passe par AgLibraryFile.id_global = AgDNGProxyInfo.fileUUID
                try:
                    cursor = self.conn.cursor()
                    logger.debug(f"Requête AgDNGProxyInfo pour photo {photo_id}")
                    
                    # Jointure correcte : Adobe_images → AgLibraryFile → AgDNGProxyInfo
                    cursor.execute("""
                        SELECT dnp.fileUUID
                        FROM Adobe_images ai
                        INNER JOIN AgLibraryFile alf ON ai.rootFile = alf.id_local
                        INNER JOIN AgDNGProxyInfo dnp ON alf.id_global = dnp.fileUUID
                        WHERE ai.id_local = ?
                    """, (photo_id,))
                    row = cursor.fetchone()
                    
                    if row and row[0]:
                        file_uuid = row[0]
                        logger.debug(f"  fileUUID trouvé: {file_uuid}")
                        
                        # Format : XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
                        # Structure observée: 2/2252/22525EB1-CB1F-4C04-9347-237F3FD2F64A.dng
                        
                        # Calcul des composants du chemin
                        first_char = file_uuid[:1]
                        first_four = file_uuid[:4]
                        logger.debug(f"  Composants chemin: premier='{first_char}', quatre='{first_four}'")
                        
                        # Patterns basés sur fileUUID (pas id_global !)
                        patterns = [
                            # Pattern moderne: X/XXXX/UUID.dng (tout majuscules)
                            os.path.join(lrdata_path, file_uuid[:1], file_uuid[:4], f"{file_uuid}.dng"),
                            # Variantes de casse
                            os.path.join(lrdata_path, file_uuid[:1].lower(), file_uuid[:4].lower(), f"{file_uuid}.dng"),
                            os.path.join(lrdata_path, file_uuid[:1].upper(), file_uuid[:4].upper(), f"{file_uuid.upper()}.dng"),
                            # Patterns anciens
                            os.path.join(lrdata_path, file_uuid[:1], f"{file_uuid}.dng"),
                            os.path.join(lrdata_path, f"{file_uuid}.dng"),
                        ]
                        
                        logger.debug(f"Recherche Smart Preview pour photo {photo_id}")
                        logger.debug(f"  fileUUID: {file_uuid}")
                        logger.debug(f"  Dossier .lrdata: {lrdata_path}")
                        logger.debug(f"  Nombre de patterns à tester: {len(patterns)}")
                        
                        for i, pattern in enumerate(patterns, 1):
                            relative = pattern.replace(lrdata_path + '/', '')
                            logger.debug(f"  Pattern {i}/5: {relative}")
                            logger.debug(f"    Chemin complet: {pattern}")
                            exists = os.path.exists(pattern)
                            logger.debug(f"    Existe: {exists}")
                            if exists:
                                try:
                                    image = Image.open(pattern)
                                    logger.debug(f"Smart Preview DNG chargé pour photo {photo_id}: {image.size}")
                                    return image
                                except Exception as e:
                                    logger.debug(f"Erreur chargement Smart Preview DNG {pattern}: {e}")
                                    continue
                        
                        logger.debug(f"Aucun pattern ne correspond pour photo {photo_id} (fileUUID: {file_uuid})")
                        logger.debug(f"  Patterns testés:")
                        for pattern in patterns:
                            logger.debug(f"    • {pattern}")
                    else:
                        logger.debug(f"Photo {photo_id} n'a pas d'entrée dans AgDNGProxyInfo (pas de Smart Preview)")
                    
                except Exception as e:
                    logger.error(f"ERREUR recherche Smart Preview pour photo {photo_id}: {e}", exc_info=True)
            else:
                logger.debug(f"Aucun dossier Smart Previews trouvé pour: {catalog_base}")
        
        return None
    
    def _get_standard_preview(self, photo_id: int) -> Optional[Image.Image]:
        """
        Récupère le Preview standard d'une photo depuis le cache.
        Utilisé pour les JPEG qui n'ont souvent pas de Smart Preview.
        
        Args:
            photo_id: ID de la photo
            
        Returns:
            Image PIL ou None
        """
        # Essayer la table SQL (si détectée)
        if not self.preview_table:
            logger.debug(f"Pas de table preview détectée, impossible de récupérer le preview standard")
            return None
            
        try:
            cursor = self.conn.cursor()
            
            # Chercher le preview standard dans la table détectée
            query = f"""
            SELECT data
            FROM {self.preview_table}
            WHERE image = ?
            AND data IS NOT NULL
            ORDER BY dimension DESC
            LIMIT 1
            """
            
            cursor.execute(query, (photo_id,))
            row = cursor.fetchone()
            
            if row and row[0]:
                blob_data = row[0]
                try:
                    image = Image.open(BytesIO(blob_data))
                    logger.debug(f"Preview standard chargé pour photo {photo_id}: {image.size}")
                    return image
                except Exception as e:
                    logger.debug(f"Erreur décodage Preview standard photo {photo_id}: {e}")
                    return None
            else:
                return None
                
        except sqlite3.Error as e:
            logger.debug(f"Erreur récupération Preview standard photo {photo_id}: {e}")
            return None
    
    def load_image_from_file(self, photo_path: str) -> Optional[Image.Image]:
        """
        Charge une image directement depuis le fichier.
        
        Args:
            photo_path: Chemin complet de la photo
            
        Returns:
            Image PIL ou None si erreur
        """
        if not os.path.exists(photo_path):
            logger.error(f"Fichier introuvable: {photo_path}")
            return None
        
        try:
            image = Image.open(photo_path)
            logger.debug(f"Image chargée: {photo_path}")
            return image
        except Exception as e:
            logger.error(f"Erreur chargement image {photo_path}: {e}")
            return None
    
    def get_existing_tags(self, photo_id: int) -> List[str]:
        """
        Récupère les tags existants d'une photo.
        
        Args:
            photo_id: ID de la photo
            
        Returns:
            Liste des tags existants
        """
        if not self.conn:
            logger.error("Pas de connexion au catalogue")
            return []
        
        try:
            cursor = self.conn.cursor()
            
            query = """
            SELECT DISTINCT alk.name
            FROM AgLibraryKeyword alk
            INNER JOIN AgLibraryKeywordImage alki ON alk.id_local = alki.tag
            WHERE alki.image = ?
            ORDER BY alk.name
            """
            
            cursor.execute(query, (photo_id,))
            rows = cursor.fetchall()
            
            tags = [row[0] for row in rows if row[0]]
            logger.debug(f"Tags existants pour photo {photo_id}: {tags}")
            return tags
            
        except sqlite3.Error as e:
            logger.error(f"Erreur récupération tags photo {photo_id}: {e}")
            return []
    
    def add_tags(self, photo_id: int, tags: List[str]) -> bool:
        """
        Ajoute des tags à une photo (sans supprimer les existants).
        
        Args:
            photo_id: ID de la photo
            tags: Liste des tags à ajouter
            
        Returns:
            True si succès, False sinon
        """
        if not self.conn:
            logger.error("Pas de connexion au catalogue")
            return False
        
        if not tags:
            logger.warning("Aucun tag à ajouter")
            return True
        
        try:
            # Récupérer les tags existants
            existing_tags = self.get_existing_tags(photo_id)
            existing_tags_lower = [t.lower() for t in existing_tags]
            
            cursor = self.conn.cursor()
            added_count = 0
            
            # Commencer une transaction
            cursor.execute("BEGIN TRANSACTION")
            
            for tag in tags:
                # Ne pas ajouter si déjà existant (insensible à la casse)
                if tag.lower() in existing_tags_lower:
                    logger.debug(f"Tag '{tag}' déjà existant pour photo {photo_id}")
                    continue
                
                # Créer le keyword s'il n'existe pas
                keyword_id = self._get_or_create_keyword(cursor, tag)
                
                if keyword_id is None:
                    logger.error(f"Impossible de créer/trouver le keyword '{tag}'")
                    continue
                
                # Vérifier que l'association n'existe pas déjà
                cursor.execute("""
                    SELECT 1 FROM AgLibraryKeywordImage
                    WHERE image = ? AND tag = ?
                """, (photo_id, keyword_id))
                
                if cursor.fetchone():
                    logger.debug(f"Association déjà existante: photo {photo_id} - tag '{tag}'")
                    continue
                
                # Créer l'association photo-keyword
                cursor.execute("""
                    INSERT INTO AgLibraryKeywordImage (image, tag)
                    VALUES (?, ?)
                """, (photo_id, keyword_id))
                
                added_count += 1
                logger.debug(f"Tag '{tag}' ajouté à photo {photo_id}")
            
            # Valider la transaction
            cursor.execute("COMMIT")
            
            logger.info(f"{added_count} nouveaux tags ajoutés à photo {photo_id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Erreur ajout tags photo {photo_id}: {e}")
            if self.conn:
                try:
                    self.conn.execute("ROLLBACK")
                except:
                    pass
            return False
    
    def _get_or_create_keyword(self, cursor: sqlite3.Cursor, tag: str) -> Optional[int]:
        """
        Récupère l'ID d'un keyword ou le crée s'il n'existe pas.
        
        Args:
            cursor: Curseur SQLite
            tag: Nom du tag
            
        Returns:
            ID du keyword ou None si erreur
        """
        import uuid
        
        try:
            # Chercher si le keyword existe déjà
            cursor.execute("""
                SELECT id_local FROM AgLibraryKeyword
                WHERE name = ?
            """, (tag,))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            
            # Le keyword n'existe pas, le créer
            # Générer un UUID unique pour id_global (requis par Lightroom)
            id_global = str(uuid.uuid4()).upper()
            
            # Trouver le prochain ID disponible
            cursor.execute("SELECT MAX(id_local) FROM AgLibraryKeyword")
            max_id = cursor.fetchone()[0]
            new_id = (max_id or 0) + 1
            
            # Insérer le nouveau keyword avec tous les champs requis
            cursor.execute("""
                INSERT INTO AgLibraryKeyword (id_local, id_global, name, lc_name, dateCreated, genealogy)
                VALUES (?, ?, ?, ?, datetime('now'), ?)
            """, (new_id, id_global, tag, tag.lower(), f"/{tag}"))
            
            logger.debug(f"Nouveau keyword créé: '{tag}' (ID: {new_id}, UUID: {id_global})")
            return new_id
            
        except sqlite3.Error as e:
            logger.error(f"Erreur création keyword '{tag}': {e}")
            return None
    
    def get_photo_path(self, photo_id: int) -> Optional[str]:
        """
        Récupère le chemin complet d'une photo.
        Compatible avec Lightroom Classic v12 à v15.
        
        Args:
            photo_id: ID de la photo
            
        Returns:
            Chemin complet ou None si introuvable
        """
        if not self.conn:
            logger.error("Pas de connexion au catalogue")
            return None
        
        try:
            cursor = self.conn.cursor()
            
            # Requête compatible avec Lightroom Classic v15
            query = """
            SELECT 
                rf.absolutePath,
                alf.pathFromRoot,
                af.baseName,
                af.extension
            FROM Adobe_images ai
            INNER JOIN AgLibraryFile af ON ai.rootFile = af.id_local
            INNER JOIN AgLibraryFolder alf ON af.folder = alf.id_local
            INNER JOIN AgLibraryRootFolder rf ON alf.rootFolder = rf.id_local
            WHERE ai.id_local = ?
            """
            
            cursor.execute(query, (photo_id,))
            row = cursor.fetchone()
            
            if row:
                absolute_path, path_from_root, base_name, extension = row
                
                # Construire le chemin complet
                if absolute_path and path_from_root and base_name and extension:
                    full_path = os.path.join(
                        absolute_path,
                        path_from_root.lstrip('/'),
                        f"{base_name}.{extension}"
                    )
                    logger.debug(f"Chemin photo {photo_id}: {full_path}")
                    return full_path
                else:
                    logger.warning(f"Chemin incomplet pour photo {photo_id}")
            
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Erreur récupération chemin photo {photo_id}: {e}")
            return None


if __name__ == "__main__":
    # Test du module
    logging.basicConfig(level=logging.DEBUG)
    
    manager = LightroomManager()
    
    # Test avec un catalogue fictif
    catalog_path = "/path/to/test.lrcat"
    
    if manager.connect(catalog_path):
        print("✓ Connexion réussie")
        
        photos = manager.get_photos_list()
        print(f"Photos trouvées: {len(photos)}")
        
        if photos:
            photo = photos[0]
            print(f"Première photo: {photo}")
            
            # Test récupération Smart Preview
            image = manager.get_smart_preview(photo['photo_id'])
            if image:
                print(f"✓ Smart Preview chargé: {image.size}")
            
            # Test récupération tags
            tags = manager.get_existing_tags(photo['photo_id'])
            print(f"Tags existants: {tags}")
        
        manager.close()
    else:
        print("✗ Échec connexion")
