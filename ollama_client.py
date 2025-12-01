"""
Module de communication avec l'API Ollama pour l'analyse d'images et la génération de tags.
"""

import base64
import json
import logging
import requests
from io import BytesIO
from PIL import Image
from typing import List, Optional, Tuple
import config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client pour interagir avec l'API Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300):
        """
        Initialise le client Ollama.
        
        Args:
            base_url: URL de base du serveur Ollama
            timeout: Timeout en secondes pour les requêtes
        """
        self.base_url = base_url
        self.timeout = timeout
        self.api_url = f"{base_url}/api/generate"
        self.max_retries = 2  # Nombre de tentatives en cas d'échec
        
    def is_available(self) -> bool:
        """
        Vérifie si le serveur Ollama est accessible.
        
        Returns:
            True si Ollama répond, False sinon
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Ollama non accessible: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        Liste TOUS les modèles disponibles dans Ollama.
        Inclut les modèles personnalisés (ex: qwen-fast) et tous les modèles de vision.
        
        Returns:
            Liste des noms de modèles
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Récupérer TOUS les modèles sans filtrage
            models = []
            for model in data.get('models', []):
                model_name = model.get('name', '')
                if model_name:
                    models.append(model_name)
            
            # Trier par nom pour faciliter la sélection
            models.sort()
            
            logger.info(f"{len(models)} modèles trouvés: {models}")
            return models
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []
    
    def encode_image(self, image: Image.Image, max_size: int = 1024) -> str:
        """
        Encode une image PIL en base64.
        
        Args:
            image: Image PIL à encoder
            max_size: Taille maximale (largeur ou hauteur) pour redimensionner
            
        Returns:
            Image encodée en base64
        """
        # Redimensionner de manière plus agressive pour réduire le temps de traitement
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Image redimensionnée à {new_size}")
        
        # Convertir en RGB si nécessaire
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Encoder en base64 avec qualité réduite pour les gros fichiers
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=70, optimize=True)
        img_bytes = buffered.getvalue()
        logger.debug(f"Taille image encodée: {len(img_bytes)} octets")
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def generate_tags_auto(self, image: Image.Image, model: str) -> List[str]:
        """
        Génère des tags descriptifs automatiques pour une image.
        
        Args:
            image: Image PIL à analyser
            model: Nom du modèle Ollama à utiliser
            
        Returns:
            Liste de tags générés
        """
        # Utiliser le prompt configuré avec la langue spécifiée
        prompt = config.AUTO_PROMPT.format(language=config.TAG_LANGUAGE)
        
        return self._generate_tags(image, model, prompt)
    
    def generate_tags_targeted(self, image: Image.Image, model: str, 
                              criteria: str, target_tag: str) -> Tuple[bool, Optional[str]]:
        """
        Analyse une image pour un critère spécifique.
        
        Args:
            image: Image PIL à analyser
            model: Nom du modèle Ollama à utiliser
            criteria: Critère de recherche (ex: "la tour eiffel")
            target_tag: Tag à appliquer si le critère est détecté
            
        Returns:
            Tuple (détecté: bool, tag: Optional[str])
        """
        prompt = f"""Analyse cette photo et réponds uniquement par OUI ou NON.

Question: Cette photo contient-elle {criteria} ?

Réponds UNIQUEMENT par:
- OUI si tu détectes clairement {criteria} dans l'image
- NON sinon

Ne donne aucune explication, juste OUI ou NON.
"""
        
        try:
            image_b64 = self.encode_image(image)
            
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Réponse plus déterministe
                    "num_predict": 10    # Limite la réponse
                }
            }
            
            logger.debug(f"Envoi requête ciblée à Ollama pour critère: {criteria}")
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip().upper()
            
            logger.debug(f"Réponse Ollama: {response_text}")
            
            # Analyse de la réponse
            if 'OUI' in response_text or 'YES' in response_text:
                logger.info(f"Critère '{criteria}' détecté → tag '{target_tag}'")
                return True, target_tag
            else:
                logger.debug(f"Critère '{criteria}' non détecté")
                return False, None
                
        except requests.RequestException as e:
            logger.error(f"Erreur Ollama pour critère '{criteria}': {e}")
            return False, None
    
    def _generate_tags(self, image: Image.Image, model: str, prompt: str) -> List[str]:
        """
        Méthode interne pour générer des tags avec un prompt donné.
        Inclut une logique de retry en cas de timeout.
        
        Args:
            image: Image PIL à analyser
            model: Nom du modèle Ollama
            prompt: Prompt à envoyer
            
        Returns:
            Liste de tags
        """
        for attempt in range(self.max_retries):
            try:
                image_b64 = self.encode_image(image)
                
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 100  # Limiter la longueur de réponse
                    }
                }
                
                logger.info(f"Envoi requête à Ollama (modèle: {model}, tentative {attempt + 1}/{self.max_retries})")
                response = requests.post(self.api_url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('response', '')
                
                logger.debug(f"Réponse brute Ollama: {response_text}")
                
                # Parser la réponse pour extraire les tags
                tags = self._parse_tags(response_text)
                
                if tags:
                    logger.info(f"Tags générés: {tags}")
                    return tags
                else:
                    logger.warning("Aucun tag extrait de la réponse")
                    if attempt < self.max_retries - 1:
                        logger.info("Nouvelle tentative...")
                        continue
                    return []
                
            except requests.Timeout as e:
                logger.warning(f"Timeout lors de la tentative {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    logger.info("Nouvelle tentative avec timeout étendu...")
                    # Augmenter progressivement le timeout
                    self.timeout = min(self.timeout + 60, 600)
                else:
                    logger.error(f"Toutes les tentatives ont échoué pour ce prompt")
                    return []
            except requests.RequestException as e:
                logger.error(f"Erreur lors de la génération de tags (tentative {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    logger.info("Nouvelle tentative...")
                    continue
                return []
        
        return []
    
    def _parse_tags(self, response_text: str) -> List[str]:
        """
        Parse la réponse d'Ollama pour extraire les tags.
        
        Args:
            response_text: Texte de réponse brut
            
        Returns:
            Liste de tags nettoyés
        """
        # Nettoyer la réponse
        response_text = response_text.strip()
        
        # Supprimer les numéros et tirets de début de ligne
        lines = response_text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Enlever les numéros (1., 2., etc.) et tirets (-, *, •)
            if line:
                line = line.lstrip('0123456789.-*• \t')
                if line:
                    cleaned_lines.append(line)
        
        # Recombiner
        text = ', '.join(cleaned_lines) if cleaned_lines else response_text
        
        # Séparer par virgules
        tags = [tag.strip() for tag in text.split(',')]
        
        # Nettoyer chaque tag
        cleaned_tags = []
        for tag in tags:
            # Enlever les guillemets, parenthèses, etc.
            tag = tag.strip('"\'()[]{}')
            # Enlever les articles en début de tag
            for article in ['le ', 'la ', 'les ', 'un ', 'une ', 'des ', 'du ', 'de la ']:
                if tag.lower().startswith(article):
                    tag = tag[len(article):]
            tag = tag.strip()
            
            # Ne garder que les tags non vides et pas trop longs
            if tag and len(tag) > 1 and len(tag) < 50:
                # Capitaliser la première lettre
                tag = tag[0].upper() + tag[1:]
                cleaned_tags.append(tag)
        
        # Dédupliquer tout en préservant l'ordre
        seen = set()
        unique_tags = []
        for tag in cleaned_tags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag)
        
        return unique_tags[:15]  # Limiter à 15 tags maximum


if __name__ == "__main__":
    # Test du module
    logging.basicConfig(level=logging.DEBUG)
    
    client = OllamaClient()
    
    print("Test de connexion à Ollama...")
    if client.is_available():
        print("✓ Ollama est accessible")
        
        print("\nModèles disponibles:")
        models = client.list_models()
        for model in models:
            print(f"  - {model}")
    else:
        print("✗ Ollama n'est pas accessible")
