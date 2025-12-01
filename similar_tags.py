"""
Module de détection et fusion de tags similaires.
Utilise la distance de Levenshtein et sauvegarde les choix utilisateur.
"""

import json
import sqlite3
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SimilarTagDetector:
    """Détection et fusion de tags similaires."""
    
    def __init__(self, decisions_file: str = "tag_merge_decisions.json"):
        """
        Initialise le détecteur.
        
        Args:
            decisions_file: Fichier de sauvegarde des décisions
        """
        self.decisions_file = Path(decisions_file)
        self.decisions = self._load_decisions()
        self.similarity_threshold = 0.7  # 70% de similarité minimum
    
    def _load_decisions(self) -> Dict:
        """
        Charge les décisions précédentes.
        
        Returns:
            Dictionnaire des décisions
        """
        if self.decisions_file.exists():
            try:
                with open(self.decisions_file, 'r', encoding='utf-8') as f:
                    decisions = json.load(f)
                logger.info(f"{len(decisions)} décision(s) de fusion chargée(s)")
                return decisions
            except Exception as e:
                logger.error(f"Erreur chargement décisions: {e}")
        
        return {}
    
    def _save_decisions(self):
        """Sauvegarde les décisions."""
        try:
            with open(self.decisions_file, 'w', encoding='utf-8') as f:
                json.dump(self.decisions, f, indent=2, ensure_ascii=False)
            logger.info(f"Décisions sauvegardées: {self.decisions_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde décisions: {e}")
    
    def similarity(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes.
        
        Args:
            str1: Première chaîne
            str2: Deuxième chaîne
            
        Returns:
            Score de similarité (0-1)
        """
        # Normaliser (minuscules, strip)
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # SequenceMatcher de difflib
        ratio = SequenceMatcher(None, s1, s2).ratio()
        
        return ratio
    
    def find_similar_tags(self, conn: sqlite3.Connection) -> List[Dict]:
        """
        Trouve les tags similaires dans le catalogue.
        
        Args:
            conn: Connexion au catalogue Lightroom
            
        Returns:
            Liste de groupes de tags similaires
        """
        try:
            cursor = conn.cursor()
            
            # Récupérer tous les keywords avec leur utilisation
            cursor.execute("""
                SELECT 
                    k.id_local,
                    k.name,
                    COUNT(ki.image) as usage_count
                FROM AgLibraryKeyword k
                LEFT JOIN AgLibraryKeywordImage ki ON k.id_local = ki.tag
                GROUP BY k.id_local, k.name
                HAVING COUNT(ki.image) > 0
                ORDER BY k.name
            """)
            
            tags = cursor.fetchall()
            logger.info(f"{len(tags)} tag(s) avec utilisation trouvé(s)")
            
            # Trouver les groupes similaires
            similar_groups = []
            processed = set()
            
            for i, (id1, name1, count1) in enumerate(tags):
                if name1 in processed:
                    continue
                
                group = [(id1, name1, count1)]
                
                for id2, name2, count2 in tags[i+1:]:
                    if name2 in processed:
                        continue
                    
                    # Vérifier si décision déjà prise
                    decision_key = f"{name1}||{name2}"
                    reverse_key = f"{name2}||{name1}"
                    
                    if decision_key in self.decisions or reverse_key in self.decisions:
                        continue  # Déjà traité
                    
                    # Calculer similarité
                    sim = self.similarity(name1, name2)
                    
                    if sim >= self.similarity_threshold:
                        group.append((id2, name2, count2))
                        processed.add(name2)
                
                if len(group) > 1:
                    similar_groups.append({
                        'tags': group,
                        'similarity_scores': [
                            self.similarity(group[0][1], tag[1])
                            for tag in group[1:]
                        ]
                    })
                    processed.add(name1)
            
            logger.info(f"{len(similar_groups)} groupe(s) de tags similaires trouvé(s)")
            return similar_groups
            
        except Exception as e:
            logger.error(f"Erreur détection tags similaires: {e}")
            return []
    
    def merge_tags(self, conn: sqlite3.Connection, source_ids: List[int], target_id: int) -> bool:
        """
        Fusionne plusieurs tags en un seul.
        
        Args:
            conn: Connexion au catalogue
            source_ids: IDs des tags à fusionner
            target_id: ID du tag cible
            
        Returns:
            True si succès
        """
        try:
            cursor = conn.cursor()
            
            for source_id in source_ids:
                if source_id == target_id:
                    continue
                
                # Récupérer toutes les associations du tag source
                cursor.execute("""
                    SELECT image FROM AgLibraryKeywordImage
                    WHERE tag = ?
                """, (source_id,))
                
                images = cursor.fetchall()
                
                # Réassocier au tag cible
                for (image_id,) in images:
                    # Vérifier si l'association n'existe pas déjà
                    cursor.execute("""
                        SELECT COUNT(*) FROM AgLibraryKeywordImage
                        WHERE tag = ? AND image = ?
                    """, (target_id, image_id))
                    
                    if cursor.fetchone()[0] == 0:
                        # Créer l'association
                        cursor.execute("""
                            INSERT INTO AgLibraryKeywordImage (tag, image)
                            VALUES (?, ?)
                        """, (target_id, image_id))
                
                # Supprimer les anciennes associations
                cursor.execute("""
                    DELETE FROM AgLibraryKeywordImage
                    WHERE tag = ?
                """, (source_id,))
                
                # Supprimer le tag source
                cursor.execute("""
                    DELETE FROM AgLibraryKeyword
                    WHERE id_local = ?
                """, (source_id,))
            
            conn.commit()
            logger.info(f"Fusion réussie: {len(source_ids)} tag(s) → tag {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur fusion tags: {e}")
            if conn:
                conn.rollback()
            return False
    
    def save_decision(self, tag_names: List[str], chosen_tag: str, action: str):
        """
        Sauvegarde une décision de l'utilisateur.
        
        Args:
            tag_names: Liste des tags similaires
            chosen_tag: Tag choisi
            action: 'merge' ou 'keep_separate'
        """
        # Créer une clé pour cette décision
        key = "||".join(sorted(tag_names))
        
        self.decisions[key] = {
            'tags': tag_names,
            'chosen': chosen_tag,
            'action': action,
            'timestamp': str(Path(__file__).stat().st_mtime)
        }
        
        self._save_decisions()
        logger.info(f"Décision sauvegardée: {action} - {chosen_tag}")
    
    def get_decision(self, tag_names: List[str]) -> Optional[Dict]:
        """
        Récupère une décision précédente.
        
        Args:
            tag_names: Liste des tags
            
        Returns:
            Décision ou None
        """
        key = "||".join(sorted(tag_names))
        return self.decisions.get(key)
    
    def clear_decisions(self):
        """Efface toutes les décisions."""
        self.decisions = {}
        if self.decisions_file.exists():
            self.decisions_file.unlink()
        logger.info("Décisions effacées")
    
    def export_report(self, similar_groups: List[Dict], output_file: str):
        """
        Exporte un rapport des tags similaires.
        
        Args:
            similar_groups: Groupes de tags similaires
            output_file: Fichier de sortie
        """
        try:
            report = {
                'generated': str(Path(__file__).stat().st_mtime),
                'total_groups': len(similar_groups),
                'groups': []
            }
            
            for group in similar_groups:
                report['groups'].append({
                    'tags': [
                        {'id': tag_id, 'name': name, 'usage': count}
                        for tag_id, name, count in group['tags']
                    ],
                    'similarity_scores': group['similarity_scores']
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Rapport exporté: {output_file}")
            
        except Exception as e:
            logger.error(f"Erreur export rapport: {e}")
