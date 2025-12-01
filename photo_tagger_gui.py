"""
Photo Auto Tagger - Application GUI principale
Tagging automatique de photos Lightroom avec Ollama
"""

import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
from datetime import datetime
import json

# Import des modules locaux
import config
from ollama_client import OllamaClient
from lightroom_manager import LightroomManager
from xmp_manager import XMPManager

# Configuration du logging depuis config.py
log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PhotoTaggerGUI:
    """Application GUI pour le tagging automatique de photos."""
    
    def __init__(self, root):
        """
        Initialise l'interface graphique.
        
        Args:
            root: Fenêtre Tkinter principale
        """
        self.root = root
        self.root.title("Photo Auto Tagger - Lightroom & Ollama")
        self.root.geometry("1200x900")
        
        # Initialiser les gestionnaires
        self.ollama_client = OllamaClient()
        self.lightroom_manager = LightroomManager()
        self.xmp_manager = XMPManager()
        
        # Variables d'état
        self.source_mode = tk.StringVar(value="catalog")  # "catalog" ou "folder"
        self.catalog_path = tk.StringVar()
        self.folder_path = tk.StringVar()
        self.selected_model = tk.StringVar()
        self.write_to_catalog = tk.BooleanVar(value=True)
        self.write_to_xmp = tk.BooleanVar(value=True)
        self.tagging_mode = tk.StringVar(value="auto")  # "auto" ou "targeted"
        
        # Variables de progression
        self.is_processing = False
        self.should_stop = False
        self.should_pause = False
        self.current_photo = 0
        self.total_photos = 0
        self.photos_analyzed = 0  # Nombre de photos analysées
        self.photos_tagged = 0    # Nombre de photos où on a ajouté des tags
        self.processing_thread = None
        
        # Cache pour l'accessibilité des disques (optimisation)
        self.disk_accessible_cache = {}  # {'/Volumes/DD3Photo': False, ...}
        
        # Compteurs de résultats
        self.stats_tags_written_catalog = 0
        self.stats_tags_written_xmp = 0
        self.stats_xmp_skipped_no_file = 0
        
        # Fichier de sauvegarde d'état
        self.state_file = "photo_tagger_state.json"
        
        # Vérifier si un état sauvegardé existe
        self.has_saved_state = os.path.exists(self.state_file)
        
        # Si un état sauvegardé existe, informer l'utilisateur
        if self.has_saved_state:
            root.after(500, self._show_resume_notification)
        
        # Mappings critère/tag
        self.mappings: List[Tuple[str, str]] = []
        
        # Créer l'interface
        self._create_ui()
        
        # Charger les modèles Ollama
        self._load_models()
    
    def _create_ui(self):
        """Crée tous les éléments de l'interface."""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal avec scrollbar si nécessaire
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Section 1: Configuration du modèle
        self._create_model_section(main_frame)
        
        # Section 2: Source des photos
        self._create_source_section(main_frame)
        
        # Section 3: Destination des tags
        self._create_destination_section(main_frame)
        
        # Section 4: Mode de tagging
        self._create_tagging_mode_section(main_frame)
        
        # Section 5: Contrôle et progression
        self._create_control_section(main_frame)
    
    def _create_model_section(self, parent):
        """Crée la section de sélection du modèle."""
        frame = ttk.LabelFrame(parent, text="1. Configuration du modèle", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Modèle Ollama:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.model_combo = ttk.Combobox(
            frame,
            textvariable=self.selected_model,
            state="readonly",
            width=50
        )
        self.model_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
    
    def _create_source_section(self, parent):
        """Crée la section de sélection de la source."""
        frame = ttk.LabelFrame(parent, text="2. Source des photos", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # Radio: Catalogue Lightroom
        catalog_radio = ttk.Radiobutton(
            frame,
            text="Catalogue Lightroom",
            variable=self.source_mode,
            value="catalog",
            command=self._on_source_mode_changed
        )
        catalog_radio.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.catalog_entry = ttk.Entry(frame, textvariable=self.catalog_path, width=70)
        self.catalog_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.catalog_browse_btn = ttk.Button(
            frame,
            text="Parcourir...",
            command=self._browse_catalog
        )
        self.catalog_browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Radio: Répertoire de photos
        folder_radio = ttk.Radiobutton(
            frame,
            text="Répertoire de photos",
            variable=self.source_mode,
            value="folder",
            command=self._on_source_mode_changed
        )
        folder_radio.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.folder_entry = ttk.Entry(frame, textvariable=self.folder_path, width=70)
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)
        self.folder_entry.config(state=tk.DISABLED)
        
        self.folder_browse_btn = ttk.Button(
            frame,
            text="Parcourir...",
            command=self._browse_folder,
            state=tk.DISABLED
        )
        self.folder_browse_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Warning
        self.warning_label = ttk.Label(
            frame,
            text="⚠️ Attention: l'analyse directe des photos sera plus lente que l'utilisation des Smart Previews du catalogue",
            foreground="orange",
            font=("TkDefaultFont", 9)
        )
        self.warning_label.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)
        self.warning_label.grid_remove()  # Masquer par défaut
    
    def _create_destination_section(self, parent):
        """Crée la section de destination des tags."""
        frame = ttk.LabelFrame(parent, text="3. Destination des tags", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # Ligne 1 : Catalogue et XMP
        self.catalog_check = ttk.Checkbutton(
            frame,
            text="Écrire dans le catalogue Lightroom (.lrcat)",
            variable=self.write_to_catalog
        )
        self.catalog_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.xmp_check = ttk.Checkbutton(
            frame,
            text="Écrire dans les fichiers XMP (portabilité)",
            variable=self.write_to_xmp
        )
        self.xmp_check.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Ligne 2 : Suffixe de tags
        suffix_frame = ttk.Frame(frame)
        suffix_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.tag_suffix_enabled = tk.BooleanVar(value=config.TAG_SUFFIX_ENABLED)
        suffix_check = ttk.Checkbutton(
            suffix_frame,
            text="Ajouter un suffixe aux tags automatiques",
            variable=self.tag_suffix_enabled,
            command=self._update_suffix_example
        )
        suffix_check.pack(side=tk.LEFT)
        
        # Entrée pour le suffixe
        ttk.Label(suffix_frame, text="Suffixe:").pack(side=tk.LEFT, padx=(10, 5))
        self.tag_suffix_var = tk.StringVar(value=config.TAG_SUFFIX)
        self.tag_suffix_entry = ttk.Entry(suffix_frame, width=10, textvariable=self.tag_suffix_var)
        self.tag_suffix_entry.pack(side=tk.LEFT)
        
        # Lier le changement de texte à la mise à jour de l'exemple
        self.tag_suffix_var.trace_add('write', lambda *args: self._update_suffix_example())
        
        # Label d'exemple (mis à jour dynamiquement)
        self.suffix_example_label = ttk.Label(suffix_frame, text="", foreground="gray")
        self.suffix_example_label.pack(side=tk.LEFT, padx=10)
        
        # Initialiser l'exemple
        self._update_suffix_example()
    
    def _create_tagging_mode_section(self, parent):
        """Crée la section du mode de tagging."""
        frame = ttk.LabelFrame(parent, text="4. Mode de tagging", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Radio buttons
        auto_radio = ttk.Radiobutton(
            frame,
            text="Mode automatique (tags descriptifs généraux)",
            variable=self.tagging_mode,
            value="auto",
            command=self._on_tagging_mode_changed
        )
        auto_radio.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        targeted_radio = ttk.Radiobutton(
            frame,
            text="Mode ciblé (recherche par critères spécifiques)",
            variable=self.tagging_mode,
            value="targeted",
            command=self._on_tagging_mode_changed
        )
        targeted_radio.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Table de mapping
        self._create_mapping_table(frame)
    
    def _create_mapping_table(self, parent):
        """Crée la table de mapping critère/tag."""
        table_frame = ttk.Frame(parent)
        table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=10)
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        
        ttk.Label(table_frame, text="Mapping Critère → Tag", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        # Frame avec scrollbar
        tree_scroll_frame = ttk.Frame(table_frame)
        tree_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview pour la table
        self.mapping_tree = ttk.Treeview(
            tree_scroll_frame,
            columns=("criteria", "tag"),
            show="headings",
            height=5,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.mapping_tree.yview)
        
        self.mapping_tree.heading("criteria", text="Critère de recherche")
        self.mapping_tree.heading("tag", text="Tag à appliquer")
        self.mapping_tree.column("criteria", width=500)
        self.mapping_tree.column("tag", width=450)
        
        self.mapping_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Boutons d'action
        btn_frame = ttk.Frame(table_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.add_mapping_btn = ttk.Button(
            btn_frame,
            text="➕ Ajouter un mapping",
            command=self._add_mapping,
            state=tk.DISABLED
        )
        self.add_mapping_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_mapping_btn = ttk.Button(
            btn_frame,
            text="✏️ Modifier",
            command=self._edit_mapping,
            state=tk.DISABLED
        )
        self.edit_mapping_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_mapping_btn = ttk.Button(
            btn_frame,
            text="🗑️ Supprimer",
            command=self._delete_mapping,
            state=tk.DISABLED
        )
        self.delete_mapping_btn.pack(side=tk.LEFT, padx=5)
        
        # Exemples par défaut
        self._add_example_mappings()
    
    def _create_control_section(self, parent):
        """Crée la section de contrôle et progression."""
        frame = ttk.LabelFrame(parent, text="5. Contrôle et progression", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # Boutons START/STOP/PAUSE/RESUME
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(
            btn_frame,
            text="▶️ START",
            command=self._start_processing,
            style="Start.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(
            btn_frame,
            text="⏸️ PAUSE",
            command=self._pause_processing,
            state=tk.DISABLED,
            style="Pause.TButton"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.resume_btn = ttk.Button(
            btn_frame,
            text="▶️ RESUME",
            command=self._resume_processing,
            state=tk.DISABLED if not self.has_saved_state else tk.NORMAL,
            style="Resume.TButton"
        )
        self.resume_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹️ STOP",
            command=self._stop_processing,
            state=tk.DISABLED,
            style="Stop.TButton"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Barre de progression
        progress_frame = ttk.Frame(frame)
        progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        
        # Sous-frame pour la barre seule
        bar_frame = ttk.Frame(progress_frame)
        bar_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(bar_frame, text="Progression:").pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(
            bar_frame,
            mode="determinate",
            length=400
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Frame pour les indicateurs (SOUS la barre)
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X)
        
        # Indicateur 1 : Progression en %
        progress_pct_frame = ttk.Frame(stats_frame)
        progress_pct_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(progress_pct_frame, text="📊 Progression:", foreground="blue").pack(side=tk.LEFT)
        self.progress_pct_label = ttk.Label(progress_pct_frame, text="0.000%", font=("TkDefaultFont", 10, "bold"))
        self.progress_pct_label.pack(side=tk.LEFT, padx=3)
        
        # Séparateur
        ttk.Label(stats_frame, text="│").pack(side=tk.LEFT, padx=5)
        
        # Indicateur 2 : Taguées
        tagged_frame = ttk.Frame(stats_frame)
        tagged_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(tagged_frame, text="✅ Taguées:", foreground="green").pack(side=tk.LEFT)
        self.tagged_label = ttk.Label(tagged_frame, text="0", font=("TkDefaultFont", 10, "bold"))
        self.tagged_label.pack(side=tk.LEFT, padx=3)
        
        # Séparateur
        ttk.Label(stats_frame, text="│").pack(side=tk.LEFT, padx=5)
        
        # Indicateur 3 : Total
        total_frame = ttk.Frame(stats_frame)
        total_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(total_frame, text="📷 Total:", foreground="gray").pack(side=tk.LEFT)
        self.total_label = ttk.Label(total_frame, text="0", font=("TkDefaultFont", 10, "bold"))
        self.total_label.pack(side=tk.LEFT, padx=3)
        
        # Configurer les styles des boutons
        style = ttk.Style()
        style.configure("Start.TButton", foreground="green")
        style.configure("Resume.TButton", foreground="blue")
        style.configure("Pause.TButton", foreground="orange")
        style.configure("Stop.TButton", foreground="red")
    
    # ===== Méthodes de gestion des événements =====
    
    def _load_models(self):
        """Charge la liste des modèles Ollama disponibles."""
        try:
            if not self.ollama_client.is_available():
                messagebox.showerror(
                    "Erreur Ollama",
                    "Impossible de se connecter à Ollama.\n\n"
                    "Vérifiez qu'Ollama est lancé:\n"
                    "  ollama serve"
                )
                self.model_combo['values'] = ["Ollama non disponible"]
                return
            
            models = self.ollama_client.list_models()
            
            if not models:
                messagebox.showwarning(
                    "Aucun modèle",
                    "Aucun modèle de vision trouvé dans Ollama.\n\n"
                    "Installez un modèle:\n"
                    "  ollama pull qwen2-vl"
                )
                self.model_combo['values'] = ["Aucun modèle"]
                return
            
            self.model_combo['values'] = models
            self.selected_model.set(models[0])
            logger.info(f"Modèles chargés: {models}")
            
        except Exception as e:
            logger.error(f"Erreur chargement modèles: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des modèles:\n{e}")
    
    def _on_source_mode_changed(self):
        """Appelé quand le mode source change."""
        mode = self.source_mode.get()
        
        if mode == "catalog":
            # Activer catalogue, désactiver folder
            self.catalog_entry.config(state=tk.NORMAL)
            self.catalog_browse_btn.config(state=tk.NORMAL)
            self.folder_entry.config(state=tk.DISABLED)
            self.folder_browse_btn.config(state=tk.DISABLED)
            self.warning_label.grid_remove()
            
            # Activer option catalogue
            self.catalog_check.config(state=tk.NORMAL)
            
        else:  # folder
            # Désactiver catalogue, activer folder
            self.catalog_entry.config(state=tk.DISABLED)
            self.catalog_browse_btn.config(state=tk.DISABLED)
            self.folder_entry.config(state=tk.NORMAL)
            self.folder_browse_btn.config(state=tk.NORMAL)
            self.warning_label.grid()
            
            # Désactiver option catalogue, forcer XMP
            self.catalog_check.config(state=tk.DISABLED)
            self.write_to_catalog.set(False)
            self.write_to_xmp.set(True)
    
    def _on_tagging_mode_changed(self):
        """Appelé quand le mode de tagging change."""
        mode = self.tagging_mode.get()
        
        if mode == "auto":
            # Désactiver les boutons de mapping
            self.add_mapping_btn.config(state=tk.DISABLED)
            self.edit_mapping_btn.config(state=tk.DISABLED)
            self.delete_mapping_btn.config(state=tk.DISABLED)
        else:  # targeted
            # Activer les boutons de mapping
            self.add_mapping_btn.config(state=tk.NORMAL)
            self.edit_mapping_btn.config(state=tk.NORMAL)
            self.delete_mapping_btn.config(state=tk.NORMAL)
    
    def _update_suffix_example(self):
        """Met à jour l'exemple de suffixe dynamiquement."""
        if self.tag_suffix_enabled.get():
            suffix = self.tag_suffix_var.get()
            if suffix:
                example_text = f"(ex: Montagne → Montagne{suffix})"
            else:
                example_text = "(ex: Montagne → Montagne)"
        else:
            example_text = "(suffixe désactivé)"
        
        self.suffix_example_label.config(text=example_text)
    
    def _browse_catalog(self):
        """Ouvre un dialogue pour sélectionner le catalogue."""
        filename = filedialog.askopenfilename(
            title="Sélectionner un catalogue Lightroom",
            filetypes=[("Lightroom Catalog", "*.lrcat"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            self.catalog_path.set(filename)
    
    def _browse_folder(self):
        """Ouvre un dialogue pour sélectionner un dossier."""
        folder = filedialog.askdirectory(
            title="Sélectionner un dossier de photos"
        )
        if folder:
            self.folder_path.set(folder)
    
    def _add_example_mappings(self):
        """Ajoute des exemples de mapping par défaut."""
        examples = [
            ("la tour eiffel", "TourEiffel"),
            ("des bâtiments", "Architecture"),
            ("un coucher de soleil", "Sunset")
        ]
        
        for criteria, tag in examples:
            self.mappings.append((criteria, tag))
            self.mapping_tree.insert("", tk.END, values=(criteria, tag))
    
    def _add_mapping(self):
        """Ajoute un nouveau mapping."""
        dialog = MappingDialog(self.root, "Ajouter un mapping")
        if dialog.result:
            criteria, tag = dialog.result
            self.mappings.append((criteria, tag))
            self.mapping_tree.insert("", tk.END, values=(criteria, tag))
    
    def _edit_mapping(self):
        """Modifie le mapping sélectionné."""
        selection = self.mapping_tree.selection()
        if not selection:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un mapping à modifier")
            return
        
        item = selection[0]
        values = self.mapping_tree.item(item, 'values')
        
        dialog = MappingDialog(self.root, "Modifier le mapping", values[0], values[1])
        if dialog.result:
            criteria, tag = dialog.result
            index = self.mapping_tree.index(item)
            self.mappings[index] = (criteria, tag)
            self.mapping_tree.item(item, values=(criteria, tag))
    
    def _delete_mapping(self):
        """Supprime le mapping sélectionné."""
        selection = self.mapping_tree.selection()
        if not selection:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un mapping à supprimer")
            return
        
        item = selection[0]
        index = self.mapping_tree.index(item)
        
        if messagebox.askyesno("Confirmation", "Supprimer ce mapping ?"):
            self.mappings.pop(index)
            self.mapping_tree.delete(item)
    
    # ===== Méthodes de traitement =====
    
    def _start_processing(self):
        """Lance le traitement des photos."""
        # Validation
        if not self._validate_inputs():
            return
        
        # Désactiver les contrôles
        self.start_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Réinitialiser les compteurs
        self.is_processing = True
        self.should_stop = False
        self.should_pause = False
        self.current_photo = 0
        self.total_photos = 0
        self.photos_analyzed = 0
        self.photos_tagged = 0
        self.stats_tags_written_catalog = 0
        self.stats_tags_written_xmp = 0
        self.stats_xmp_skipped_no_file = 0
        
        # Réinitialiser le cache d'accessibilité des disques
        self.disk_accessible_cache = {}
        
        # Lancer le thread de traitement
        self.processing_thread = threading.Thread(target=self._process_photos)
        self.processing_thread.start()
    
    def _show_resume_notification(self):
        """Affiche une notification si un traitement en pause est détecté."""
        if not os.path.exists(self.state_file):
            return
        
        # Charger l'état pour afficher les infos
        state = self._load_state()
        if not state:
            return
        
        current = state.get('current_photo', 0)
        total = state.get('total_photos', 0)
        timestamp = state.get('timestamp', 'inconnu')
        percentage = (current / total * 100) if total > 0 else 0
        
        message = (
            f"🔄 Traitement en pause détecté !\n\n"
            f"📅 Date de la pause : {timestamp}\n"
            f"📊 Progression sauvegardée : {current} / {total} photos ({percentage:.1f}%)\n\n"
            f"Vous pouvez :\n"
            f"  ▶️ Cliquer sur RESUME pour reprendre exactement où vous vous étiez arrêté\n"
            f"  ▶️ Cliquer sur START pour recommencer un nouveau traitement\n\n"
            f"💡 Tous vos paramètres (modèle, mappings, options) seront automatiquement restaurés."
        )
        
        messagebox.showinfo("Reprise disponible", message)
    
    def _stop_processing(self):
        """Arrête le traitement en cours."""
        if messagebox.askyesno("Confirmation", "Arrêter le traitement en cours ?\n\nL'état ne sera pas sauvegardé."):
            self.should_stop = True
            # Supprimer l'état sauvegardé s'il existe
            if os.path.exists(self.state_file):
                try:
                    os.remove(self.state_file)
                    logger.info("État sauvegardé supprimé")
                except:
                    pass
            logger.info("Arrêt demandé par l'utilisateur")
    
    def _pause_processing(self):
        """Met en pause le traitement et sauvegarde l'état."""
        if messagebox.askyesno("Pause", "Mettre en pause le traitement ?\n\nL'état sera sauvegardé pour reprendre ultérieurement."):
            self.should_pause = True
            logger.info("Pause demandée par l'utilisateur")
    
    def _resume_processing(self):
        """Reprend le traitement depuis l'état sauvegardé."""
        if not os.path.exists(self.state_file):
            messagebox.showerror("Erreur", "Aucun état sauvegardé trouvé")
            return
        
        # Charger l'état
        state = self._load_state()
        if not state:
            messagebox.showerror("Erreur", "Impossible de charger l'état sauvegardé")
            return
        
        # Afficher un résumé de ce qui va être restauré
        current = state.get('current_photo', 0)
        total = state.get('total_photos', 0)
        model = state.get('selected_model', 'inconnu')
        timestamp = state.get('timestamp', 'inconnu')
        
        confirm_msg = (
            f"📋 Confirmation de reprise\n\n"
            f"État sauvegardé le : {timestamp}\n"
            f"Progression : {current} / {total} photos ({(current/total*100):.1f}%)\n"
            f"Modèle : {model}\n\n"
            f"Le traitement reprendra à la photo {current + 1}.\n"
            f"Tous vos paramètres seront restaurés.\n\n"
            f"Continuer ?"
        )
        
        if not messagebox.askyesno("Reprendre le traitement", confirm_msg):
            return
        
        # Restaurer la configuration
        self._restore_state(state)
        
        # Désactiver les contrôles
        self.start_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Réinitialiser les flags
        self.is_processing = True
        self.should_stop = False
        self.should_pause = False
        
        # Lancer le thread de traitement
        self.processing_thread = threading.Thread(target=self._process_photos)
        self.processing_thread.start()
        
        logger.info(f"Reprise du traitement à partir de la photo {self.current_photo}/{self.total_photos}")
        logger.info(f"Configuration restaurée : modèle={model}, source={state.get('source_mode')}")
    
    def _save_state(self):
        """Sauvegarde l'état actuel du traitement."""
        import json
        
        state = {
            'version': '1.3',
            'timestamp': str(datetime.now()),
            'source_mode': self.source_mode.get(),
            'catalog_path': self.catalog_path.get(),
            'folder_path': self.folder_path.get(),
            'selected_model': self.selected_model.get(),
            'write_to_catalog': self.write_to_catalog.get(),
            'write_to_xmp': self.write_to_xmp.get(),
            'tagging_mode': self.tagging_mode.get(),
            'mappings': self.mappings,
            'current_photo': self.current_photo,
            'total_photos': self.total_photos,
            'photos_analyzed': self.photos_analyzed,
            'photos_tagged': self.photos_tagged,
            'stats_tags_written_catalog': self.stats_tags_written_catalog,
            'stats_tags_written_xmp': self.stats_tags_written_xmp,
            'stats_xmp_skipped_no_file': self.stats_xmp_skipped_no_file
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            logger.info(f"État sauvegardé: photo {self.current_photo}/{self.total_photos}, analysées: {self.photos_analyzed}, taguées: {self.photos_tagged}")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde état: {e}")
            return False
    
    def _load_state(self) -> dict:
        """Charge l'état sauvegardé."""
        import json
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            logger.info(f"État chargé: photo {state['current_photo']}/{state['total_photos']}")
            return state
        except Exception as e:
            logger.error(f"Erreur chargement état: {e}")
            return None
    
    def _restore_state(self, state: dict):
        """Restaure l'état de l'interface depuis l'état sauvegardé."""
        # Restaurer les paramètres
        self.source_mode.set(state['source_mode'])
        self.catalog_path.set(state['catalog_path'])
        self.folder_path.set(state['folder_path'])
        self.selected_model.set(state['selected_model'])
        self.write_to_catalog.set(state['write_to_catalog'])
        self.write_to_xmp.set(state['write_to_xmp'])
        self.tagging_mode.set(state['tagging_mode'])
        
        # Restaurer les mappings
        self.mappings = state['mappings']
        self.mapping_tree.delete(*self.mapping_tree.get_children())
        for criteria, tag in self.mappings:
            self.mapping_tree.insert("", tk.END, values=(criteria, tag))
        
        # Restaurer la progression
        self.current_photo = state['current_photo']
        self.total_photos = state['total_photos']
        self.photos_analyzed = state.get('photos_analyzed', 0)  # Compatibilité anciennes versions
        self.photos_tagged = state.get('photos_tagged', 0)  # Compatibilité anciennes versions
        self.stats_tags_written_catalog = state['stats_tags_written_catalog']
        self.stats_tags_written_xmp = state['stats_tags_written_xmp']
        self.stats_xmp_skipped_no_file = state['stats_xmp_skipped_no_file']
        
        # Mettre à jour l'interface
        self._on_source_mode_changed()
        self._on_tagging_mode_changed()
        self._update_progress()
    
    def _validate_inputs(self) -> bool:
        """
        Valide les entrées utilisateur.
        
        Returns:
            True si valide, False sinon
        """
        # Vérifier le modèle
        if not self.selected_model.get() or self.selected_model.get() in ["Ollama non disponible", "Aucun modèle"]:
            messagebox.showerror("Erreur", "Veuillez sélectionner un modèle Ollama valide")
            return False
        
        # Vérifier la source
        mode = self.source_mode.get()
        if mode == "catalog":
            catalog = self.catalog_path.get()
            if not catalog:
                messagebox.showerror("Erreur", "Veuillez sélectionner un catalogue Lightroom")
                return False
            if not os.path.exists(catalog):
                messagebox.showerror("Erreur", f"Catalogue introuvable:\n{catalog}")
                return False
        else:  # folder
            folder = self.folder_path.get()
            if not folder:
                messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de photos")
                return False
            if not os.path.exists(folder):
                messagebox.showerror("Erreur", f"Dossier introuvable:\n{folder}")
                return False
        
        # Vérifier la destination
        if not self.write_to_catalog.get() and not self.write_to_xmp.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner au moins une destination (Catalogue ou XMP)")
            return False
        
        # NOUVELLE VÉRIFICATION: Mode catalogue avec uniquement XMP
        if mode == "catalog" and not self.write_to_catalog.get() and self.write_to_xmp.get():
            response = messagebox.askyesno(
                "Attention - Photos originales requises",
                "Vous avez sélectionné le mode Catalogue avec écriture XMP uniquement.\n\n"
                "⚠️ IMPORTANT : L'application ne créera des fichiers XMP que si les photos "
                "originales sont accessibles sur le disque.\n\n"
                "Si seuls les Smart Previews sont disponibles (sans photos originales), "
                "aucun XMP ne sera créé.\n\n"
                "Recommandation : Cochez aussi 'Écrire dans le catalogue' pour garantir "
                "que les tags soient sauvegardés.\n\n"
                "Voulez-vous continuer quand même ?",
                icon='warning'
            )
            if not response:
                return False
        
        # Vérifier les mappings en mode ciblé
        if self.tagging_mode.get() == "targeted" and not self.mappings:
            messagebox.showerror("Erreur", "Veuillez ajouter au moins un mapping critère/tag")
            return False
        
        return True
    
    def _process_photos(self):
        """Thread de traitement principal."""
        try:
            logger.info("Début du traitement")
            
            # Récupérer les photos à traiter
            photos = self._get_photos_to_process()
            
            if not photos:
                self._show_error("Aucune photo à traiter")
                return
            
            self.total_photos = len(photos)
            logger.info(f"{self.total_photos} photos à traiter")
            
            # Traiter chaque photo
            for i, photo in enumerate(photos):
                # Reprendre depuis la photo sauvegardée si c'est une reprise
                if self.current_photo > 0 and i < self.current_photo:
                    # Mettre à jour la progression même si on ignore cette photo
                    self._update_progress()
                    continue
                
                if self.should_stop:
                    logger.info("Traitement arrêté par l'utilisateur")
                    break
                
                if self.should_pause:
                    logger.info("Traitement mis en pause")
                    self._save_state()
                    self._show_info(
                        f"⏸️ Traitement mis en pause !\n\n"
                        f"📊 Progression sauvegardée : {self.current_photo} / {self.total_photos} photos\n"
                        f"📈 Pourcentage : {(self.current_photo / self.total_photos * 100):.1f}%\n\n"
                        f"💾 État sauvegardé dans : {self.state_file}\n\n"
                        f"✅ Vous pouvez maintenant :\n"
                        f"   • FERMER cette application\n"
                        f"   • Éteindre votre ordinateur\n"
                        f"   • Faire autre chose\n\n"
                        f"🔄 Pour reprendre :\n"
                        f"   1. Relancer l'application\n"
                        f"   2. Cliquer sur le bouton RESUME\n"
                        f"   3. Tous vos paramètres seront restaurés automatiquement\n"
                        f"   4. Le traitement reprendra à la photo {self.current_photo + 1}"
                    )
                    return
                
                self.current_photo = i + 1
                self._update_progress()
                
                try:
                    self._process_single_photo(photo)
                except Exception as e:
                    logger.error(f"Erreur traitement photo {photo}: {e}")
                    continue
            
            # Fin du traitement
            if not self.should_stop and not self.should_pause:
                # Traitement terminé complètement - supprimer l'état sauvegardé
                if os.path.exists(self.state_file):
                    try:
                        os.remove(self.state_file)
                        logger.info("État sauvegardé supprimé (traitement terminé)")
                    except:
                        pass
                
                # Construire le rapport
                report = f"Traitement terminé !\n\n"
                report += f"Photos traitées : {self.current_photo} / {self.total_photos}\n"
                
                if self.stats_tags_written_catalog > 0:
                    report += f"\n✅ Tags écrits dans le catalogue : {self.stats_tags_written_catalog}"
                
                if self.stats_tags_written_xmp > 0:
                    report += f"\n✅ Fichiers XMP créés/mis à jour : {self.stats_tags_written_xmp}"
                
                if self.stats_xmp_skipped_no_file > 0:
                    report += f"\n\n⚠️ XMP non créés (photos originales introuvables) : {self.stats_xmp_skipped_no_file}"
                    report += f"\n   → Vérifiez que les disques contenant les photos sont montés"
                
                self._show_info(report)
            
        except Exception as e:
            logger.error(f"Erreur traitement: {e}", exc_info=True)
            self._show_error(f"Erreur lors du traitement:\n{e}")
        
        finally:
            # Fermer les connexions
            if self.lightroom_manager.conn:
                self.lightroom_manager.close()
            
            # Réactiver les contrôles
            self._reset_ui()
    
    def _get_photos_to_process(self) -> List:
        """
        Récupère la liste des photos à traiter.
        
        Returns:
            Liste de photos (format dépend du mode)
        """
        mode = self.source_mode.get()
        
        if mode == "catalog":
            # Mode catalogue
            catalog_path = self.catalog_path.get()
            if not self.lightroom_manager.connect(catalog_path):
                raise Exception("Impossible de se connecter au catalogue")
            
            photos = self.lightroom_manager.get_photos_list()
            return photos
            
        else:  # folder
            # Mode répertoire
            folder_path = self.folder_path.get()
            supported_formats = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.cr2', '.nef', '.arw', '.dng']
            
            photos = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_formats:
                        full_path = os.path.join(root, file)
                        photos.append({'full_path': full_path, 'filename': file})
            
            return photos
    
    def _process_single_photo(self, photo: Dict):
        """
        Traite une seule photo.
        
        Args:
            photo: Dictionnaire contenant les infos de la photo
        """
        mode = self.source_mode.get()
        
        try:
            # Charger l'image
            if mode == "catalog":
                photo_id = photo['photo_id']
                
                # Récupérer le chemin complet pour les logs
                photo_path = self.lightroom_manager.get_photo_path(photo_id)
                if photo_path:
                    logger.info(f"Traitement photo ID {photo_id}: {photo.get('filename', 'N/A')} [{photo_path}]")
                else:
                    logger.info(f"Traitement photo ID {photo_id}: {photo.get('filename', 'N/A')} [chemin inconnu]")
                
                # Essayer Smart Preview puis Preview standard
                image = self.lightroom_manager.get_smart_preview(photo_id)
                
                # Si aucun preview disponible, essayer le fichier original
                if image is None and photo.get('full_path'):
                    photo_path = photo['full_path']
                    
                    # Extraire le point de montage du disque (ex: /Volumes/DD3Photo)
                    # Pour optimiser, on ne teste qu'une fois par disque
                    path_parts = photo_path.split(os.sep)
                    
                    # Identifier le point de montage
                    if photo_path.startswith('/Volumes/'):
                        # macOS: /Volumes/DiskName/...
                        disk_mount = os.sep.join(path_parts[:3])  # /Volumes/DiskName
                    elif photo_path.startswith('/media/'):
                        # Linux: /media/user/DiskName/...
                        disk_mount = os.sep.join(path_parts[:4])  # /media/user/DiskName
                    elif len(path_parts) > 1 and path_parts[0] == '' and len(path_parts[1]) == 2 and path_parts[1].endswith(':'):
                        # Windows: C:\...
                        disk_mount = path_parts[1]  # C:
                    else:
                        # Chemin local, probablement accessible
                        disk_mount = os.sep.join(path_parts[:2])  # /home ou similaire
                    
                    # Vérifier le cache d'abord
                    if disk_mount in self.disk_accessible_cache:
                        disk_accessible = self.disk_accessible_cache[disk_mount]
                        logger.debug(f"Cache disque: {disk_mount} → {'accessible' if disk_accessible else 'non accessible'}")
                    else:
                        # Tester l'accessibilité du disque (une seule fois)
                        disk_accessible = os.path.exists(disk_mount)
                        self.disk_accessible_cache[disk_mount] = disk_accessible
                        
                        if disk_accessible:
                            logger.info(f"✅ Disque accessible: {disk_mount}")
                        else:
                            logger.warning(
                                f"❌ Disque non monté: {disk_mount}\n"
                                f"   → Les photos sur ce disque seront ignorées sans Smart Preview/Preview\n"
                                f"   → Créez des Smart Previews dans Lightroom pour traiter sans les fichiers originaux"
                            )
                    
                    # Charger le fichier si le disque est accessible
                    if disk_accessible:
                        logger.info(f"Pas de preview disponible, chargement depuis fichier: {photo_path}")
                        image = self.lightroom_manager.load_image_from_file(photo_path)
                    else:
                        logger.debug(
                            f"Photo {photo_id} ignorée (disque non monté: {disk_mount})"
                        )
            
            else:  # folder
                photo_path = photo['full_path']
                logger.info(f"Traitement photo: {photo['filename']} [{photo_path}]")
                image = Image.open(photo_path)
            
            if image is None:
                logger.error(f"Impossible de charger l'image: {photo}")
                return
            
            # Afficher la taille de l'image pour debug
            logger.info(f"Image chargée: {image.size} pixels, mode: {image.mode}")
            
            # Incrémenter le compteur de photos analysées
            self.photos_analyzed += 1
            
            # Générer les tags avec gestion d'erreur
            try:
                tags = self._generate_tags_for_image(image)
            except Exception as e:
                logger.error(f"Erreur génération tags: {e}", exc_info=True)
                tags = []
            
            if not tags:
                if mode == "catalog":
                    photo_path = self.lightroom_manager.get_photo_path(photo['photo_id'])
                    logger.warning(f"Aucun tag généré pour photo ID {photo['photo_id']}: {photo.get('filename', 'N/A')} [{photo_path or 'chemin inconnu'}]")
                else:
                    logger.warning(f"Aucun tag généré pour: {photo.get('filename', photo)} [{photo.get('full_path', 'N/A')}]")
                # Continuer quand même pour la photo suivante
                return
            
            # Log avec chemin complet
            if mode == "catalog":
                photo_path = self.lightroom_manager.get_photo_path(photo['photo_id'])
                logger.info(f"Tags générés pour {photo.get('filename', 'N/A')} [{photo_path or 'chemin inconnu'}]: {tags}")
            else:
                logger.info(f"Tags générés pour {photo.get('filename', 'N/A')} [{photo.get('full_path', 'N/A')}]: {tags}")
            
            # Variable pour suivre si au moins un tag a été écrit
            tags_written = False
            
            # Écrire les tags
            try:
                if mode == "catalog":
                    # Écrire dans le catalogue
                    if self.write_to_catalog.get():
                        success = self.lightroom_manager.add_tags(photo_id, tags)
                        if success:
                            photo_path = self.lightroom_manager.get_photo_path(photo_id)
                            logger.info(f"Tags écrits dans le catalogue pour photo {photo_id} [{photo_path or 'chemin inconnu'}]: {', '.join(tags)}")
                            self.stats_tags_written_catalog += 1
                            tags_written = True
                        else:
                            photo_path = self.lightroom_manager.get_photo_path(photo_id)
                            logger.error(f"Échec écriture catalogue pour photo {photo_id} [{photo_path or 'chemin inconnu'}]")
                    
                    # Écrire dans XMP uniquement si la photo originale existe
                    if self.write_to_xmp.get():
                        photo_path = self.lightroom_manager.get_photo_path(photo_id)
                        
                        if photo_path and os.path.exists(photo_path):
                            # Photo originale accessible
                            success = self.xmp_manager.write_tags(photo_path, tags)
                            if success:
                                logger.info(f"Tags écrits dans XMP: {photo_path}")
                                self.stats_tags_written_xmp += 1
                                tags_written = True
                            else:
                                logger.error(f"Échec écriture XMP pour: {photo_path}")
                        elif photo_path:
                            # Photo dans le catalogue mais fichier absent
                            self.stats_xmp_skipped_no_file += 1
                            logger.warning(
                                f"Photo originale introuvable, XMP non créé: {photo_path}\n"
                                f"  → La photo est dans le catalogue mais le fichier n'est pas accessible.\n"
                                f"  → Vérifiez que le disque/dossier contenant les photos est monté."
                            )
                        else:
                            # Impossible de déterminer le chemin
                            self.stats_xmp_skipped_no_file += 1
                            logger.error(
                                f"Impossible de déterminer le chemin pour photo {photo_id}\n"
                                f"  → XMP non créé car chemin de la photo introuvable dans le catalogue."
                            )
                
                else:  # folder
                    # Écrire uniquement dans XMP
                    if self.write_to_xmp.get():
                        success = self.xmp_manager.write_tags(photo['full_path'], tags)
                        if success:
                            logger.info(f"Tags écrits dans XMP: {photo['full_path']}")
                            self.stats_tags_written_xmp += 1
                            tags_written = True
                        else:
                            logger.error(f"Échec écriture XMP pour: {photo['full_path']}")
            
            except Exception as e:
                logger.error(f"Erreur écriture tags: {e}", exc_info=True)
            
            # Incrémenter le compteur de photos taguées si au moins un tag a été écrit
            if tags_written:
                self.photos_tagged += 1
        
        except Exception as e:
            logger.error(f"Erreur traitement photo {photo}: {e}", exc_info=True)
    
    def _generate_tags_for_image(self, image: Image.Image) -> List[str]:
        """
        Génère les tags pour une image selon le mode sélectionné.
        Ajoute automatiquement le suffixe configuré (ex: "_ai").
        
        Args:
            image: Image PIL
            
        Returns:
            Liste de tags (avec suffixe si activé)
        """
        from tag_suffix import apply_suffix_to_tags
        
        model = self.selected_model.get()
        mode = self.tagging_mode.get()
        
        if mode == "auto":
            # Mode automatique
            tags = self.ollama_client.generate_tags_auto(image, model)
        
        else:  # targeted
            # Mode ciblé
            tags = []
            for criteria, target_tag in self.mappings:
                detected, tag = self.ollama_client.generate_tags_targeted(
                    image, model, criteria, target_tag
                )
                if detected and tag:
                    tags.append(tag)
        
        # Ajouter le suffixe aux tags générés automatiquement
        if self.tag_suffix_enabled.get():
            suffix = self.tag_suffix_var.get()
            if suffix:  # Seulement si le suffixe n'est pas vide
                tags_with_suffix = apply_suffix_to_tags(tags, suffix=suffix, enabled=True)
                logger.info(f"Suffixe '{suffix}' ajouté: {tags} → {tags_with_suffix}")
            else:
                tags_with_suffix = tags
                logger.info(f"Suffixe vide, tags originaux conservés: {tags}")
        else:
            tags_with_suffix = tags
            logger.info(f"Suffixe désactivé, tags originaux conservés: {tags}")
        
        return tags_with_suffix
    
    # ===== Méthodes UI =====
    
    def _update_progress(self):
        """Met à jour la barre de progression et les indicateurs."""
        if self.total_photos > 0:
            progress = (self.current_photo / self.total_photos) * 100
            self.progress_bar['value'] = progress
            
            # Mettre à jour les indicateurs
            self.progress_pct_label.config(text=f"{progress:.3f}%")
            self.tagged_label.config(text=str(self.photos_tagged))
            self.total_label.config(text=str(self.total_photos))
            
            self.root.update_idletasks()
    
    def _reset_ui(self):
        """Réinitialise l'interface après traitement."""
        self.is_processing = False
        self.should_stop = False
        self.should_pause = False
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        # Activer Resume seulement s'il y a un état sauvegardé
        if os.path.exists(self.state_file):
            self.resume_btn.config(state=tk.NORMAL)
        else:
            self.resume_btn.config(state=tk.DISABLED)
    
    def _show_error(self, message: str):
        """Affiche un message d'erreur (thread-safe)."""
        self.root.after(0, lambda: messagebox.showerror("Erreur", message))
    
    def _show_info(self, message: str):
        """Affiche un message d'information (thread-safe)."""
        self.root.after(0, lambda: messagebox.showinfo("Information", message))


class MappingDialog(tk.Toplevel):
    """Dialogue pour ajouter/modifier un mapping."""
    
    def __init__(self, parent, title: str, criteria: str = "", tag: str = ""):
        """
        Initialise le dialogue.
        
        Args:
            parent: Fenêtre parente
            title: Titre du dialogue
            criteria: Critère initial (pour modification)
            tag: Tag initial (pour modification)
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("500x150")
        self.resizable(False, False)
        
        self.result = None
        
        # Critère
        ttk.Label(self, text="Critère de recherche:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.criteria_entry = ttk.Entry(self, width=50)
        self.criteria_entry.grid(row=0, column=1, padx=10, pady=10)
        self.criteria_entry.insert(0, criteria)
        
        # Tag
        ttk.Label(self, text="Tag à appliquer:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.tag_entry = ttk.Entry(self, width=50)
        self.tag_entry.grid(row=1, column=1, padx=10, pady=10)
        self.tag_entry.insert(0, tag)
        
        # Boutons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Focus
        self.criteria_entry.focus()
        
        # Modal
        self.transient(parent)
        self.grab_set()
        self.wait_window()
    
    def _on_ok(self):
        """Valide et ferme le dialogue."""
        criteria = self.criteria_entry.get().strip()
        tag = self.tag_entry.get().strip()
        
        if not criteria or not tag:
            messagebox.showwarning("Validation", "Veuillez remplir les deux champs")
            return
        
        self.result = (criteria, tag)
        self.destroy()


def main():
    """Point d'entrée de l'application."""
    root = tk.Tk()
    app = PhotoTaggerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
