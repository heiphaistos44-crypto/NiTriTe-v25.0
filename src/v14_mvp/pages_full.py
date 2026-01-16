#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pages Complètes CORRIGÉES - NiTriTe V17
Updates, Backup, Diagnostic, Optimizations avec vraies commandes
"""

import customtkinter as ctk
import tkinter as tk
import subprocess
import platform
import os
import sys
import json
import shutil
import threading
import ctypes
from datetime import datetime
from pathlib import Path
from v14_mvp.design_system import DesignTokens
from v14_mvp.components import ModernCard, ModernButton, ModernStatsCard, ModernSearchBar, SectionHeader
from v14_mvp.progress_dialog import ProgressDialog

# ACTIVER LES ICÔNES COLORÉES AUTOMATIQUEMENT
# Note: auto_color_icons supprimé, remplacé par icons_system.py
try:
    from v14_mvp.icons_system import ColoredIconsManager
    print("Icones colorees activees pour pages_full.py (nouveau système)")
except Exception as e:
    print(f"Impossible d'activer les icones colorees: {e}")

# Import du système de chemins portables
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from portable_paths import get_portable_temp_dir
except ImportError:
    def get_portable_temp_dir(subfolder=None):
        import tempfile
        if subfolder:
            return Path(tempfile.gettempdir()) / "nitrite_temp" / subfolder
        return Path(tempfile.gettempdir()) / "nitrite_temp"

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print(" psutil non disponible - installation: pip install psutil")


def get_local_software_folder():
    """Obtenir le dossier 'logiciel' à côté de l'exécutable ou à la racine du projet"""
    if getattr(sys, 'frozen', False):
        # Version compilée (PyInstaller) - chercher à côté de l'exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Mode développement - chercher depuis le script actuel
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. D'abord, chercher à côté de l'exécutable (pour version portable distribuée)
    logiciel_dir = os.path.join(base_dir, "logiciel")
    if os.path.exists(logiciel_dir):
        return logiciel_dir

    # 2. Si pas trouvé, chercher en remontant dans l'arborescence (pour développement)
    current_dir = base_dir
    for _ in range(3):  # Remonter jusqu'à 3 niveaux maximum
        logiciel_dir = os.path.join(current_dir, "logiciel")
        if os.path.exists(logiciel_dir):
            return logiciel_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Racine atteinte
            break
        current_dir = parent_dir

    # 3. Si toujours pas trouvé, chercher la racine du projet (présence de src/)
    project_root = base_dir
    while True:
        parent = os.path.dirname(project_root)
        if parent == project_root:  # Racine du système atteinte
            break
        # Vérifier si on est à la racine du projet (présence de src/)
        if os.path.exists(os.path.join(project_root, "src")):
            logiciel_dir = os.path.join(project_root, "logiciel")
            if os.path.exists(logiciel_dir):
                return logiciel_dir
            break
        project_root = parent

    # 4. Fallback: créer à côté de l'exécutable
    logiciel_dir = os.path.join(base_dir, "logiciel")
    os.makedirs(logiciel_dir, exist_ok=True)
    return logiciel_dir


def create_portable_temp_file(suffix='.bat', content=''):
    """
    Créer un fichier temporaire dans le dossier temp portable

    Args:
        suffix: Extension du fichier (.bat, .ps1, etc.)
        content: Contenu à écrire dans le fichier

    Returns:
        str: Chemin absolu du fichier temporaire créé
    """
    import tempfile
    temp_dir = get_portable_temp_dir('scripts')
    temp_file_path = temp_dir / f'script_{os.getpid()}_{int(datetime.now().timestamp())}{suffix}'

    # Déterminer l'encodage selon l'extension
    encoding = 'cp1252' if suffix == '.bat' else 'utf-8'

    with open(temp_file_path, 'w', encoding=encoding) as f:
        f.write(content)

    return str(temp_file_path)


def is_admin():
    """Vérifier si l'application a les droits administrateur"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin(command, wait=False):
    """Exécuter une commande en mode administrateur sans prompt UAC"""
    try:
        if is_admin():
            # Déjà admin, exécuter directement
            if wait:
                subprocess.run(command, shell=True, check=True)
            else:
                subprocess.Popen(command, shell=True)
        else:
            # Pas admin, utiliser PowerShell avec Start-Process -Verb RunAs
            ps_command = f'Start-Process powershell -ArgumentList "-NoExit","-Command","{command}" -Verb RunAs'
            subprocess.Popen(['powershell', '-Command', ps_command], shell=False)
    except Exception as e:
        print(f"Erreur run_as_admin: {e}")
        # Fallback: essayer quand même
        subprocess.Popen(command, shell=True)


class UpdatesPage(ctk.CTkFrame):
    """Page Mises à jour avec vraies commandes WinGet"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        # Créer UN SEUL scrollable frame pour TOUTE la page
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
        self.main_scroll.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._create_header()
        self._create_terminal()
        self._create_content()

    def _create_header(self):
        """Header"""
        header = ModernCard(self.main_scroll)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)
        
        title_frame = SectionHeader(container, text="🔄 Mises à Jour")
        title_frame.pack(side=tk.LEFT)

        # Actions
        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(side=tk.RIGHT)
        
        ModernButton(
            actions,
            text="🔎 Rechercher",
            variant="filled",
            command=self._check_updates
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            actions,
            text="⚡ Tout Mettre à Jour",
            variant="outlined",
            command=self._update_all
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_terminal(self):
        """Terminal intégré avec redimensionnement"""
        self.terminal_card = ModernCard(self.main_scroll)
        self.terminal_card.pack(fill=tk.X, padx=20, pady=10)

        # Header avec icône de redimensionnement
        header_frame = ctk.CTkFrame(self.terminal_card, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        term_title = SectionHeader(header_frame, text="⚡ Terminal")
        term_title.pack(side=tk.LEFT)

        # Boutons de taille
        size_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        size_frame.pack(side=tk.RIGHT)

        # Contrôles de police
        ctk.CTkButton(
            size_frame,
            text="A-",
            width=30,
            height=20,
            font=(DesignTokens.FONT_FAMILY, 10, "bold"),
            command=lambda: self._change_font_size(-1),
            fg_color=DesignTokens.BG_ELEVATED,
            hover_color=DesignTokens.BG_HOVER
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            size_frame,
            text="A+",
            width=30,
            height=20,
            font=(DesignTokens.FONT_FAMILY, 10, "bold"),
            command=lambda: self._change_font_size(1),
            fg_color=DesignTokens.BG_ELEVATED,
            hover_color=DesignTokens.BG_HOVER
        ).pack(side=tk.LEFT, padx=2)

        # Séparateur
        ctk.CTkLabel(size_frame, text="|", text_color=DesignTokens.TEXT_TERTIARY).pack(side=tk.LEFT, padx=5)

        # Contrôles de hauteur
        ctk.CTkButton(
            size_frame,
            text="▼",
            width=30,
            height=20,
            font=(DesignTokens.FONT_FAMILY, 12),
            command=lambda: self._resize_terminal(-100),
            fg_color=DesignTokens.BG_ELEVATED,
            hover_color=DesignTokens.BG_HOVER
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            size_frame,
            text="▲",
            width=30,
            height=20,
            font=(DesignTokens.FONT_FAMILY, 12),
            command=lambda: self._resize_terminal(100),
            fg_color=DesignTokens.BG_ELEVATED,
            hover_color=DesignTokens.BG_HOVER
        ).pack(side=tk.LEFT, padx=2)

        # Zone de sortie - Style Matrix (noir + vert)
        self.terminal_height = 300  # Hauteur par défaut augmentée
        self.terminal_font_size = 11  # Taille police par défaut
        self.terminal_output = ctk.CTkTextbox(
            self.terminal_card,
            height=self.terminal_height,
            font=("Consolas", self.terminal_font_size),
            fg_color="#000000",  # Fond noir
            text_color="#00FF00",  # Texte vert style Matrix
            wrap="word",
            border_width=2,
            border_color="#00FF00"
        )
        self.terminal_output.pack(fill=tk.X, padx=20, pady=(0, 15))
        self.terminal_output.insert("1.0", "█ Terminal prêt. Cliquez sur un bouton pour exécuter une commande.\n")
        self.terminal_output.configure(state="disabled")

    def _resize_terminal(self, delta):
        """Redimensionner le terminal"""
        self.terminal_height = max(100, min(800, self.terminal_height + delta))
        self.terminal_output.configure(height=self.terminal_height)

    def _change_font_size(self, delta):
        """Changer la taille de la police du terminal"""
        self.terminal_font_size = max(8, min(16, self.terminal_font_size + delta))
        self.terminal_output.configure(font=("Consolas", self.terminal_font_size))

    def _log_to_terminal(self, message):
        """Ajouter message au terminal"""
        self.terminal_output.configure(state="normal")
        self.terminal_output.insert("end", f"{message}\n")
        self.terminal_output.see("end")
        self.terminal_output.configure(state="disabled")
    
    def _create_content(self):
        """Contenu (déjà dans main_scroll)"""
        # Stats
        stats_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_installed = ModernStatsCard(
            stats_frame,
            "Installées",
            "...",
            "",
            DesignTokens.INFO
        )
        self.stats_installed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stats_uptodate = ModernStatsCard(
            stats_frame,
            "À jour",
            "...",
            "",
            DesignTokens.SUCCESS
        )
        self.stats_uptodate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stats_updates = ModernStatsCard(
            stats_frame,
            "Mises à jour",
            "...",
            "",
            DesignTokens.WARNING
        )
        self.stats_updates.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Liste mises à jour avec redimensionnement
        self.updates_card = ModernCard(self.main_scroll)
        self.updates_card.pack(fill=tk.X, padx=20, pady=10)

        # Header avec boutons de redimensionnement
        header_frame = ctk.CTkFrame(self.updates_card, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=20, pady=15)

        header = SectionHeader(header_frame, text="📋 Mises à jour disponibles")
        header.pack(side=tk.LEFT)

        # Boutons de taille
        size_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        size_frame.pack(side=tk.RIGHT)

        ctk.CTkButton(
            size_frame,
            text="▼",
            width=30,
            height=20,
            font=(DesignTokens.FONT_FAMILY, 12),
            command=lambda: self._resize_updates(-100),
            fg_color=DesignTokens.BG_ELEVATED,
            hover_color=DesignTokens.BG_HOVER
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            size_frame,
            text="▲",
            width=30,
            height=20,
            font=(DesignTokens.FONT_FAMILY, 12),
            command=lambda: self._resize_updates(100),
            fg_color=DesignTokens.BG_ELEVATED,
            hover_color=DesignTokens.BG_HOVER
        ).pack(side=tk.LEFT, padx=2)

        # Frame scrollable avec hauteur fixe
        self.updates_height = 500  # Hauteur par défaut augmentée
        self.updates_scroll = ctk.CTkScrollableFrame(
            self.updates_card,
            fg_color="transparent",
            height=self.updates_height
        )
        self.updates_scroll.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Note: La barre de progression sera créée dynamiquement dans _update_all()

        # Message initial
        initial_msg = ctk.CTkLabel(
            self.updates_scroll,
            text="Cliquez sur ' Rechercher' pour scanner les mises à jour disponibles",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        initial_msg.pack(pady=20)

        # Section Gestionnaires de paquets
        self._create_package_managers_section()

        # Section Outils constructeurs
        self._create_manufacturer_tools_section()

        # Section Snappy Driver Installer
        self._create_snappy_section()

        # Isoler le scroll de updates_scroll
        self._bind_scroll_isolation()

    def _resize_updates(self, delta):
        """Redimensionner la section mises à jour"""
        self.updates_height = max(200, min(1000, self.updates_height + delta))
        self.updates_scroll.configure(height=self.updates_height)

    def _bind_scroll_isolation(self):
        """Empêcher la propagation du scroll vers le parent quand on scroll dans updates_scroll"""
        def on_mousewheel(event):
            # Obtenir le widget sous le curseur
            try:
                x, y = event.x_root, event.y_root
                # Vérifier si le curseur est au-dessus de updates_scroll
                scroll_x = self.updates_scroll.winfo_rootx()
                scroll_y = self.updates_scroll.winfo_rooty()
                scroll_w = self.updates_scroll.winfo_width()
                scroll_h = self.updates_scroll.winfo_height()

                if scroll_x <= x <= scroll_x + scroll_w and scroll_y <= y <= scroll_y + scroll_h:
                    # On est dans updates_scroll, bloquer la propagation au parent
                    return "break"
            except:
                pass
            return None

        # Lier l'événement de molette
        self.updates_scroll.bind("<MouseWheel>", on_mousewheel)
        self.updates_scroll.bind("<Button-4>", on_mousewheel)  # Linux scroll up
        self.updates_scroll.bind("<Button-5>", on_mousewheel)  # Linux scroll down

        # Lier aussi aux widgets enfants
        for child in self.updates_scroll.winfo_children():
            child.bind("<MouseWheel>", on_mousewheel)

    def _create_package_managers_section(self):
        """Section gestionnaires de paquets"""
        card = ModernCard(self.main_scroll)
        card.pack(fill=tk.X, padx=20, pady=10)

        title = SectionHeader(card, text="📦 Gestionnaires de Paquets")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Grid layout pour les gestionnaires de paquets
        pm_grid = ctk.CTkFrame(content, fg_color="transparent")
        pm_grid.pack(fill=tk.X)

        # Row 1: WinGet et Chocolatey
        row1 = ctk.CTkFrame(pm_grid, fg_color="transparent")
        row1.pack(fill=tk.X, pady=5)

        ModernButton(
            row1,
            text="🔄 WinGet (Scan + Update)",
            variant="outlined",
            command=self._update_winget
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ModernButton(
            row1,
            text="🍫 Chocolatey (Auto-install + Update)",
            variant="outlined",
            command=self._update_chocolatey
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Row 2: Scoop et pip
        row2 = ctk.CTkFrame(pm_grid, fg_color="transparent")
        row2.pack(fill=tk.X, pady=5)

        ModernButton(
            row2,
            text="🪣 Scoop (Auto-install + Update)",
            variant="outlined",
            command=self._update_scoop
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ModernButton(
            row2,
            text="🐍 pip (Python packages)",
            variant="outlined",
            command=self._update_pip
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Row 3: npm
        row3 = ctk.CTkFrame(pm_grid, fg_color="transparent")
        row3.pack(fill=tk.X, pady=5)

        ModernButton(
            row3,
            text="📦 npm (Node.js packages)",
            variant="outlined",
            command=self._update_npm
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _create_manufacturer_tools_section(self):
        """Section outils constructeurs"""
        card = ModernCard(self.main_scroll)
        card.pack(fill=tk.X, padx=20, pady=10)

        title = SectionHeader(card, text="🏭 Outils de Mise à Jour Constructeurs")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Grille de boutons
        button_grid = ctk.CTkFrame(content, fg_color="transparent")
        button_grid.pack(fill=tk.X)

        manufacturers = [
            ("💻 Dell SupportAssist", "https://www.dell.com/support/home/"),
            ("🖨️ HP Support Assistant", "https://support.hp.com/drivers"),
            ("💼 Lenovo Vantage", "https://support.lenovo.com/solutions/ht505081"),
            ("⚡ Intel Driver Assistant", "https://www.intel.com/content/www/us/en/support/detect.html"),
            ("🎮 NVIDIA GeForce Experience", "https://www.nvidia.com/geforce/geforce-experience/"),
            ("🔴 AMD Software Adrenalin", "https://www.amd.com/support"),
            ("⚙️ ASUS MyASUS", "https://www.asus.com/support/download-center/"),
            ("🐉 MSI Center", "https://www.msi.com/Landing/msi-center"),
            ("🌟 Acer Care Center", "https://www.acer.com/ac/en/US/content/software-download"),
        ]

        row = 0
        col = 0
        for text, url in manufacturers:
            btn = ModernButton(
                button_grid,
                text=text,
                variant="outlined",
                command=lambda u=url: self._open_url(u)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1
            if col > 2:  # 3 colonnes
                col = 0
                row += 1

        # Configure colonnes pour expansion égale
        for i in range(3):
            button_grid.grid_columnconfigure(i, weight=1, uniform="manufacturer")

    def _create_snappy_section(self):
        """Section Snappy Driver Installer"""
        card = ModernCard(self.main_scroll)
        card.pack(fill=tk.X, padx=20, pady=10)

        title = SectionHeader(card, text="💿 Snappy Driver Installer")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Description
        desc = ctk.CTkLabel(
            content,
            text="Téléchargez Snappy Driver Installer pour mettre à jour automatiquement tous vos drivers.\n"
                 "Version Full (~40 GB) : Tous les drivers | Version Lite (~2 GB) : Télécharge à la demande",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w",
            wraplength=800,
            justify="left"
        )
        desc.pack(fill=tk.X, pady=(0, 10))

        # Boutons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill=tk.X)

        ModernButton(
            btn_frame,
            text="⬇️ Télécharger Snappy Full (~40 GB)",
            variant="filled",
            command=self._download_snappy_full
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ModernButton(
            btn_frame,
            text="⬇️ Télécharger Snappy Lite (~2 GB)",
            variant="outlined",
            command=self._download_snappy_lite
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _update_chocolatey(self):
        """Mettre à jour via Chocolatey (auto-install si nécessaire)"""
        self._log_to_terminal(" Vérification de Chocolatey...")

        def run_choco_update():
            try:
                # Vérifier si Chocolatey est installé
                check_result = subprocess.run(
                    ["choco", "--version"],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    shell=True
                )

                if check_result.returncode != 0:
                    # Chocolatey n'est pas installé, l'installer
                    self._log_to_terminal(" Chocolatey n'est pas installé")
                    self._log_to_terminal(" Installation automatique de Chocolatey...")

                    from tkinter import messagebox
                    response = messagebox.askyesno(
                        "Installer Chocolatey?",
                        "Chocolatey n'est pas installé.\n\n"
                        "Voulez-vous l'installer automatiquement?\n"
                        "(Une fenêtre PowerShell admin va s'ouvrir)"
                    )

                    if not response:
                        self._log_to_terminal(" Installation annulée par l'utilisateur")
                        return

                    # Script d'installation Chocolatey
                    install_cmd = (
                        'Set-ExecutionPolicy Bypass -Scope Process -Force; '
                        '[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                        'iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\')); '
                        'Write-Host ""; '
                        'Write-Host "Installation terminee! Appuyez sur Entree pour fermer..." -ForegroundColor Green; '
                        'Read-Host'
                    )

                    subprocess.Popen(
                        f'powershell -NoExit -Command "Start-Process powershell -Verb RunAs -ArgumentList \'-NoExit\',\'-Command\',\'{install_cmd}\'"',
                        shell=True
                    )

                    self._log_to_terminal(" Installation lancée! Patientez...")
                    self._log_to_terminal(" Après installation, re-cliquez sur le bouton pour mettre à jour")
                    return

                self._log_to_terminal(" Chocolatey détecté")
                self._log_to_terminal(" Mise à jour de tous les packages...")

                # Lancer mise à jour dans PowerShell visible
                subprocess.Popen(
                    'powershell -NoExit -Command "Write-Host \'Mise a jour via Chocolatey...\' -ForegroundColor Cyan; '
                    'choco upgrade all -y; '
                    'Write-Host \'\'; '
                    'Write-Host \'Termine! Appuyez sur Entree pour fermer...\' -ForegroundColor Green; '
                    'Read-Host"',
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    shell=True
                )

                self._log_to_terminal(" Mise à jour Chocolatey lancée dans PowerShell")

            except FileNotFoundError as e:
                self._log_to_terminal(f" Erreur: {str(e)}")
            except Exception as e:
                self._log_to_terminal(f" Erreur: {str(e)}")

        threading.Thread(target=run_choco_update, daemon=True).start()

    def _open_url(self, url):
        """Ouvrir une URL dans le navigateur"""
        import webbrowser
        try:
            webbrowser.open(url)
            self._log_to_terminal(f" Ouverture de {url}")
        except Exception as e:
            self._log_to_terminal(f" Erreur: {e}")

    def _update_winget(self):
        """Scanner et mettre à jour via WinGet dans PowerShell visible"""
        self._log_to_terminal(" Scan des mises à jour WinGet...")

        def run_winget_update():
            try:
                # Lancer dans PowerShell visible pour voir toutes les mises à jour
                subprocess.Popen(
                    'powershell -NoExit -Command "Write-Host \'Scan des mises a jour disponibles...\' -ForegroundColor Cyan; '
                    'Write-Host \'\'; '
                    'winget upgrade --accept-source-agreements --accept-package-agreements; '
                    'Write-Host \'\'; '
                    'Write-Host \'Voulez-vous tout mettre a jour? (y/n)\' -ForegroundColor Yellow; '
                    '$response = Read-Host; '
                    'if ($response -eq \'y\' -or $response -eq \'Y\') { '
                    '    Write-Host \'Mise a jour en cours...\' -ForegroundColor Cyan; '
                    '    winget upgrade --all --accept-source-agreements --accept-package-agreements; '
                    '    Write-Host \'\'; '
                    '    Write-Host \'Termine!\' -ForegroundColor Green '
                    '} else { '
                    '    Write-Host \'Annule.\' -ForegroundColor Yellow '
                    '}; '
                    'Write-Host \'\'; '
                    'Write-Host \'Appuyez sur Entree pour fermer...\' -ForegroundColor Gray; '
                    'Read-Host"',
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    shell=True
                )
                self._log_to_terminal(" Scan WinGet lancé dans PowerShell")
                self._log_to_terminal(" Vous pouvez voir toutes les mises à jour dans la fenêtre PowerShell")
            except Exception as e:
                self._log_to_terminal(f" Erreur: {str(e)}")

        threading.Thread(target=run_winget_update, daemon=True).start()

    def _update_scoop(self):
        """Mettre à jour via Scoop (auto-install si nécessaire)"""
        self._log_to_terminal("🪣 Vérification de Scoop...")

        def run_scoop_update():
            try:
                # Vérifier si Scoop est installé
                check_result = subprocess.run(
                    "scoop --version",
                    capture_output=True,
                    text=True, encoding='utf-8', errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    shell=True
                )

                if check_result.returncode != 0:
                    # Scoop n'est pas installé
                    self._log_to_terminal(" Scoop n'est pas installé")
                    self._log_to_terminal(" Installation automatique de Scoop...")

                    from tkinter import messagebox
                    response = messagebox.askyesno(
                        "Installer Scoop?",
                        "Scoop n'est pas installé.\n\n"
                        "Voulez-vous l'installer automatiquement?\n"
                        "(Une fenêtre PowerShell va s'ouvrir)"
                    )

                    if not response:
                        self._log_to_terminal(" Installation annulée")
                        return

                    # Installation Scoop
                    subprocess.Popen(
                        'powershell -NoExit -Command "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force; '
                        'irm get.scoop.sh | iex; '
                        'Write-Host \'\'; '
                        'Write-Host \'Installation terminee!\' -ForegroundColor Green; '
                        'Write-Host \'Appuyez sur Entree pour fermer...\' -ForegroundColor Gray; '
                        'Read-Host"',
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        shell=True
                    )

                    self._log_to_terminal(" Installation Scoop lancée")
                    self._log_to_terminal(" Après installation, re-cliquez pour mettre à jour")
                    return

                self._log_to_terminal(" Scoop détecté")
                self._log_to_terminal(" Mise à jour Scoop + packages...")

                # Mise à jour Scoop et packages
                subprocess.Popen(
                    'powershell -NoExit -Command "Write-Host \'Mise a jour Scoop...\' -ForegroundColor Cyan; '
                    'scoop update; '
                    'Write-Host \'\'; '
                    'Write-Host \'Mise a jour des packages...\' -ForegroundColor Cyan; '
                    'scoop update *; '
                    'Write-Host \'\'; '
                    'Write-Host \'Termine!\' -ForegroundColor Green; '
                    'Write-Host \'Appuyez sur Entree pour fermer...\' -ForegroundColor Gray; '
                    'Read-Host"',
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    shell=True
                )

                self._log_to_terminal(" Mise à jour Scoop lancée")

            except FileNotFoundError as e:
                self._log_to_terminal(f" Erreur: {str(e)}")
            except Exception as e:
                self._log_to_terminal(f" Erreur: {str(e)}")

        threading.Thread(target=run_scoop_update, daemon=True).start()

    def _update_pip(self):
        """Mettre à jour les packages Python via pip"""
        self._log_to_terminal(" Vérification de pip...")

        def run_pip_update():
            try:
                # Vérifier si Python/pip est installé
                check_result = subprocess.run(
                    ["python", "-m", "pip", "--version"],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if check_result.returncode != 0:
                    self._log_to_terminal(" Python/pip n'est pas installé")
                    self._log_to_terminal(" Installez Python depuis https://www.python.org/")
                    return

                self._log_to_terminal(" pip détecté")
                self._log_to_terminal(" Mise à jour des packages Python...")

                # Liste packages obsolètes et mise à jour
                subprocess.Popen(
                    ['powershell', '-NoExit', '-Command',
                     'Write-Host "Packages Python obsoletes..." -ForegroundColor Cyan; '
                     'python -m pip list --outdated; '
                     'Write-Host ""; '
                     'Write-Host "Mise a jour de pip..." -ForegroundColor Cyan; '
                     'python -m pip install --upgrade pip; '
                     'Write-Host ""; '
                     'Write-Host "Termine!" -ForegroundColor Green; '
                     'Write-Host "Pour mettre a jour un package: pip install --upgrade <package>" -ForegroundColor Yellow; '
                     'Write-Host "Appuyez sur Entree pour fermer..." -ForegroundColor Gray; '
                     'Read-Host'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                self._log_to_terminal(" Scan pip lancé")

            except FileNotFoundError:
                self._log_to_terminal(" Python n'est pas installé ou pas dans PATH")
            except Exception as e:
                self._log_to_terminal(f" Erreur: {str(e)}")

        threading.Thread(target=run_pip_update, daemon=True).start()

    def _update_npm(self):
        """Mettre à jour les packages Node.js via npm"""
        self._log_to_terminal(" Vérification de npm...")

        def run_npm_update():
            try:
                # Vérifier si Node.js/npm est installé
                check_result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if check_result.returncode != 0:
                    self._log_to_terminal(" Node.js/npm n'est pas installé")
                    self._log_to_terminal(" Installez Node.js depuis https://nodejs.org/")
                    return

                self._log_to_terminal(" npm détecté")
                self._log_to_terminal(" Mise à jour packages Node.js...")

                # Liste et mise à jour packages globaux
                subprocess.Popen(
                    ['powershell', '-NoExit', '-Command',
                     'Write-Host "Packages npm globaux obsoletes..." -ForegroundColor Cyan; '
                     'npm outdated -g; '
                     'Write-Host ""; '
                     'Write-Host "Mise a jour de npm..." -ForegroundColor Cyan; '
                     'npm install -g npm; '
                     'Write-Host ""; '
                     'Write-Host "Mise a jour des packages globaux..." -ForegroundColor Cyan; '
                     'npm update -g; '
                     'Write-Host ""; '
                     'Write-Host "Termine!" -ForegroundColor Green; '
                     'Write-Host "Appuyez sur Entree pour fermer..." -ForegroundColor Gray; '
                     'Read-Host'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

                self._log_to_terminal(" Mise à jour npm lancée")

            except FileNotFoundError:
                self._log_to_terminal(" Node.js/npm n'est pas installé ou pas dans PATH")
            except Exception as e:
                self._log_to_terminal(f" Erreur: {str(e)}")

        threading.Thread(target=run_npm_update, daemon=True).start()

    def _download_snappy_full(self):
        """Télécharger Snappy Driver Installer Full"""
        import webbrowser
        from tkinter import messagebox

        self._log_to_terminal(" Ouverture page Snappy Full (~40 GB)...")

        response = messagebox.askyesno(
            "Snappy Driver Installer Full",
            "Vous allez télécharger Snappy Driver Installer Full (~40 GB).\n\n"
            "Cette version contient TOUS les drivers et ne nécessite pas de connexion Internet.\n\n"
            " Le téléchargement est très volumineux!\n\n"
            "Continuer?"
        )

        if response:
            webbrowser.open("https://sdi-tool.org/download/")
            self._log_to_terminal(" Page de téléchargement Snappy Full ouverte")
            messagebox.showinfo(
                "Instructions",
                "Sur la page web:\n\n"
                "1. Cherchez 'Snappy Driver Installer Full'\n"
                "2. Téléchargez le fichier (~40 GB)\n"
                "3. Extrayez et lancez SDI.exe"
            )
        else:
            self._log_to_terminal(" Téléchargement annulé")

    def _download_snappy_lite(self):
        """Télécharger Snappy Driver Installer Lite"""
        import webbrowser
        from tkinter import messagebox

        self._log_to_terminal(" Ouverture page Snappy Lite (~2 GB)...")

        response = messagebox.askyesno(
            "Snappy Driver Installer Lite",
            "Vous allez télécharger Snappy Driver Installer Lite (~2 GB).\n\n"
            "Cette version télécharge les drivers à la demande (nécessite Internet).\n\n"
            "Continuer?"
        )

        if response:
            webbrowser.open("https://sdi-tool.org/download/")
            self._log_to_terminal(" Page de téléchargement Snappy Lite ouverte")
            messagebox.showinfo(
                "Instructions",
                "Sur la page web:\n\n"
                "1. Cherchez 'Snappy Driver Installer Lite'\n"
                "2. Téléchargez le fichier (~2 GB)\n"
                "3. Extrayez et lancez SDI.exe"
            )
        else:
            self._log_to_terminal(" Téléchargement annulé")

    def _check_updates(self):
        """Rechercher mises à jour avec WinGet ET Windows Update - VERSION AMÉLIORÉE"""
        self._log_to_terminal("🔍 Recherche des mises à jour...")

        # Clear liste
        for widget in self.updates_scroll.winfo_children():
            widget.destroy()

        # Message de chargement
        loading_msg = ctk.CTkLabel(
            self.updates_scroll,
            text="⏳ Recherche en cours...\n\nVérification WinGet + Windows Update\n(peut prendre 30-60 secondes)",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        loading_msg.pack(pady=20)

        # Stocker les mises à jour trouvées pour le bouton "Tout mettre à jour"
        self.found_winget_updates = []
        self.found_windows_updates = []

        # Lancer la recherche en arrière-plan pour éviter le freeze
        def search_updates():
            winget_count = 0
            windows_updates_count = 0
            winget_updates = []

            # 1. Recherche WinGet avec --include-unknown pour plus de résultats
            try:
                self._log_to_terminal("📦 Recherche mises à jour WinGet...")

                # Utiliser PowerShell pour un meilleur parsing
                # Accepter automatiquement les conditions pour éviter le blocage
                ps_cmd = '''
$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
winget upgrade --include-unknown --accept-source-agreements --accept-package-agreements 2>$null
'''
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_cmd],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=90,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                output = result.stdout + result.stderr
                lines = output.split('\n')
                self._log_to_terminal(f"📦 {len(lines)} lignes reçues de WinGet")

                # Parser le tableau WinGet de manière robuste
                in_table = False
                separator_found = False

                for line in lines:
                    line_stripped = line.strip()

                    # Ignorer lignes vides
                    if not line_stripped:
                        if in_table and separator_found:
                            # Fin du tableau si ligne vide après données
                            continue
                        continue

                    # Détecter l'en-tête du tableau (plusieurs langues)
                    if any(header in line for header in ['Name', 'Nom', 'Id', 'ID', 'Version', 'Available', 'Disponible']):
                        if 'Name' in line or 'Nom' in line:
                            in_table = True
                            self._log_to_terminal("📦 Tableau WinGet détecté")
                            continue

                    # Détecter le séparateur -----
                    if in_table and line_stripped.startswith('-') and '--' in line_stripped:
                        separator_found = True
                        continue

                    # Ligne de mise à jour si on est dans le tableau après le séparateur
                    if in_table and separator_found and line_stripped:
                        lower_line = line_stripped.lower()

                        # Ignorer les messages d'info et de fin (validation TRÈS stricte)
                        skip_keywords = [
                            'upgrade', 'available', 'disponible', 'package', 'packages',
                            'the following', 'les suivants', 'mise à jour', 'mises a jour',
                            'update', 'no applicable', 'aucune', 'winget', 'have version',
                            'pinned', 'installed', 'installé', 'newer', 'plus récent',
                            'explicitly', 'explicitement', 'found', 'trouvé', 'total',
                            'skipping', 'ignoré', 'no installed', 'aucun installé',
                            'unknown', 'inconnu', 'failed', 'échoué', 'error', 'erreur',
                            'no upgrade', 'aucune mise', 'up to date', 'à jour',
                            'successfully', 'avec succès', 'downloading', 'téléchargement',
                            'starting', 'démarrage', 'applicable', 'source agreement',
                            'agreements', 'terms', 'conditions', 'license', 'licence'
                        ]
                        if any(skip in lower_line for skip in skip_keywords):
                            continue

                        # Ignorer lignes commençant par des mots-clés d'erreur/info
                        if line_stripped.startswith(('Warning', 'Avertissement', 'Error', 'Erreur', '-', 'No ', 'Aucun', ' ', '(', '[', 'The ', 'Le ', 'Les ', 'A ', 'Un ')):
                            continue

                        # Ignorer lignes trop courtes ou sans assez de colonnes
                        parts = line_stripped.split()
                        if len(parts) < 4:
                            continue

                        # Validation STRICTE:
                        # 1. Doit avoir un ID avec un point (ex: Microsoft.PowerShell)
                        # 2. Doit avoir DEUX versions (actuelle et disponible)
                        has_valid_id = False
                        version_count = 0

                        for i, p in enumerate(parts):
                            # ID de package: contient un point, pas de chiffres au début, au moins 6 chars
                            if '.' in p and len(p) > 5 and not p[0].isdigit():
                                if not p.startswith('.') and not p.endswith('.'):
                                    # Vérifier que c'est bien un ID (format Publisher.Package)
                                    id_parts = p.split('.')
                                    if len(id_parts) >= 2 and all(len(part) > 0 for part in id_parts):
                                        has_valid_id = True

                            # Version: commence par un chiffre et contient un point
                            if p and p[0].isdigit() and '.' in p and len(p) >= 3:
                                version_count += 1

                        # Ne compter que si on a un ID valide ET au moins 2 versions
                        # (version actuelle + version disponible)
                        if has_valid_id and version_count >= 2:
                            winget_updates.append({
                                'raw_line': line_stripped,
                                'display': line_stripped[:100]
                            })
                            winget_count += 1

                self._log_to_terminal(f"✅ WinGet: {winget_count} mises à jour trouvées")

                # Afficher quelques exemples dans le terminal
                for i, upd in enumerate(winget_updates[:5]):
                    self._log_to_terminal(f"  📦 {upd['display'][:70]}")
                if winget_count > 5:
                    self._log_to_terminal(f"  ... et {winget_count - 5} autres")

            except FileNotFoundError:
                self._log_to_terminal("❌ WinGet non installé")
            except subprocess.TimeoutExpired:
                self._log_to_terminal("⚠️ WinGet timeout (> 90s)")
            except Exception as e:
                self._log_to_terminal(f"❌ Erreur WinGet: {str(e)[:80]}")

            # 2. Recherche Windows Update via PowerShell (plus fiable)
            windows_updates = []
            try:
                self._log_to_terminal("🪟 Recherche Windows Update...")

                # Utiliser PowerShell pour lister les mises à jour Windows disponibles
                ps_wu_cmd = '''
try {
    $Session = New-Object -ComObject Microsoft.Update.Session
    $Searcher = $Session.CreateUpdateSearcher()
    $Results = $Searcher.Search("IsInstalled=0")
    foreach ($Update in $Results.Updates) {
        Write-Output "WU_UPDATE:$($Update.Title)"
    }
    Write-Output "WU_COUNT:$($Results.Updates.Count)"
} catch {
    Write-Output "WU_ERROR:$($_.Exception.Message)"
}
'''
                wu_result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_wu_cmd],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=120,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                wu_output = wu_result.stdout
                for line in wu_output.split('\n'):
                    line = line.strip()
                    if line.startswith('WU_UPDATE:'):
                        title = line[10:]
                        windows_updates.append({'title': title})
                    elif line.startswith('WU_COUNT:'):
                        try:
                            windows_updates_count = int(line[9:])
                        except:
                            windows_updates_count = len(windows_updates)
                    elif line.startswith('WU_ERROR:'):
                        self._log_to_terminal(f"⚠️ Windows Update: {line[9:][:60]}")

                if windows_updates_count == 0:
                    windows_updates_count = len(windows_updates)

                self._log_to_terminal(f"🪟 Windows Update: {windows_updates_count} mises à jour trouvées")

                # Afficher quelques détails
                for i, upd in enumerate(windows_updates[:5]):
                    self._log_to_terminal(f"  🪟 {upd['title'][:70]}")
                if windows_updates_count > 5:
                    self._log_to_terminal(f"  ... et {windows_updates_count - 5} autres")

            except subprocess.TimeoutExpired:
                self._log_to_terminal("⚠️ Windows Update timeout (> 120s)")
                windows_updates_count = -1
            except Exception as e:
                self._log_to_terminal(f"⚠️ Erreur Windows Update: {str(e)[:80]}")
                windows_updates_count = -1

            # Stocker pour le bouton "Tout mettre à jour"
            self.found_winget_updates = winget_updates
            self.found_windows_updates = windows_updates

            # Mettre à jour l'UI dans le thread principal
            def update_ui():
                # Clear
                for widget in self.updates_scroll.winfo_children():
                    widget.destroy()

                total_updates = winget_count
                if windows_updates_count >= 0:
                    total_updates += windows_updates_count

                # Update stats
                self.stats_updates.update_value(str(total_updates))

                # Afficher résumé
                if winget_count > 0 or windows_updates_count > 0:
                    # Section WinGet
                    if winget_count > 0:
                        winget_header_frame = ctk.CTkFrame(
                            self.updates_scroll,
                            fg_color=DesignTokens.BG_ELEVATED,
                            corner_radius=DesignTokens.RADIUS_MD
                        )
                        winget_header_frame.pack(fill=tk.X, pady=5, padx=10)

                        ctk.CTkLabel(
                            winget_header_frame,
                            text=f" WinGet: {winget_count} mises à jour d'applications",
                            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD, "bold"),
                            text_color=DesignTokens.TEXT_PRIMARY,
                            anchor="w"
                        ).pack(padx=15, pady=10, anchor="w")

                        # Afficher les détails de chaque mise à jour
                        for update_info in winget_updates:
                            update_frame = ctk.CTkFrame(
                                self.updates_scroll,
                                fg_color=DesignTokens.BG_SECONDARY,
                                corner_radius=DesignTokens.RADIUS_SM
                            )
                            update_frame.pack(fill=tk.X, pady=2, padx=20)

                            # Afficher la ligne complète de winget
                            update_text = update_info['raw_line']
                            ctk.CTkLabel(
                                update_frame,
                                text=f"  {update_text}",
                                font=("Consolas", 10),
                                text_color=DesignTokens.TEXT_PRIMARY,
                                anchor="w"
                            ).pack(padx=10, pady=5, anchor="w")

                        # Bouton pour tout mettre à jour
                        action_frame = ctk.CTkFrame(
                            self.updates_scroll,
                            fg_color="transparent"
                        )
                        action_frame.pack(fill=tk.X, pady=5, padx=20)

                        ctk.CTkLabel(
                            action_frame,
                            text="Utilisez 'Tout Mettre à Jour' ou le bouton ' WinGet (Scan + Update)' pour installer",
                            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
                            text_color=DesignTokens.TEXT_SECONDARY,
                            anchor="w"
                        ).pack(padx=0, pady=5, anchor="w")

                    # Section Windows Update
                    if windows_updates_count > 0:
                        wu_frame = ctk.CTkFrame(
                            self.updates_scroll,
                            fg_color=DesignTokens.BG_ELEVATED,
                            corner_radius=DesignTokens.RADIUS_MD
                        )
                        wu_frame.pack(fill=tk.X, pady=5, padx=10)

                        ctk.CTkLabel(
                            wu_frame,
                            text=f"🪟 Windows Update: {windows_updates_count} mises à jour système",
                            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD, "bold"),
                            text_color=DesignTokens.TEXT_PRIMARY,
                            anchor="w"
                        ).pack(padx=15, pady=10, anchor="w")

                        ctk.CTkLabel(
                            wu_frame,
                            text="Ouvrez Windows Update dans les Paramètres pour installer",
                            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
                            text_color=DesignTokens.TEXT_SECONDARY,
                            anchor="w"
                        ).pack(padx=15, pady=(0, 5), anchor="w")

                        # Bouton pour ouvrir Windows Update
                        ModernButton(
                            wu_frame,
                            text="🪟 Ouvrir Windows Update",
                            variant="outlined",
                            size="sm",
                            command=self._open_windows_update
                        ).pack(padx=15, pady=(0, 10), anchor="w")

                    elif windows_updates_count == -1:
                        # Erreur Windows Update
                        wu_frame = ctk.CTkFrame(
                            self.updates_scroll,
                            fg_color=DesignTokens.BG_ELEVATED,
                            corner_radius=DesignTokens.RADIUS_MD
                        )
                        wu_frame.pack(fill=tk.X, pady=5, padx=10)

                        ctk.CTkLabel(
                            wu_frame,
                            text=" Windows Update non disponible",
                            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD, "bold"),
                            text_color=DesignTokens.WARNING,
                            anchor="w"
                        ).pack(padx=15, pady=10, anchor="w")

                        ctk.CTkLabel(
                            wu_frame,
                            text="Installez pywin32: pip install pywin32",
                            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
                            text_color=DesignTokens.TEXT_SECONDARY,
                            anchor="w"
                        ).pack(padx=15, pady=(0, 10), anchor="w")
                else:
                    # Aucune mise à jour
                    msg = ctk.CTkLabel(
                        self.updates_scroll,
                        text=" Aucune mise à jour disponible\n\nVotre système est à jour !",
                        font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                        text_color=DesignTokens.SUCCESS
                    )
                    msg.pack(pady=20)

                self._log_to_terminal(f" Scan terminé: {total_updates} mises à jour au total")

            # Scheduler l'update UI dans le thread principal
            self.after(0, update_ui)

        # Lancer la recherche dans un thread
        threading.Thread(target=search_updates, daemon=True).start()

    def _open_windows_update(self):
        """Ouvrir Windows Update dans les Paramètres"""
        try:
            subprocess.Popen('start ms-settings:windowsupdate', shell=True)
            self._log_to_terminal(" Windows Update ouvert")
        except Exception as e:
            self._log_to_terminal(f" Erreur: {e}")
    
    def _update_all(self):
        """Mettre à jour toutes les apps avec barre de progression intégrée"""
        import re

        self._log_to_terminal("🔄 Lancement de la mise à jour globale...")

        try:
            # Vider la liste des mises à jour
            for widget in self.updates_scroll.winfo_children():
                widget.destroy()

            # Créer la barre de progression dynamiquement
            self.progress_frame = ctk.CTkFrame(self.updates_scroll, fg_color=DesignTokens.BG_TERTIARY, corner_radius=10)
            self.progress_frame.pack(fill=tk.X, padx=10, pady=20)

            self.progress_label = ctk.CTkLabel(
                self.progress_frame,
                text="⏳ Démarrage de winget upgrade --all...",
                font=(DesignTokens.FONT_FAMILY, 14, "bold"),
                text_color=DesignTokens.TEXT_PRIMARY
            )
            self.progress_label.pack(pady=(15, 10))

            self.progress_bar = ctk.CTkProgressBar(
                self.progress_frame,
                height=25,
                fg_color=DesignTokens.BG_SECONDARY,
                progress_color=DesignTokens.ACCENT_PRIMARY
            )
            self.progress_bar.pack(fill=tk.X, padx=20, pady=(0, 15))
            self.progress_bar.set(0)

            # Forcer le rafraîchissement
            self.update_idletasks()
            self._log_to_terminal("📊 Barre de progression créée!")

        except Exception as e:
            self._log_to_terminal(f"❌ ERREUR création barre: {str(e)}")
            return

        # Variable pour suivre l'état
        self._update_in_progress = True

        def run_updates():
            completed = 0
            total_found = 0

            try:
                # Lancer winget upgrade --all
                process = subprocess.Popen(
                    ['powershell', '-NoProfile', '-Command',
                     'winget upgrade --all --accept-source-agreements --accept-package-agreements --include-unknown'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                for line in process.stdout:
                    line = line.strip()
                    if not line:
                        continue

                    # Afficher dans le terminal
                    if len(line) > 5:
                        self.after(0, lambda l=line: self._log_to_terminal(f"  {l[:100]}"))

                    lower_line = line.lower()

                    # Détecter le nombre total
                    if 'upgrades available' in lower_line or 'upgrade available' in lower_line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            total_found = int(match.group(1))
                            self.after(0, lambda t=total_found: self._update_progress_label(f"0/{t} - Installation..."))

                    # Détecter succès
                    if any(s in lower_line for s in ['successfully', 'avec succès']):
                        completed += 1
                        if total_found > 0:
                            progress = min(completed / total_found, 1.0)
                            self.after(0, lambda p=progress, c=completed, t=total_found: self._update_progress(p, c, t))
                        else:
                            self.after(0, lambda c=completed: self._update_progress_label(f"{c} installé(s)..."))

                process.wait()
                self.after(0, lambda c=completed, t=total_found: self._finish_update_all(c, t))

            except Exception as e:
                self.after(0, lambda err=str(e): self._log_to_terminal(f"❌ Erreur: {err}"))
                self.after(0, self._restore_updates_view)

        threading.Thread(target=run_updates, daemon=True).start()

    def _update_progress_label(self, text):
        """Mettre à jour le texte de progression"""
        try:
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"⏳ {text}")
        except:
            pass

    def _update_progress(self, progress, completed, total):
        """Mettre à jour la barre de progression"""
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(progress)
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"⏳ {completed}/{total} - Mise à jour en cours...")
        except:
            pass

    def _finish_update_all(self, completed, total):
        """Finaliser les mises à jour"""
        self._update_in_progress = False
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                self.progress_bar.set(1.0)
            if hasattr(self, 'progress_label') and self.progress_label.winfo_exists():
                self.progress_label.configure(text=f"✅ Terminé: {completed} packages mis à jour")
        except:
            pass

        self._log_to_terminal(f"✅ Mise à jour terminée: {completed} packages")

        # Rafraîchir après 3 secondes
        self.after(3000, self._check_updates)

    def _restore_updates_view(self):
        """Restaurer la vue normale"""
        self._update_in_progress = False
        self._check_updates()


class BackupPage(ctk.CTkFrame):
    """Page Sauvegarde avec vraies fonctions"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        # Utiliser le dossier backups portable (à côté de l'exe)
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from portable_paths import get_portable_backups_dir
            self.backup_dir = get_portable_backups_dir()
        except:
            # Fallback si portable_paths non disponible
            if getattr(sys, 'frozen', False):
                app_dir = Path(sys.executable).parent
            else:
                app_dir = Path(__file__).parent.parent.parent
            self.backup_dir = app_dir / 'backups'
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self._create_header()
        self._create_content()
    
    def _create_header(self):
        """Header"""
        header = ModernCard(self)
        header.pack(fill=tk.X, padx=20, pady=10)

        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)

        title_frame = SectionHeader(container, text="💾 Sauvegarde")
        title_frame.pack(side=tk.LEFT)

        # Bouton pour ouvrir le dossier de sauvegarde
        ModernButton(
            container,
            text="📂 Ouvrir le dossier",
            variant="outlined",
            size="sm",
            command=self._open_backup_folder
        ).pack(side=tk.RIGHT, padx=10)

        location = ctk.CTkLabel(
            container,
            text=f" {self.backup_dir}",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        location.pack(side=tk.RIGHT)
    
    def _create_content(self):
        """Contenu"""
        scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
        scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self._create_backup_section(scroll)
        self._create_restore_section(scroll)
        self._create_backups_list_section(scroll)
    
    def _create_backup_section(self, parent):
        """Section création sauvegarde"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="💾 Créer une Sauvegarde")
        title.pack(fill=tk.X)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Options
        self.backup_options = {}
        options = [
            ("apps", "📱 Liste des applications installées", True),
            ("drivers", "🔧 Liste des drivers système", True),
            ("settings", "⚙️ Paramètres NiTriTe", True),
            ("diagnostic_logs", "📋 Logs de diagnostic PC", True),
            ("network_config", "🌐 Configuration réseau (IP, WiFi, DNS)", True),
            ("startup_programs", "🚀 Programmes au démarrage", True),
            ("browser_bookmarks", "🔖 Favoris navigateurs (Chrome, Brave, Edge, Opera, Firefox, Vivaldi, Avast, Opera GX)", True),
            ("desktop_files", "🖥️ Liste fichiers Bureau", True),
            ("env_variables", "🌍 Variables d'environnement système", True),
            ("bitlocker_keys", "🔐 Clés de récupération BitLocker", True),
            ("windows_license", "🪟 Licence Windows (clé produit)", True),
            ("office_license", "📄 Licence Microsoft Office", True),
            ("registry_keys", "🗝️ Clés de registre importantes", True),
            ("firewall_rules", "🛡️ Règles pare-feu Windows", True),
            ("browser_passwords", "🔑 Mots de passe navigateurs (chiffrés)", True),
            ("installed_fonts", "🔤 Liste des polices installées", True),
            ("scheduled_tasks", "⏰ Tâches planifiées Windows", True),
            ("windows_features", "🎯 Fonctionnalités Windows activées", True),
            ("folder_sizes", "📁 Taille dossiers utilisateur (AppData, Roaming, Local, etc.)", True),
            ("suspicious_processes", "🔍 Analyse processus suspects (virus, malwares)", True),
        ]
        
        for key, text, default in options:
            var = tk.BooleanVar(value=default)
            self.backup_options[key] = var
            check = ctk.CTkCheckBox(
                content,
                text=text,
                variable=var,
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                fg_color=DesignTokens.ACCENT_PRIMARY
            )
            check.pack(anchor="w", pady=5)
        
        # Bouton
        ModernButton(
            content,
            text="💾 Créer Sauvegarde",
            variant="filled",
            command=self._create_backup_with_progress
        ).pack(pady=15)
    
    def _create_restore_section(self, parent):
        """Section restauration"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="♻️ Restaurer une Sauvegarde")
        title.pack(fill=tk.X)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        desc = ctk.CTkLabel(
            content,
            text="Sélectionnez une sauvegarde ci-dessous pour la restaurer",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=10)
    
    def _create_backups_list_section(self, parent):
        """Liste des sauvegardes"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="📂 Sauvegardes Disponibles")
        title.pack(fill=tk.X)
        
        self.backups_container = ctk.CTkFrame(card, fg_color="transparent")
        self.backups_container.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self._refresh_backups_list()
    
    def _refresh_backups_list(self):
        """Rafraîchir liste des sauvegardes"""
        # Clear
        for widget in self.backups_container.winfo_children():
            widget.destroy()
        
        # Lister fichiers backup
        backups = sorted(self.backup_dir.glob("backup_*.json"), reverse=True)
        
        if not backups:
            msg = ctk.CTkLabel(
                self.backups_container,
                text="Aucune sauvegarde disponible",
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                text_color=DesignTokens.TEXT_SECONDARY
            )
            msg.pack(pady=10)
            return
        
        for backup_file in backups[:10]:  # Max 10
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                name = backup_file.stem
                info = f"{data.get('apps_count', 0)} apps"
                size = f"{backup_file.stat().st_size / 1024:.1f} KB"
                
                self._create_backup_row(self.backups_container, name, info, size, backup_file)
            except:
                continue
    
    def _create_backup_row(self, parent, name, info, size, filepath):
        """Ligne de sauvegarde"""
        row = ctk.CTkFrame(
            parent,
            fg_color=DesignTokens.BG_ELEVATED,
            corner_radius=DesignTokens.RADIUS_MD
        )
        row.pack(fill=tk.X, pady=5)
        
        container = ctk.CTkFrame(row, fg_color="transparent")
        container.pack(fill=tk.X, padx=15, pady=12)
        
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        name_label = ctk.CTkLabel(
            left,
            text=name,
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        info_label = ctk.CTkLabel(
            left,
            text=f"{info} • {size}",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_TERTIARY,
            anchor="w"
        )
        info_label.pack(anchor="w")
        
        buttons = ctk.CTkFrame(container, fg_color="transparent")
        buttons.pack(side=tk.RIGHT)
        
        ModernButton(
            buttons,
            text="♻️ Restaurer",
            variant="filled",
            size="sm",
            command=lambda: self._restore_backup(filepath)
        ).pack(side=tk.LEFT, padx=3)
        
        ModernButton(
            buttons,
            text="",
            variant="text",
            size="sm",
            command=lambda: self._delete_backup(filepath)
        ).pack(side=tk.LEFT, padx=3)
    
    def _create_backup_with_progress(self):
        """Wrapper pour _create_backup avec dialogue de progression"""
        # Créer le dialogue de progression
        progress = ProgressDialog(self, title="Création de sauvegarde en cours...")
        progress.add_log("Démarrage de la création de la sauvegarde", "info")
        
        # Sauvegarder la fonction print originale
        original_print = print
        step_count = [0]
        
        # Rediriger print vers le dialogue
        def progress_print(*args, **kwargs):
            message = ' '.join(str(arg) for arg in args)
            progress.add_log(message.replace('💾 ', '').replace('🔐 ', '').replace('🪟 ', '').replace('📄 ', '').replace('🛡️ ', '').replace('🔤 ', '').replace('⏰ ', '').replace('🎯 ', '').replace('🔑 ', '').replace('⚠️ ', ''), "info")
            step_count[0] += 1
            progress.update_progress(min(step_count[0] / 20, 0.95), f"Étape {step_count[0]}/20...")
            original_print(*args, **kwargs)
        
        # Remplacer temporairement print
        import builtins
        builtins.print = progress_print
        
        try:
            # Appeler la méthode originale
            self._create_backup()
            progress.update_progress(1.0, "Sauvegarde terminée!")
            progress.add_log("=== SAUVEGARDE CRÉÉE AVEC SUCCÈS ===", "success")
            progress.mark_completed(success=True)
        except Exception as e:
            progress.add_log(f"Erreur: {str(e)}", "error")
            progress.mark_completed(success=False)
        finally:
            # Restaurer print
            builtins.print = original_print

    def _create_backup(self):
        """Créer sauvegarde"""
        print(" Création de la sauvegarde...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{timestamp}.json"
        
        backup_data = {
            "timestamp": timestamp,
            "date": datetime.now().isoformat(),
            "apps_count": 0,
            "apps": []
        }
        
        # Sauvegarder liste apps installées si demandé
        if self.backup_options["apps"].get():
            try:
                result = subprocess.run(
                    ["winget", "list"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    backup_data["apps"] = [line.strip() for line in lines if line.strip()]
                    backup_data["apps_count"] = len(backup_data["apps"])
            except:
                pass

        # Sauvegarder logs de diagnostic si demandé
        if self.backup_options["diagnostic_logs"].get():
            try:
                logs_dir = Path("data/logs")
                if logs_dir.exists():
                    backup_data["diagnostic_logs"] = {
                        "included": True,
                        "log_files": []
                    }

                    # Copier tous les fichiers logs dans le backup
                    logs_backup_dir = self.backup_dir / f"logs_{timestamp}"
                    logs_backup_dir.mkdir(exist_ok=True)

                    import shutil
                    for log_file in logs_dir.glob("*.log"):
                        try:
                            dest_file = logs_backup_dir / log_file.name
                            shutil.copy2(log_file, dest_file)
                            backup_data["diagnostic_logs"]["log_files"].append(log_file.name)
                        except Exception as e:
                            print(f" Erreur copie {log_file.name}: {e}")

                    backup_data["diagnostic_logs"]["count"] = len(backup_data["diagnostic_logs"]["log_files"])
                    backup_data["diagnostic_logs"]["path"] = str(logs_backup_dir)
                    print(f" {backup_data['diagnostic_logs']['count']} fichiers logs sauvegardés")
                else:
                    backup_data["diagnostic_logs"] = {"included": False, "reason": "Aucun log trouvé"}
            except Exception as e:
                backup_data["diagnostic_logs"] = {"included": False, "error": str(e)}
                print(f" Erreur sauvegarde logs: {e}")

        # Sauvegarder configuration réseau
        if self.backup_options.get("network_config", tk.BooleanVar(value=False)).get():
            try:
                result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                backup_data["network_config"] = result.stdout if result.returncode == 0 else "Erreur"
                print(" Configuration réseau sauvegardée")
            except Exception as e:
                backup_data["network_config"] = {"error": str(e)}

        # Sauvegarder programmes au démarrage
        if self.backup_options.get("startup_programs", tk.BooleanVar(value=False)).get():
            try:
                result = subprocess.run(
                    ['powershell', '-Command', 'Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | ConvertTo-Json'],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore'
                )
                if result.returncode == 0:
                    backup_data["startup_programs"] = result.stdout
                    print(" Programmes au démarrage sauvegardés")
            except Exception as e:
                backup_data["startup_programs"] = {"error": str(e)}

        # Sauvegarder variables d'environnement
        if self.backup_options.get("env_variables", tk.BooleanVar(value=False)).get():
            try:
                import os
                backup_data["env_variables"] = dict(os.environ)
                print(f" {len(backup_data['env_variables'])} variables d'environnement sauvegardées")
            except Exception as e:
                backup_data["env_variables"] = {"error": str(e)}

        # Sauvegarder liste fichiers Bureau
        if self.backup_options.get("desktop_files", tk.BooleanVar(value=False)).get():
            try:
                desktop_path = Path.home() / "Desktop"
                if desktop_path.exists():
                    files = [f.name for f in desktop_path.iterdir()]
                    backup_data["desktop_files"] = files
                    print(f" {len(files)} fichiers Bureau listés")
            except Exception as e:
                backup_data["desktop_files"] = {"error": str(e)}

        # Fonction helper pour décoder DigitalProductId
        def decode_product_key(digital_product_id, key_offset=52):
            """Décode une clé produit depuis DigitalProductId (registre Windows/Office)"""
            try:
                if not digital_product_id or len(digital_product_id) < key_offset + 15:
                    return None

                # Caractères pour l'encodage Base24
                chars = "BCDFGHJKMPQRTVWXY2346789"

                # Extraire les 15 octets de la clé
                key_bytes = list(digital_product_id[key_offset:key_offset + 15])

                # Décoder
                decoded = []
                for i in range(24, -1, -1):
                    current = 0
                    for j in range(14, -1, -1):
                        current = current * 256 ^ key_bytes[j]
                        key_bytes[j] = current // 24
                        current = current % 24
                    decoded.insert(0, chars[current])

                # Formater XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
                key = ''.join(decoded)
                return f"{key[0:5]}-{key[5:10]}-{key[10:15]}-{key[15:20]}-{key[20:25]}"
            except:
                return None

        # Sauvegarder clés BitLocker
        if self.backup_options.get("bitlocker_keys", tk.BooleanVar(value=False)).get():
            try:
                result = subprocess.run(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-Command',
                     'Get-BitLockerVolume | Select-Object MountPoint, ProtectionStatus, KeyProtector | ConvertTo-Json'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if result.returncode == 0 and result.stdout.strip():
                    backup_data["bitlocker_keys"] = result.stdout
                    print("🔐 Clés BitLocker sauvegardées")
                else:
                    backup_data["bitlocker_keys"] = {"included": False, "reason": "BitLocker non configuré ou accès refusé"}
            except Exception as e:
                backup_data["bitlocker_keys"] = {"error": str(e)}
                print(f"⚠️ Erreur sauvegarde BitLocker: {e}")

        # Sauvegarder licence Windows (incluant OEM)
        if self.backup_options.get("windows_license", tk.BooleanVar(value=False)).get():
            try:
                license_info = {
                    "product_key": None,
                    "oem_key": None,
                    "activation_status": None,
                    "edition": None,
                    "methods_tried": []
                }

                # Méthode 1: Clé OEM UEFI (Windows 8+)
                try:
                    result = subprocess.run(
                        ['powershell', '-Command',
                         '(Get-WmiObject -query "select * from SoftwareLicensingService").OA3xOriginalProductKey'],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        timeout=15,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )

                    if result.returncode == 0:
                        key = result.stdout.strip()
                        if key and len(key) > 10:
                            license_info["oem_key"] = key
                            license_info["methods_tried"].append("WMI OA3xOriginalProductKey")
                except:
                    pass

                # Méthode 2: Clé produit actuelle via slmgr
                try:
                    result = subprocess.run(['cscript', '//Nologo', 'C:\\Windows\\System32\\slmgr.vbs', '/dli'],
                        capture_output=True, text=True, timeout=15,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                        encoding='utf-8', errors='ignore')

                    if result.returncode == 0:
                        output = result.stdout
                        # Extraire les infos
                        if "Product Key Channel" in output or "Partial Product Key" in output:
                            license_info["activation_status"] = "Activé" if "Licensed" in output else "Non activé"
                            # Extraire les 5 derniers caractères de la clé
                            import re
                            partial_match = re.search(r'Partial Product Key:\s*([A-Z0-9]{5})', output)
                            if partial_match:
                                license_info["product_key"] = f"*****-*****-*****-*****-{partial_match.group(1)}"
                        license_info["methods_tried"].append("slmgr /dli")
                except:
                    pass

                # Méthode 3: Edition Windows
                try:
                    result = subprocess.run(
                        ['powershell', '-Command', '(Get-WmiObject -Class Win32_OperatingSystem).Caption'],
                        capture_output=True, text=True, timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                        encoding='utf-8', errors='ignore'
                    )

                    if result.returncode == 0:
                        license_info["edition"] = result.stdout.strip()
                        license_info["methods_tried"].append("WMI Win32_OperatingSystem")
                except:
                    pass

                # Méthode 4: Clé depuis le registre (décodage DigitalProductId)
                try:
                    import winreg
                    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as reg_key:
                        try:
                            product_id = winreg.QueryValueEx(reg_key, "ProductId")[0]
                            license_info["product_id"] = product_id
                        except:
                            pass

                        # Décoder la clé depuis DigitalProductId
                        try:
                            digital_pid = winreg.QueryValueEx(reg_key, "DigitalProductId")[0]
                            if digital_pid:
                                decoded_key = decode_product_key(digital_pid, key_offset=52)
                                if decoded_key and len(decoded_key) == 29:
                                    license_info["decoded_key"] = decoded_key
                                    license_info["methods_tried"].append("Registry DigitalProductId (décodé)")
                        except:
                            pass

                        # Essayer aussi DigitalProductId4 (Windows 8+)
                        try:
                            digital_pid4 = winreg.QueryValueEx(reg_key, "DigitalProductId4")[0]
                            if digital_pid4:
                                decoded_key4 = decode_product_key(digital_pid4, key_offset=808)
                                if decoded_key4 and len(decoded_key4) == 29:
                                    license_info["decoded_key4"] = decoded_key4
                                    license_info["methods_tried"].append("Registry DigitalProductId4 (décodé)")
                        except:
                            pass
                except:
                    pass

                # Construire le résultat final
                result_text = []
                result_text.append("=== LICENCE WINDOWS ===\n")

                if license_info["edition"]:
                    result_text.append(f"Édition: {license_info['edition']}")

                # Afficher les clés en priorité
                if license_info["oem_key"]:
                    result_text.append(f"\n🔑 CLÉ OEM (UEFI - COMPLÈTE):")
                    result_text.append(f"   {license_info['oem_key']}")

                if license_info.get("decoded_key"):
                    result_text.append(f"\n🔑 CLÉ REGISTRE (DÉCODÉE):")
                    result_text.append(f"   {license_info['decoded_key']}")

                if license_info.get("decoded_key4"):
                    result_text.append(f"\n🔑 CLÉ REGISTRE v4 (DÉCODÉE):")
                    result_text.append(f"   {license_info['decoded_key4']}")

                if license_info["product_key"] and not license_info.get("decoded_key"):
                    result_text.append(f"\nClé partielle: {license_info['product_key']}")

                if license_info.get("product_id"):
                    result_text.append(f"\nProduct ID: {license_info['product_id']}")

                if license_info["activation_status"]:
                    result_text.append(f"Statut: {license_info['activation_status']}")

                result_text.append(f"\nMéthodes: {', '.join(license_info['methods_tried'])}")

                backup_data["windows_license"] = "\n".join(result_text) if result_text else "Impossible de récupérer la licence"
                print(f"🪟 Licence Windows sauvegardée (OEM: {'Oui' if license_info['oem_key'] else 'Non'})")
            except Exception as e:
                backup_data["windows_license"] = {"error": str(e)}

        # Sauvegarder licence Office (incluant OEM)
        if self.backup_options.get("office_license", tk.BooleanVar(value=False)).get():
            try:
                license_info = {
                    "installed_products": [],
                    "activation_status": {},
                    "product_keys": {},
                    "oem_keys": {},
                    "methods_tried": []
                }

                # Méthode 1: OSPP.vbs pour information détaillée (Office 2010+)
                ospp_paths = [
                    r"C:\Program Files\Microsoft Office\Office16\OSPP.VBS",  # Office 2016/2019/2021
                    r"C:\Program Files (x86)\Microsoft Office\Office16\OSPP.VBS",
                    r"C:\Program Files\Microsoft Office\Office15\OSPP.VBS",  # Office 2013
                    r"C:\Program Files (x86)\Microsoft Office\Office15\OSPP.VBS",
                    r"C:\Program Files\Microsoft Office\Office14\OSPP.VBS",  # Office 2010
                    r"C:\Program Files (x86)\Microsoft Office\Office14\OSPP.VBS",
                ]

                ospp_found = False
                for ospp_path in ospp_paths:
                    if Path(ospp_path).exists():
                        try:
                            result = subprocess.run(
                                ['cscript', '//Nologo', ospp_path, '/dstatus'],
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                timeout=20,
                                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                            )

                            if result.returncode == 0:
                                ospp_found = True
                                output = result.stdout

                                # Extraire les informations
                                import re
                                product_names = re.findall(r'LICENSE NAME:\s*(.+)', output)
                                partial_keys = re.findall(r'Last 5 characters of installed product key:\s*([A-Z0-9]{5})', output)
                                license_status = re.findall(r'LICENSE STATUS:\s*(.+)', output)

                                for i, name in enumerate(product_names):
                                    product_info = {
                                        "name": name.strip(),
                                        "partial_key": f"{partial_keys[i]}" if i < len(partial_keys) else "Non disponible",
                                        "status": license_status[i].strip() if i < len(license_status) else "Inconnu"
                                    }
                                    license_info["installed_products"].append(product_info)
                                    license_info["activation_status"][name.strip()] = license_status[i].strip() if i < len(license_status) else "Inconnu"

                                license_info["methods_tried"].append(f"OSPP.vbs ({ospp_path})")
                                break
                        except Exception as e:
                            pass

                # Méthode 2: WMI SoftwareLicensingProduct (activations actuelles)
                if not ospp_found:
                    try:
                        result = subprocess.run(
                            ['powershell', '-Command',
                             'Get-WmiObject -Namespace root/CIMV2 -Query "SELECT * FROM SoftwareLicensingProduct WHERE Name LIKE \'Microsoft Office%\' AND LicenseStatus = 1" | Select-Object Name, PartialProductKey, LicenseStatus | ConvertTo-Json'],
                            capture_output=True,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            timeout=20,
                            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                        )

                        if result.returncode == 0 and result.stdout.strip():
                            wmi_data = json.loads(result.stdout)

                            if not isinstance(wmi_data, list):
                                wmi_data = [wmi_data]

                            for product in wmi_data:
                                product_info = {
                                    "name": product.get("Name", "Inconnu"),
                                    "partial_key": f"{product.get('PartialProductKey', 'N/A')}" if product.get('PartialProductKey') else "Non disponible",
                                    "status": "Activé" if product.get("LicenseStatus") == 1 else "Non activé"
                                }
                                license_info["installed_products"].append(product_info)
                                license_info["activation_status"][product.get("Name", "Inconnu")] = product_info["status"]

                            license_info["methods_tried"].append("WMI SoftwareLicensingProduct")
                    except:
                        pass

                # Méthode 3: Clés de registre Office (OEM et installations) - AVEC DÉCODAGE
                try:
                    import winreg
                    office_versions = {
                        "17.0": "Office 2024",
                        "16.0": "Office 2016/2019/2021/365",
                        "15.0": "Office 2013",
                        "14.0": "Office 2010",
                        "12.0": "Office 2007"
                    }

                    for version, name in office_versions.items():
                        try:
                            # Clé de registre Registration
                            reg_paths = [
                                rf"SOFTWARE\Microsoft\Office\{version}\Registration",
                                rf"SOFTWARE\WOW6432Node\Microsoft\Office\{version}\Registration"
                            ]

                            for reg_path in reg_paths:
                                try:
                                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as reg_key:
                                        # Parcourir les sous-clés
                                        i = 0
                                        while True:
                                            try:
                                                subkey_name = winreg.EnumKey(reg_key, i)
                                                with winreg.OpenKey(reg_key, subkey_name) as subkey:
                                                    try:
                                                        product_name = winreg.QueryValueEx(subkey, "ProductName")[0]
                                                        decoded_key = None

                                                        # Décoder DigitalProductId
                                                        try:
                                                            digital_pid = winreg.QueryValueEx(subkey, "DigitalProductId")[0]
                                                            if digital_pid:
                                                                # Essayer plusieurs offsets pour Office
                                                                for offset in [52, 808, 0]:
                                                                    decoded = decode_product_key(digital_pid, key_offset=offset)
                                                                    if decoded and len(decoded) == 29 and decoded[0] != 'B':
                                                                        decoded_key = decoded
                                                                        break
                                                        except:
                                                            pass

                                                        # Stocker la clé décodée
                                                        if decoded_key:
                                                            license_info["oem_keys"][product_name] = decoded_key
                                                        else:
                                                            license_info["oem_keys"][product_name] = "Clé présente (non décodable)"

                                                        # Vérifier si déjà dans la liste
                                                        if not any(p["name"] == product_name for p in license_info["installed_products"]):
                                                            license_info["installed_products"].append({
                                                                "name": product_name,
                                                                "decoded_key": decoded_key if decoded_key else "Non disponible",
                                                                "status": "Installé"
                                                            })
                                                    except:
                                                        pass
                                                i += 1
                                            except OSError:
                                                break
                                except:
                                    pass
                        except:
                            pass

                    license_info["methods_tried"].append("Registry Office Registration (décodé)")
                except:
                    pass

                # Méthode 4: Détection via fichiers installés
                try:
                    office_install_paths = [
                        r"C:\Program Files\Microsoft Office",
                        r"C:\Program Files (x86)\Microsoft Office"
                    ]

                    for base_path in office_install_paths:
                        if Path(base_path).exists():
                            # Vérifier les versions installées
                            for item in Path(base_path).iterdir():
                                if item.is_dir() and item.name.startswith("Office"):
                                    version_num = item.name.replace("Office", "")
                                    version_map = {
                                        "17": "2024",
                                        "16": "2016/2019/2021/365",
                                        "15": "2013",
                                        "14": "2010",
                                        "12": "2007"
                                    }

                                    if version_num in version_map:
                                        version_name = f"Microsoft Office {version_map[version_num]}"
                                        if not any(version_name in p["name"] for p in license_info["installed_products"]):
                                            license_info["installed_products"].append({
                                                "name": version_name,
                                                "partial_key": "Détecté par fichiers",
                                                "status": "Installé (non vérifié)"
                                            })

                    license_info["methods_tried"].append("File System Detection")
                except:
                    pass

                # Construire le résultat final
                result_text = []
                result_text.append("=== LICENCES MICROSOFT OFFICE ===\n")

                if license_info["installed_products"]:
                    result_text.append(f"Produits détectés: {len(license_info['installed_products'])}\n")

                    for i, product in enumerate(license_info["installed_products"], 1):
                        result_text.append(f"\n{'='*50}")
                        result_text.append(f"[Produit {i}] {product['name']}")
                        result_text.append(f"{'='*50}")
                        result_text.append(f"  Statut: {product.get('status', 'Inconnu')}")

                        # Afficher la clé décodée si disponible
                        if product.get('decoded_key') and product['decoded_key'] != "Non disponible":
                            result_text.append(f"\n  🔑 CLÉ COMPLÈTE (DÉCODÉE):")
                            result_text.append(f"     {product['decoded_key']}")
                        elif product.get('partial_key') and product['partial_key'] not in ["Voir registre", "Non disponible"]:
                            result_text.append(f"  Clé partielle: *****-*****-*****-*****-{product['partial_key']}")

                        # Ajouter info OEM si disponible et différente
                        if product['name'] in license_info["oem_keys"]:
                            oem_key = license_info['oem_keys'][product['name']]
                            if oem_key and "non décodable" not in oem_key.lower() and oem_key != product.get('decoded_key'):
                                if len(oem_key) == 29:  # Format XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
                                    result_text.append(f"\n  🔑 CLÉ OEM:")
                                    result_text.append(f"     {oem_key}")
                else:
                    result_text.append("Aucun produit Office détecté")

                result_text.append(f"\n\nMéthodes: {', '.join(license_info['methods_tried'])}")

                backup_data["office_license"] = "\n".join(result_text) if license_info["installed_products"] else "Aucune installation Office détectée"
                print(f"📄 Licence Office sauvegardée ({len(license_info['installed_products'])} produit(s) trouvé(s))")
            except Exception as e:
                backup_data["office_license"] = {"error": str(e)}

        # Sauvegarder règles pare-feu
        if self.backup_options.get("firewall_rules", tk.BooleanVar(value=False)).get():
            try:
                result = subprocess.run(
                    ['powershell', '-Command',
                     'Get-NetFirewallRule | Where-Object {$_.Enabled -eq "True"} | Select-Object DisplayName, Direction, Action, Profile | ConvertTo-Json'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if result.returncode == 0:
                    backup_data["firewall_rules"] = result.stdout
                    print("🛡️ Règles pare-feu sauvegardées")
            except Exception as e:
                backup_data["firewall_rules"] = {"error": str(e)}

        # Sauvegarder polices installées
        if self.backup_options.get("installed_fonts", tk.BooleanVar(value=False)).get():
            try:
                fonts_dir = Path("C:/Windows/Fonts")
                if fonts_dir.exists():
                    fonts = [f.name for f in fonts_dir.iterdir() if f.is_file()]
                    backup_data["installed_fonts"] = {
                        "count": len(fonts),
                        "fonts": fonts
                    }
                    print(f"🔤 {len(fonts)} polices sauvegardées")
            except Exception as e:
                backup_data["installed_fonts"] = {"error": str(e)}

        # Sauvegarder tâches planifiées
        if self.backup_options.get("scheduled_tasks", tk.BooleanVar(value=False)).get():
            try:
                result = subprocess.run(
                    ['powershell', '-Command',
                     'Get-ScheduledTask | Where-Object {$_.State -ne "Disabled"} | Select-Object TaskName, TaskPath, State | ConvertTo-Json'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if result.returncode == 0:
                    backup_data["scheduled_tasks"] = result.stdout
                    print("⏰ Tâches planifiées sauvegardées")
            except Exception as e:
                backup_data["scheduled_tasks"] = {"error": str(e)}

        # Sauvegarder fonctionnalités Windows
        if self.backup_options.get("windows_features", tk.BooleanVar(value=False)).get():
            try:
                result = subprocess.run(
                    ['powershell', '-Command',
                     'Get-WindowsOptionalFeature -Online | Where-Object {$_.State -eq "Enabled"} | Select-Object FeatureName, State | ConvertTo-Json'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=45,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                if result.returncode == 0:
                    backup_data["windows_features"] = result.stdout
                    print("🎯 Fonctionnalités Windows sauvegardées")
            except Exception as e:
                backup_data["windows_features"] = {"error": str(e)}

        # Sauvegarder tailles des dossiers utilisateur
        if self.backup_options.get("folder_sizes", tk.BooleanVar(value=False)).get():
            try:
                def get_folder_size(path):
                    """Calcule la taille d'un dossier en bytes"""
                    total = 0
                    try:
                        for entry in os.scandir(path):
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    total += entry.stat().st_size
                                elif entry.is_dir(follow_symlinks=False):
                                    total += get_folder_size(entry.path)
                            except (PermissionError, OSError):
                                pass
                    except (PermissionError, OSError):
                        pass
                    return total

                def format_size(size_bytes):
                    """Formate une taille en bytes vers une chaîne lisible"""
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if size_bytes < 1024.0:
                            return f"{size_bytes:.2f} {unit}"
                        size_bytes /= 1024.0
                    return f"{size_bytes:.2f} PB"

                user_home = Path.home()
                appdata = os.environ.get('APPDATA', str(user_home / 'AppData' / 'Roaming'))
                localappdata = os.environ.get('LOCALAPPDATA', str(user_home / 'AppData' / 'Local'))
                locallow = str(user_home / 'AppData' / 'LocalLow')

                folder_info = {
                    "user_folder": str(user_home),
                    "folders": []
                }

                # Liste des dossiers à analyser
                folders_to_check = [
                    ("📁 Dossier Utilisateur Complet", str(user_home)),
                    ("📂 AppData\\Roaming", appdata),
                    ("📂 AppData\\Local", localappdata),
                    ("📂 AppData\\LocalLow", locallow),
                    ("🖥️ Bureau", str(user_home / 'Desktop')),
                    ("📄 Documents", str(user_home / 'Documents')),
                    ("⬇️ Téléchargements", str(user_home / 'Downloads')),
                    ("🖼️ Images", str(user_home / 'Pictures')),
                    ("🎵 Musique", str(user_home / 'Music')),
                    ("🎬 Vidéos", str(user_home / 'Videos')),
                ]

                result_text = ["=== TAILLE DES DOSSIERS UTILISATEUR ===\n"]

                for name, path in folders_to_check:
                    if Path(path).exists():
                        try:
                            size = get_folder_size(path)
                            formatted = format_size(size)
                            folder_info["folders"].append({
                                "name": name,
                                "path": path,
                                "size_bytes": size,
                                "size_formatted": formatted
                            })
                            result_text.append(f"{name}")
                            result_text.append(f"   Chemin: {path}")
                            result_text.append(f"   Taille: {formatted}")
                            result_text.append("")
                        except Exception as e:
                            result_text.append(f"{name}: Erreur - {str(e)[:50]}")

                # Calculer le total
                total_size = sum(f["size_bytes"] for f in folder_info["folders"] if "Complet" not in f["name"])
                result_text.append(f"\n{'='*50}")
                result_text.append(f"TOTAL (hors dossier utilisateur complet): {format_size(total_size)}")

                backup_data["folder_sizes"] = "\n".join(result_text)
                print(f"📁 Tailles dossiers sauvegardées ({len(folder_info['folders'])} dossiers)")
            except Exception as e:
                backup_data["folder_sizes"] = {"error": str(e)}

        # Analyser processus suspects
        if self.backup_options.get("suspicious_processes", tk.BooleanVar(value=False)).get():
            try:
                result_text = ["=== ANALYSE DES PROCESSUS SUSPECTS ===\n"]
                suspicious_findings = {
                    "critical": [],
                    "warning": [],
                    "info": [],
                    "total_processes": 0
                }

                # Noms de processus connus comme malveillants ou suspects
                known_malware = [
                    'coinminer', 'xmrig', 'cryptonight', 'minerd', 'cgminer', 'bfgminer',
                    'kryptex', 'nicehash', 'phoenixminer', 'ethminer', 'nbminer',
                    'wannacry', 'petya', 'notpetya', 'locky', 'cerber', 'cryptolocker',
                    'teslacrypt', 'gandcrab', 'ryuk', 'maze', 'revil', 'darkside',
                    'keylogger', 'spyware', 'trojan', 'backdoor', 'rootkit',
                    'rat', 'botnet', 'ddos', 'ransomware', 'adware', 'hijacker'
                ]

                # Processus légitimes souvent usurpés (vérifier le chemin)
                suspicious_if_wrong_path = {
                    'svchost.exe': r'C:\Windows\System32',
                    'csrss.exe': r'C:\Windows\System32',
                    'services.exe': r'C:\Windows\System32',
                    'lsass.exe': r'C:\Windows\System32',
                    'winlogon.exe': r'C:\Windows\System32',
                    'explorer.exe': r'C:\Windows',
                    'smss.exe': r'C:\Windows\System32',
                    'wininit.exe': r'C:\Windows\System32',
                    'taskmgr.exe': r'C:\Windows\System32',
                }

                # Chemins suspects
                suspicious_paths = [
                    r'\Temp\\', r'\AppData\Local\Temp\\', r'%temp%',
                    r'\ProgramData\\', r'\Users\Public\\',
                    r'C:\$Recycle.Bin', r'\System Volume Information\\'
                ]

                # Récupérer la liste des processus avec PowerShell
                ps_cmd = '''
Get-Process | Select-Object Id, ProcessName, Path, Company, Description,
    @{Name='Memory_MB';Expression={[math]::Round($_.WorkingSet64/1MB, 2)}},
    @{Name='CPU';Expression={$_.CPU}},
    @{Name='StartTime';Expression={$_.StartTime}} | ConvertTo-Json -Depth 3
'''
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_cmd],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=60,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )

                if result.returncode == 0 and result.stdout.strip():
                    processes = json.loads(result.stdout)
                    if not isinstance(processes, list):
                        processes = [processes]

                    suspicious_findings["total_processes"] = len(processes)

                    for proc in processes:
                        proc_name = (proc.get('ProcessName') or '').lower()
                        proc_path = proc.get('Path') or ''
                        proc_company = proc.get('Company') or ''
                        proc_desc = proc.get('Description') or ''
                        proc_mem = proc.get('Memory_MB') or 0

                        issues = []
                        severity = None

                        # Vérifier nom malveillant connu
                        for malware in known_malware:
                            if malware in proc_name:
                                issues.append(f"⚠️ Nom contient '{malware}' (malware connu)")
                                severity = "critical"

                        # Vérifier chemin suspect pour processus système
                        if proc_name + '.exe' in suspicious_if_wrong_path:
                            expected_path = suspicious_if_wrong_path[proc_name + '.exe']
                            if proc_path and expected_path.lower() not in proc_path.lower():
                                issues.append(f"🚨 Chemin inattendu (devrait être dans {expected_path})")
                                severity = "critical"

                        # Vérifier chemin dans dossier suspect
                        for susp_path in suspicious_paths:
                            if susp_path.lower().replace('\\\\', '\\') in proc_path.lower():
                                issues.append(f"⚠️ Exécuté depuis un emplacement suspect")
                                if not severity:
                                    severity = "warning"

                        # Processus sans éditeur signé (sauf processus système)
                        if not proc_company and proc_path and 'windows' not in proc_path.lower():
                            issues.append("ℹ️ Aucun éditeur/signature détecté")
                            if not severity:
                                severity = "info"

                        # Consommation mémoire excessive (> 1GB)
                        if proc_mem > 1000:
                            issues.append(f"ℹ️ Consommation mémoire élevée ({proc_mem} MB)")
                            if not severity:
                                severity = "info"

                        # Ajouter aux résultats si suspect
                        if issues:
                            finding = {
                                "name": proc.get('ProcessName'),
                                "pid": proc.get('Id'),
                                "path": proc_path,
                                "company": proc_company,
                                "memory_mb": proc_mem,
                                "issues": issues
                            }

                            if severity == "critical":
                                suspicious_findings["critical"].append(finding)
                            elif severity == "warning":
                                suspicious_findings["warning"].append(finding)
                            else:
                                suspicious_findings["info"].append(finding)

                # Construire le rapport
                result_text.append(f"Total processus analysés: {suspicious_findings['total_processes']}\n")

                if suspicious_findings["critical"]:
                    result_text.append(f"\n{'='*60}")
                    result_text.append("🚨 CRITIQUES - ACTION REQUISE ({} trouvé(s))".format(len(suspicious_findings['critical'])))
                    result_text.append(f"{'='*60}")
                    for proc in suspicious_findings["critical"]:
                        result_text.append(f"\n  ❌ {proc['name']} (PID: {proc['pid']})")
                        result_text.append(f"     Chemin: {proc['path']}")
                        result_text.append(f"     Éditeur: {proc['company'] or 'Non signé'}")
                        for issue in proc['issues']:
                            result_text.append(f"     {issue}")

                if suspicious_findings["warning"]:
                    result_text.append(f"\n{'='*60}")
                    result_text.append("⚠️ AVERTISSEMENTS ({} trouvé(s))".format(len(suspicious_findings['warning'])))
                    result_text.append(f"{'='*60}")
                    for proc in suspicious_findings["warning"]:
                        result_text.append(f"\n  ⚠️ {proc['name']} (PID: {proc['pid']})")
                        result_text.append(f"     Chemin: {proc['path']}")
                        for issue in proc['issues']:
                            result_text.append(f"     {issue}")

                if suspicious_findings["info"]:
                    result_text.append(f"\n{'='*60}")
                    result_text.append("ℹ️ INFORMATIONS ({} trouvé(s))".format(len(suspicious_findings['info'])))
                    result_text.append(f"{'='*60}")
                    for proc in suspicious_findings["info"][:20]:  # Limiter à 20
                        result_text.append(f"\n  ℹ️ {proc['name']} (PID: {proc['pid']})")
                        for issue in proc['issues']:
                            result_text.append(f"     {issue}")
                    if len(suspicious_findings["info"]) > 20:
                        result_text.append(f"\n  ... et {len(suspicious_findings['info']) - 20} autres processus")

                if not any([suspicious_findings["critical"], suspicious_findings["warning"], suspicious_findings["info"]]):
                    result_text.append("\n✅ Aucun processus suspect détecté !")

                result_text.append(f"\n\n{'='*60}")
                result_text.append("RÉSUMÉ")
                result_text.append(f"{'='*60}")
                result_text.append(f"  🚨 Critiques: {len(suspicious_findings['critical'])}")
                result_text.append(f"  ⚠️ Avertissements: {len(suspicious_findings['warning'])}")
                result_text.append(f"  ℹ️ Informations: {len(suspicious_findings['info'])}")

                backup_data["suspicious_processes"] = "\n".join(result_text)
                print(f"🔍 Analyse processus terminée ({len(suspicious_findings['critical'])} critiques, {len(suspicious_findings['warning'])} avertissements)")
            except Exception as e:
                backup_data["suspicious_processes"] = {"error": str(e)}

        # Sauvegarder mots de passe navigateurs (DÉCHIFFRÉS)
        if self.backup_options.get("browser_passwords", tk.BooleanVar(value=False)).get():
            try:
                import sqlite3
                import win32crypt
                import base64
                from Crypto.Cipher import AES
                import shutil

                passwords_data = {
                    "chrome": [],
                    "brave": [],
                    "edge": [],
                    "total_passwords": 0,
                    "warning": "⚠️ SENSIBLE - Mots de passe déchiffrés - NE PAS PARTAGER ce fichier !"
                }

                def get_encryption_key(browser_path):
                    """Récupérer la clé de chiffrement AES du navigateur"""
                    local_state_path = browser_path / "Local State"
                    if not local_state_path.exists():
                        return None

                    with open(local_state_path, "r", encoding="utf-8") as f:
                        local_state = json.load(f)

                    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                    encrypted_key = encrypted_key[5:]  # Retirer "DPAPI"
                    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

                def decrypt_password(password, key):
                    """Déchiffrer un mot de passe"""
                    try:
                        iv = password[3:15]
                        password = password[15:]
                        cipher = AES.new(key, AES.MODE_GCM, iv)
                        return cipher.decrypt(password)[:-16].decode()
                    except:
                        return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])

                # Chrome
                chrome_path = Path.home() / "AppData/Local/Google/Chrome/User Data/Default"
                if chrome_path.exists():
                    try:
                        key = get_encryption_key(Path.home() / "AppData/Local/Google/Chrome/User Data")
                        login_db = chrome_path / "Login Data"

                        # Copier la DB (car elle est verrouillée si Chrome est ouvert)
                        temp_db = Path(tempfile.gettempdir()) / "ChromeLoginData"
                        shutil.copy2(login_db, temp_db)

                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

                        for row in cursor.fetchall():
                            url, username, encrypted_password = row
                            if username and encrypted_password:
                                try:
                                    password = decrypt_password(encrypted_password, key)
                                    passwords_data["chrome"].append({
                                        "url": url,
                                        "username": username,
                                        "password": password
                                    })
                                    passwords_data["total_passwords"] += 1
                                except:
                                    pass

                        conn.close()
                        temp_db.unlink()
                    except Exception as e:
                        passwords_data["chrome"] = {"error": str(e)}

                # Brave
                brave_path = Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default"
                if brave_path.exists():
                    try:
                        key = get_encryption_key(Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/User Data")
                        login_db = brave_path / "Login Data"

                        temp_db = Path(tempfile.gettempdir()) / "BraveLoginData"
                        shutil.copy2(login_db, temp_db)

                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

                        for row in cursor.fetchall():
                            url, username, encrypted_password = row
                            if username and encrypted_password:
                                try:
                                    password = decrypt_password(encrypted_password, key)
                                    passwords_data["brave"].append({
                                        "url": url,
                                        "username": username,
                                        "password": password
                                    })
                                    passwords_data["total_passwords"] += 1
                                except:
                                    pass

                        conn.close()
                        temp_db.unlink()
                    except Exception as e:
                        passwords_data["brave"] = {"error": str(e)}

                # Edge
                edge_path = Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default"
                if edge_path.exists():
                    try:
                        key = get_encryption_key(Path.home() / "AppData/Local/Microsoft/Edge/User Data")
                        login_db = edge_path / "Login Data"

                        temp_db = Path(tempfile.gettempdir()) / "EdgeLoginData"
                        shutil.copy2(login_db, temp_db)

                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

                        for row in cursor.fetchall():
                            url, username, encrypted_password = row
                            if username and encrypted_password:
                                try:
                                    password = decrypt_password(encrypted_password, key)
                                    passwords_data["edge"].append({
                                        "url": url,
                                        "username": username,
                                        "password": password
                                    })
                                    passwords_data["total_passwords"] += 1
                                except:
                                    pass

                        conn.close()
                        temp_db.unlink()
                    except Exception as e:
                        passwords_data["edge"] = {"error": str(e)}

                backup_data["browser_passwords"] = passwords_data
                print(f"🔑 {passwords_data['total_passwords']} mots de passe déchiffrés (Chrome: {len(passwords_data.get('chrome', []))}, Brave: {len(passwords_data.get('brave', []))}, Edge: {len(passwords_data.get('edge', []))})")
            except Exception as e:
                backup_data["browser_passwords"] = {"error": str(e)}

        # Sauvegarder favoris navigateurs (Chrome, Brave, Edge, Opera, Firefox, Vivaldi, Avast, Opera GX)
        if self.backup_options.get("browser_bookmarks", tk.BooleanVar(value=False)).get():
            try:
                bookmarks_data = {
                    "chrome": None,
                    "brave": None,
                    "edge": None,
                    "opera": None,
                    "opera_gx": None,
                    "vivaldi": None,
                    "avast": None,
                    "firefox": None,
                    "total_bookmarks": 0
                }

                # Chrome
                chrome_bookmarks = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Bookmarks"
                if chrome_bookmarks.exists():
                    try:
                        with open(chrome_bookmarks, 'r', encoding='utf-8') as f:
                            chrome_data = json.load(f)
                            bookmarks_data["chrome"] = {"included": True, "file": str(chrome_bookmarks)}
                            # Compter les favoris (récursif dans les dossiers)
                            def count_bookmarks(node):
                                count = 0
                                if node.get("type") == "url":
                                    count = 1
                                elif node.get("type") == "folder" and "children" in node:
                                    for child in node["children"]:
                                        count += count_bookmarks(child)
                                return count
                            if "roots" in chrome_data:
                                for root_key in ["bookmark_bar", "other", "synced"]:
                                    if root_key in chrome_data["roots"]:
                                        bookmarks_data["total_bookmarks"] += count_bookmarks(chrome_data["roots"][root_key])
                    except Exception as e:
                        bookmarks_data["chrome"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["chrome"] = {"included": False, "reason": "Chrome non installé ou pas de favoris"}

                # Brave (même structure que Chrome - Chromium-based)
                brave_bookmarks = Path.home() / "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Bookmarks"
                if brave_bookmarks.exists():
                    try:
                        with open(brave_bookmarks, 'r', encoding='utf-8') as f:
                            brave_data = json.load(f)
                            bookmarks_data["brave"] = {"included": True, "file": str(brave_bookmarks)}
                            # Compter les favoris
                            def count_bookmarks(node):
                                count = 0
                                if node.get("type") == "url":
                                    count = 1
                                elif node.get("type") == "folder" and "children" in node:
                                    for child in node["children"]:
                                        count += count_bookmarks(child)
                                return count
                            if "roots" in brave_data:
                                for root_key in ["bookmark_bar", "other", "synced"]:
                                    if root_key in brave_data["roots"]:
                                        bookmarks_data["total_bookmarks"] += count_bookmarks(brave_data["roots"][root_key])
                    except Exception as e:
                        bookmarks_data["brave"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["brave"] = {"included": False, "reason": "Brave non installé ou pas de favoris"}

                # Edge (même structure que Chrome)
                edge_bookmarks = Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default/Bookmarks"
                if edge_bookmarks.exists():
                    try:
                        with open(edge_bookmarks, 'r', encoding='utf-8') as f:
                            edge_data = json.load(f)
                            bookmarks_data["edge"] = {"included": True, "file": str(edge_bookmarks)}
                    except Exception as e:
                        bookmarks_data["edge"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["edge"] = {"included": False, "reason": "Edge non installé ou pas de favoris"}

                # Opera (Chromium-based)
                opera_bookmarks = Path.home() / "AppData/Roaming/Opera Software/Opera Stable/Bookmarks"
                if opera_bookmarks.exists():
                    try:
                        with open(opera_bookmarks, 'r', encoding='utf-8') as f:
                            opera_data = json.load(f)
                            bookmarks_data["opera"] = {"included": True, "file": str(opera_bookmarks)}
                    except Exception as e:
                        bookmarks_data["opera"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["opera"] = {"included": False, "reason": "Opera non installé ou pas de favoris"}

                # Opera GX (Chromium-based)
                opera_gx_bookmarks = Path.home() / "AppData/Roaming/Opera Software/Opera GX Stable/Bookmarks"
                if opera_gx_bookmarks.exists():
                    try:
                        with open(opera_gx_bookmarks, 'r', encoding='utf-8') as f:
                            opera_gx_data = json.load(f)
                            bookmarks_data["opera_gx"] = {"included": True, "file": str(opera_gx_bookmarks)}
                    except Exception as e:
                        bookmarks_data["opera_gx"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["opera_gx"] = {"included": False, "reason": "Opera GX non installé ou pas de favoris"}

                # Vivaldi (Chromium-based)
                vivaldi_bookmarks = Path.home() / "AppData/Local/Vivaldi/User Data/Default/Bookmarks"
                if vivaldi_bookmarks.exists():
                    try:
                        with open(vivaldi_bookmarks, 'r', encoding='utf-8') as f:
                            vivaldi_data = json.load(f)
                            bookmarks_data["vivaldi"] = {"included": True, "file": str(vivaldi_bookmarks)}
                    except Exception as e:
                        bookmarks_data["vivaldi"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["vivaldi"] = {"included": False, "reason": "Vivaldi non installé ou pas de favoris"}

                # Avast Secure Browser (Chromium-based)
                avast_bookmarks = Path.home() / "AppData/Local/AVAST Software/Browser/User Data/Default/Bookmarks"
                if avast_bookmarks.exists():
                    try:
                        with open(avast_bookmarks, 'r', encoding='utf-8') as f:
                            avast_data = json.load(f)
                            bookmarks_data["avast"] = {"included": True, "file": str(avast_bookmarks)}
                    except Exception as e:
                        bookmarks_data["avast"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["avast"] = {"included": False, "reason": "Avast Secure Browser non installé ou pas de favoris"}

                # Firefox (places.sqlite - plus complexe, nécessite SQLite)
                firefox_profiles = Path.home() / "AppData/Roaming/Mozilla/Firefox/Profiles"
                if firefox_profiles.exists():
                    try:
                        # Trouver le profil par défaut
                        default_profile = None
                        for profile_dir in firefox_profiles.iterdir():
                            if profile_dir.is_dir() and "default" in profile_dir.name.lower():
                                default_profile = profile_dir
                                break

                        if default_profile:
                            places_db = default_profile / "places.sqlite"
                            if places_db.exists():
                                bookmarks_data["firefox"] = {"included": True, "file": str(places_db), "note": "Base de données SQLite - utiliser un visualiseur SQLite pour accéder"}
                            else:
                                bookmarks_data["firefox"] = {"included": False, "reason": "Base de données places.sqlite non trouvée"}
                        else:
                            bookmarks_data["firefox"] = {"included": False, "reason": "Profil Firefox par défaut non trouvé"}
                    except Exception as e:
                        bookmarks_data["firefox"] = {"included": False, "error": str(e)}
                else:
                    bookmarks_data["firefox"] = {"included": False, "reason": "Firefox non installé"}

                backup_data["browser_bookmarks"] = bookmarks_data
                print(f"🔖 Favoris navigateurs sauvegardés (Chrome: {bookmarks_data['total_bookmarks']} favoris)")
            except Exception as e:
                backup_data["browser_bookmarks"] = {"error": str(e)}

        # NOUVEAU: Lancer un Scan Diagnostic Système Complet
        print("\n🔬 Lancement du Diagnostic Scan Total...")
        try:
            diagnostic_info = self._get_diagnostic_system_info()
            backup_data["diagnostic_scan"] = diagnostic_info
            print("✅ Diagnostic Scan Total terminé")
            print(f"   • CPU: {diagnostic_info.get('cpu_name', 'N/A')}")
            print(f"   • RAM: {diagnostic_info.get('ram_total_gb', 0):.2f} GB")
            print(f"   • GPU: {len(diagnostic_info.get('gpus', []))} carte(s)")
            print(f"   • Stockage: {len(diagnostic_info.get('storage_devices', []))} disque(s)")
        except Exception as e:
            backup_data["diagnostic_scan"] = {"error": str(e)}
            print(f"⚠️ Erreur Diagnostic Scan: {e}")

        # Sauvegarder en 4 formats : JSON, HTML, TXT, MD
        # Chaque format dans son propre try/except pour isolation des erreurs
        formats_created = []

        # Format JSON
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            formats_created.append(f"JSON: {backup_file.name}")
            print(f"✅ JSON créé: {backup_file.name}")
        except Exception as e:
            print(f"❌ Erreur JSON: {e}")
            import traceback
            traceback.print_exc()

        # Format HTML
        try:
            html_file = self.backup_dir / f"backup_{timestamp}.html"
            self._export_to_html(backup_data, html_file)
            formats_created.append(f"HTML: {html_file.name}")
            print(f"✅ HTML créé: {html_file.name}")
        except Exception as e:
            print(f"❌ Erreur HTML: {e}")
            import traceback
            traceback.print_exc()

        # Format TXT
        try:
            txt_file = self.backup_dir / f"backup_{timestamp}.txt"
            self._export_to_txt(backup_data, txt_file)
            formats_created.append(f"TXT: {txt_file.name}")
            print(f"✅ TXT créé: {txt_file.name}")
        except Exception as e:
            print(f"❌ Erreur TXT: {e}")
            import traceback
            traceback.print_exc()

        # Format Markdown
        try:
            md_file = self.backup_dir / f"backup_{timestamp}.md"
            self._export_to_md(backup_data, md_file)
            formats_created.append(f"MD: {md_file.name}")
            print(f"✅ Markdown créé: {md_file.name}")
        except Exception as e:
            print(f"❌ Erreur Markdown: {e}")
            import traceback
            traceback.print_exc()

        # Afficher résumé
        if formats_created:
            print(f"\n💾 Sauvegarde créée ({len(formats_created)} format(s)):")
            for fmt in formats_created:
                print(f"   • {fmt}")
        else:
            print(f"❌ ERREUR: Aucun format créé!")

        self._refresh_backups_list()

    def _open_backup_folder(self):
        """Ouvrir le dossier de sauvegarde dans l'explorateur"""
        try:
            import os
            import subprocess
            if os.name == 'nt':  # Windows
                os.startfile(self.backup_dir)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', str(self.backup_dir)])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}")

    def _get_diagnostic_system_info(self):
        """Obtenir informations système complètes pour le diagnostic"""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

        # Obtenir détails matériels via WMI (Windows)
        try:
            import wmi
            w = wmi.WMI()

            # CPU
            for cpu in w.Win32_Processor():
                info["cpu_name"] = cpu.Name.strip()
                info["cpu_manufacturer"] = cpu.Manufacturer
                info["cpu_cores"] = cpu.NumberOfCores
                info["cpu_threads"] = cpu.NumberOfLogicalProcessors
                info["cpu_max_speed"] = cpu.MaxClockSpeed
                break

            # RAM
            info["ram_modules"] = []
            total_ram_gb = 0
            for mem in w.Win32_PhysicalMemory():
                capacity_gb = int(mem.Capacity) / (1024**3)
                total_ram_gb += capacity_gb
                info["ram_modules"].append({
                    "manufacturer": mem.Manufacturer.strip() if mem.Manufacturer else "Unknown",
                    "capacity_gb": capacity_gb,
                    "speed_mhz": mem.Speed if mem.Speed else 0
                })
            info["ram_total_gb"] = total_ram_gb

            # Carte mère
            for board in w.Win32_BaseBoard():
                info["motherboard_manufacturer"] = board.Manufacturer
                info["motherboard_product"] = board.Product
                break

            # GPU
            info["gpus"] = []
            for gpu in w.Win32_VideoController():
                vram_gb = gpu.AdapterRAM / (1024**3) if gpu.AdapterRAM else 0
                info["gpus"].append({
                    "name": gpu.Name,
                    "vram_gb": vram_gb,
                    "driver_version": gpu.DriverVersion if gpu.DriverVersion else "N/A"
                })

            # Disques
            info["storage_devices"] = []
            for disk in w.Win32_DiskDrive():
                size_gb = int(disk.Size) / (1024**3) if disk.Size else 0
                info["storage_devices"].append({
                    "model": disk.Model if disk.Model else "Unknown",
                    "size_gb": size_gb,
                    "interface": disk.InterfaceType if disk.InterfaceType else "Unknown"
                })

        except Exception as e:
            info["wmi_error"] = str(e)

        # Données psutil (usage actuel)
        try:
            import psutil

            # CPU usage
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)

            # RAM usage
            mem = psutil.virtual_memory()
            info["ram_total"] = mem.total / (1024**3)
            info["ram_used"] = mem.used / (1024**3)
            info["ram_percent"] = mem.percent

            # Partitions
            info["disks"] = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info["disks"].append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total / (1024**3),
                        "used": usage.used / (1024**3),
                        "free": usage.free / (1024**3),
                        "percent": usage.percent
                    })
                except:
                    continue

            # Réseau
            net = psutil.net_io_counters()
            info["net_sent"] = net.bytes_sent / (1024**2)
            info["net_recv"] = net.bytes_recv / (1024**2)

        except Exception as e:
            info["psutil_error"] = str(e)

        return info

    def _format_diagnostic_html(self, diag):
        """Formater les données de diagnostic en HTML"""
        if not diag or 'error' in diag:
            return '<div class="section"><h2>🔬 Diagnostic Scan Total</h2><p style="color: #ef4444;">❌ Erreur lors du diagnostic</p></div>'

        html_sections = ['<div class="section"><h2>🔬 Diagnostic Scan Total</h2>']

        # Système d'exploitation
        html_sections.append('<h3>💻 Système d\'exploitation</h3><table>')
        html_sections.append(f'<tr><td><strong>OS</strong></td><td>{diag.get("os", "N/A")}</td></tr>')
        html_sections.append(f'<tr><td><strong>Version</strong></td><td>{diag.get("os_version", "N/A")}</td></tr>')
        html_sections.append(f'<tr><td><strong>Release</strong></td><td>{diag.get("os_release", "N/A")}</td></tr>')
        html_sections.append(f'<tr><td><strong>Architecture</strong></td><td>{diag.get("architecture", "N/A")}</td></tr>')
        html_sections.append(f'<tr><td><strong>Hostname</strong></td><td>{diag.get("hostname", "N/A")}</td></tr>')
        html_sections.append('</table>')

        # CPU
        html_sections.append('<h3>🖥️ Processeur</h3><table>')
        html_sections.append(f'<tr><td><strong>Modèle</strong></td><td>{diag.get("cpu_name", diag.get("processor", "N/A"))}</td></tr>')
        if 'cpu_manufacturer' in diag:
            html_sections.append(f'<tr><td><strong>Fabricant</strong></td><td>{diag.get("cpu_manufacturer", "N/A")}</td></tr>')
        if 'cpu_cores' in diag:
            html_sections.append(f'<tr><td><strong>Cœurs</strong></td><td>{diag.get("cpu_cores", "N/A")}</td></tr>')
            html_sections.append(f'<tr><td><strong>Threads</strong></td><td>{diag.get("cpu_threads", "N/A")}</td></tr>')
        if 'cpu_percent' in diag:
            html_sections.append(f'<tr><td><strong>Utilisation</strong></td><td>{diag.get("cpu_percent", 0):.1f}%</td></tr>')
        html_sections.append('</table>')

        # RAM
        html_sections.append('<h3>💾 Mémoire RAM</h3><table>')
        if 'ram_total_gb' in diag:
            html_sections.append(f'<tr><td><strong>Total</strong></td><td>{diag.get("ram_total_gb", 0):.2f} GB</td></tr>')
        if 'ram_used' in diag:
            html_sections.append(f'<tr><td><strong>Utilisée</strong></td><td>{diag.get("ram_used", 0):.2f} GB ({diag.get("ram_percent", 0):.1f}%)</td></tr>')
        if 'ram_modules' in diag and diag['ram_modules']:
            html_sections.append(f'<tr><td><strong>Modules</strong></td><td>{len(diag["ram_modules"])} module(s)</td></tr>')
        html_sections.append('</table>')

        # GPU
        if 'gpus' in diag and diag['gpus']:
            html_sections.append(f'<h3>🎮 Carte(s) Graphique(s) ({len(diag["gpus"])})</h3><table>')
            for i, gpu in enumerate(diag['gpus'], 1):
                html_sections.append(f'<tr><td><strong>GPU {i}</strong></td><td>{gpu.get("name", "N/A")}</td></tr>')
                if gpu.get('vram_gb', 0) > 0:
                    html_sections.append(f'<tr><td><strong>VRAM</strong></td><td>{gpu.get("vram_gb", 0):.2f} GB</td></tr>')
                html_sections.append(f'<tr><td><strong>Driver</strong></td><td>{gpu.get("driver_version", "N/A")}</td></tr>')
            html_sections.append('</table>')

        # Stockage
        if 'storage_devices' in diag and diag['storage_devices']:
            html_sections.append(f'<h3>💿 Disques de Stockage ({len(diag["storage_devices"])})</h3><table>')
            for i, disk in enumerate(diag['storage_devices'], 1):
                html_sections.append(f'<tr><td><strong>Disque {i}</strong></td><td>{disk.get("model", "N/A")}</td></tr>')
                html_sections.append(f'<tr><td><strong>Capacité</strong></td><td>{disk.get("size_gb", 0):.2f} GB</td></tr>')
                html_sections.append(f'<tr><td><strong>Interface</strong></td><td>{disk.get("interface", "N/A")}</td></tr>')
            html_sections.append('</table>')

        # Partitions
        if 'disks' in diag and diag['disks']:
            html_sections.append(f'<h3>📂 Partitions ({len(diag["disks"])})</h3><table>')
            html_sections.append('<tr><th>Lecteur</th><th>Total</th><th>Utilisé</th><th>Libre</th><th>%</th></tr>')
            for disk in diag['disks']:
                html_sections.append(f'<tr>')
                html_sections.append(f'<td><code>{disk.get("mountpoint", "N/A")}</code></td>')
                html_sections.append(f'<td>{disk.get("total", 0):.1f} GB</td>')
                html_sections.append(f'<td>{disk.get("used", 0):.1f} GB</td>')
                html_sections.append(f'<td>{disk.get("free", 0):.1f} GB</td>')
                html_sections.append(f'<td>{disk.get("percent", 0):.1f}%</td>')
                html_sections.append('</tr>')
            html_sections.append('</table>')

        html_sections.append('</div>')
        return '\n'.join(html_sections)

    def _format_diagnostic_txt(self, diag):
        """Formater les données de diagnostic en TXT"""
        if not diag or 'error' in diag:
            return "\n================================================================================\nDIAGNOSTIC SCAN TOTAL\n================================================================================\n\n❌ Erreur lors du diagnostic\n\n"

        txt_lines = [
            "\n================================================================================",
            "DIAGNOSTIC SCAN TOTAL",
            "================================================================================\n",
            "\n💻 SYSTÈME D'EXPLOITATION",
            "-" * 80,
            f"OS: {diag.get('os', 'N/A')}",
            f"Version: {diag.get('os_version', 'N/A')}",
            f"Release: {diag.get('os_release', 'N/A')}",
            f"Architecture: {diag.get('architecture', 'N/A')}",
            f"Hostname: {diag.get('hostname', 'N/A')}\n",
            "\n🖥️ PROCESSEUR",
            "-" * 80,
            f"Modèle: {diag.get('cpu_name', diag.get('processor', 'N/A'))}"
        ]

        if 'cpu_cores' in diag:
            txt_lines.extend([
                f"Cœurs: {diag.get('cpu_cores', 'N/A')}",
                f"Threads: {diag.get('cpu_threads', 'N/A')}"
            ])
        if 'cpu_percent' in diag:
            txt_lines.append(f"Utilisation: {diag.get('cpu_percent', 0):.1f}%")

        txt_lines.extend(["\n💾 MÉMOIRE RAM", "-" * 80])
        if 'ram_total_gb' in diag:
            txt_lines.append(f"Total: {diag.get('ram_total_gb', 0):.2f} GB")
        if 'ram_used' in diag:
            txt_lines.append(f"Utilisée: {diag.get('ram_used', 0):.2f} GB ({diag.get('ram_percent', 0):.1f}%)")

        if 'gpus' in diag and diag['gpus']:
            txt_lines.extend([f"\n🎮 CARTE(S) GRAPHIQUE(S) ({len(diag['gpus'])})", "-" * 80])
            for i, gpu in enumerate(diag['gpus'], 1):
                txt_lines.append(f"\nGPU {i}: {gpu.get('name', 'N/A')}")
                if gpu.get('vram_gb', 0) > 0:
                    txt_lines.append(f"  VRAM: {gpu.get('vram_gb', 0):.2f} GB")
                txt_lines.append(f"  Driver: {gpu.get('driver_version', 'N/A')}")

        if 'storage_devices' in diag and diag['storage_devices']:
            txt_lines.extend([f"\n💿 DISQUES DE STOCKAGE ({len(diag['storage_devices'])})", "-" * 80])
            for i, disk in enumerate(diag['storage_devices'], 1):
                txt_lines.append(f"\nDisque {i}: {disk.get('model', 'N/A')}")
                txt_lines.append(f"  Capacité: {disk.get('size_gb', 0):.2f} GB")
                txt_lines.append(f"  Interface: {disk.get('interface', 'N/A')}")

        if 'disks' in diag and diag['disks']:
            txt_lines.extend([f"\n📂 PARTITIONS ({len(diag['disks'])})", "-" * 80])
            for disk in diag['disks']:
                txt_lines.append(f"\n{disk.get('mountpoint', 'N/A')} ({disk.get('fstype', 'N/A')})")
                txt_lines.append(f"  Total: {disk.get('total', 0):.1f} GB")
                txt_lines.append(f"  Utilisé: {disk.get('used', 0):.1f} GB ({disk.get('percent', 0):.1f}%)")
                txt_lines.append(f"  Libre: {disk.get('free', 0):.1f} GB")

        txt_lines.append("\n")
        return '\n'.join(txt_lines)

    def _format_diagnostic_md(self, diag):
        """Formater les données de diagnostic en Markdown"""
        if not diag or 'error' in diag:
            return "\n## 🔬 Diagnostic Scan Total\n\n❌ Erreur lors du diagnostic\n\n"

        md_lines = [
            "\n## 🔬 Diagnostic Scan Total\n",
            "### 💻 Système d'exploitation\n",
            f"- **OS:** {diag.get('os', 'N/A')}",
            f"- **Version:** {diag.get('os_version', 'N/A')}",
            f"- **Release:** {diag.get('os_release', 'N/A')}",
            f"- **Architecture:** {diag.get('architecture', 'N/A')}",
            f"- **Hostname:** {diag.get('hostname', 'N/A')}\n",
            "### 🖥️ Processeur\n",
            f"- **Modèle:** `{diag.get('cpu_name', diag.get('processor', 'N/A'))}`"
        ]

        if 'cpu_cores' in diag:
            md_lines.extend([
                f"- **Cœurs:** {diag.get('cpu_cores', 'N/A')}",
                f"- **Threads:** {diag.get('cpu_threads', 'N/A')}"
            ])
        if 'cpu_percent' in diag:
            md_lines.append(f"- **Utilisation:** {diag.get('cpu_percent', 0):.1f}%")

        md_lines.extend(["\n### 💾 Mémoire RAM\n"])
        if 'ram_total_gb' in diag:
            md_lines.append(f"- **Total:** {diag.get('ram_total_gb', 0):.2f} GB")
        if 'ram_used' in diag:
            md_lines.append(f"- **Utilisée:** {diag.get('ram_used', 0):.2f} GB ({diag.get('ram_percent', 0):.1f}%)")

        if 'gpus' in diag and diag['gpus']:
            md_lines.append(f"\n### 🎮 Carte(s) Graphique(s) ({len(diag['gpus'])})\n")
            for i, gpu in enumerate(diag['gpus'], 1):
                md_lines.append(f"\n**GPU {i}:** `{gpu.get('name', 'N/A')}`")
                if gpu.get('vram_gb', 0) > 0:
                    md_lines.append(f"- **VRAM:** {gpu.get('vram_gb', 0):.2f} GB")
                md_lines.append(f"- **Driver:** {gpu.get('driver_version', 'N/A')}")

        if 'storage_devices' in diag and diag['storage_devices']:
            md_lines.append(f"\n### 💿 Disques de Stockage ({len(diag['storage_devices'])})\n")
            for i, disk in enumerate(diag['storage_devices'], 1):
                md_lines.append(f"\n**Disque {i}:** `{disk.get('model', 'N/A')}`")
                md_lines.append(f"- **Capacité:** {disk.get('size_gb', 0):.2f} GB")
                md_lines.append(f"- **Interface:** {disk.get('interface', 'N/A')}")

        if 'disks' in diag and diag['disks']:
            md_lines.append(f"\n### 📂 Partitions ({len(diag['disks'])})\n")
            md_lines.append("| Lecteur | Total | Utilisé | Libre | % |")
            md_lines.append("|---------|-------|---------|-------|---|")
            for disk in diag['disks']:
                md_lines.append(f"| `{disk.get('mountpoint', 'N/A')}` | {disk.get('total', 0):.1f} GB | {disk.get('used', 0):.1f} GB | {disk.get('free', 0):.1f} GB | {disk.get('percent', 0):.1f}% |")

        md_lines.append("\n")
        return '\n'.join(md_lines)

    def _export_to_html(self, data, filepath):
        """Exporter les données en HTML"""
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sauvegarde NiTriTe - {data.get('date', '')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #1e40af; margin-top: 30px; }}
        .info-box {{ background: #eff6ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #2563eb; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
        tr:hover {{ background: #f9fafb; }}
        .section {{ margin: 30px 0; }}
        code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💾 Sauvegarde NiTriTe V20</h1>
        <div class="info-box">
            <strong>Date:</strong> {data.get('date', 'N/A')}<br>
            <strong>Applications:</strong> {data.get('apps_count', 0)}<br>
            <strong>Timestamp:</strong> {data.get('timestamp', 'N/A')}
        </div>

        <div class="section">
            <h2>📱 Applications Installées ({data.get('apps_count', 0)})</h2>
            <table>
                <tr><th>#</th><th>Application</th></tr>
                {''.join(f'<tr><td>{i+1}</td><td><code>{app}</code></td></tr>' for i, app in enumerate(data.get('apps', [])))}
            </table>
        </div>

        {'<div class="section"><h2>🌐 Configuration Réseau</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('network_config', 'Non sauvegardée')) + '</pre></div>' if data.get('network_config') else ''}

        {'<div class="section"><h2>🚀 Programmes au Démarrage</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('startup_programs', 'Non sauvegardés')) + '</pre></div>' if data.get('startup_programs') else ''}

        {'<div class="section"><h2>🔖 Favoris Navigateurs</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + json.dumps(data.get('browser_bookmarks', {}), indent=2, ensure_ascii=False) + '</pre></div>' if data.get('browser_bookmarks') else ''}

        {'<div class="section"><h2>🔧 Liste des Drivers Système</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + json.dumps(data.get('drivers', []), indent=2, ensure_ascii=False) + '</pre></div>' if data.get('drivers') else ''}

        {'<div class="section"><h2>🔐 Clés de Récupération BitLocker</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('bitlocker_keys', 'Aucune clé trouvée')) + '</pre></div>' if data.get('bitlocker_keys') else ''}

        {'<div class="section"><h2>🪟 Licence Windows</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('windows_license', 'Non récupérée')) + '</pre></div>' if data.get('windows_license') else ''}

        {'<div class="section"><h2>📄 Licence Microsoft Office</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('office_license', 'Non récupérée')) + '</pre></div>' if data.get('office_license') else ''}

        {'<div class="section"><h2>🗝️ Clés de Registre Importantes</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + json.dumps(data.get('registry_keys', {}), indent=2, ensure_ascii=False) + '</pre></div>' if data.get('registry_keys') else ''}

        {'<div class="section"><h2>🔑 Mots de Passe Navigateurs</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('browser_passwords', 'Non sauvegardés')) + '</pre></div>' if data.get('browser_passwords') else ''}

        {'<div class="section"><h2>📁 Taille des Dossiers Utilisateur</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('folder_sizes', 'Non analysé')) + '</pre></div>' if data.get('folder_sizes') else ''}

        {'<div class="section"><h2>🔍 Analyse des Processus Suspects</h2><pre style="background: #fff3cd; padding: 15px; border-radius: 4px; overflow-x: auto; border-left: 4px solid #ffc107;">' + str(data.get('suspicious_processes', 'Non analysé')) + '</pre></div>' if data.get('suspicious_processes') else ''}

        {'<div class="section"><h2>⚙️ Fonctionnalités Windows</h2><pre style="background: #f3f4f6; padding: 15px; border-radius: 4px; overflow-x: auto;">' + str(data.get('windows_features', 'Non sauvegardées')) + '</pre></div>' if data.get('windows_features') else ''}

        {self._format_diagnostic_html(data.get('diagnostic_scan', {})) if data.get('diagnostic_scan') else ''}

        <div class="info-box" style="margin-top: 40px; background: #dcfce7; border-left-color: #16a34a;">
            <strong>✅ Sauvegarde générée avec NiTriTe V20</strong><br>
            Fichier créé le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
        </div>
    </div>
</body>
</html>"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)

    def _export_to_txt(self, data, filepath):
        """Exporter les données en TXT"""
        txt = f"""================================================================================
                    SAUVEGARDE NiTriTe V20
================================================================================

Date: {data.get('date', 'N/A')}
Timestamp: {data.get('timestamp', 'N/A')}
Applications: {data.get('apps_count', 0)}

================================================================================
APPLICATIONS INSTALLÉES ({data.get('apps_count', 0)})
================================================================================

{''.join(f"{i+1}. {app}\n" for i, app in enumerate(data.get('apps', [])))}

"""
        if data.get('network_config'):
            txt += f"""================================================================================
CONFIGURATION RÉSEAU
================================================================================

{data.get('network_config')}

"""
        if data.get('startup_programs'):
            txt += f"""================================================================================
PROGRAMMES AU DÉMARRAGE
================================================================================

{data.get('startup_programs')}

"""
        if data.get('browser_bookmarks'):
            txt += f"""================================================================================
FAVORIS NAVIGATEURS
================================================================================

{json.dumps(data.get('browser_bookmarks'), indent=2, ensure_ascii=False)}

"""
        if data.get('drivers'):
            txt += f"""================================================================================
LISTE DES DRIVERS SYSTÈME
================================================================================

{json.dumps(data.get('drivers'), indent=2, ensure_ascii=False)}

"""
        if data.get('bitlocker_keys'):
            txt += f"""================================================================================
CLÉS DE RÉCUPÉRATION BITLOCKER
================================================================================

{data.get('bitlocker_keys')}

"""
        if data.get('windows_license'):
            txt += f"""================================================================================
LICENCE WINDOWS
================================================================================

{data.get('windows_license')}

"""
        if data.get('office_license'):
            txt += f"""================================================================================
LICENCE MICROSOFT OFFICE
================================================================================

{data.get('office_license')}

"""
        if data.get('registry_keys'):
            txt += f"""================================================================================
CLÉS DE REGISTRE IMPORTANTES
================================================================================

{json.dumps(data.get('registry_keys'), indent=2, ensure_ascii=False)}

"""
        if data.get('browser_passwords'):
            txt += f"""================================================================================
MOTS DE PASSE NAVIGATEURS
================================================================================

{data.get('browser_passwords')}

"""
        if data.get('folder_sizes'):
            txt += f"""================================================================================
TAILLE DES DOSSIERS UTILISATEUR
================================================================================

{data.get('folder_sizes')}

"""
        if data.get('suspicious_processes'):
            txt += f"""================================================================================
ANALYSE DES PROCESSUS SUSPECTS
================================================================================

{data.get('suspicious_processes')}

"""
        if data.get('windows_features'):
            txt += f"""================================================================================
FONCTIONNALITÉS WINDOWS
================================================================================

{data.get('windows_features')}

"""
        # Ajouter le diagnostic scan
        if data.get('diagnostic_scan'):
            txt += self._format_diagnostic_txt(data.get('diagnostic_scan'))

        txt += f"""================================================================================
Sauvegarde générée avec NiTriTe V20
Fichier créé le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
================================================================================
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(txt)

    def _export_to_md(self, data, filepath):
        """Exporter les données en Markdown"""
        md = f"""# 💾 Sauvegarde NiTriTe V20

## 📋 Informations

- **Date:** {data.get('date', 'N/A')}
- **Timestamp:** {data.get('timestamp', 'N/A')}
- **Applications:** {data.get('apps_count', 0)}

---

## 📱 Applications Installées ({data.get('apps_count', 0)})

| # | Application |
|---|------------|
{''.join(f"| {i+1} | `{app}` |\n" for i, app in enumerate(data.get('apps', [])))}

"""
        if data.get('network_config'):
            md += f"""---

## 🌐 Configuration Réseau

```
{data.get('network_config')}
```

"""
        if data.get('startup_programs'):
            md += f"""---

## 🚀 Programmes au Démarrage

```json
{data.get('startup_programs')}
```

"""
        if data.get('browser_bookmarks'):
            md += f"""---

## 🔖 Favoris Navigateurs

```json
{json.dumps(data.get('browser_bookmarks'), indent=2, ensure_ascii=False)}
```

"""
        if data.get('drivers'):
            md += f"""---

## 🔧 Liste des Drivers Système

```json
{json.dumps(data.get('drivers'), indent=2, ensure_ascii=False)}
```

"""
        if data.get('bitlocker_keys'):
            md += f"""---

## 🔐 Clés de Récupération BitLocker

```
{data.get('bitlocker_keys')}
```

"""
        if data.get('windows_license'):
            md += f"""---

## 🪟 Licence Windows

```
{data.get('windows_license')}
```

"""
        if data.get('office_license'):
            md += f"""---

## 📄 Licence Microsoft Office

```
{data.get('office_license')}
```

"""
        if data.get('registry_keys'):
            md += f"""---

## 🗝️ Clés de Registre Importantes

```json
{json.dumps(data.get('registry_keys'), indent=2, ensure_ascii=False)}
```

"""
        if data.get('browser_passwords'):
            md += f"""---

## 🔑 Mots de Passe Navigateurs

```
{data.get('browser_passwords')}
```

"""
        if data.get('folder_sizes'):
            md += f"""---

## 📁 Taille des Dossiers Utilisateur

```
{data.get('folder_sizes')}
```

"""
        if data.get('suspicious_processes'):
            md += f"""---

## 🔍 Analyse des Processus Suspects

```
{data.get('suspicious_processes')}
```

"""
        if data.get('windows_features'):
            md += f"""---

## ⚙️ Fonctionnalités Windows

```
{data.get('windows_features')}
```

"""
        # Ajouter le diagnostic scan
        if data.get('diagnostic_scan'):
            md += "---\n"
            md += self._format_diagnostic_md(data.get('diagnostic_scan'))

        md += f"""---

*✅ Sauvegarde générée avec NiTriTe V20*
*Fichier créé le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

    def _restore_backup(self, filepath):
        """Restaurer sauvegarde"""
        print(f" Restauration de {filepath.name}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f" Backup chargé: {data.get('apps_count', 0)} apps")
            # TODO: Implémenter restauration réelle
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _delete_backup(self, filepath):
        """Supprimer sauvegarde"""
        try:
            filepath.unlink()
            print(f" Suppression de {filepath.name}")
            self._refresh_backups_list()
        except Exception as e:
            print(f" Erreur: {e}")


class DiagnosticPage(ctk.CTkFrame):
    """Page Diagnostic avec vraie détection psutil"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        try:
            # OPTIMISATION: Initialisation rapide avec chargement asynchrone
            self.system_info = None
            self.cpu_card = None
            self.ram_card = None
            self.update_timer = None
            self.loading_label = None

            # Afficher écran de chargement
            self._show_loading_screen()

            # Charger les infos système dans un thread séparé (évite freeze)
            import threading
            threading.Thread(target=self._load_system_info_async, daemon=True).start()

        except Exception as e:
            print(f"ERREUR CRITIQUE DiagnosticPage.__init__: {e}")
            import traceback
            traceback.print_exc()

            # Afficher l'erreur à l'utilisateur
            error_label = ctk.CTkLabel(
                self,
                text=f"Erreur lors du chargement de la page Diagnostic:\n{str(e)}\n\nVoir console pour détails",
                font=(DesignTokens.FONT_FAMILY, 14),
                text_color="red",
                wraplength=600
            )
            error_label.pack(padx=20, pady=20)

    def _show_loading_screen(self):
        """Afficher un écran de chargement pendant la collecte des infos"""
        loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        loading_frame.pack(expand=True, fill=tk.BOTH)

        # Icône et texte de chargement
        self.loading_label = ctk.CTkLabel(
            loading_frame,
            text="🔍 Chargement des informations système...\n\nCollecte des données : CPU, RAM, GPU, Disques...\nCela peut prendre 1-2 secondes.",
            font=(DesignTokens.FONT_FAMILY, 16),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        self.loading_label.pack(expand=True)

    def _load_system_info_async(self):
        """Charger les infos système dans un thread séparé (évite freeze UI)"""
        try:
            # Collecter les infos (opération lourde)
            self.system_info = self._get_system_info()

            # Une fois terminé, construire l'interface dans le thread principal
            self.after(0, self._build_ui_after_loading)

        except Exception as e:
            print(f"Erreur chargement système: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self._show_error(str(e)))

    def _build_ui_after_loading(self):
        """Construire l'interface après le chargement des données"""
        try:
            # Supprimer l'écran de chargement
            if self.loading_label:
                self.loading_label.master.destroy()

            # Construire l'interface
            self._create_header()
            self._create_content()

            # Démarrer la mise à jour en temps réel
            if PSUTIL_AVAILABLE:
                self._start_realtime_updates()

        except Exception as e:
            print(f"Erreur construction UI: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(str(e))

    def _show_error(self, error_msg):
        """Afficher une erreur"""
        error_label = ctk.CTkLabel(
            self,
            text=f"❌ Erreur lors du chargement:\n{error_msg}\n\nVoir console pour détails",
            font=(DesignTokens.FONT_FAMILY, 14),
            text_color="red",
            wraplength=600
        )
        error_label.pack(padx=20, pady=20)
    
    def _get_ram_type_name(self, memory_type_code):
        """Convertir le code WMI MemoryType en nom lisible (DDR3, DDR4, DDR5)"""
        memory_types = {
            0: "Unknown",
            1: "Other",
            2: "DRAM",
            3: "Synchronous DRAM",
            4: "Cache DRAM",
            5: "EDO",
            6: "EDRAM",
            7: "VRAM",
            8: "SRAM",
            9: "💾 RAM",
            10: "ROM",
            11: "Flash",
            12: "EEPROM",
            13: "FEPROM",
            14: "EPROM",
            15: "CDRAM",
            16: "3DRAM",
            17: "SDRAM",
            18: "SGRAM",
            19: "RDRAM",
            20: "DDR",
            21: "DDR2",
            22: "DDR2 FB-DIMM",
            24: "DDR3",
            25: "FBD2",
            26: "DDR4",
            27: "LPDDR",
            28: "LPDDR2",
            29: "LPDDR3",
            30: "LPDDR4",
            34: "DDR5",
            35: "LPDDR5"
        }
        return memory_types.get(memory_type_code, f"Unknown ({memory_type_code})")

    def _get_system_info(self):
        """Obtenir vraies informations système avec détails matériels"""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

        # Obtenir noms exacts des composants via WMI (Windows uniquement)
        try:
            import wmi
            w = wmi.WMI()

            # CPU - Nom exact
            for cpu in w.Win32_Processor():
                info["cpu_name"] = cpu.Name.strip()
                info["cpu_manufacturer"] = cpu.Manufacturer
                info["cpu_cores"] = cpu.NumberOfCores
                info["cpu_threads"] = cpu.NumberOfLogicalProcessors
                info["cpu_max_speed"] = cpu.MaxClockSpeed  # MHz
                break

            # RAM - Modules détaillés avec génération DDR (utilise SMBIOSMemoryType pour meilleure détection)
            info["ram_modules"] = []
            total_ram_gb = 0
            for mem in w.Win32_PhysicalMemory():
                capacity_gb = int(mem.Capacity) / (1024**3)
                total_ram_gb += capacity_gb

                # Essayer d'abord SMBIOSMemoryType (plus fiable), puis MemoryType en fallback
                memory_type_code = 0
                if hasattr(mem, 'SMBIOSMemoryType') and mem.SMBIOSMemoryType:
                    memory_type_code = mem.SMBIOSMemoryType
                elif mem.MemoryType:
                    memory_type_code = mem.MemoryType

                # Si toujours 0, essayer de deviner selon la vitesse
                if memory_type_code == 0 or memory_type_code == 2:  # Unknown ou DRAM générique
                    speed = mem.Speed if mem.Speed else 0
                    if speed >= 4800:
                        memory_type_code = 34  # DDR5
                    elif speed >= 2133:
                        memory_type_code = 26  # DDR4
                    elif speed >= 800:
                        memory_type_code = 24  # DDR3
                    elif speed > 0:
                        memory_type_code = 21  # DDR2

                memory_type_name = self._get_ram_type_name(memory_type_code)

                info["ram_modules"].append({
                    "manufacturer": mem.Manufacturer.strip() if mem.Manufacturer else "Unknown",
                    "capacity_gb": capacity_gb,
                    "speed_mhz": mem.Speed if mem.Speed else 0,
                    "type_code": memory_type_code,
                    "type_name": memory_type_name,
                    "form_factor": mem.FormFactor if mem.FormFactor else 0,
                    "device_locator": mem.DeviceLocator if mem.DeviceLocator else "Unknown"
                })
            info["ram_total_gb"] = total_ram_gb

            # Déterminer type RAM dominant (le plus courant)
            if info["ram_modules"]:
                from collections import Counter
                type_counts = Counter(m["type_name"] for m in info["ram_modules"])
                info["ram_type_dominant"] = type_counts.most_common(1)[0][0]
                speed_values = [m["speed_mhz"] for m in info["ram_modules"] if m["speed_mhz"] > 0]
                info["ram_speed_avg"] = sum(speed_values) / len(speed_values) if speed_values else 0
            
            # Carte mère
            for board in w.Win32_BaseBoard():
                info["motherboard_manufacturer"] = board.Manufacturer
                info["motherboard_product"] = board.Product
                break
            
            # GPU - Cartes graphiques
            info["gpus"] = []
            for gpu in w.Win32_VideoController():
                info["gpus"].append({
                    "name": gpu.Name,
                    "ram_bytes": gpu.AdapterRAM if gpu.AdapterRAM else 0,
                    "driver_version": gpu.DriverVersion if gpu.DriverVersion else "N/A"
                })
            
            # Disques - Modèles exacts
            info["storage_devices"] = []
            for disk in w.Win32_DiskDrive():
                size_gb = int(disk.Size) / (1024**3) if disk.Size else 0
                info["storage_devices"].append({
                    "model": disk.Model if disk.Model else "Unknown",
                    "size_gb": size_gb,
                    "interface": disk.InterfaceType if disk.InterfaceType else "Unknown"
                })
            
        except ImportError:
            print(" Module wmi non disponible - installation: pip install wmi")
            # Fallback sans WMI
            info["cpu_name"] = platform.processor()
        except Exception as e:
            print(f" Erreur WMI: {e}")
        
        # Données psutil (usage actuel)
        if PSUTIL_AVAILABLE:
            # CPU usage - OPTIMISÉ: interval=0.1 au lieu de 1 (10x plus rapide!)
            info["cpu_count"] = psutil.cpu_count(logical=False)
            info["cpu_threads"] = psutil.cpu_count(logical=True)
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)  # OPTIMISATION: 0.1s au lieu de 1s
            info["cpu_freq"] = psutil.cpu_freq()
            
            # RAM usage
            mem = psutil.virtual_memory()
            info["ram_total"] = mem.total / (1024**3)  # GB
            info["ram_used"] = mem.used / (1024**3)
            info["ram_percent"] = mem.percent
            
            # Partitions disques
            info["disks"] = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info["disks"].append({
                        "mount": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total / (1024**3),
                        "used": usage.used / (1024**3),
                        "percent": usage.percent
                    })
                except:
                    continue
            
            # Réseau
            net = psutil.net_io_counters()
            info["net_sent"] = net.bytes_sent / (1024**2)  # MB
            info["net_recv"] = net.bytes_recv / (1024**2)
        
        return info
    
    def _create_header(self):
        """Header"""
        header = ModernCard(self)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)
        
        title_frame = SectionHeader(container, text="🔍 Diagnostic")
        title_frame.pack(side=tk.LEFT)

        # Boutons d'action
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(side=tk.RIGHT)

        ModernButton(
            btn_frame,
            text="💾 Exporter",
            variant="outlined",
            command=self._export_pc_info
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            btn_frame,
            text="🔬 Analyser",
            variant="outlined",
            command=self._run_diagnostic
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            btn_frame,
            text="🔍 Scan Total",
            variant="filled",
            command=self._perform_full_system_scan
        ).pack(side=tk.LEFT)
    
    def _create_content(self):
        """Contenu"""
        # Stats système (avec mise à jour temps réel)
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        cpu_val = f"{self.system_info.get('cpu_percent', 0):.1f}%" if PSUTIL_AVAILABLE else "N/A"
        self.cpu_card = ModernStatsCard(
            stats_frame,
            "🖥️ CPU",
            cpu_val,
            "",
            DesignTokens.INFO
        )
        self.cpu_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        if PSUTIL_AVAILABLE:
            ram_val = f"{self.system_info['ram_used']:.1f}/{self.system_info['ram_total']:.1f} GB"
        else:
            ram_val = "N/A"
        self.ram_card = ModernStatsCard(
            stats_frame,
            "💾 RAM",
            ram_val,
            "",
            DesignTokens.SUCCESS
        )
        self.ram_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        if PSUTIL_AVAILABLE and self.system_info.get('disks'):
            disk = self.system_info['disks'][0]
            disk_val = f"{disk['used']:.0f}/{disk['total']:.0f} GB"
        else:
            disk_val = "N/A"
        ModernStatsCard(
            stats_frame,
            "💿 Disque",
            disk_val,
            "",
            DesignTokens.WARNING
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        net_val = "OK" if PSUTIL_AVAILABLE else "N/A"
        ModernStatsCard(
            stats_frame,
            "🌐 Réseau",
            net_val,
            "",
            DesignTokens.SUCCESS
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Résultats diagnostic
        scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
        scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sections avec vraies données
        self._create_system_section(scroll)
        self._create_hardware_section(scroll)
        self._create_storage_section(scroll)
        self._create_network_section(scroll)
        self._create_tools_section(scroll)
    
    def _create_system_section(self, parent):
        """Section système"""
        items = [
            ("🪟 OS", f"{self.system_info['os']} {self.system_info['os_release']}", ""),
            ("📄 Version", self.system_info['os_version'][:50], ""),
            ("⚙️ Architecture", self.system_info['architecture'], ""),
            ("🖥️ Hostname", self.system_info['hostname'], ""),
        ]

        # Carte mère si disponible
        if 'motherboard_product' in self.system_info:
            mb_info = f"{self.system_info.get('motherboard_manufacturer', 'N/A')} {self.system_info.get('motherboard_product', 'N/A')}"
            items.append(("🔧 Carte mère", mb_info, ""))

        self._create_diagnostic_section(parent, "💻 Système", items)
    
    def _create_hardware_section(self, parent):
        """Section matériel avec noms exacts"""
        items = []
        
        # CPU - Nom exact si disponible via WMI
        if 'cpu_name' in self.system_info:
            cpu_name = self.system_info['cpu_name']
            cpu_details = f"{self.system_info.get('cpu_cores', '?')} cores / {self.system_info.get('cpu_threads', '?')} threads"
            if 'cpu_max_speed' in self.system_info:
                cpu_details += f" @ {self.system_info['cpu_max_speed']} MHz"
            items.append(("🖥️ Processeur", cpu_name, ""))
            items.append(("⚙️ Configuration CPU", cpu_details, ""))
            
            if PSUTIL_AVAILABLE:
                items.append(("📊 Utilisation CPU", f"{self.system_info.get('cpu_percent', 0):.1f}%", ""))
        else:
            # Fallback
            if PSUTIL_AVAILABLE:
                cpu_count = self.system_info.get('cpu_count', '?')
                cpu_threads = self.system_info.get('cpu_threads', '?')
                cpu_info = f"{cpu_count} cores / {cpu_threads} threads"
                items.append(("🖥️ Processeur", self.system_info.get('processor', 'N/A'), ""))
                items.append(("Configuration", cpu_info, ""))
            else:
                items.append(("🖥️ Processeur", self.system_info.get('processor', 'N/A'), ""))
        
        # RAM - Modules détaillés si disponibles
        if 'ram_modules' in self.system_info and self.system_info['ram_modules']:
            total_ram = self.system_info.get('ram_total_gb', 0)
            ram_type = self.system_info.get('ram_type_dominant', 'Unknown')
            ram_speed = self.system_info.get('ram_speed_avg', 0)

            # Ligne 1: Total RAM avec type et fréquence (génération bien visible)
            if ram_speed > 0:
                ram_summary = f"{total_ram:.1f} GB de RAM {ram_type} @ {ram_speed:.0f} MHz"
            else:
                ram_summary = f"{total_ram:.1f} GB de RAM {ram_type}"
            items.append(("💾 RAM Totale", ram_summary, ""))

            # Ligne supplémentaire pour type/génération de RAM (plus visible)
            items.append(("💾 Génération RAM", f"{ram_type}", ""))

            # Afficher chaque module avec détails complets
            for i, module in enumerate(self.system_info['ram_modules'][:4], 1):  # Max 4 modules
                module_info = f"{module['manufacturer']} {module['capacity_gb']:.0f}GB {module['type_name']}"
                if module['speed_mhz'] > 0:
                    module_info += f" @ {module['speed_mhz']}MHz"
                if module['device_locator'] != "Unknown":
                    module_info += f" ({module['device_locator']})"
                items.append((f"💾 Module {i}", module_info, ""))

            if PSUTIL_AVAILABLE:
                ram_used = self.system_info.get('ram_used', 0)
                ram_percent = self.system_info.get('ram_percent', 0)
                ram_usage = f"{ram_used:.1f} GB utilisés ({ram_percent:.1f}%)"
                items.append(("📊 Utilisation RAM", ram_usage, ""))
        else:
            # Fallback
            if PSUTIL_AVAILABLE:
                ram_total = self.system_info.get('ram_total', 0)
                ram_percent = self.system_info.get('ram_percent', 0)
                ram_info = f"{ram_total:.1f} GB ({ram_percent:.1f}% utilisés)"
                items.append(("💾 RAM", ram_info, ""))
            else:
                items.append(("💾 RAM", "psutil requis", ""))
        
        # GPU - Cartes graphiques
        if 'gpus' in self.system_info and self.system_info['gpus']:
            for i, gpu in enumerate(self.system_info['gpus'][:3], 1):  # Max 3 GPUs
                gpu_name = gpu['name']
                gpu_ram = gpu['ram_bytes'] / (1024**3) if gpu['ram_bytes'] > 0 else 0
                if gpu_ram > 0:
                    gpu_info = f"{gpu_name} ({gpu_ram:.0f} GB VRAM)"
                else:
                    gpu_info = gpu_name
                items.append((f"🎮 GPU {i}" if len(self.system_info['gpus']) > 1 else "🎮 GPU", gpu_info, ""))
        
        self._create_diagnostic_section(parent, "🔧 Matériel", items)
    
    def _create_storage_section(self, parent):
        """Section stockage avec modèles de disques"""
        items = []

        # Disques physiques avec modèles
        if 'storage_devices' in self.system_info and self.system_info['storage_devices']:
            for i, device in enumerate(self.system_info['storage_devices'], 1):
                device_info = f"{device['model']} - {device['size_gb']:.0f} GB ({device['interface']})"
                items.append((f"💿 Disque {i}", device_info, ""))

        # Partitions avec usage
        if PSUTIL_AVAILABLE and self.system_info.get('disks'):
            if items:  # Si on a déjà des disques physiques
                items.append(("", "--- Partitions ---", ""))  # Séparateur
            for disk in self.system_info['disks']:
                try:
                    percent = float(disk.get('percent', 0))
                    status = "✅" if percent < 80 else "⚠️"
                    used = float(disk.get('used', 0))
                    total = float(disk.get('total', 0))
                    items.append((
                        f"📂 Partition {disk['mount']}",
                        f"{used:.1f} / {total:.1f} GB ({percent:.1f}%) - {disk.get('fstype', 'N/A')}",
                        status
                    ))
                except (TypeError, ValueError, KeyError):
                    continue
        elif not items:
            items = [("💿 Disques", "Informations non disponibles", "")]

        self._create_diagnostic_section(parent, "💿 Stockage", items)
    
    def _create_network_section(self, parent):
        """Section réseau avec détails complets (portable - sans netifaces)"""
        items = []

        if PSUTIL_AVAILABLE:
            # Données envoyées/reçues
            items.append(("⬆️ Données envoyées", f"{self.system_info['net_sent']:.1f} MB", ""))
            items.append(("⬇️ Données reçues", f"{self.system_info['net_recv']:.1f} MB", ""))

            # Informations réseau détaillées via psutil (portable)
            try:
                import socket

                # Nom d'hôte
                hostname = socket.gethostname()
                items.append(("🖥️ Nom d'hôte", hostname, ""))

                # Utiliser psutil.net_if_addrs() au lieu de netifaces (portable)
                net_if_addrs = psutil.net_if_addrs()

                for iface_name, addrs in net_if_addrs.items():
                    for addr in addrs:
                        # IPv4
                        if addr.family == socket.AF_INET:
                            if not addr.address.startswith('127.'):
                                netmask = addr.netmask if addr.netmask else 'N/A'
                                items.append((f"🌐 IPv4 ({iface_name})", f"{addr.address} / {netmask}", ""))

                        # IPv6
                        elif addr.family == socket.AF_INET6:
                            if not addr.address.startswith('::1') and not addr.address.startswith('fe80'):
                                items.append((f"🌍 IPv6 ({iface_name})", addr.address.split('%')[0], ""))

                # Obtenir la passerelle via ipconfig (Windows uniquement - portable)
                if platform.system() == "Windows":
                    try:
                        import subprocess
                        result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5, encoding='utf-8', errors='ignore')
                        output = result.stdout

                        # Parser la sortie pour trouver la passerelle par défaut
                        for line in output.split('\n'):
                            if 'Passerelle par défaut' in line or 'Default Gateway' in line:
                                gateway = line.split(':')[-1].strip()
                                if gateway and gateway != '' and not gateway.startswith('fe80'):
                                    items.append(("🔌 Passerelle par défaut", gateway, ""))
                                    break
                    except Exception as e:
                        pass  # Ignorer les erreurs de parsing

            except Exception as e:
                items.append(("❌ Erreur réseau", str(e)[:50], ""))
        else:
            items = [("🌐 Réseau", "psutil requis", "")]

        # Créer la section
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        # Header avec icône colorée
        header_container = ctk.CTkFrame(card, fg_color="transparent")
        header_container.pack(fill=tk.X)

        header_left = ctk.CTkFrame(header_container, fg_color="transparent")
        header_left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Utiliser SectionHeader pour le titre avec icône colorée
        header_section = SectionHeader(header_left, text="🌐 Réseau")
        header_section.pack(fill=tk.X)

        # Boutons à droite
        buttons_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        buttons_frame.pack(side=tk.RIGHT, padx=20, pady=15)

        # Bouton Speed Test CLI
        ModernButton(
            buttons_frame,
            text="⚡ Speedtest CLI",
            variant="filled",
            size="sm",
            command=self._launch_speedtest_portable
        ).pack(side=tk.RIGHT)

        # Bouton Speed Test Web
        ModernButton(
            buttons_frame,
            text="🌐 Speedtest Web",
            variant="outlined",
            size="sm",
            command=self._launch_speedtest_web
        ).pack(side=tk.RIGHT, padx=(0, 5))

        # Items
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 20))

        for label, value, status in items:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill=tk.X, pady=2)

            status_label = ctk.CTkLabel(
                row,
                text=status,
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                width=30
            )
            status_label.pack(side=tk.LEFT)

            label_widget = ctk.CTkLabel(
                row,
                text=label,
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD, "bold"),
                text_color=DesignTokens.TEXT_PRIMARY,
                anchor="w",
                width=200
            )
            label_widget.pack(side=tk.LEFT, padx=10)

            value_widget = ctk.CTkLabel(
                row,
                text=str(value),
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                text_color=DesignTokens.TEXT_SECONDARY,
                anchor="w"
            )
            value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_tools_section(self, parent):
        """Section outils de diagnostic avancés"""
        self.tools_card = ModernCard(parent)
        self.tools_card.pack(fill=tk.X, pady=10)

        # Header avec icône colorée et bouton
        header_main = ctk.CTkFrame(self.tools_card, fg_color="transparent")
        header_main.pack(fill=tk.X)

        header_left = ctk.CTkFrame(header_main, fg_color="transparent")
        header_left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Utiliser SectionHeader pour le titre avec icône colorée
        header_section = SectionHeader(header_left, text="🔧 Outils de Diagnostic")
        header_section.pack(fill=tk.X)

        # Bouton pour ajouter une app personnalisée
        button_frame = ctk.CTkFrame(header_main, fg_color="transparent")
        button_frame.pack(side=tk.RIGHT, padx=20, pady=15)

        ModernButton(
            button_frame,
            text="➕ Ajouter Application",
            variant="outlined",
            size="sm",
            command=self._add_custom_tool_dialog
        ).pack()

        # Barre de recherche
        search_frame = ctk.CTkFrame(self.tools_card, fg_color="transparent")
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        search_bar = ModernSearchBar(
            search_frame,
            placeholder="Rechercher un outil...",
            on_search=self._on_search_tools
        )
        search_bar.pack(fill=tk.X)

        # Boutons d'outils
        self.tools_frame = ctk.CTkFrame(self.tools_card, fg_color="transparent")
        self.tools_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Stocker les outils pour le filtrage
        self.all_tools = []
        self._populate_tools()

    def _populate_tools(self):
        """Peupler la liste des outils (built-in + custom)"""
        # Outils intégrés
        self.all_tools = [
            {"text": "⌨️ Test Clavier AZERTY", "command": self._launch_keyboard_test},
            {"text": "💿 CrystalDiskInfo", "command": self._launch_crystaldiskinfo},
            {"text": "🌡️ OCCT (Temp & Stress)", "command": self._launch_occt},
            {"text": "🔋 Test Batterie OrdiPlus", "command": self._test_battery},
            {"text": "🔋 Test Batterie NiTrite", "command": self._test_battery_nitrite},
            {"text": "🚀 Autoruns", "command": self._launch_autoruns},
            {"text": "🛡️ Malwarebytes Portable", "command": self._launch_malwarebytes},
            {"text": "🛡️ Spybot Search & Destroy", "command": self._launch_spybot},
            {"text": "🛡️ AdwCleaner Portable", "command": self._launch_adwcleaner},
            {"text": "🧹 Wise Disk Cleaner", "command": self._launch_wisediskcleaner},
            {"text": "📊 HWMonitor", "command": self._launch_hwmonitor},
            {"text": "📊 HWinfo", "command": self._launch_hwinfo},
            {"text": "⚡ CrystalDiskMark", "command": self._launch_crystaldiskmark},
            {"text": "🖥️ CPU-Z", "command": self._launch_cpuz},
            {"text": "🎮 GPU-Z", "command": self._launch_gpuz},
            {"text": "🔧 Wise Care 365", "command": self._launch_wisecare365},
            {"text": "🔍 UserDiag (Diagnostic Complet)", "command": self._launch_userdiag},
            {"text": "🤖 BenchMaster.AI (Sonde Diagnostic)", "command": self._launch_benchmaster},
            {"text": "🔑 Activation Windows/Office", "command": self._activate_windows_office},
            {"text": "⚙️ MSCONFIG", "command": lambda: self._execute_tool("MSCONFIG", "msconfig")},
            {"text": "📋 Gestionnaire des Tâches", "command": lambda: self._execute_tool("Gestionnaire des tâches", "taskmgr")},
            {"text": "ℹ MSINFO", "command": lambda: self._execute_tool("MSINFO", "msinfo32")},
            {"text": "📁 Dossier Temp", "command": self._open_temp_folder},
            {"text": "📁 AppData Local", "command": self._open_appdata_local},
            {"text": "🪟 Version Windows", "command": lambda: self._execute_tool("Version Windows", "winver")},
            {"text": "📥 Tout Mettre à Jour", "command": self._update_all_apps},
            {"text": "🎮 Drivers NVIDIA", "command": self._update_nvidia_drivers},
            {"text": "🎮 Drivers AMD", "command": self._update_amd_drivers},
            {"text": "🔧 Réparer Image Windows", "command": self._repair_windows_image},
            {"text": "👤 Propriétés Utilisateur", "command": self._open_user_properties},
            {"text": "💻 Système", "command": lambda: self._execute_tool("Système", "sysdm.cpl")},
            {"text": "🔍 CHKDSK Complet", "command": self._run_chkdsk},
        ]

        # Charger et ajouter les outils personnalisés
        custom_tools = self._load_custom_tools()
        for tool in custom_tools:
            if tool.get("enabled", True):
                self.all_tools.append({
                    "text": f"{tool['emoji']} {tool['name']}",
                    "command": lambda t=tool: self._launch_custom_tool(t),
                    "custom": True,
                    "tool_id": tool['id']
                })

        self._render_tools()

    def _on_search_tools(self, search_text):
        """Callback quand l'utilisateur tape dans la barre de recherche"""
        self._filter_tools(search_text)

    def _filter_tools(self, search_text=""):
        """Filtrer les outils selon la recherche"""
        search_text = search_text.lower()

        if not search_text:
            filtered_tools = self.all_tools
        else:
            filtered_tools = [
                tool for tool in self.all_tools
                if search_text in tool["text"].lower()
            ]

        self._render_tools(filtered_tools)

    def _render_tools(self, tools=None):
        """Afficher les outils (tous ou filtrés)"""
        try:
            # Supprimer les widgets existants
            for widget in self.tools_frame.winfo_children():
                widget.destroy()

            if tools is None:
                tools = self.all_tools

            if not tools:
                # Message si aucun outil trouvé
                no_result = ctk.CTkLabel(
                    self.tools_frame,
                    text="Aucun outil trouvé",
                    font=(DesignTokens.FONT_FAMILY, 14),
                    text_color=DesignTokens.TEXT_SECONDARY
                )
                no_result.pack(pady=20)
                return

            # Créer les lignes avec 3 boutons par ligne
            current_row = None
            for i, tool in enumerate(tools):
                if i % 3 == 0:
                    current_row = ctk.CTkFrame(self.tools_frame, fg_color="transparent")
                    current_row.pack(fill=tk.X, pady=5)

                # Si c'est un outil personnalisé, ajouter un conteneur avec bouton supprimer
                if tool.get("custom", False):
                    btn_container = ctk.CTkFrame(current_row, fg_color="transparent")
                    btn_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

                    # Bouton principal de l'outil
                    main_btn = ModernButton(
                        btn_container,
                        text=tool["text"],
                        variant="outlined",
                        size="md",
                        command=tool["command"]
                    )
                    main_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

                    # Petit bouton supprimer
                    remove_btn = ctk.CTkButton(
                        btn_container,
                        text="❌",
                        width=35,
                        height=35,
                        fg_color="transparent",
                        hover_color=DesignTokens.ERROR,
                        text_color=DesignTokens.ERROR,
                        font=(DesignTokens.FONT_FAMILY, 16),
                        command=lambda tid=tool['tool_id']: self._remove_custom_tool(tid)
                    )
                    remove_btn.pack(side=tk.RIGHT, padx=(5, 0))
                else:
                    # Outil intégré classique
                    ModernButton(
                        current_row,
                        text=tool["text"],
                        variant="outlined",
                        size="md",
                        command=tool["command"]
                    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        except Exception as e:
            print(f"ERREUR _render_tools: {e}")
            import traceback
            traceback.print_exc()

    def _start_realtime_updates(self):
        """Démarrer les mises à jour en temps réel des statistiques"""
        self._update_stats()

    def _update_stats(self):
        """Mettre à jour les statistiques CPU et RAM en temps réel"""
        try:
            if PSUTIL_AVAILABLE and self.cpu_card and self.ram_card:
                # Mise à jour CPU
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.cpu_card.update_value(f"{cpu_percent:.1f}%")

                # Mise à jour RAM
                ram = psutil.virtual_memory()
                ram_used = ram.used / (1024**3)
                ram_total = ram.total / (1024**3)
                self.ram_card.update_value(f"{ram_used:.1f}/{ram_total:.1f} GB")

                # Planifier la prochaine mise à jour dans 2 secondes
                self.update_timer = self.after(2000, self._update_stats)
        except Exception as e:
            print(f"Erreur mise à jour stats: {e}")

    def destroy(self):
        """Nettoyer les timers quand la page est détruite"""
        if self.update_timer:
            self.after_cancel(self.update_timer)
        super().destroy()

    def _run_speed_test_OLD(self):
        """Exécuter un test de vitesse intégré (ANCIENNE VERSION - BACKUP)"""
        from tkinter import messagebox
        import threading

        # Créer fenêtre de test
        test_window = ctk.CTkToplevel(self)
        test_window.title(" Speed Test - Test de connexion")
        test_window.geometry("600x500")
        test_window.resizable(False, False)

        # Centrer
        test_window.update_idletasks()
        x = (test_window.winfo_screenwidth() // 2) - (300)
        y = (test_window.winfo_screenheight() // 2) - (250)
        test_window.geometry(f"600x500+{x}+{y}")

        # Contenu
        content = ctk.CTkFrame(test_window, fg_color=DesignTokens.BG_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(
            content,
            text="🚀 Test de Vitesse de Connexion",
            font=(DesignTokens.FONT_FAMILY, 24, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY
        )
        header.pack(pady=(0, 20))

        # Status
        status_label = ctk.CTkLabel(
            content,
            text="Initialisation...",
            font=(DesignTokens.FONT_FAMILY, 16),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        status_label.pack(pady=10)

        # Progress
        progress = ctk.CTkProgressBar(
            content,
            width=500,
            height=25,
            corner_radius=12
        )
        progress.pack(pady=20)
        progress.set(0)

        # Résultats
        results_frame = ctk.CTkFrame(content, fg_color=DesignTokens.BG_ELEVATED, corner_radius=DesignTokens.RADIUS_LG)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        def run_test():
            try:
                status_label.configure(text="Vérification du module speedtest...")
                progress.set(0.1)
                test_window.update()

                try:
                    import speedtest
                except ImportError:
                    status_label.configure(text=" Module speedtest-cli manquant")
                    messagebox.showwarning(
                        "Module manquant",
                        "Le module speedtest-cli n'est pas installé.\n\n"
                        "Installation requise:\n"
                        "pip install speedtest-cli"
                    )
                    return

                status_label.configure(text=" Recherche du meilleur serveur...")
                progress.set(0.2)
                test_window.update()

                st = speedtest.Speedtest()
                st.get_best_server()

                status_label.configure(text=" Test de téléchargement...")
                progress.set(0.4)
                test_window.update()

                download_speed = st.download() / 1_000_000  # Convertir en Mbps

                status_label.configure(text=" Test d'envoi...")
                progress.set(0.7)
                test_window.update()

                upload_speed = st.upload() / 1_000_000  # Convertir en Mbps

                status_label.configure(text=" Test de ping...")
                progress.set(0.9)
                test_window.update()

                results = st.results.dict()
                ping = results['ping']
                server = results['server']

                progress.set(1.0)
                status_label.configure(text=" Test terminé!")

                # Afficher les résultats
                results_text = f"""
 RÉSULTATS DU TEST DE VITESSE

 Téléchargement: {download_speed:.2f} Mbps
 Envoi: {upload_speed:.2f} Mbps
 Ping: {ping:.0f} ms

 Serveur: {server['sponsor']}
 Localisation: {server['name']}, {server['country']}
 Hébergeur: {server['host']}

 Évaluation:
"""
                if download_speed > 100:
                    results_text += " Excellente connexion !"
                elif download_speed > 50:
                    results_text += " Bonne connexion"
                elif download_speed > 10:
                    results_text += " Connexion correcte"
                else:
                    results_text += " Connexion lente"

                result_label = ctk.CTkLabel(
                    results_frame,
                    text=results_text,
                    font=(DesignTokens.FONT_FAMILY, 14),
                    text_color=DesignTokens.TEXT_PRIMARY,
                    justify="left"
                )
                result_label.pack(padx=20, pady=20)

            except Exception as e:
                status_label.configure(text=f" Erreur: {str(e)[:50]}")
                messagebox.showerror(
                    "Erreur Speed Test",
                    f"Impossible d'exécuter le test de vitesse:\n\n{str(e)}"
                )

        # Bouton fermer
        close_btn = ModernButton(
            content,
            text="✖️ Fermer",
            variant="outlined",
            command=test_window.destroy
        )
        close_btn.pack(pady=10)

        # Lancer le test dans un thread
        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()

    def _launch_crystaldiskinfo(self):
        """Lancer CrystalDiskInfo portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()
            cdi_dir = os.path.join(tools_dir, "CrystalDiskInfo")
            os.makedirs(cdi_dir, exist_ok=True)

            # Chercher l'exécutable (nom peut varier)
            cdi_exe = None
            if os.path.exists(cdi_dir):
                for file in os.listdir(cdi_dir):
                    if file.endswith('.exe') and 'DiskInfo' in file and '64' in file:
                        cdi_exe = os.path.join(cdi_dir, file)
                        break

            # Vérifier si déjà téléchargé
            if not cdi_exe or not os.path.exists(cdi_exe):
                response = messagebox.askyesno(
                    "Télécharger CrystalDiskInfo",
                    "CrystalDiskInfo n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~6 MB, version portable, téléchargement unique)",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL CrystalDiskInfo Portable (lien direct depuis le site officiel)
                # Version portable Shizuku Edition (plus jolie interface)
                url = "https://sourceforge.net/projects/crystaldiskinfo/files/latest/download"
                zip_path = os.path.join(tools_dir, "cdi.zip")

                # Télécharger
                print(f" Téléchargement de CrystalDiskInfo...")
                try:
                    urllib.request.urlretrieve(url, zip_path)

                    # Extraire
                    print(f" Extraction...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(cdi_dir)

                    # Nettoyer
                    os.remove(zip_path)
                    print(f" CrystalDiskInfo installé dans: {cdi_dir}")

                    # Rechercher l'exécutable après extraction
                    cdi_exe = None
                    for file in os.listdir(cdi_dir):
                        if file.endswith('.exe') and 'DiskInfo' in file and '64' in file:
                            cdi_exe = os.path.join(cdi_dir, file)
                            break

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger CrystalDiskInfo:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://crystalmark.info/en/software/crystaldiskinfo/\n\n"
                        f"Et placez les fichiers dans:\n{cdi_dir}"
                    )
                    return

            # Lancer
            if cdi_exe and os.path.exists(cdi_exe):
                subprocess.Popen([cdi_exe], shell=True)
                messagebox.showinfo(
                    "CrystalDiskInfo",
                    f"CrystalDiskInfo lancé!\n\n"
                    f"Emplacement: {cdi_exe}"
                )
            else:
                raise FileNotFoundError("Exécutable CrystalDiskInfo introuvable après extraction")

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer CrystalDiskInfo:\n\n{str(e)}\n\n"
                f"Vous pouvez le télécharger manuellement depuis:\n"
                f"https://crystalmark.info/en/software/crystaldiskinfo/\n\n"
                f"Et placer les fichiers dans:\n{os.path.join(get_local_software_folder(), 'CrystalDiskInfo')}"
            )

    def _launch_occt(self):
        """Lancer OCCT portable (Monitoring température + Stress test)"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Créer dossier portable_tools dans downloads portable
            try:
                from portable_paths import get_portable_downloads_dir
                downloads_dir = get_portable_downloads_dir()
                tools_dir = str(downloads_dir / "NiTriTe_Tools")
            except:
                # Fallback
                if getattr(sys, 'frozen', False):
                    app_dir = Path(sys.executable).parent
                else:
                    app_dir = Path(__file__).parent.parent.parent
                tools_dir = str(app_dir / 'downloads' / 'NiTriTe_Tools')

            os.makedirs(tools_dir, exist_ok=True)

            occt_dir = os.path.join(tools_dir, "OCCT")

            # Chercher l'exécutable (nom peut varier)
            occt_exe = None
            if os.path.exists(occt_dir):
                for file in os.listdir(occt_dir):
                    if file.endswith('.exe') and 'OCCT' in file:
                        occt_exe = os.path.join(occt_dir, file)
                        break

            # Vérifier si déjà téléchargé
            if not occt_exe or not os.path.exists(occt_exe):
                response = messagebox.askyesno(
                    "Télécharger OCCT",
                    "OCCT n'est pas encore téléchargé.\n\n"
                    "OCCT est un outil professionnel pour:\n"
                    "• Surveiller les températures CPU/GPU\n"
                    "• Tester la stabilité du système\n"
                    "• Détecter les problèmes de surchauffe\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~25 MB, téléchargement unique)",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants...\n"
                    "OCCT est un outil gratuit pour usage personnel."
                )

                # URL OCCT portable (version gratuite)
                # Note: OCCT peut être un .exe portable ou un .zip
                url = "https://www.ocbase.com/download/occt"
                download_path = os.path.join(tools_dir, "occt_download")

                try:
                    # Télécharger
                    print(f" Téléchargement d'OCCT...")
                    urllib.request.urlretrieve(url, download_path)

                    os.makedirs(occt_dir, exist_ok=True)

                    # Vérifier le type de fichier téléchargé
                    # Lire les premiers bytes pour détecter le format
                    with open(download_path, 'rb') as f:
                        header = f.read(4)

                    # Vérifier si c'est un ZIP (commence par PK)
                    if header[:2] == b'PK':
                        # C'est un fichier ZIP - extraire
                        print(f" Extraction du ZIP...")
                        with zipfile.ZipFile(download_path, 'r') as zip_ref:
                            zip_ref.extractall(occt_dir)

                        # Rechercher l'exécutable après extraction
                        occt_exe = None
                        for file in os.listdir(occt_dir):
                            if file.endswith('.exe') and 'OCCT' in file:
                                occt_exe = os.path.join(occt_dir, file)
                                break

                    # Vérifier si c'est un EXE (commence par MZ)
                    elif header[:2] == b'MZ':
                        # C'est un exécutable portable - sauvegarder directement
                        print(f" Installation de l'exécutable portable...")
                        occt_exe = os.path.join(occt_dir, "OCCT.exe")

                        # Copier le fichier téléchargé vers le dossier OCCT
                        import shutil
                        shutil.move(download_path, occt_exe)
                        print(f" OCCT installé: {occt_exe}")

                    else:
                        raise ValueError("Format de fichier non reconnu (ni ZIP ni EXE)")

                    # Nettoyer le fichier temporaire s'il existe encore
                    if os.path.exists(download_path):
                        os.remove(download_path)

                    print(f" OCCT installé dans: {occt_dir}")

                except Exception as download_error:
                    # Nettoyer en cas d'erreur
                    if os.path.exists(download_path):
                        try:
                            os.remove(download_path)
                        except:
                            pass

                    # Si le téléchargement échoue, proposer le téléchargement manuel
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger OCCT automatiquement:\n\n{str(download_error)}\n\n"
                        f"Veuillez télécharger OCCT manuellement:\n"
                        f"1. Visitez: https://www.ocbase.com\n"
                        f"2. Téléchargez la version portable\n"
                        f"3. Extrayez dans: {occt_dir}"
                    )
                    return

            # Lancer
            if occt_exe and os.path.exists(occt_exe):
                # Lancer sans UAC en utilisant os.startfile (comme double-clic)
                # Cela évite l'erreur 740 (elevation required)
                try:
                    os.startfile(occt_exe)
                    messagebox.showinfo(
                        "OCCT",
                        f"OCCT lancé!\n\n"
                        f"Fonctionnalités:\n"
                        f"• Monitoring en temps réel des températures\n"
                        f"• Test de stabilité CPU/GPU/RAM\n"
                        f"• Détection de surchauffe\n"
                        f"• Graphiques de performance\n\n"
                        f" Attention: Les tests de stress chauffent le PC!\n"
                        f"Surveillez les températures pendant les tests.\n\n"
                        f"Emplacement: {occt_dir}"
                    )
                except OSError as e:
                    # Si os.startfile échoue, essayer avec subprocess et shell=True
                    subprocess.Popen(f'start "" "{occt_exe}"', shell=True)
                    messagebox.showinfo("OCCT", "OCCT lancé!")
            else:
                raise FileNotFoundError("Exécutable OCCT introuvable après extraction")

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer OCCT:\n\n{str(e)}\n\n"
                f"Vous pouvez le télécharger manuellement depuis:\n"
                f"https://www.ocbase.com"
            )

    def _test_battery(self):
        """Tester la batterie (pour portables) avec détails avancés"""
        from tkinter import messagebox
        import subprocess
        import os

        # Essayer de lancer l'outil externe Battery Tester s'il existe
        try:
            tools_dir = get_local_software_folder()
            battery_tester_path = os.path.join(tools_dir, "Ordi Plus - Battery Tester.exe")

            if os.path.exists(battery_tester_path):
                subprocess.Popen([battery_tester_path], shell=True)
                messagebox.showinfo(
                    "Test Batterie",
                    " Outil Battery Tester lancé!\n\n"
                    f"Emplacement: {battery_tester_path}"
                )
                return
        except Exception as e:
            print(f"Erreur lancement Battery Tester: {e}")
            # Continuer avec la méthode interne

        # Méthode interne (fallback)
        try:
            if PSUTIL_AVAILABLE:
                battery = psutil.sensors_battery()

                if battery is None:
                    messagebox.showinfo(
                        "Batterie",
                        " Aucune batterie détectée.\n\n"
                        "Ce PC est probablement un ordinateur de bureau."
                    )
                    return

                percent = battery.percent
                plugged = battery.power_plugged
                time_left = battery.secsleft

                # Calculer le temps restant
                if time_left == psutil.POWER_TIME_UNLIMITED:
                    time_str = "Illimité (branché)"
                elif time_left == psutil.POWER_TIME_UNKNOWN:
                    time_str = "Inconnu"
                else:
                    hours = time_left // 3600
                    minutes = (time_left % 3600) // 60
                    time_str = f"{hours}h {minutes}min"

                # Obtenir détails avancés via WMI
                battery_info = ""
                try:
                    import wmi
                    w = wmi.WMI()

                    for bat in w.Win32_Battery():
                        design_capacity = getattr(bat, 'DesignCapacity', None)
                        full_charge_capacity = getattr(bat, 'FullChargeCapacity', None)
                        design_voltage = getattr(bat, 'DesignVoltage', None)
                        battery_status = getattr(bat, 'BatteryStatus', None)
                        chemistry = getattr(bat, 'Chemistry', None)
                        device_id = getattr(bat, 'DeviceID', 'N/A')

                        # Calculer santé de la batterie
                        if design_capacity and full_charge_capacity:
                            health_percent = (full_charge_capacity / design_capacity) * 100

                            # Calculer capacité en mAh
                            design_mah = None
                            current_mah = None

                            # Essayer de récupérer le voltage (plusieurs méthodes)
                            voltage_v = None
                            if design_voltage and design_voltage > 0:
                                # Voltage en mV, convertir en V
                                voltage_v = design_voltage / 1000.0

                            # Si pas de voltage, estimer selon le type de batterie
                            # Laptops modernes utilisent généralement 11.1V (3 cellules) ou 14.8V (4 cellules)
                            if not voltage_v or voltage_v == 0:
                                # Estimer selon la capacité (heuristique)
                                if design_capacity < 35000:
                                    voltage_v = 11.1  # Batterie 3 cellules
                                elif design_capacity < 50000:
                                    voltage_v = 14.4  # Batterie 4 cellules
                                else:
                                    voltage_v = 14.8  # Batterie haute capacité

                            if voltage_v and voltage_v > 0:
                                # Convertir mWh en mAh: mAh = mWh / V
                                design_mah = design_capacity / voltage_v
                                current_mah = full_charge_capacity / voltage_v

                            battery_info += f"\n\n"
                            battery_info += f"\n SANTÉ BATTERIE: {health_percent:.1f}%"
                            battery_info += f"\n"

                            # Toujours afficher en mAh (estimé si voltage inconnu)
                            if design_mah and current_mah:
                                battery_info += f"\n Capacité ORIGINALE: {design_mah:.0f} mAh ({design_capacity} mWh)"
                                battery_info += f"\n Capacité ACTUELLE: {current_mah:.0f} mAh ({full_charge_capacity} mWh)"
                                battery_info += f"\n Usure: {design_mah - current_mah:.0f} mAh ({100 - health_percent:.1f}%)"
                                if not design_voltage or design_voltage == 0:
                                    battery_info += f"\n Voltage estimé: {voltage_v:.1f}V (capacités mAh approximatives)"
                                else:
                                    battery_info += f"\n Voltage: {voltage_v:.1f}V"
                            else:
                                battery_info += f"\n Capacité ORIGINALE: {design_capacity} mWh"
                                battery_info += f"\n Capacité ACTUELLE: {full_charge_capacity} mWh"
                                battery_info += f"\n Usure: {design_capacity - full_charge_capacity} mWh ({100 - health_percent:.1f}%)"

                        if device_id:
                            battery_info += f"\n Référence: {device_id}"

                        # Type de chimie
                        chemistry_types = {
                            1: "Autre", 2: "Inconnu", 3: "Lead Acid",
                            4: "Nickel Cadmium", 5: "Nickel Metal Hydride",
                            6: "Lithium-ion", 7: "Zinc air", 8: "Lithium Polymer"
                        }
                        if chemistry in chemistry_types:
                            battery_info += f"\n Type: {chemistry_types[chemistry]}"

                        break  # Une seule batterie normalement
                except:
                    pass  # Si WMI échoue, continuer sans détails avancés

                # Déterminer le statut
                if percent > 80:
                    status_emoji = ""
                    health = "Excellente"
                elif percent > 50:
                    status_emoji = ""
                    health = "Bonne"
                elif percent > 20:
                    status_emoji = ""
                    health = "Faible"
                else:
                    status_emoji = ""
                    health = "Critique"

                plugged_str = " Branché" if plugged else " Sur batterie"

                messagebox.showinfo(
                    "État de la Batterie",
                    f"{status_emoji} Niveau actuel: {percent}%\n"
                    f"État de charge: {health}\n"
                    f"Alimentation: {plugged_str}\n"
                    f"Autonomie restante: {time_str}"
                    f"{battery_info}\n\n"
                    f" Recommandation:\n"
                    f"{' Niveau optimal' if percent > 50 else ' Pensez à recharger'}"
                )
            else:
                messagebox.showwarning(
                    "Test Batterie",
                    "Le module psutil est requis pour tester la batterie.\n\n"
                    "Installation: pip install psutil"
                )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Erreur lors du test de batterie:\n\n{str(e)}"
            )

    def _test_battery_nitrite(self):
        """Test batterie NiTrite - Affichage simple style Ordi Plus"""
        from tkinter import messagebox
        import subprocess
        import tempfile
        import os

        try:
            # Vérifier si batterie présente via WMI
            battery_name = "Inconnue"
            design_capacity = 0
            full_charge_capacity = 0
            cycle_count = 0
            health_percent = 0

            try:
                import wmi
                w = wmi.WMI()
                for bat in w.Win32_Battery():
                    battery_name = getattr(bat, 'Name', None) or getattr(bat, 'DeviceID', 'Inconnue')
                    design_capacity = getattr(bat, 'DesignCapacity', 0) or 0
                    full_charge_capacity = getattr(bat, 'FullChargeCapacity', 0) or 0
                    cycle_count_val = getattr(bat, 'CycleCount', None)
                    if cycle_count_val:
                        cycle_count = cycle_count_val
                    break
            except ImportError:
                messagebox.showwarning("Module manquant", "Le module WMI est requis.\n\nInstallation: pip install WMI")
                return
            except Exception as e:
                pass

            # Si pas de données WMI, essayer powercfg XML
            if design_capacity == 0 or full_charge_capacity == 0:
                try:
                    temp_dir = tempfile.gettempdir()
                    xml_report = os.path.join(temp_dir, "battery-report-nitrite.xml")
                    result = subprocess.run(
                        ['powercfg', '/batteryreport', '/output', xml_report, '/xml'],
                        capture_output=True,
                        text=True,
                        timeout=15,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if result.returncode == 0 and os.path.exists(xml_report):
                        import xml.etree.ElementTree as ET
                        tree = ET.parse(xml_report)
                        root = tree.getroot()

                        # Namespace du rapport PowerCfg
                        ns = {'bat': 'http://schemas.microsoft.com/battery/2012'}

                        # Chercher les données dans le XML avec namespace
                        # D'abord chercher dans la section Batteries/Battery
                        battery_elem = root.find('.//bat:Battery', ns)
                        if battery_elem is not None:
                            design_elem = battery_elem.find('bat:DesignCapacity', ns)
                            full_elem = battery_elem.find('bat:FullChargeCapacity', ns)
                            cycle_elem = battery_elem.find('bat:CycleCount', ns)
                            id_elem = battery_elem.find('bat:Id', ns)

                            if design_elem is not None and design_elem.text:
                                design_capacity = int(design_elem.text)
                            if full_elem is not None and full_elem.text:
                                full_charge_capacity = int(full_elem.text)
                            if cycle_elem is not None and cycle_elem.text:
                                cycle_count = int(cycle_elem.text)
                            if id_elem is not None and id_elem.text:
                                battery_name = id_elem.text

                        try:
                            os.remove(xml_report)
                        except:
                            pass
                except Exception:
                    pass

            # Vérifier qu'on a des données
            if design_capacity == 0 and full_charge_capacity == 0:
                # Vérifier si batterie existe
                if not PSUTIL_AVAILABLE or psutil.sensors_battery() is None:
                    messagebox.showinfo(
                        "NiTriTe - Test de batterie",
                        "Aucune batterie détectée.\n\n"
                        "Ce PC est probablement un ordinateur de bureau."
                    )
                    return
                else:
                    messagebox.showwarning(
                        "NiTriTe - Test de batterie",
                        "Impossible de récupérer les données de la batterie.\n\n"
                        "Le service DPS est peut-être désactivé.\n"
                        "Ouvrez services.msc et activez\n"
                        "'Service de stratégie de diagnostic'"
                    )
                    return

            # Calculer la santé de la batterie
            if design_capacity > 0:
                health_percent = round((full_charge_capacity / design_capacity) * 100, 1)
            else:
                health_percent = 0

            # Couleur selon santé
            if health_percent >= 80:
                health_color = "#4CAF50"  # Vert
            elif health_percent >= 60:
                health_color = "#FFA500"  # Orange
            elif health_percent >= 40:
                health_color = "#FF6B35"  # Orange foncé
            else:
                health_color = "#F44336"  # Rouge

            # Créer fenêtre simple
            battery_window = ctk.CTkToplevel(self)
            battery_window.title("NiTriTe - Test de batterie")
            battery_window.geometry("420x280")
            battery_window.resizable(False, False)

            # Centrer la fenêtre
            battery_window.update_idletasks()
            x = (battery_window.winfo_screenwidth() // 2) - 210
            y = (battery_window.winfo_screenheight() // 2) - 140
            battery_window.geometry(f"420x280+{x}+{y}")

            # Frame principal
            main_frame = ctk.CTkFrame(battery_window, fg_color="transparent")
            main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

            # Titre: La vie de la batterie
            title_label = ctk.CTkLabel(
                main_frame,
                text=f"La vie de la batterie est de : {health_percent}%",
                font=("Segoe UI", 18, "bold"),
                text_color=health_color
            )
            title_label.pack(anchor="w", pady=(0, 15))

            # Informations détaillées
            info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            info_frame.pack(fill=tk.X, anchor="w")

            # Nom
            ctk.CTkLabel(
                info_frame,
                text=f"Nom : {battery_name}",
                font=("Segoe UI", 13),
                text_color="#2196F3"
            ).pack(anchor="w", pady=2)

            # Capacité originale
            ctk.CTkLabel(
                info_frame,
                text=f"Capacité originale : {design_capacity} mWh",
                font=("Segoe UI", 13),
                text_color="#4CAF50"
            ).pack(anchor="w", pady=2)

            # Capacité actuelle
            ctk.CTkLabel(
                info_frame,
                text=f"Capacité actuelle : {full_charge_capacity} mWh",
                font=("Segoe UI", 13),
                text_color="#FF9800"
            ).pack(anchor="w", pady=2)

            # Nombre de cycles
            ctk.CTkLabel(
                info_frame,
                text=f"Nombre de cycles : {cycle_count}",
                font=("Segoe UI", 13),
                text_color="#F44336"
            ).pack(anchor="w", pady=2)

            # Frame boutons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill=tk.X, pady=(25, 0))

            # Fonction pour ouvrir le rapport HTML
            def open_html_report():
                try:
                    temp_dir = tempfile.gettempdir()
                    html_report = os.path.join(temp_dir, "battery-report-nitrite.html")
                    result = subprocess.run(
                        ['powercfg', '/batteryreport', '/output', html_report],
                        capture_output=True,
                        text=True,
                        timeout=15,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    if result.returncode == 0 and os.path.exists(html_report):
                        os.startfile(html_report)
                    else:
                        messagebox.showwarning(
                            "Erreur",
                            "Impossible de générer le rapport HTML.\n\n"
                            "Le service DPS est peut-être désactivé."
                        )
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur: {str(e)}")

            # Bouton Ouvrir le HTML détaillé
            ctk.CTkButton(
                button_frame,
                text="Ouvrir le HTML détaillé",
                command=open_html_report,
                width=180,
                height=35,
                font=("Segoe UI", 12),
                fg_color="#4CAF50",
                hover_color="#45A049"
            ).pack(side=tk.LEFT, padx=(0, 10))

            # Bouton OK
            ctk.CTkButton(
                button_frame,
                text="OK",
                command=battery_window.destroy,
                width=100,
                height=35,
                font=("Segoe UI", 12),
                fg_color="#607D8B",
                hover_color="#546E7A"
            ).pack(side=tk.LEFT)

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Erreur lors du test de batterie:\n\n{str(e)}"
            )

    def _launch_autoruns(self):
        """Lancer Autoruns (Sysinternals)"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Créer dossier portable_tools dans downloads portable
            try:
                from portable_paths import get_portable_downloads_dir
                downloads_dir = get_portable_downloads_dir()
                tools_dir = str(downloads_dir / "NiTriTe_Tools")
            except:
                # Fallback
                if getattr(sys, 'frozen', False):
                    app_dir = Path(sys.executable).parent
                else:
                    app_dir = Path(__file__).parent.parent.parent
                tools_dir = str(app_dir / 'downloads' / 'NiTriTe_Tools')

            os.makedirs(tools_dir, exist_ok=True)

            autoruns_dir = os.path.join(tools_dir, "Autoruns")
            autoruns_exe = os.path.join(autoruns_dir, "Autoruns64.exe")

            # Vérifier si déjà téléchargé
            if not os.path.exists(autoruns_exe):
                response = messagebox.askyesno(
                    "Télécharger Autoruns",
                    "Autoruns n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~2 MB, téléchargement unique)\n\n"
                    "Autoruns est un outil Microsoft Sysinternals\n"
                    "pour gérer les programmes au démarrage.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL Autoruns (Microsoft Sysinternals)
                url = "https://download.sysinternals.com/files/Autoruns.zip"
                zip_path = os.path.join(tools_dir, "autoruns.zip")

                # Télécharger
                print(f" Téléchargement d'Autoruns...")
                urllib.request.urlretrieve(url, zip_path)

                # Extraire
                print(f" Extraction...")
                os.makedirs(autoruns_dir, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(autoruns_dir)

                # Nettoyer
                os.remove(zip_path)
                print(f" Autoruns installé dans: {autoruns_dir}")

            # Lancer
            if os.path.exists(autoruns_exe):
                subprocess.Popen([autoruns_exe], shell=True)
                messagebox.showinfo(
                    "Autoruns",
                    f"Autoruns lancé!\n\n"
                    f"Cet outil vous permet de:\n"
                    f"• Voir tous les programmes au démarrage\n"
                    f"• Désactiver les logiciels indésirables\n"
                    f"• Améliorer les performances de démarrage\n\n"
                    f"Emplacement: {autoruns_dir}"
                )
            else:
                raise FileNotFoundError("Autoruns64.exe introuvable après extraction")

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer Autoruns:\n\n{str(e)}\n\n"
                f"Vous pouvez le télécharger manuellement depuis:\n"
                f"https://docs.microsoft.com/sysinternals/downloads/autoruns"
            )

    def _launch_malwarebytes(self):
        """Ouvrir la page de téléchargement Malwarebytes"""
        import webbrowser
        from tkinter import messagebox

        try:
            response = messagebox.askyesno(
                "Télécharger Malwarebytes",
                "Malwarebytes est un outil anti-malware professionnel.\n\n"
                "Cette action va ouvrir la page de téléchargement officielle\n"
                "de Malwarebytes dans votre navigateur.\n\n"
                "Voulez-vous continuer?",
                icon='question'
            )

            if not response:
                return

            # Ouvrir la page de téléchargement dans le navigateur
            webbrowser.open("https://www.malwarebytes.com/fr/mwb-download")

            messagebox.showinfo(
                "Page ouverte",
                "La page de téléchargement Malwarebytes a été ouverte\n"
                "dans votre navigateur.\n\n"
                "Téléchargez et installez Malwarebytes depuis cette page."
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir la page de téléchargement:\n\n{str(e)}\n\n"
                f"Visitez manuellement:\n"
                f"https://www.malwarebytes.com/fr/mwb-download"
            )

    def _launch_spybot(self):
        """Lancer Spybot Search & Destroy Portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()

            # Chercher d'abord dans SpybotPortable (PortableApps)
            spybot_portable_dir = os.path.join(tools_dir, "SpybotPortable")
            spybot_portable_exe = os.path.join(spybot_portable_dir, "SpybotPortable.exe")

            if os.path.exists(spybot_portable_exe):
                os.startfile(spybot_portable_exe)
                messagebox.showinfo(
                    "Spybot",
                    f"Spybot Search & Destroy lancé!\n\nEmplacement: {spybot_portable_exe}"
                )
                return

            # Sinon, chercher dans dossier classique Spybot
            spybot_dir = os.path.join(tools_dir, "Spybot")
            os.makedirs(spybot_dir, exist_ok=True)

            # Chercher l'exécutable Spybot
            spybot_exe = None
            if os.path.exists(spybot_dir):
                for file in os.listdir(spybot_dir):
                    if file.lower().endswith('.exe') and 'spybot' in file.lower():
                        spybot_exe = os.path.join(spybot_dir, file)
                        break

            # Si pas trouvé, télécharger
            if not spybot_exe or not os.path.exists(spybot_exe):
                response = messagebox.askyesno(
                    "Télécharger Spybot",
                    "Spybot Search & Destroy n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~50 MB, téléchargement unique)\n\n"
                    "Spybot détecte et élimine les malwares.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques minutes..."
                )

                # URL Spybot (version portable depuis PortableApps)
                url = "https://portableapps.com/redirect/?a=SpybotSD&s=s&d=pa&f=SpybotSDPortable_2.9.82.0.paf.exe"
                spybot_installer = os.path.join(tools_dir, "SpybotPortable.exe")

                # Télécharger
                print(f" Téléchargement de Spybot...")
                try:
                    urllib.request.urlretrieve(url, spybot_installer)
                    print(f" Spybot téléchargé dans: {tools_dir}")

                    # L'installer portable s'auto-extrait
                    messagebox.showinfo(
                        "Installation",
                        "Spybot va s'installer.\n\n"
                        "Choisissez comme destination:\n"
                        f"{spybot_dir}\n\n"
                        "Puis cliquez à nouveau sur le bouton Spybot."
                    )
                    os.startfile(spybot_installer)
                    return

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger Spybot:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://www.safer-networking.org/download/"
                    )
                    return

            # Lancer
            os.startfile(spybot_exe)
            messagebox.showinfo(
                "Spybot",
                f"Spybot Search & Destroy lancé!\n\n"
                f"Emplacement: {spybot_exe}"
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer Spybot:\n\n{str(e)}\n\n"
                f"Téléchargez-le depuis:\n"
                f"https://www.safer-networking.org"
            )

    def _launch_adwcleaner(self):
        """Lancer AdwCleaner Portable"""
        import subprocess
        import os
        import urllib.request
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()
            adw_dir = os.path.join(tools_dir, "AdwCleaner")
            os.makedirs(adw_dir, exist_ok=True)
            adw_exe = os.path.join(adw_dir, "adwcleaner.exe")

            # Vérifier si déjà téléchargé
            if not os.path.exists(adw_exe):
                response = messagebox.askyesno(
                    "Télécharger AdwCleaner",
                    "AdwCleaner n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~8 MB, téléchargement unique)\n\n"
                    "AdwCleaner supprime les adwares et PUPs.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL AdwCleaner (Malwarebytes)
                url = "https://adwcleaner.malwarebytes.com/adwcleaner?channel=release"
                os.makedirs(adw_dir, exist_ok=True)

                # Télécharger
                print(f" Téléchargement d'AdwCleaner...")
                urllib.request.urlretrieve(url, adw_exe)
                print(f" AdwCleaner installé dans: {adw_dir}")

            # Lancer
            if os.path.exists(adw_exe):
                os.startfile(adw_exe)
                messagebox.showinfo(
                    "AdwCleaner",
                    f"AdwCleaner lancé!\n\n"
                    f"Emplacement: {adw_dir}"
                )
            else:
                raise FileNotFoundError("AdwCleaner introuvable")

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer AdwCleaner:\n\n{str(e)}\n\n"
                f"Vous pouvez le télécharger manuellement depuis:\n"
                f"https://www.malwarebytes.com/adwcleaner"
            )

    def _launch_wisediskcleaner(self):
        """Lancer Wise Disk Cleaner Portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()

            # Chercher d'abord dans WiseDiskCleanerPortable (PortableApps)
            wise_portable_dir = os.path.join(tools_dir, "WiseDiskCleanerPortable")
            wise_portable_exe = os.path.join(wise_portable_dir, "WiseDiskCleanerPortable.exe")

            if os.path.exists(wise_portable_exe):
                os.startfile(wise_portable_exe)
                messagebox.showinfo(
                    "Wise Disk Cleaner",
                    f"Wise Disk Cleaner lancé!\n\nEmplacement: {wise_portable_exe}"
                )
                return

            # Sinon, chercher dans dossier classique WiseDiskCleaner
            wise_dir = os.path.join(tools_dir, "WiseDiskCleaner")
            os.makedirs(wise_dir, exist_ok=True)

            # Chercher l'exécutable Wise Disk Cleaner
            wise_exe = None
            if os.path.exists(wise_dir):
                for file in os.listdir(wise_dir):
                    if file.lower().endswith('.exe') and 'wise' in file.lower():
                        wise_exe = os.path.join(wise_dir, file)
                        break

            # Si pas trouvé, télécharger
            if not wise_exe or not os.path.exists(wise_exe):
                response = messagebox.askyesno(
                    "Télécharger Wise Disk Cleaner",
                    "Wise Disk Cleaner n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~5 MB, téléchargement unique)\n\n"
                    "Wise Disk Cleaner nettoie les fichiers inutiles.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL Wise Disk Cleaner Portable (depuis PortableApps)
                url = "https://portableapps.com/redirect/?a=WiseDiskCleanerPortable&s=s&d=pa&f=WiseDiskCleanerPortable_11.1.5.655.paf.exe"
                wise_installer = os.path.join(tools_dir, "WiseDiskCleanerPortable.exe")

                # Télécharger
                print(f" Téléchargement de Wise Disk Cleaner...")
                try:
                    urllib.request.urlretrieve(url, wise_installer)
                    print(f" Wise Disk Cleaner téléchargé dans: {tools_dir}")

                    # L'installer portable s'auto-extrait
                    messagebox.showinfo(
                        "Installation",
                        "Wise Disk Cleaner va s'installer.\n\n"
                        "Choisissez comme destination:\n"
                        f"{wise_dir}\n\n"
                        "Puis cliquez à nouveau sur le bouton Wise Disk Cleaner."
                    )
                    os.startfile(wise_installer)
                    return

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger Wise Disk Cleaner:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://www.wisecleaner.com/wise-disk-cleaner.html"
                    )
                    return

            # Lancer
            os.startfile(wise_exe)
            messagebox.showinfo(
                "Wise Disk Cleaner",
                f"Wise Disk Cleaner lancé!\n\n"
                f"Emplacement: {wise_exe}"
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer Wise Disk Cleaner:\n\n{str(e)}\n\n"
                f"Téléchargez-le depuis:\n"
                f"https://www.wisecleaner.com"
            )

    def _launch_portable_tool(self, tool_name, folder_name, file_pattern, description, download_url=None):
        """Template générique pour lancer un outil portable depuis le dossier logiciel"""
        import os
        from tkinter import messagebox

        try:
            tools_dir = get_local_software_folder()
            tool_dir = os.path.join(tools_dir, folder_name)
            os.makedirs(tool_dir, exist_ok=True)

            # Chercher l'exécutable
            tool_exe = None
            if os.path.exists(tool_dir):
                for file in os.listdir(tool_dir):
                    if file.lower().endswith('.exe') and file_pattern.lower() in file.lower():
                        tool_exe = os.path.join(tool_dir, file)
                        break

            if tool_exe and os.path.exists(tool_exe):
                # Lancer l'outil
                os.startfile(tool_exe)
                messagebox.showinfo(
                    tool_name,
                    f"{tool_name} lancé!\n\nEmplacement: {tool_exe}"
                )
            else:
                # Outil non trouvé
                messagebox.showwarning(
                    f"{tool_name} non trouvé",
                    f"{tool_name} n'est pas installé dans le dossier logiciel.\n\n"
                    f"Veuillez placer {tool_name} dans:\n{tool_dir}\n\n"
                    f"{description}"
                )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer {tool_name}:\n\n{str(e)}"
            )

    def _launch_hwmonitor(self):
        """Lancer HWMonitor portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()
            hwm_dir = os.path.join(tools_dir, "HWMonitor")
            os.makedirs(hwm_dir, exist_ok=True)

            # Chercher l'exécutable
            hwm_exe = None
            if os.path.exists(hwm_dir):
                for file in os.listdir(hwm_dir):
                    if file.lower().endswith('.exe') and 'hwmonitor' in file.lower():
                        hwm_exe = os.path.join(hwm_dir, file)
                        break

            # Vérifier si déjà téléchargé
            if not hwm_exe or not os.path.exists(hwm_exe):
                response = messagebox.askyesno(
                    "Télécharger HWMonitor",
                    "HWMonitor n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~2 MB, version portable, téléchargement unique)\n\n"
                    "HWMonitor surveille températures, tensions et vitesses des ventilateurs.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL HWMonitor Portable (lien direct depuis CPUID)
                url = "https://download.cpuid.com/hwmonitor/hwmonitor_1.53.zip"
                zip_path = os.path.join(tools_dir, "hwmonitor.zip")

                # Télécharger
                print(f" Téléchargement de HWMonitor...")
                try:
                    urllib.request.urlretrieve(url, zip_path)

                    # Extraire
                    print(f" Extraction...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(hwm_dir)

                    # Nettoyer
                    os.remove(zip_path)
                    print(f" HWMonitor installé dans: {hwm_dir}")

                    # Rechercher l'exécutable après extraction
                    hwm_exe = None
                    for file in os.listdir(hwm_dir):
                        if file.lower().endswith('.exe') and 'hwmonitor' in file.lower():
                            hwm_exe = os.path.join(hwm_dir, file)
                            break

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger HWMonitor:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://www.cpuid.com/softwares/hwmonitor.html\n\n"
                        f"Et placez les fichiers dans:\n{hwm_dir}"
                    )
                    return

            # Lancer
            if hwm_exe and os.path.exists(hwm_exe):
                os.startfile(hwm_exe)
                messagebox.showinfo(
                    "HWMonitor",
                    f"HWMonitor lancé!\n\nEmplacement: {hwm_exe}"
                )
            else:
                messagebox.showwarning(
                    "HWMonitor non trouvé",
                    f"HWMonitor n'est pas installé dans le dossier logiciel.\n\n"
                    f"Veuillez placer HWMonitor portable dans:\n{hwm_dir}\n\n"
                    f"Téléchargeable depuis: https://www.cpuid.com/softwares/hwmonitor.html"
                )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer HWMonitor:\n\n{str(e)}"
            )

    def _launch_userdiag(self):
        """Lancer UserDiag portable (sans installation)"""
        import subprocess
        import os
        import webbrowser
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local
            tools_dir = get_local_software_folder()
            userdiag_dir = os.path.join(tools_dir, "UserDiag")
            os.makedirs(userdiag_dir, exist_ok=True)

            # Chercher l'exécutable UserDiag
            userdiag_exe = None
            if os.path.exists(userdiag_dir):
                for file in os.listdir(userdiag_dir):
                    if file.lower().endswith('.exe') and 'userdiag' in file.lower():
                        userdiag_exe = os.path.join(userdiag_dir, file)
                        break

            # Si pas trouvé, guider l'utilisateur
            if not userdiag_exe or not os.path.exists(userdiag_exe):
                response = messagebox.askyesnocancel(
                    "Télécharger UserDiag Portable",
                    f"UserDiag n'a pas été trouvé dans:\n{userdiag_dir}\n\n"
                    "Voulez-vous:\n"
                    "• OUI = Ouvrir le site de téléchargement\n"
                    "• NON = Ouvrir le dossier de destination\n"
                    "• ANNULER = Annuler\n\n"
                    "Après téléchargement, placez UserDiag.exe dans le dossier\n"
                    "puis relancez ce bouton.",
                    icon='question'
                )

                if response is None:  # Annuler
                    return
                elif response:  # Oui - Ouvrir site
                    webbrowser.open("https://userdiag.com/fr/")
                    messagebox.showinfo(
                        "Instructions",
                        f"1. Téléchargez UserDiag depuis le site (version portable)\n"
                        f"2. Extrayez le fichier UserDiag.exe\n"
                        f"3. Placez-le dans:\n   {userdiag_dir}\n"
                        f"4. Relancez ce bouton\n\n"
                        f"Le dossier de destination va s'ouvrir..."
                    )
                    subprocess.Popen(f'explorer "{userdiag_dir}"', shell=True)
                else:  # Non - Ouvrir dossier uniquement
                    subprocess.Popen(f'explorer "{userdiag_dir}"', shell=True)
                    messagebox.showinfo(
                        "Dossier ouvert",
                        f"Placez UserDiag.exe dans ce dossier,\n"
                        f"puis relancez ce bouton."
                    )
                return

            # Lancer UserDiag portable
            print(f" Lancement de UserDiag portable: {userdiag_exe}")
            os.startfile(userdiag_exe)
            messagebox.showinfo(
                "UserDiag",
                f"UserDiag portable lancé!\n\n"
                f"Version portable - Aucune installation requise\n"
                f"Emplacement: {userdiag_exe}"
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer UserDiag:\n\n{str(e)}\n\n"
                f"Téléchargez-le depuis: https://userdiag.com/fr/"
            )

    def _launch_speedtest_web(self):
        """Ouvrir Speedtest dans le navigateur web"""
        import webbrowser
        from tkinter import messagebox

        try:
            print(" Ouverture de Speedtest.net...")
            webbrowser.open("https://www.speedtest.net/fr")
            messagebox.showinfo(
                "Speedtest",
                "Speedtest s'ouvre dans votre navigateur.\n\n"
                "Cliquez sur 'GO' pour lancer le test."
            )
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir Speedtest:\n\n{str(e)}"
            )

    def _launch_keyboard_test(self):
        """Lancer le testeur de clavier AZERTY en ligne"""
        import webbrowser
        from tkinter import messagebox

        try:
            print("⌨️ Ouverture du testeur de clavier AZERTY...")
            webbrowser.open("https://www.test-clavier.fr/")
            self._log_to_terminal("⌨️ Testeur de clavier AZERTY ouvert dans le navigateur")
            messagebox.showinfo(
                "Testeur de Clavier",
                "Le testeur de clavier AZERTY s'ouvre dans votre navigateur.\n\n"
                "Utilisez-le pour vérifier le bon fonctionnement de votre clavier."
            )
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir le testeur de clavier:\n\n{str(e)}"
            )

    def _launch_speedtest_portable(self):
        """Lancer Speedtest CLI portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()
            speedtest_dir = os.path.join(tools_dir, "Speedtest")
            os.makedirs(speedtest_dir, exist_ok=True)

            # Chercher l'exécutable
            speedtest_exe = None
            if os.path.exists(speedtest_dir):
                speedtest_exe_path = os.path.join(speedtest_dir, "speedtest.exe")
                if os.path.exists(speedtest_exe_path):
                    speedtest_exe = speedtest_exe_path

            # Vérifier si déjà téléchargé
            if not speedtest_exe or not os.path.exists(speedtest_exe):
                response = messagebox.askyesno(
                    "Télécharger Speedtest CLI",
                    "Speedtest CLI n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(version portable officielle Ookla, téléchargement unique)\n\n"
                    "Speedtest CLI est l'outil officiel de test de vitesse.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL Speedtest CLI Portable (Ookla officiel)
                url = "https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-win64.zip"
                zip_path = os.path.join(tools_dir, "speedtest.zip")

                # Télécharger
                print(f" Téléchargement de Speedtest CLI...")
                try:
                    urllib.request.urlretrieve(url, zip_path)

                    # Extraire
                    print(f" Extraction...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(speedtest_dir)

                    # Nettoyer
                    os.remove(zip_path)
                    print(f" Speedtest CLI installé dans: {speedtest_dir}")

                    # Vérifier l'exécutable après extraction
                    speedtest_exe_path = os.path.join(speedtest_dir, "speedtest.exe")
                    if os.path.exists(speedtest_exe_path):
                        speedtest_exe = speedtest_exe_path

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger Speedtest CLI:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://www.speedtest.net/apps/cli\n\n"
                        f"Et placez les fichiers dans:\n{speedtest_dir}"
                    )
                    return

            # Lancer dans un terminal
            if speedtest_exe and os.path.exists(speedtest_exe):
                # Ouvrir un terminal avec speedtest
                subprocess.Popen(
                    f'start cmd /k "cd /d {speedtest_dir} && echo Speedtest CLI pret! && echo. && echo Commandes disponibles: && echo   speedtest           - Lancer un test && echo   speedtest --help    - Aide complete && echo. && echo Tapez speedtest pour commencer... && echo."',
                    shell=True
                )

                messagebox.showinfo(
                    "Speedtest lancé!",
                    "Speedtest CLI lancé!\n\n"
                    "Utilisez les commandes:\n"
                    "  speedtest - Test rapide\n"
                    "  speedtest --help - Aide complète\n\n"
                    "Le test s'exécute dans le terminal."
                )
            else:
                messagebox.showwarning(
                    "Speedtest non trouvé",
                    f"Speedtest CLI n'est pas installé dans le dossier logiciel.\n\n"
                    f"Veuillez placer Speedtest CLI dans:\n{speedtest_dir}\n\n"
                    f"Téléchargeable depuis: https://www.speedtest.net/apps/cli"
                )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer Speedtest CLI:\n\n{str(e)}"
            )

    def _launch_hwinfo(self):
        """Lancer HWinfo portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()

            # Chercher d'abord dans HWiNFOPortable (PortableApps)
            hwi_portable_dir = os.path.join(tools_dir, "HWiNFOPortable")
            hwi_portable_exe = os.path.join(hwi_portable_dir, "HWiNFOPortable.exe")

            if os.path.exists(hwi_portable_exe):
                # Lancer la version PortableApps
                os.startfile(hwi_portable_exe)
                messagebox.showinfo(
                    "HWinfo",
                    f"HWinfo lancé!\n\nEmplacement: {hwi_portable_exe}"
                )
                return

            # Sinon, chercher dans HWinfo (dossier classique)
            hwi_dir = os.path.join(tools_dir, "HWinfo")
            os.makedirs(hwi_dir, exist_ok=True)

            # Chercher l'exécutable
            hwi_exe = None
            if os.path.exists(hwi_dir):
                for file in os.listdir(hwi_dir):
                    if file.lower().endswith('.exe') and 'hwinfo' in file.lower() and '64' in file.lower():
                        hwi_exe = os.path.join(hwi_dir, file)
                        break

            # Vérifier si déjà téléchargé
            if not hwi_exe or not os.path.exists(hwi_exe):
                response = messagebox.askyesno(
                    "Télécharger HWinfo",
                    "HWinfo n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~5 MB, version portable, téléchargement unique)\n\n"
                    "HWinfo fournit des informations détaillées sur le matériel système.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL HWinfo Portable (lien direct depuis le site officiel)
                url = "https://www.fosshub.com/HWiNFO.html?dwl=hwi_800.zip"
                zip_path = os.path.join(tools_dir, "hwinfo.zip")

                # Télécharger
                print(f" Téléchargement de HWinfo...")
                try:
                    urllib.request.urlretrieve(url, zip_path)

                    # Extraire
                    print(f" Extraction...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(hwi_dir)

                    # Nettoyer
                    os.remove(zip_path)
                    print(f" HWinfo installé dans: {hwi_dir}")

                    # Rechercher l'exécutable après extraction
                    hwi_exe = None
                    for file in os.listdir(hwi_dir):
                        if file.lower().endswith('.exe') and 'hwinfo' in file.lower() and '64' in file.lower():
                            hwi_exe = os.path.join(hwi_dir, file)
                            break

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger HWinfo:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://www.hwinfo.com/download/\n\n"
                        f"Et placez les fichiers dans:\n{hwi_dir}"
                    )
                    return

            # Lancer
            if hwi_exe and os.path.exists(hwi_exe):
                os.startfile(hwi_exe)
                messagebox.showinfo(
                    "HWinfo",
                    f"HWinfo lancé!\n\nEmplacement: {hwi_exe}"
                )
            else:
                messagebox.showwarning(
                    "HWinfo non trouvé",
                    f"HWinfo n'est pas installé dans le dossier logiciel.\n\n"
                    f"Veuillez placer HWinfo portable dans:\n{hwi_dir}\n\n"
                    f"Téléchargeable depuis: https://www.hwinfo.com/download/"
                )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer HWinfo:\n\n{str(e)}"
            )

    def _launch_crystaldiskmark(self):
        """Lancer CrystalDiskMark portable"""
        import subprocess
        import os
        import urllib.request
        import zipfile
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()
            cdm_dir = os.path.join(tools_dir, "CrystalDiskMark")
            os.makedirs(cdm_dir, exist_ok=True)

            # Chercher l'exécutable (nom peut varier)
            cdm_exe = None
            if os.path.exists(cdm_dir):
                for file in os.listdir(cdm_dir):
                    if file.endswith('.exe') and 'DiskMark' in file and '64' in file:
                        cdm_exe = os.path.join(cdm_dir, file)
                        break

            # Vérifier si déjà téléchargé
            if not cdm_exe or not os.path.exists(cdm_exe):
                response = messagebox.askyesno(
                    "Télécharger CrystalDiskMark",
                    "CrystalDiskMark n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~4 MB, version portable, téléchargement unique)\n\n"
                    "CrystalDiskMark teste les performances de lecture/écriture des disques.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL CrystalDiskMark Portable (lien direct depuis le site officiel)
                url = "https://sourceforge.net/projects/crystaldiskmark/files/latest/download"
                zip_path = os.path.join(tools_dir, "cdm.zip")

                # Télécharger
                print(f" Téléchargement de CrystalDiskMark...")
                try:
                    urllib.request.urlretrieve(url, zip_path)

                    # Extraire
                    print(f" Extraction...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(cdm_dir)

                    # Nettoyer
                    os.remove(zip_path)
                    print(f" CrystalDiskMark installé dans: {cdm_dir}")

                    # Rechercher l'exécutable après extraction
                    cdm_exe = None
                    for file in os.listdir(cdm_dir):
                        if file.endswith('.exe') and 'DiskMark' in file and '64' in file:
                            cdm_exe = os.path.join(cdm_dir, file)
                            break

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger CrystalDiskMark:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://crystalmark.info/en/software/crystaldiskmark/\n\n"
                        f"Et placez les fichiers dans:\n{cdm_dir}"
                    )
                    return

            # Lancer
            if cdm_exe and os.path.exists(cdm_exe):
                subprocess.Popen([cdm_exe], shell=True)
                messagebox.showinfo(
                    "CrystalDiskMark",
                    f"CrystalDiskMark lancé!\n\n"
                    f"Emplacement: {cdm_exe}"
                )
            else:
                raise FileNotFoundError("Exécutable CrystalDiskMark introuvable après extraction")

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer CrystalDiskMark:\n\n{str(e)}\n\n"
                f"Vous pouvez le télécharger manuellement depuis:\n"
                f"https://crystalmark.info/en/software/crystaldiskmark/\n\n"
                f"Et placer les fichiers dans:\n{os.path.join(get_local_software_folder(), 'CrystalDiskMark')}"
            )

    def _launch_cpuz(self):
        """Lancer CPU-Z portable"""
        import os
        from tkinter import messagebox

        try:
            tools_dir = get_local_software_folder()

            # Chercher d'abord dans CPU-ZPortable (PortableApps)
            cpuz_portable_dir = os.path.join(tools_dir, "CPU-ZPortable")
            cpuz_portable_exe = os.path.join(cpuz_portable_dir, "CPU-ZPortable.exe")

            if os.path.exists(cpuz_portable_exe):
                os.startfile(cpuz_portable_exe)
                messagebox.showinfo(
                    "CPU-Z",
                    f"CPU-Z lancé!\n\nEmplacement: {cpuz_portable_exe}"
                )
                return

            # Sinon, chercher dans dossier classique CPU-Z
            self._launch_portable_tool(
                tool_name="CPU-Z",
                folder_name="CPU-Z",
                file_pattern="cpuz",
                description="CPU-Z affiche les informations détaillées du processeur."
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer CPU-Z:\n\n{str(e)}"
            )

    def _launch_gpuz(self):
        """Lancer GPU-Z portable"""
        import os
        from tkinter import messagebox

        try:
            tools_dir = get_local_software_folder()

            # Chercher GPU-Z dans le dossier logiciel
            gpuz_exe = os.path.join(tools_dir, "GPU-Z.0.7.0.exe")

            if os.path.exists(gpuz_exe):
                os.startfile(gpuz_exe)
                messagebox.showinfo(
                    "GPU-Z",
                    " GPU-Z lancé!\n\n"
                    f"Emplacement: {gpuz_exe}\n\n"
                    "GPU-Z affiche les informations détaillées de votre carte graphique."
                )
                return

            # Chercher dans un sous-dossier GPU-Z
            gpuz_dir = os.path.join(tools_dir, "GPU-Z")
            if os.path.exists(gpuz_dir):
                for file in os.listdir(gpuz_dir):
                    if file.lower().endswith('.exe') and 'gpu-z' in file.lower():
                        gpuz_path = os.path.join(gpuz_dir, file)
                        os.startfile(gpuz_path)
                        messagebox.showinfo(
                            "GPU-Z",
                            f" GPU-Z lancé!\n\nEmplacement: {gpuz_path}"
                        )
                        return

            # Pas trouvé
            messagebox.showwarning(
                "GPU-Z non trouvé",
                "GPU-Z n'est pas encore installé.\n\n"
                f"Emplacement attendu:\n{gpuz_exe}\n\n"
                "Vous pouvez le télécharger depuis:\n"
                "https://www.techpowerup.com/gpuz/"
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer GPU-Z:\n\n{str(e)}"
            )

    def _launch_wisecare365(self):
        """Lancer Wise Care 365 Portable"""
        import subprocess
        import os
        import urllib.request
        from tkinter import messagebox

        try:
            # Utiliser dossier 'logiciel' local à côté de l'exécutable
            tools_dir = get_local_software_folder()
            wc365_dir = os.path.join(tools_dir, "WiseCare365")
            os.makedirs(wc365_dir, exist_ok=True)

            # Chercher l'exécutable Wise Care 365
            wc365_exe = None
            if os.path.exists(wc365_dir):
                for file in os.listdir(wc365_dir):
                    if file.lower().endswith('.exe') and 'wisecare' in file.lower():
                        wc365_exe = os.path.join(wc365_dir, file)
                        break

            # Si pas trouvé, télécharger
            if not wc365_exe or not os.path.exists(wc365_exe):
                response = messagebox.askyesno(
                    "Télécharger Wise Care 365",
                    "Wise Care 365 n'est pas encore téléchargé.\n\n"
                    "Voulez-vous le télécharger maintenant?\n"
                    "(~15 MB, version portable, téléchargement unique)\n\n"
                    "Wise Care 365 optimise et nettoie le système Windows.",
                    icon='question'
                )

                if not response:
                    return

                messagebox.showinfo(
                    "Téléchargement",
                    "Le téléchargement va démarrer.\n\n"
                    "Cela peut prendre quelques instants..."
                )

                # URL Wise Care 365 Portable (depuis PortableApps)
                url = "https://portableapps.com/redirect/?a=WiseCare365Portable&s=s&d=pa&f=WiseCare365Portable_6.7.4.paf.exe"
                wc365_installer = os.path.join(tools_dir, "WiseCare365Portable.exe")

                # Télécharger
                print(f" Téléchargement de Wise Care 365...")
                try:
                    urllib.request.urlretrieve(url, wc365_installer)
                    print(f" Wise Care 365 téléchargé dans: {tools_dir}")

                    # L'installer portable s'auto-extrait
                    messagebox.showinfo(
                        "Installation",
                        "Wise Care 365 va s'installer.\n\n"
                        "Choisissez comme destination:\n"
                        f"{wc365_dir}\n\n"
                        "Puis cliquez à nouveau sur le bouton Wise Care 365."
                    )
                    os.startfile(wc365_installer)
                    return

                except Exception as download_error:
                    messagebox.showerror(
                        "Erreur de téléchargement",
                        f"Impossible de télécharger Wise Care 365:\n\n{str(download_error)}\n\n"
                        f"Téléchargez-le manuellement depuis:\n"
                        f"https://www.wisecleaner.com/wise-care-365.html\n"
                        f"ou depuis PortableApps.com"
                    )
                    return

            # Lancer
            os.startfile(wc365_exe)
            messagebox.showinfo(
                "Wise Care 365",
                f"Wise Care 365 lancé!\n\n"
                f"Emplacement: {wc365_exe}"
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer Wise Care 365:\n\n{str(e)}\n\n"
                f"Téléchargez-le depuis:\n"
                f"https://www.wisecleaner.com"
            )

    def _create_diagnostic_section(self, parent, title, items):
        """Section de diagnostic avec icônes colorées"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        # Utiliser SectionHeader pour le titre avec icône colorée
        header = SectionHeader(card, text=title)
        header.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        for label, value, status in items:
            row = ctk.CTkFrame(
                content,
                fg_color=DesignTokens.BG_ELEVATED,
                corner_radius=DesignTokens.RADIUS_SM
            )
            row.pack(fill=tk.X, pady=3)

            row_content = ctk.CTkFrame(row, fg_color="transparent")
            row_content.pack(fill=tk.X, padx=12, pady=8)

            # Extraire l'emoji du label si présent
            try:
                from v14_mvp.auto_color_icons import extract_emoji
                from v14_mvp.icons_system import ColoredIconsManager
                emoji, clean_label = extract_emoji(label)

                # Si emoji détecté, créer une icône colorée
                if emoji:
                    icon_image = ColoredIconsManager.create_colored_icon(emoji, size=20)
                    icon_label = ctk.CTkLabel(
                        row_content,
                        image=icon_image,
                        text=""
                    )
                    icon_label.image = icon_image  # Garder référence
                    icon_label.pack(side=tk.LEFT, padx=(0, 8))

                    # Label sans emoji
                    label_widget = ctk.CTkLabel(
                        row_content,
                        text=clean_label,
                        font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM, "bold"),
                        text_color=DesignTokens.TEXT_PRIMARY,
                        anchor="w",
                        width=130
                    )
                    label_widget.pack(side=tk.LEFT)
                else:
                    # Pas d'emoji, affichage classique
                    label_widget = ctk.CTkLabel(
                        row_content,
                        text=label,
                        font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM, "bold"),
                        text_color=DesignTokens.TEXT_PRIMARY,
                        anchor="w",
                        width=150
                    )
                    label_widget.pack(side=tk.LEFT)
            except Exception as e:
                # Fallback en cas d'erreur
                label_widget = ctk.CTkLabel(
                    row_content,
                    text=label,
                    font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM, "bold"),
                    text_color=DesignTokens.TEXT_PRIMARY,
                    anchor="w",
                    width=150
                )
                label_widget.pack(side=tk.LEFT)

            value_widget = ctk.CTkLabel(
                row_content,
                text=value,
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
                text_color=DesignTokens.TEXT_SECONDARY,
                anchor="w"
            )
            value_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

            status_widget = ctk.CTkLabel(
                row_content,
                text=status,
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                text_color=DesignTokens.SUCCESS if status == "" else DesignTokens.WARNING
            )
            status_widget.pack(side=tk.RIGHT)
    
    def _run_diagnostic(self):
        """Lancer diagnostic"""
        print(" Lancement du diagnostic complet...")
        # Rafraîchir infos
        self.system_info = self._get_system_info()
        # Recréer contenu
        for widget in self.winfo_children():
            widget.destroy()
        self._create_header()
        self._create_content()
        print(" Diagnostic terminé")

    def _export_pc_info(self):
        """Exporter les informations PC vers un fichier texte"""
        from tkinter import filedialog, messagebox
        from datetime import datetime

        try:
            # Demander l'emplacement du fichier
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
                initialfile=f"info_pc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if not filename:
                return

            # Rafraîchir les infos avant export
            self.system_info = self._get_system_info()

            # Créer le contenu du fichier
            content = []
            content.append("=" * 80)
            content.append(" INFORMATIONS SYSTÈME - NITRITE V20.0")
            content.append("=" * 80)
            content.append(f"\nDate de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Système
            content.append("\n" + "=" * 80)
            content.append("SYSTÈME D'EXPLOITATION")
            content.append("=" * 80)
            content.append(f"OS: {self.system_info.get('os', 'N/A')}")
            content.append(f"Version: {self.system_info.get('os_version', 'N/A')}")
            content.append(f"Release: {self.system_info.get('os_release', 'N/A')}")
            content.append(f"Architecture: {self.system_info.get('architecture', 'N/A')}")
            content.append(f"Hostname: {self.system_info.get('hostname', 'N/A')}")

            # Carte mère
            if 'motherboard_product' in self.system_info:
                content.append(f"\nCarte mère: {self.system_info.get('motherboard_manufacturer', 'N/A')} {self.system_info.get('motherboard_product', 'N/A')}")

            # Processeur
            content.append("\n" + "=" * 80)
            content.append("PROCESSEUR")
            content.append("=" * 80)
            if 'cpu_name' in self.system_info:
                content.append(f"Modèle: {self.system_info.get('cpu_name', 'N/A')}")
                content.append(f"Fabricant: {self.system_info.get('cpu_manufacturer', 'N/A')}")
                content.append(f"Cores: {self.system_info.get('cpu_cores', 'N/A')}")
                content.append(f"Threads: {self.system_info.get('cpu_threads', 'N/A')}")
                content.append(f"Fréquence max: {self.system_info.get('cpu_max_speed', 'N/A')} MHz")
            else:
                content.append(f"Processeur: {self.system_info.get('processor', 'N/A')}")

            if PSUTIL_AVAILABLE:
                content.append(f"Utilisation actuelle: {self.system_info.get('cpu_percent', 0):.1f}%")

            # Mémoire RAM
            content.append("\n" + "=" * 80)
            content.append("MÉMOIRE RAM")
            content.append("=" * 80)
            if 'ram_modules' in self.system_info and self.system_info['ram_modules']:
                content.append(f"Total: {self.system_info.get('ram_total_gb', 0):.2f} GB")
                content.append(f"\nModules installés:")
                for i, module in enumerate(self.system_info['ram_modules'], 1):
                    content.append(f"  Module {i}:")
                    content.append(f"    - Fabricant: {module.get('manufacturer', 'Unknown')}")
                    content.append(f"    - Capacité: {module.get('capacity_gb', 0):.2f} GB")
                    content.append(f"    - Vitesse: {module.get('speed_mhz', 0)} MHz")
            if PSUTIL_AVAILABLE:
                content.append(f"\nUtilisation: {self.system_info.get('ram_used', 0):.2f} / {self.system_info.get('ram_total', 0):.2f} GB")
                content.append(f"Pourcentage: {self.system_info.get('ram_percent', 0):.1f}%")

            # Cartes graphiques
            if 'gpus' in self.system_info and self.system_info['gpus']:
                content.append("\n" + "=" * 80)
                content.append("CARTES GRAPHIQUES")
                content.append("=" * 80)
                for i, gpu in enumerate(self.system_info['gpus'], 1):
                    content.append(f"\nGPU {i}:")
                    content.append(f"  Nom: {gpu.get('name', 'N/A')}")
                    vram_gb = gpu.get('ram_bytes', 0) / (1024**3)
                    if vram_gb > 0:
                        content.append(f"  VRAM: {vram_gb:.2f} GB")
                    content.append(f"  Driver: {gpu.get('driver_version', 'N/A')}")

            # Stockage
            if 'storage_devices' in self.system_info and self.system_info['storage_devices']:
                content.append("\n" + "=" * 80)
                content.append("DISQUES DE STOCKAGE")
                content.append("=" * 80)
                for i, disk in enumerate(self.system_info['storage_devices'], 1):
                    content.append(f"\nDisque {i}:")
                    content.append(f"  Modèle: {disk.get('model', 'N/A')}")
                    content.append(f"  Capacité: {disk.get('size_gb', 0):.2f} GB")
                    content.append(f"  Interface: {disk.get('interface', 'N/A')}")

            # Partitions
            if PSUTIL_AVAILABLE and 'disks' in self.system_info:
                content.append("\n" + "=" * 80)
                content.append("PARTITIONS")
                content.append("=" * 80)
                for disk in self.system_info['disks']:
                    content.append(f"\n{disk.get('device', 'N/A')} ({disk.get('fstype', 'N/A')})")
                    content.append(f"  Mountpoint: {disk.get('mountpoint', 'N/A')}")
                    content.append(f"  Total: {disk.get('total', 0):.2f} GB")
                    content.append(f"  Utilisé: {disk.get('used', 0):.2f} GB ({disk.get('percent', 0):.1f}%)")
                    content.append(f"  Libre: {disk.get('free', 0):.2f} GB")

            # Réseau
            if PSUTIL_AVAILABLE:
                content.append("\n" + "=" * 80)
                content.append("RÉSEAU")
                content.append("=" * 80)
                content.append(f"Données envoyées: {self.system_info.get('net_sent', 0):.2f} MB")
                content.append(f"Données reçues: {self.system_info.get('net_recv', 0):.2f} MB")

            content.append("\n" + "=" * 80)
            content.append("FIN DU RAPPORT")
            content.append("=" * 80)

            # Écrire dans le fichier
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            messagebox.showinfo(
                "Export réussi",
                f"Les informations PC ont été exportées vers:\n\n{filename}\n\n"
                f"Vous pouvez maintenant partager ce fichier pour obtenir de l'aide."
            )

            # Ouvrir le fichier
            import subprocess
            subprocess.Popen(['notepad.exe', filename])

        except Exception as e:
            messagebox.showerror(
                "Erreur d'export",
                f"Impossible d'exporter les informations:\n\n{str(e)}"
            )

    def _perform_full_system_scan(self):
        """Lancer le scan avec barre de chargement"""
        import threading
        import tkinter as tk

        # Créer fenêtre de chargement
        loading_window = ctk.CTkToplevel(self)
        loading_window.title("Scan en cours...")
        loading_window.geometry("600x250")
        loading_window.resizable(False, False)

        # Centrer la fenêtre
        loading_window.transient(self)
        loading_window.grab_set()

        # Header
        header_frame = ctk.CTkFrame(loading_window, fg_color="#2196F3", corner_radius=0)
        header_frame.pack(fill=tk.X)

        ctk.CTkLabel(
            header_frame,
            text="🔍 SCAN TOTAL EN COURS",
            font=("Segoe UI", 22, "bold"),
            text_color="white"
        ).pack(pady=20)

        # Message
        self.loading_label = ctk.CTkLabel(
            loading_window,
            text="⏳ Démarrage du scan...",
            font=("Segoe UI", 14)
        )
        self.loading_label.pack(pady=(30, 10))

        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(loading_window, width=500, height=25)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        # Pourcentage
        self.progress_label = ctk.CTkLabel(
            loading_window,
            text="0%",
            font=("Segoe UI", 12, "bold")
        )
        self.progress_label.pack(pady=5)

        # Message de patience
        ctk.CTkLabel(
            loading_window,
            text="⌛ Veuillez patienter, analyse en cours...",
            font=("Segoe UI", 11),
            text_color="gray"
        ).pack(pady=(10, 20))

        # Fonction pour mettre à jour la progression
        self.scan_progress = 0
        self.scan_status = "Démarrage..."

        def update_progress(progress, status):
            self.scan_progress = progress
            self.scan_status = status
            loading_window.after(0, lambda: self._update_loading_ui(loading_window))

        # Lancer le scan dans un thread
        def run_scan():
            results = self._do_full_system_scan(update_progress)
            loading_window.after(0, lambda: self._finish_scan(loading_window, results))

        scan_thread = threading.Thread(target=run_scan, daemon=True)
        scan_thread.start()

    def _update_loading_ui(self, window):
        """Mettre à jour l'UI de chargement"""
        try:
            self.progress_bar.set(self.scan_progress / 100)
            self.progress_label.configure(text=f"{int(self.scan_progress)}%")
            self.loading_label.configure(text=f"⏳ {self.scan_status}")
        except:
            pass

    def _finish_scan(self, loading_window, scan_results):
        """Terminer le scan et afficher résultats"""
        loading_window.grab_release()
        loading_window.destroy()
        self._show_scan_results(scan_results)

    def _do_full_system_scan(self, update_progress):
        """
        Scan total du PC avec détection automatique de tous les problèmes

        Détecte:
        - Températures CPU/GPU excessives
        - Services/processus gourmands
        - RAM saturée
        - Disques pleins
        - Windows Defender status
        - Mises à jour manquantes
        """
        from tkinter import messagebox
        import subprocess

        print("🔍 Démarrage du scan total du PC...")

        update_progress(5, "Initialisation du scan...")

        # Rafraîchir les infos système
        self.system_info = self._get_system_info()

        update_progress(10, "Informations système récupérées...")

        # Stocker les résultats du scan
        scan_results = {
            'critical': [],  # Problèmes critiques (rouge)
            'warning': [],   # Avertissements (orange)
            'ok': []         # Tout va bien (vert)
        }

        # ═══════════════════════════════════════════════════════════════════
        # 1️⃣ VÉRIFICATION TEMPÉRATURES CPU/GPU
        # ═══════════════════════════════════════════════════════════════════
        update_progress(15, "Vérification températures CPU/GPU...")
        try:
            # Essayer d'obtenir la température via WMI
            import wmi
            w = wmi.WMI(namespace="root\\wmi")

            temps_found = False
            for sensor in w.MSAcpi_ThermalZoneTemperature():
                temp_kelvin = sensor.CurrentTemperature
                temp_celsius = (temp_kelvin / 10.0) - 273.15

                if temp_celsius > 90:
                    scan_results['critical'].append({
                        'category': '🌡️ Température',
                        'issue': f'CPU/Composant surchauffe: {temp_celsius:.1f}°C',
                        'recommendation': 'Vérifier refroidissement, nettoyer ventilos, changer pâte thermique'
                    })
                elif temp_celsius > 75:
                    scan_results['warning'].append({
                        'category': '🌡️ Température',
                        'issue': f'CPU/Composant chaud: {temp_celsius:.1f}°C',
                        'recommendation': 'Surveiller température, nettoyer PC si poussière'
                    })
                else:
                    scan_results['ok'].append({
                        'category': '🌡️ Température',
                        'message': f'Températures normales ({temp_celsius:.1f}°C)'
                    })
                temps_found = True
                break

            if not temps_found:
                scan_results['ok'].append({
                    'category': '🌡️ Température',
                    'message': 'Capteurs température non accessibles (normal sur certains PC)'
                })
        except:
            scan_results['ok'].append({
                'category': '🌡️ Température',
                'message': 'Capteurs température non accessibles (normal sur certains PC)'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 2️⃣ VÉRIFICATION CPU & PROCESSUS GOURMANDS
        # ═══════════════════════════════════════════════════════════════════
        update_progress(25, "Analyse CPU et processus...")

        # Obtenir nom complet du CPU
        cpu_name = self.system_info.get('cpu_name', 'CPU')
        cpu_cores = self.system_info.get('cpu_cores', 'N/A')
        cpu_threads = self.system_info.get('cpu_threads', 'N/A')
        cpu_specs = f"{cpu_name} ({cpu_cores}C/{cpu_threads}T)"

        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)

            if cpu_percent > 90:
                scan_results['critical'].append({
                    'category': '🖥️ CPU',
                    'issue': f'CPU surchargé: {cpu_percent:.1f}%\n{cpu_specs}',
                    'recommendation': 'Fermer applications inutilisées, vérifier processus avec Gestionnaire de tâches'
                })
            elif cpu_percent > 70:
                scan_results['warning'].append({
                    'category': '🖥️ CPU',
                    'issue': f'CPU élevé: {cpu_percent:.1f}%\n{cpu_specs}',
                    'recommendation': 'Surveiller utilisation CPU'
                })
            else:
                scan_results['ok'].append({
                    'category': '🖥️ CPU',
                    'message': f'Usage normal: {cpu_percent:.1f}%\n{cpu_specs}'
                })

            # Détecter top 5 processus gourmands
            processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] and proc_info['cpu_percent'] > 10:
                        processes.append((proc_info['name'], proc_info['cpu_percent']))
                except:
                    pass

            processes.sort(key=lambda x: x[1], reverse=True)
            if processes[:3]:  # Top 3
                top_procs = ', '.join([f"{name} ({cpu:.0f}%)" for name, cpu in processes[:3]])
                scan_results['warning'].append({
                    'category': '⚙️ Processus',
                    'issue': f'Processus gourmands: {top_procs}',
                    'recommendation': 'Vérifier si ces processus sont nécessaires'
                })

        # ═══════════════════════════════════════════════════════════════════
        # 3️⃣ VÉRIFICATION RAM
        # ═══════════════════════════════════════════════════════════════════
        update_progress(35, "Vérification mémoire RAM...")

        # Obtenir détails RAM (type, vitesse) - CORRIGÉ
        ram_details = ""
        if 'ram_modules' in self.system_info and self.system_info['ram_modules']:
            first_module = self.system_info['ram_modules'][0]
            ram_type = first_module.get('type_name', 'Unknown')  # CORRIGÉ: type_name au lieu de type
            ram_speed = first_module.get('speed_mhz', 0)  # CORRIGÉ: speed_mhz au lieu de speed
            ram_count = len(self.system_info['ram_modules'])
            if ram_speed > 0:
                ram_details = f"\n{ram_count}x {ram_type} @ {ram_speed} MHz"
            else:
                ram_details = f"\n{ram_count}x {ram_type}"

        if PSUTIL_AVAILABLE:
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            ram_total_gb = ram.total / (1024**3)
            ram_used_gb = ram.used / (1024**3)

            if ram_percent > 90:
                scan_results['critical'].append({
                    'category': '💾 RAM',
                    'issue': f'RAM saturée: {ram_percent:.1f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f} GB){ram_details}',
                    'recommendation': 'Fermer applications, redémarrer PC, envisager upgrade RAM'
                })
            elif ram_percent > 80:
                scan_results['warning'].append({
                    'category': '💾 RAM',
                    'issue': f'RAM élevée: {ram_percent:.1f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f} GB){ram_details}',
                    'recommendation': 'Fermer applications inutilisées'
                })
            else:
                scan_results['ok'].append({
                    'category': '💾 RAM',
                    'message': f'Usage normal: {ram_percent:.1f}% ({ram_used_gb:.1f}/{ram_total_gb:.1f} GB){ram_details}'
                })

        # ═══════════════════════════════════════════════════════════════════
        # 4️⃣ VÉRIFICATION DISQUES - REGROUPÉS
        # ═══════════════════════════════════════════════════════════════════

        # Obtenir modèles de disques
        disk_models = {}
        try:
            import wmi
            w = wmi.WMI()
            for disk in w.Win32_DiskDrive():
                # Associer le modèle au premier mountpoint trouvé
                model = disk.Model.strip() if disk.Model else "Disque"
                size_gb = int(disk.Size) / (1024**3) if disk.Size else 0
                disk_models[disk.DeviceID] = {'model': model, 'size': size_gb}
        except:
            pass

        # Collecter toutes les partitions
        disk_partitions_info = []
        if PSUTIL_AVAILABLE:
            partition_index = 0
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    percent = usage.percent
                    total_gb = usage.total / (1024**3)
                    free_gb = usage.free / (1024**3)

                    # Essayer de trouver le modèle du disque
                    disk_model = ""
                    if disk_models and partition_index < len(disk_models):
                        disk_list = list(disk_models.values())
                        if partition_index < len(disk_list):
                            disk_model = disk_list[partition_index]['model']

                    disk_partitions_info.append({
                        'mountpoint': partition.mountpoint,
                        'percent': percent,
                        'free_gb': free_gb,
                        'total_gb': total_gb,
                        'model': disk_model
                    })
                    partition_index += 1
                except:
                    pass

        # Regrouper tous les disques dans une seule catégorie
        if disk_partitions_info:
            # Vérifier s'il y a des problèmes critiques/warnings
            critical_disks = [d for d in disk_partitions_info if d['percent'] > 95]
            warning_disks = [d for d in disk_partitions_info if 85 < d['percent'] <= 95]
            ok_disks = [d for d in disk_partitions_info if d['percent'] <= 85]

            # Créer une entrée séparée pour chaque disque critique
            for d in critical_disks:
                disk_info = f"{d['mountpoint']}: {d['percent']:.1f}% plein ({d['free_gb']:.1f}/{d['total_gb']:.1f} GB)"
                if d['model']:
                    disk_info += f"\n{d['model']}"
                scan_results['critical'].append({
                    'category': f"💿 Disque {d['mountpoint']}",
                    'issue': disk_info,
                    'recommendation': 'URGENT: Libérer espace (supprimer fichiers, nettoyer disque)'
                })

            # Créer une entrée séparée pour chaque disque warning
            for d in warning_disks:
                disk_info = f"{d['mountpoint']}: {d['percent']:.1f}% ({d['free_gb']:.1f}/{d['total_gb']:.1f} GB)"
                if d['model']:
                    disk_info += f"\n{d['model']}"
                scan_results['warning'].append({
                    'category': f"💿 Disque {d['mountpoint']}",
                    'issue': disk_info,
                    'recommendation': 'Libérer espace: NiTriTe > Optimisations > Nettoyage'
                })

            # Créer une entrée séparée pour chaque disque OK
            for d in ok_disks:
                disk_info = f"{d['mountpoint']}: {d['percent']:.1f}% ({d['free_gb']:.1f}/{d['total_gb']:.1f} GB)"
                if d['model']:
                    disk_info += f"\n{d['model']}"
                scan_results['ok'].append({
                    'category': f"💿 Disque {d['mountpoint']}",
                    'message': disk_info
                })

        # ═══════════════════════════════════════════════════════════════════
        # 4️⃣-B INFORMATION GPU - REGROUPÉS
        # ═══════════════════════════════════════════════════════════════════

        # Ajouter info GPU au scan (tous regroupés)
        if 'gpus' in self.system_info and self.system_info['gpus']:
            gpu_info_list = []
            for i, gpu in enumerate(self.system_info['gpus'], 1):
                gpu_name = gpu.get('name', 'GPU Inconnu')
                gpu_ram_gb = gpu.get('ram_bytes', 0) / (1024**3) if gpu.get('ram_bytes', 0) > 0 else 0
                gpu_driver = gpu.get('driver_version', 'N/A')

                gpu_line = f"GPU #{i}: {gpu_name}"
                if gpu_ram_gb > 0:
                    gpu_line += f" - {gpu_ram_gb:.1f} GB VRAM"
                gpu_line += f" - Driver: {gpu_driver}"
                gpu_info_list.append(gpu_line)

            gpu_summary = "\n".join(gpu_info_list)
            scan_results['ok'].append({
                'category': '🎮 GPU',
                'message': gpu_summary
            })
        else:
            scan_results['ok'].append({
                'category': '🎮 GPU',
                'message': 'Carte graphique: Informations non disponibles'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 5️⃣ VÉRIFICATION WINDOWS DEFENDER
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Vérifier le status de Windows Defender via PowerShell
            result = subprocess.run(
                ['powershell', '-Command', 'Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, NISEnabled'],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )

            if 'True' in result.stdout:
                # Defender actif
                scan_results['ok'].append({
                    'category': '🛡️ Sécurité',
                    'message': 'Windows Defender actif et fonctionnel'
                })
            else:
                scan_results['critical'].append({
                    'category': '🛡️ Sécurité',
                    'issue': 'Windows Defender désactivé ou non fonctionnel',
                    'recommendation': 'URGENT: Activer Windows Defender pour protéger votre PC'
                })
        except:
            scan_results['warning'].append({
                'category': '🛡️ Sécurité',
                'issue': 'Impossible de vérifier status Windows Defender',
                'recommendation': 'Vérifier manuellement: Paramètres > Sécurité Windows'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 6️⃣ VÉRIFICATION MISES À JOUR WINDOWS
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Vérifier si des mises à jour sont en attente
            result = subprocess.run(
                ['powershell', '-Command', '(New-Object -ComObject Microsoft.Update.AutoUpdate).Results.LastSearchSuccessDate'],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )

            # Si la dernière recherche est vieille (>7 jours), avertir
            from datetime import datetime, timedelta
            try:
                last_search = result.stdout.strip()
                if last_search and last_search != '':
                    # Parser la date et comparer
                    scan_results['ok'].append({
                        'category': '🔄 Mises à jour',
                        'message': 'Windows Update actif'
                    })
            except:
                scan_results['warning'].append({
                    'category': '🔄 Mises à jour',
                    'issue': 'Impossible de vérifier status Windows Update',
                    'recommendation': 'Vérifier manuellement: NiTriTe > Mises à jour'
                })
        except:
            scan_results['warning'].append({
                'category': '🔄 Mises à jour',
                'issue': 'Impossible de vérifier status Windows Update',
                'recommendation': 'Vérifier manuellement: NiTriTe > Mises à jour'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 7️⃣ VÉRIFICATION SANTÉ DISQUES (SMART) - REGROUPÉ AVEC DISQUES
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Vérifier SMART status via WMI
            import wmi
            w = wmi.WMI()
            disk_health_info = []
            has_critical = False
            for disk in w.Win32_DiskDrive():
                status = disk.Status
                model = disk.Model if disk.Model else "Disque"
                if status and status.lower() != 'ok':
                    disk_health_info.append(f"{model}: ERREUR Status {status}")
                    has_critical = True
                else:
                    disk_health_info.append(f"{model}: Status OK")

            # Ajouter à la catégorie Disques existante
            if disk_health_info:
                health_summary = "\n".join(disk_health_info)
                if has_critical:
                    scan_results['critical'].append({
                        'category': '💿 Disques',
                        'issue': f"Sante SMART:\n{health_summary}",
                        'recommendation': 'URGENT: Sauvegarder donnees, remplacer disque. CrystalDiskInfo pour details'
                    })
                else:
                    scan_results['ok'].append({
                        'category': '💿 Disques',
                        'message': f"Sante SMART:\n{health_summary}"
                    })
        except:
            pass

        # ═══════════════════════════════════════════════════════════════════
        # 8️⃣ VÉRIFICATION WINDOWS VERSION & ACTIVATION
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Obtenir version Windows
            win_version_cmd = """
            $os = Get-WmiObject Win32_OperatingSystem
            $productName = $os.Caption
            $buildNumber = $os.BuildNumber
            $version = $os.Version
            Write-Output "$productName|$buildNumber|$version"
            """

            result = subprocess.run(
                ['powershell', '-Command', win_version_cmd],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'
            )

            if result.stdout.strip():
                parts = result.stdout.strip().split('|')
                if len(parts) >= 2:
                    product_name = parts[0].replace('Microsoft ', '')
                    build_number = parts[1]

                    scan_results['ok'].append({
                        'category': '🪟 Windows Version',
                        'message': f'{product_name} (Build {build_number})'
                    })

            # Obtenir statut activation avec slmgr /dli (plus fiable pour MAS)
            activation_cmd = "cscript //NoLogo %windir%\\System32\\slmgr.vbs /dli"
            result = subprocess.run(
                activation_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )

            activation_output = result.stdout.strip()

            # Vérifier si Windows est activé (compatible MAS HWID/KMS38)
            is_licensed = 'license status: licensed' in activation_output.lower() or 'état de la licence : licencié' in activation_output.lower()
            is_activated = is_licensed or 'permanently activated' in activation_output.lower() or 'activé de manière permanente' in activation_output.lower()

            # Vérifier méthode d'activation
            is_kms = 'kms' in activation_output.lower()
            is_hwid = 'hwid' in activation_output.lower() or ('licensed' in activation_output.lower() and not is_kms)

            if is_activated:
                activation_method = ""
                if is_hwid:
                    activation_method = " (HWID/Digital)"
                elif is_kms:
                    activation_method = " (KMS)"

                scan_results['ok'].append({
                    'category': '✅ Windows Activation',
                    'message': f'Windows activé{activation_method}'
                })
            elif 'will expire' in activation_output.lower() or 'expirera' in activation_output.lower():
                scan_results['warning'].append({
                    'category': '⏰ Windows Activation',
                    'issue': 'Activation temporaire (expirera bientôt)',
                    'recommendation': 'Activer Windows de manière permanente'
                })
            else:
                scan_results['critical'].append({
                    'category': '❌ Windows Activation',
                    'issue': 'Windows non activé',
                    'recommendation': 'Activer Windows via NiTriTe > Diagnostic > Activer Windows/Office'
                })
        except:
            scan_results['ok'].append({
                'category': '🪟 Windows',
                'message': 'Impossible de vérifier version/activation'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 9️⃣ VÉRIFICATION BATTERIE DÉTAILLÉE (LAPTOP UNIQUEMENT)
        # ═══════════════════════════════════════════════════════════════════

        # Stocker le chemin du rapport pour le bouton
        battery_report_path = None
        result = None  # Initialiser pour éviter erreur dans else

        try:
            # Import local pour éviter UnboundLocalError
            from pathlib import Path as PathLib
            import xml.etree.ElementTree as ET

            # Exécuter Battery Report XML (plus fiable pour extraire les données)
            temp_dir = PathLib(get_portable_temp_dir())
            temp_dir.mkdir(parents=True, exist_ok=True)
            battery_report_path = temp_dir / "battery-report.html"
            xml_report_path = temp_dir / "battery-report.xml"

            print(f"[DEBUG BATTERIE] Génération rapport XML: {xml_report_path}")

            # Générer rapport XML
            result = subprocess.run(
                ['powercfg', '/batteryreport', '/output', str(xml_report_path), '/xml'],
                capture_output=True,
                text=True,
                timeout=15,
                encoding='utf-8',
                errors='ignore'
            )

            print(f"[DEBUG BATTERIE] Code retour powercfg XML: {result.returncode}")

            # Variables pour stocker les données
            design_capacity = 0
            full_capacity = 0
            battery_name = "N/A"
            battery_cycle_count = "N/A"
            battery_chemistry = "N/A"

            # Parser le XML avec namespace
            if result.returncode == 0 and xml_report_path.exists():
                try:
                    tree = ET.parse(str(xml_report_path))
                    root = tree.getroot()

                    # Namespace du rapport PowerCfg
                    ns = {'bat': 'http://schemas.microsoft.com/battery/2012'}

                    # Chercher dans la section Batteries/Battery
                    battery_elem = root.find('.//bat:Battery', ns)
                    if battery_elem is not None:
                        id_elem = battery_elem.find('bat:Id', ns)
                        design_elem = battery_elem.find('bat:DesignCapacity', ns)
                        full_elem = battery_elem.find('bat:FullChargeCapacity', ns)
                        cycle_elem = battery_elem.find('bat:CycleCount', ns)
                        chem_elem = battery_elem.find('bat:Chemistry', ns)

                        if id_elem is not None and id_elem.text:
                            battery_name = id_elem.text
                        if design_elem is not None and design_elem.text:
                            design_capacity = int(design_elem.text)
                        if full_elem is not None and full_elem.text:
                            full_capacity = int(full_elem.text)
                        if cycle_elem is not None and cycle_elem.text:
                            battery_cycle_count = cycle_elem.text
                        if chem_elem is not None and chem_elem.text:
                            battery_chemistry = chem_elem.text

                        print(f"[DEBUG BATTERIE] Données XML: nom={battery_name}, design={design_capacity}, full={full_capacity}, cycles={battery_cycle_count}")

                    # Nettoyer le fichier XML
                    try:
                        xml_report_path.unlink()
                    except:
                        pass
                except Exception as xml_err:
                    print(f"[DEBUG BATTERIE] Erreur parsing XML: {xml_err}")

            # Si XML a échoué, générer le HTML et parser
            if design_capacity == 0 or full_capacity == 0:
                result = subprocess.run(
                    ['powercfg', '/batteryreport', '/output', str(battery_report_path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='ignore'
                )

            # Si on a les données, calculer et afficher
            if design_capacity > 0 and full_capacity > 0:
                # Calculer usure et santé
                wear_percent = ((design_capacity - full_capacity) / design_capacity) * 100
                health_percent = 100 - wear_percent

                # Générer aussi le rapport HTML pour le bouton
                if not battery_report_path.exists():
                    subprocess.run(
                        ['powercfg', '/batteryreport', '/output', str(battery_report_path)],
                        capture_output=True, text=True, timeout=10,
                        encoding='utf-8', errors='ignore'
                    )

                # Créer affichage simple style "Ordi Plus"
                battery_detail = f"""La vie de la batterie est de : {health_percent:.1f}%

Nom : {battery_name}
Capacité originale : {design_capacity} mWh
Capacité actuelle : {full_capacity} mWh
Nombre de cycles : {battery_cycle_count}"""

                # Ajouter le chemin du rapport pour le bouton + données structurées
                battery_result = {
                    'category': '🔋 Batterie',
                    'battery_report_path': str(battery_report_path) if battery_report_path.exists() else None,
                    # Données structurées pour export
                    'name': battery_name,
                    'chemistry': battery_chemistry,
                    'design_capacity': design_capacity,
                    'full_capacity': full_capacity,
                    'health_percent': health_percent,
                    'wear_percent': wear_percent,
                    'cycle_count': battery_cycle_count
                }

                if wear_percent > 50:
                    battery_result['issue'] = f'Batterie fortement dégradée:\n{battery_detail}'
                    battery_result['recommendation'] = 'URGENT: Remplacer batterie (usure >50%)'
                    scan_results['critical'].append(battery_result)
                elif wear_percent > 30:
                    battery_result['issue'] = f'Batterie usée:\n{battery_detail}'
                    battery_result['recommendation'] = 'Envisager remplacement batterie bientôt'
                    scan_results['warning'].append(battery_result)
                elif wear_percent > 10:
                    battery_result['issue'] = f'Batterie légère usure:\n{battery_detail}'
                    battery_result['recommendation'] = 'Surveiller évolution de l\'usure'
                    scan_results['warning'].append(battery_result)
                else:
                    battery_result['message'] = f'Batterie en excellent état:\n{battery_detail}'
                    scan_results['ok'].append(battery_result)
            else:
                # Rapport non créé = pas de batterie OU erreur powercfg
                print(f"[DEBUG BATTERIE] Fichier rapport n'existe pas après powercfg")
                error_msg = 'Aucune batterie détectée (PC fixe)'

                # Si code retour != 0, c'est une erreur powercfg, pas un PC fixe
                if result and result.returncode != 0:
                    error_msg = f'Erreur génération rapport batterie (code {result.returncode})'
                    if result.stderr:
                        error_msg += f'\nDétail: {result.stderr[:200]}'  # Limiter à 200 chars
                elif not result:
                    error_msg = 'Erreur lors de l\'exécution de powercfg'

                scan_results['ok'].append({
                    'category': '🔋 Batterie',
                    'message': error_msg
                })

        except Exception as e:
            # Erreur lors de la génération du rapport - mais on ajoute quand même le chemin s'il existe
            print(f"[DEBUG BATTERIE] Exception: {str(e)}")
            import traceback
            traceback.print_exc()

            battery_msg = {
                'category': '🔋 Batterie',
                'message': f'Erreur rapport batterie: {str(e)}'
            }
            # Ajouter le chemin du rapport s'il a été créé avant l'erreur
            if battery_report_path and battery_report_path.exists():
                battery_msg['battery_report_path'] = str(battery_report_path)
            scan_results['ok'].append(battery_msg)

        # ═══════════════════════════════════════════════════════════════════
        # 9️⃣ VÉRIFICATION MISES À JOUR DÉTAILLÉES - REGROUPÉES
        # ═══════════════════════════════════════════════════════════════════

        update_progress(85, "Vérification mises à jour...")

        # Collecter toutes les infos de mises à jour
        updates_info = {
            'winget': {'count': 0, 'error': False},
            'windows_update': {'count': 0, 'error': False},
            'scoop': {'count': 0, 'error': False},
            'chocolatey': {'count': 0, 'error': False}
        }

        # WinGet Updates
        try:
            result = subprocess.run(
                ['winget', 'upgrade', '--include-unknown'],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )

            updates_count = 0
            in_table = False
            for line in result.stdout.split('\n'):
                if 'Name' in line and 'Id' in line and 'Version' in line:
                    in_table = True
                    continue
                if in_table and (not line.strip() or line.startswith('-')):
                    if not line.strip():
                        break
                    continue
                if in_table and line.strip():
                    import re
                    if re.search(r'\d+\.\d+', line):
                        updates_count += 1
            updates_info['winget']['count'] = updates_count
        except:
            updates_info['winget']['error'] = True

        # Windows Update
        try:
            wu_cmd = """
            $updateSession = New-Object -ComObject Microsoft.Update.Session
            $updateSearcher = $updateSession.CreateUpdateSearcher()
            $searchResult = $updateSearcher.Search("IsInstalled=0 and Type='Software'")
            Write-Output $searchResult.Updates.Count
            """
            result = subprocess.run(
                ['powershell', '-Command', wu_cmd],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            if result.stdout.strip().isdigit():
                updates_info['windows_update']['count'] = int(result.stdout.strip())
        except:
            updates_info['windows_update']['error'] = True

        # Scoop Updates
        try:
            result = subprocess.run(
                ['scoop', 'status'],
                capture_output=True,
                text=True,
                timeout=15,
                encoding='utf-8',
                errors='ignore'
            )
            scoop_updates = 0
            for line in result.stdout.split('\n'):
                if 'update available' in line.lower():
                    scoop_updates += 1
            updates_info['scoop']['count'] = scoop_updates
        except:
            updates_info['scoop']['error'] = True

        # Chocolatey Updates
        try:
            result = subprocess.run(
                ['choco', 'outdated'],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )
            choco_updates = 0
            for line in result.stdout.split('\n'):
                if '|' in line and 'package' not in line.lower():
                    choco_updates += 1
            updates_info['chocolatey']['count'] = choco_updates
        except:
            updates_info['chocolatey']['error'] = True

        # Regrouper toutes les mises à jour dans une seule catégorie
        update_lines = []
        total_updates = 0

        if not updates_info['windows_update']['error']:
            wu_count = updates_info['windows_update']['count']
            total_updates += wu_count
            if wu_count > 0:
                update_lines.append(f"Windows Update: {wu_count} MAJ")
            else:
                update_lines.append("Windows Update: À jour")

        if not updates_info['winget']['error']:
            wg_count = updates_info['winget']['count']
            total_updates += wg_count
            if wg_count > 0:
                update_lines.append(f"WinGet: {wg_count} paquets")
            else:
                update_lines.append("WinGet: À jour")

        if not updates_info['scoop']['error'] and updates_info['scoop']['count'] > 0:
            sc_count = updates_info['scoop']['count']
            total_updates += sc_count
            update_lines.append(f"Scoop: {sc_count} paquets")

        if not updates_info['chocolatey']['error'] and updates_info['chocolatey']['count'] > 0:
            ch_count = updates_info['chocolatey']['count']
            total_updates += ch_count
            update_lines.append(f"Chocolatey: {ch_count} paquets")

        # Ajouter le résultat regroupé
        if total_updates == 0:
            scan_results['ok'].append({
                'category': '🔄 Mises à jour',
                'message': "\n".join(update_lines) if update_lines else "Tous les systèmes à jour"
            })
        elif total_updates > 15 or updates_info['windows_update']['count'] > 5:
            scan_results['critical'].append({
                'category': '🔄 Mises à jour',
                'issue': f"Total: {total_updates} mises à jour\n" + "\n".join(update_lines),
                'recommendation': 'URGENT: Installer les mises à jour (surtout Windows Update)'
            })
        else:
            scan_results['warning'].append({
                'category': '🔄 Mises à jour',
                'issue': f"Total: {total_updates} mises à jour\n" + "\n".join(update_lines),
                'recommendation': 'Mettre à jour via NiTriTe > Mises à jour'
            })

        # SECTION 🔟 SUPPRIMÉE - Informations SMART déjà regroupées dans section 💿 Disques ci-dessus

        # ═══════════════════════════════════════════════════════════════════
        # 🔟➊ ANALYSE DOSSIERS TEMP ET APPDATA - REGROUPÉS "FICHIERS DIVERS"
        # ═══════════════════════════════════════════════════════════════════
        try:
            import os
            from pathlib import Path

            def get_folder_size_quick(folder_path, timeout=5):
                """Calcul rapide taille dossier avec timeout"""
                import time
                total_size = 0
                start_time = time.time()

                try:
                    with os.scandir(folder_path) as entries:
                        for entry in entries:
                            if time.time() - start_time > timeout:
                                break
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    total_size += entry.stat(follow_symlinks=False).st_size
                                elif entry.is_dir(follow_symlinks=False):
                                    # Scan 1 niveau seulement pour performance
                                    try:
                                        with os.scandir(entry.path) as sub_entries:
                                            for sub_entry in sub_entries:
                                                if time.time() - start_time > timeout:
                                                    break
                                                try:
                                                    if sub_entry.is_file(follow_symlinks=False):
                                                        total_size += sub_entry.stat(follow_symlinks=False).st_size
                                                except:
                                                    pass
                                    except:
                                        pass
                            except:
                                pass
                except:
                    pass

                return total_size / (1024**3)  # Go

            # Collecter infos pour catégorie "Fichiers divers"
            files_info = []
            has_warning = False

            # Analyser %temp%
            temp_path = Path(os.environ.get('TEMP', ''))
            temp_size = 0
            if temp_path.exists():
                print("📁 Analyse %temp%...")
                temp_size = get_folder_size_quick(temp_path, timeout=5)

                if temp_size > 10:
                    files_info.append(f"%temp%: {temp_size:.2f} Go (VOLUMINEUX)")
                    has_warning = True
                elif temp_size > 5:
                    files_info.append(f"%temp%: {temp_size:.2f} Go (a nettoyer)")
                    has_warning = True
                else:
                    files_info.append(f"%temp%: {temp_size:.2f} Go")

            # Analyser %AppData% (Roaming)
            appdata_roaming_path = Path(os.environ.get('APPDATA', ''))
            appdata_roaming_size = 0
            if appdata_roaming_path.exists():
                print("📁 Analyse %AppData% (Roaming)...")
                appdata_roaming_size = get_folder_size_quick(appdata_roaming_path, timeout=5)

            # Analyser %AppData%\Local
            appdata_local_path = Path(os.environ.get('LOCALAPPDATA', ''))
            appdata_local_size = 0
            if appdata_local_path.exists():
                print("📁 Analyse %AppData%\\Local...")
                appdata_local_size = get_folder_size_quick(appdata_local_path, timeout=5)

            # AppData Total
            appdata_total = appdata_roaming_size + appdata_local_size
            files_info.append(f"AppData Total: {appdata_total:.2f} Go (Roaming: {appdata_roaming_size:.2f} + Local: {appdata_local_size:.2f})")

            # Utilisateur actuel
            username = os.environ.get('USERNAME', 'Inconnu')
            files_info.append(f"Utilisateur: {username}")

            # Regrouper dans "Fichiers divers"
            files_summary = "\n".join(files_info)
            if has_warning and temp_size > 10:
                scan_results['warning'].append({
                    'category': '📂 Fichiers divers',
                    'issue': files_summary,
                    'recommendation': 'Nettoyer fichiers temporaires: NiTriTe > Optimisations > Nettoyage'
                })
            elif has_warning:
                scan_results['ok'].append({
                    'category': '📂 Fichiers divers',
                    'message': files_summary + "\n💡 Envisager nettoyage %temp%"
                })
            else:
                scan_results['ok'].append({
                    'category': '📂 Fichiers divers',
                    'message': files_summary
                })

        except Exception as e:
            print(f"Erreur analyse temp/appdata: {e}")

        # SECTION 🔟➋ SUPPRIMÉE - Informations GPU déjà regroupées dans section 🎮 GPU ci-dessus

        # ═══════════════════════════════════════════════════════════════════
        # 1️⃣1️⃣ ANALYSE DOSSIER UTILISATEUR (OPTIMISÉE - RAPIDE)
        # ═══════════════════════════════════════════════════════════════════
        try:
            import os
            from pathlib import Path
            import time

            # Obtenir le dossier utilisateur
            user_folder = Path.home()

            def get_folder_size_fast(folder_path, max_depth=None, timeout=10):
                """
                Calculer la taille d'un dossier en Go (version RAPIDE avec timeout)

                Args:
                    folder_path: Chemin du dossier
                    max_depth: Profondeur maximale (None = illimité)
                    timeout: Timeout en secondes (évite les freeze)
                """
                total_size = 0
                start_time = time.time()

                try:
                    # Utiliser os.scandir (plus rapide que os.walk)
                    def scan_dir(path, current_depth=0):
                        nonlocal total_size

                        # Vérifier timeout (évite freeze)
                        if time.time() - start_time > timeout:
                            return

                        # Vérifier profondeur max
                        if max_depth is not None and current_depth > max_depth:
                            return

                        try:
                            with os.scandir(path) as entries:
                                for entry in entries:
                                    # Skip si timeout dépassé
                                    if time.time() - start_time > timeout:
                                        return

                                    try:
                                        if entry.is_file(follow_symlinks=False):
                                            total_size += entry.stat(follow_symlinks=False).st_size
                                        elif entry.is_dir(follow_symlinks=False):
                                            # Ignorer dossiers système cachés (performance)
                                            if not entry.name.startswith('.') and not entry.name.startswith('$'):
                                                scan_dir(entry.path, current_depth + 1)
                                    except (PermissionError, OSError):
                                        pass  # Ignorer fichiers inaccessibles
                        except (PermissionError, OSError):
                            pass

                    scan_dir(str(folder_path))

                except Exception:
                    pass

                return total_size / (1024**3)  # Convertir en Go

            # Analyser UNIQUEMENT les sous-dossiers principaux (pas tout le dossier!)
            print(f"📁 Analyse rapide du dossier utilisateur...")

            subfolders_to_check = {
                'Documents': (user_folder / 'Documents', None, 10),
                'Téléchargements': (user_folder / 'Downloads', None, 10),
                'Bureau': (user_folder / 'Desktop', None, 5),
                'Images': (user_folder / 'Pictures', None, 10),
                'Vidéos': (user_folder / 'Videos', None, 10),
                'Musique': (user_folder / 'Music', None, 10),
                'AppData': (user_folder / 'AppData', 2, 5)  # Limite 2 niveaux + 5s max (AppData énorme!)
            }

            subfolder_sizes = {}
            for name, (path, max_depth, timeout_val) in subfolders_to_check.items():
                if path.exists():
                    print(f"  Scan {name}... (timeout: {timeout_val}s)")
                    size = get_folder_size_fast(path, max_depth=max_depth, timeout=timeout_val)
                    subfolder_sizes[name] = size
                    print(f"    → {size:.2f} Go")

            # Calculer taille totale (somme des sous-dossiers scannés)
            user_folder_size = sum(subfolder_sizes.values())

            # Trier par taille décroissante
            sorted_folders = sorted(subfolder_sizes.items(), key=lambda x: x[1], reverse=True)

            # Préparer message détaillé
            top_folders_msg = "\n".join([f"  • {name}: {size:.2f} Go" for name, size in sorted_folders[:5]])

            # Évaluer si le dossier est trop volumineux
            if user_folder_size > 500:
                scan_results['warning'].append({
                    'category': '📁 Dossier Utilisateur',
                    'issue': f'Dossier utilisateur très volumineux: ~{user_folder_size:.2f} Go\n\nTop 5 dossiers:\n{top_folders_msg}',
                    'recommendation': 'Nettoyer fichiers inutiles, déplacer données vers disque secondaire, utiliser Nettoyage de disque'
                })
            elif user_folder_size > 200:
                scan_results['warning'].append({
                    'category': '📁 Dossier Utilisateur',
                    'issue': f'Dossier utilisateur volumineux: ~{user_folder_size:.2f} Go\n\nTop 5 dossiers:\n{top_folders_msg}',
                    'recommendation': 'Surveiller espace, nettoyer si nécessaire'
                })
            else:
                scan_results['ok'].append({
                    'category': '📁 Dossier Utilisateur',
                    'message': f'Taille: ~{user_folder_size:.2f} Go\n\nTop 3 dossiers:\n' + "\n".join([f"  • {name}: {size:.2f} Go" for name, size in sorted_folders[:3]])
                })

            print(f"📁 Analyse terminée: ~{user_folder_size:.2f} Go total")

        except Exception as e:
            print(f"❌ Erreur analyse dossier: {str(e)}")
            scan_results['ok'].append({
                'category': '📁 Dossier Utilisateur',
                'message': f'Analyse non disponible'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 🔧 ANALYSE REGISTRY & EVENT LOG (API Windows)
        # ═══════════════════════════════════════════════════════════════════
        update_progress(92, "Analyse Registry & Event Log...")

        try:
            import winreg

            # --- 1. ERREURS EVENT LOG RÉCENTES (via PowerShell) ---
            print("📋 Analyse Event Log Windows...")
            try:
                # Récupérer les erreurs critiques des dernières 24h
                event_log_cmd = """
                $errors = @()
                $24hAgo = (Get-Date).AddHours(-24)

                # Erreurs Application
                try {
                    $appErrors = Get-WinEvent -FilterHashtable @{LogName='Application'; Level=1,2; StartTime=$24hAgo} -MaxEvents 10 -ErrorAction SilentlyContinue
                    foreach ($e in $appErrors) {
                        $errors += "APP|$($e.TimeCreated)|$($e.ProviderName)|$($e.Message.Substring(0, [Math]::Min(100, $e.Message.Length)))"
                    }
                } catch {}

                # Erreurs System
                try {
                    $sysErrors = Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=$24hAgo} -MaxEvents 10 -ErrorAction SilentlyContinue
                    foreach ($e in $sysErrors) {
                        $errors += "SYS|$($e.TimeCreated)|$($e.ProviderName)|$($e.Message.Substring(0, [Math]::Min(100, $e.Message.Length)))"
                    }
                } catch {}

                # BSOD récents (BugCheck)
                try {
                    $bsod = Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WER-SystemErrorReporting'} -MaxEvents 5 -ErrorAction SilentlyContinue
                    foreach ($b in $bsod) {
                        $errors += "BSOD|$($b.TimeCreated)|BSOD|$($b.Message.Substring(0, [Math]::Min(100, $b.Message.Length)))"
                    }
                } catch {}

                $errors -join '|||'
                """

                result = subprocess.run(
                    ['powershell', '-Command', event_log_cmd],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.stdout.strip():
                    events = result.stdout.strip().split('|||')
                    app_errors = [e for e in events if e.startswith('APP|')]
                    sys_errors = [e for e in events if e.startswith('SYS|')]
                    bsod_events = [e for e in events if e.startswith('BSOD|')]

                    # BSOD critique
                    if bsod_events:
                        bsod_count = len(bsod_events)
                        scan_results['critical'].append({
                            'category': '💀 BSOD Détectés',
                            'issue': f'{bsod_count} écran(s) bleu(s) récent(s) détecté(s)',
                            'recommendation': 'Vérifier drivers, RAM, disque dur. Consulter WhoCrashed pour analyse détaillée'
                        })

                    # Erreurs Application
                    if len(app_errors) > 5:
                        scan_results['warning'].append({
                            'category': '📋 Event Log Application',
                            'issue': f'{len(app_errors)} erreurs application (24h)',
                            'recommendation': 'Vérifier applications problématiques dans Event Viewer'
                        })
                    elif app_errors:
                        scan_results['ok'].append({
                            'category': '📋 Event Log Application',
                            'message': f'{len(app_errors)} erreur(s) mineure(s) (24h) - Normal'
                        })
                    else:
                        scan_results['ok'].append({
                            'category': '📋 Event Log Application',
                            'message': 'Aucune erreur critique (24h)'
                        })

                    # Erreurs Système
                    if len(sys_errors) > 5:
                        scan_results['warning'].append({
                            'category': '📋 Event Log Système',
                            'issue': f'{len(sys_errors)} erreurs système (24h)',
                            'recommendation': 'Vérifier Event Viewer > Windows Logs > System'
                        })
                    elif sys_errors:
                        scan_results['ok'].append({
                            'category': '📋 Event Log Système',
                            'message': f'{len(sys_errors)} erreur(s) mineure(s) (24h) - Normal'
                        })
                    else:
                        scan_results['ok'].append({
                            'category': '📋 Event Log Système',
                            'message': 'Aucune erreur critique (24h)'
                        })
                else:
                    scan_results['ok'].append({
                        'category': '📋 Event Log',
                        'message': 'Aucune erreur critique détectée (24h)'
                    })

            except Exception as e:
                print(f"  ⚠️ Erreur Event Log: {e}")
                scan_results['ok'].append({
                    'category': '📋 Event Log',
                    'message': 'Analyse Event Log non disponible'
                })

            # --- 2. SERVICES DÉFAILLANTS (via Registry + PowerShell) ---
            print("🔧 Analyse services Windows...")
            try:
                services_cmd = """
                $failed = Get-Service | Where-Object {$_.Status -eq 'Stopped' -and $_.StartType -eq 'Automatic'} | Select-Object -First 10 Name, DisplayName
                $failed | ForEach-Object { "$($_.Name)|$($_.DisplayName)" }
                """

                result = subprocess.run(
                    ['powershell', '-Command', services_cmd],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.stdout.strip():
                    failed_services = [s.strip() for s in result.stdout.strip().split('\n') if s.strip() and '|' in s]

                    # Filtrer les services critiques (ignorer les services normalement arrêtés)
                    non_critical = ['WbioSrvc', 'WerSvc', 'wuauserv', 'RemoteRegistry', 'Fax', 'TabletInputService']
                    critical_failed = [s for s in failed_services if s.split('|')[0] not in non_critical]

                    if len(critical_failed) > 3:
                        services_list = '\n'.join([f"  • {s.split('|')[1]}" for s in critical_failed[:5]])
                        scan_results['warning'].append({
                            'category': '🔧 Services Windows',
                            'issue': f'{len(critical_failed)} services auto arrêtés:\n{services_list}',
                            'recommendation': 'Vérifier services.msc, redémarrer services nécessaires'
                        })
                    else:
                        scan_results['ok'].append({
                            'category': '🔧 Services Windows',
                            'message': 'Services automatiques OK'
                        })
                else:
                    scan_results['ok'].append({
                        'category': '🔧 Services Windows',
                        'message': 'Tous les services automatiques fonctionnent'
                    })

            except Exception as e:
                print(f"  ⚠️ Erreur analyse services: {e}")

            # --- 3. PROGRAMMES AU DÉMARRAGE (via Registry) ---
            print("🚀 Analyse programmes démarrage (Registry)...")
            try:
                startup_locations = [
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
                ]

                startup_programs = []
                invalid_programs = []

                for hkey, subkey in startup_locations:
                    try:
                        key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                startup_programs.append((name, value))

                                # Vérifier si le chemin existe
                                import shlex
                                try:
                                    # Extraire le chemin du programme (gérer les guillemets et arguments)
                                    path = value.strip('"').split('"')[0].split(' ')[0]
                                    if path and not os.path.exists(path) and not path.startswith('%'):
                                        invalid_programs.append((name, value))
                                except:
                                    pass

                                i += 1
                            except WindowsError:
                                break
                        winreg.CloseKey(key)
                    except WindowsError:
                        continue

                if invalid_programs:
                    invalid_list = '\n'.join([f"  • {name}" for name, _ in invalid_programs[:5]])
                    scan_results['warning'].append({
                        'category': '🚀 Démarrage Windows',
                        'issue': f'{len(invalid_programs)} entrée(s) invalide(s):\n{invalid_list}',
                        'recommendation': 'Nettoyer avec CCleaner ou msconfig > Démarrage'
                    })
                else:
                    scan_results['ok'].append({
                        'category': '🚀 Démarrage Windows',
                        'message': f'{len(startup_programs)} programmes au démarrage - Tous valides'
                    })

            except Exception as e:
                print(f"  ⚠️ Erreur analyse démarrage: {e}")
                scan_results['ok'].append({
                    'category': '🚀 Démarrage Windows',
                    'message': 'Analyse démarrage non disponible'
                })

            # --- 4. ERREURS DISQUE RÉCENTES (via Registry/Event Log) ---
            print("💿 Recherche erreurs disque...")
            try:
                disk_errors_cmd = """
                $diskErrors = Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='disk','ntfs','storahci'} -MaxEvents 20 -ErrorAction SilentlyContinue |
                    Where-Object { $_.LevelDisplayName -eq 'Error' -or $_.LevelDisplayName -eq 'Warning' }
                $diskErrors.Count
                """

                result = subprocess.run(
                    ['powershell', '-Command', disk_errors_cmd],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding='utf-8',
                    errors='ignore'
                )

                if result.stdout.strip():
                    try:
                        error_count = int(result.stdout.strip())
                        if error_count > 10:
                            scan_results['critical'].append({
                                'category': '💿 Erreurs Disque',
                                'issue': f'{error_count} erreurs disque détectées dans Event Log',
                                'recommendation': 'URGENT: Sauvegarder données, vérifier SMART avec CrystalDiskInfo, envisager remplacement disque'
                            })
                        elif error_count > 0:
                            scan_results['warning'].append({
                                'category': '💿 Erreurs Disque',
                                'issue': f'{error_count} erreur(s) disque dans Event Log',
                                'recommendation': 'Surveiller santé disque avec CrystalDiskInfo'
                            })
                        else:
                            scan_results['ok'].append({
                                'category': '💿 Erreurs Disque',
                                'message': 'Aucune erreur disque dans Event Log'
                            })
                    except ValueError:
                        pass

            except Exception as e:
                print(f"  ⚠️ Erreur analyse disque: {e}")

            print("✅ Analyse Registry & Event Log terminée")

        except Exception as e:
            print(f"❌ Erreur analyse Registry: {str(e)}")
            scan_results['ok'].append({
                'category': '🔧 Registry',
                'message': f'Analyse Registry non disponible'
            })

        # ═══════════════════════════════════════════════════════════════════
        # 🔍 ANALYSE PROCESSUS SUSPECTS (VIRUS, MALWARES)
        # ═══════════════════════════════════════════════════════════════════
        update_progress(93, "Analyse processus suspects...")
        print("🔍 Analyse processus suspects (malwares, virus)...")

        try:
            # Noms de processus connus comme malveillants ou suspects
            known_malware = [
                'coinminer', 'xmrig', 'cryptonight', 'minerd', 'cgminer', 'bfgminer',
                'kryptex', 'nicehash', 'phoenixminer', 'ethminer', 'nbminer',
                'wannacry', 'petya', 'notpetya', 'locky', 'cerber', 'cryptolocker',
                'teslacrypt', 'gandcrab', 'ryuk', 'maze', 'revil', 'darkside',
                'keylogger', 'spyware', 'trojan', 'backdoor', 'rootkit',
                'rat', 'botnet', 'ddos', 'ransomware', 'adware', 'hijacker'
            ]

            # Processus légitimes souvent usurpés (vérifier le chemin)
            suspicious_if_wrong_path = {
                'svchost.exe': r'C:\Windows\System32',
                'csrss.exe': r'C:\Windows\System32',
                'services.exe': r'C:\Windows\System32',
                'lsass.exe': r'C:\Windows\System32',
                'winlogon.exe': r'C:\Windows\System32',
                'explorer.exe': r'C:\Windows',
                'smss.exe': r'C:\Windows\System32',
                'wininit.exe': r'C:\Windows\System32',
                'taskmgr.exe': r'C:\Windows\System32',
            }

            # Récupérer la liste des processus avec PowerShell
            ps_cmd = '''
Get-Process | Select-Object Id, ProcessName, Path, Company,
    @{Name='Memory_MB';Expression={[math]::Round($_.WorkingSet64/1MB, 2)}} | ConvertTo-Json -Depth 3
'''
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_cmd],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            suspicious_critical = []
            suspicious_warning = []

            if result.returncode == 0 and result.stdout.strip():
                import json as json_module
                processes = json_module.loads(result.stdout)
                if not isinstance(processes, list):
                    processes = [processes]

                for proc in processes:
                    proc_name = (proc.get('ProcessName') or '').lower()
                    proc_path = proc.get('Path') or ''
                    proc_company = proc.get('Company') or ''
                    proc_mem = proc.get('Memory_MB') or 0

                    # Vérifier nom malveillant connu
                    for malware in known_malware:
                        if malware in proc_name:
                            suspicious_critical.append({
                                'name': proc.get('ProcessName'),
                                'pid': proc.get('Id'),
                                'path': proc_path,
                                'reason': f"Nom contient '{malware}' (malware connu)"
                            })
                            break

                    # Vérifier chemin suspect pour processus système
                    if proc_name + '.exe' in suspicious_if_wrong_path:
                        expected_path = suspicious_if_wrong_path[proc_name + '.exe']
                        if proc_path and expected_path.lower() not in proc_path.lower():
                            suspicious_critical.append({
                                'name': proc.get('ProcessName'),
                                'pid': proc.get('Id'),
                                'path': proc_path,
                                'reason': f"Chemin inattendu (devrait être dans {expected_path})"
                            })

            # Ajouter aux résultats du scan
            if suspicious_critical:
                critical_list = '\n'.join([f"  • {p['name']} (PID: {p['pid']}): {p['reason']}" for p in suspicious_critical[:5]])
                scan_results['critical'].append({
                    'category': '🦠 Processus Suspects',
                    'issue': f"{len(suspicious_critical)} processus potentiellement dangereux:\n{critical_list}",
                    'recommendation': 'URGENT: Analyser avec Windows Defender, Malwarebytes ou VirusTotal. Terminer les processus suspects.'
                })
            else:
                scan_results['ok'].append({
                    'category': '🦠 Processus Suspects',
                    'message': 'Aucun processus suspect détecté'
                })

            print(f"🔍 Analyse processus terminée ({len(suspicious_critical)} critiques)")

        except Exception as e:
            print(f"❌ Erreur analyse processus: {str(e)}")
            scan_results['ok'].append({
                'category': '🦠 Processus Suspects',
                'message': 'Analyse processus non disponible'
            })

        update_progress(95, "Finalisation du scan...")

        # ═══════════════════════════════════════════════════════════════════
        # 📊 RETOURNER RÉSULTATS DU SCAN
        # ═══════════════════════════════════════════════════════════════════
        update_progress(100, "Scan terminé !")
        print("✅ Scan total terminé !")

        return scan_results

    def _show_scan_results(self, scan_results):
        """Afficher les résultats du scan dans une fenêtre dédiée"""
        import tkinter as tk
        from tkinter import messagebox
        from datetime import datetime

        # Créer fenêtre popup (CTkToplevel pour CustomTkinter)
        results_window = ctk.CTkToplevel(self)
        results_window.title("🔍 Résultats du Scan Total - NiTriTe V20.0")
        results_window.geometry("1200x800")

        # Header amélioré avec gradient visuel
        header = ctk.CTkFrame(results_window, corner_radius=15, fg_color="#2196F3")
        header.pack(fill=tk.X, padx=20, pady=20)

        # Titre principal
        title = ctk.CTkLabel(
            header,
            text="🔍 SCAN TOTAL DU PC",
            font=("Segoe UI", 28, "bold"),
            text_color="white"
        )
        title.pack(pady=(20, 5))

        # Sous-titre avec date/heure
        subtitle = ctk.CTkLabel(
            header,
            text=f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
            font=("Segoe UI", 12),
            text_color="white"
        )
        subtitle.pack(pady=(0, 15))

        # Ligne décorative
        ctk.CTkFrame(header, height=3, fg_color="white").pack(fill=tk.X, padx=40, pady=(0, 15))

        # Statistiques rapides - VERSION AMÉLIORÉE
        stats_container = ctk.CTkFrame(results_window, fg_color="transparent")
        stats_container.pack(fill=tk.X, padx=20, pady=15)

        critical_count = len(scan_results['critical'])
        warning_count = len(scan_results['warning'])
        ok_count = len(scan_results['ok'])
        total_count = critical_count + warning_count + ok_count

        # Titre stats
        ctk.CTkLabel(
            stats_container,
            text="📊 RÉSUMÉ DU SCAN",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(0, 10))

        # Stats cards avec meilleur design
        stats_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
        stats_frame.pack(fill=tk.X)

        # Stat card CRITIQUES (rouge) - CONTRASTE AMÉLIORÉ
        critical_card = ctk.CTkFrame(stats_frame, corner_radius=12, fg_color="#FFD0D0", border_width=3, border_color="#CC0000")
        critical_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ctk.CTkLabel(
            critical_card,
            text=str(critical_count),
            font=("Segoe UI", 28, "bold"),
            text_color="#CC0000"
        ).pack(pady=(8, 0))

        ctk.CTkLabel(
            critical_card,
            text="❌ Critiques",
            font=("Segoe UI", 12, "bold"),
            text_color="#990000"
        ).pack(pady=(0, 8))

        # Stat card AVERTISSEMENTS (orange) - CONTRASTE AMÉLIORÉ
        warning_card = ctk.CTkFrame(stats_frame, corner_radius=12, fg_color="#FFE8CC", border_width=3, border_color="#CC6600")
        warning_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ctk.CTkLabel(
            warning_card,
            text=str(warning_count),
            font=("Segoe UI", 28, "bold"),
            text_color="#CC6600"
        ).pack(pady=(8, 0))

        ctk.CTkLabel(
            warning_card,
            text="⚠️ Avertissements",
            font=("Segoe UI", 12, "bold"),
            text_color="#994C00"
        ).pack(pady=(0, 8))

        # Stat card OK (vert) - CONTRASTE AMÉLIORÉ
        ok_card = ctk.CTkFrame(stats_frame, corner_radius=12, fg_color="#D0FFD0", border_width=3, border_color="#008800")
        ok_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ctk.CTkLabel(
            ok_card,
            text=str(ok_count),
            font=("Segoe UI", 28, "bold"),
            text_color="#008800"
        ).pack(pady=(8, 0))

        ctk.CTkLabel(
            ok_card,
            text="✅ Statuts OK",
            font=("Segoe UI", 12, "bold"),
            text_color="#006600"
        ).pack(pady=(0, 8))

        # Total checks
        ctk.CTkLabel(
            stats_container,
            text=f"Total : {total_count} vérifications effectuées",
            font=("Segoe UI", 11),
            text_color="gray"
        ).pack(pady=(10, 0))

        # Scroll frame pour résultats détaillés
        scroll_frame = ctk.CTkScrollableFrame(results_window)
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Séparateur
        ctk.CTkFrame(scroll_frame, height=2, fg_color="#DDDDDD").pack(fill=tk.X, pady=15)

        # PROBLÈMES CRITIQUES
        if scan_results['critical']:
            # Header de section avec fond coloré
            critical_header = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#FF4444")
            critical_header.pack(fill=tk.X, pady=(10, 5))

            ctk.CTkLabel(
                critical_header,
                text="❌ PROBLÈMES CRITIQUES",
                font=("Segoe UI", 18, "bold"),
                text_color="white"
            ).pack(side=tk.LEFT, padx=20, pady=12)

            ctk.CTkLabel(
                critical_header,
                text="⚠️ ACTION URGENTE REQUISE",
                font=("Segoe UI", 11),
                text_color="white"
            ).pack(side=tk.RIGHT, padx=20, pady=12)

            # Conteneur pour les items critiques
            critical_card = ctk.CTkFrame(scroll_frame, corner_radius=10, border_width=2, border_color="#FF4444")
            critical_card.pack(fill=tk.X, pady=(0, 10))

            # Système de colonnes : 6 items par ligne (plus d'espace horizontal)
            items_per_row = 6
            row_frame = None

            for i, item in enumerate(scan_results['critical'], 1):
                # Créer une nouvelle ligne tous les 9 items
                if (i - 1) % items_per_row == 0:
                    row_frame = ctk.CTkFrame(critical_card, fg_color="transparent")
                    row_frame.pack(fill=tk.X, padx=2, pady=0)

                issue_frame = ctk.CTkFrame(row_frame, corner_radius=4, fg_color="white", border_width=1, border_color="#FF8888")
                issue_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=0)

                # Numéro + Catégorie
                header_frame = ctk.CTkFrame(issue_frame, fg_color="#FFE5E5", corner_radius=3)
                header_frame.pack(fill=tk.X, padx=1, pady=0)

                ctk.CTkLabel(
                    header_frame,
                    text=f"#{i}",
                    font=("Segoe UI", 10, "bold"),
                    text_color="#CC0000",
                    width=20
                ).pack(side=tk.LEFT, padx=(1, 0), pady=0)

                ctk.CTkLabel(
                    header_frame,
                    text=item['category'],
                    font=("Segoe UI", 11, "bold"),
                    text_color="#990000",
                    anchor="w",
                    wraplength=120
                ).pack(side=tk.LEFT, padx=1, pady=0)

                # Problème
                ctk.CTkLabel(
                    issue_frame,
                    text=f"❌ {item['issue']}",
                    font=("Segoe UI", 10),
                    text_color="#CC0000",
                    anchor="w",
                    wraplength=120,
                    justify="left"
                ).pack(anchor="w", padx=2, pady=(0, 0))

                # Recommandation avec fond
                reco_frame = ctk.CTkFrame(issue_frame, fg_color="#FFF4E5", corner_radius=3, border_width=1, border_color="#FFD699")
                reco_frame.pack(fill=tk.X, padx=1, pady=(0, 0))

                ctk.CTkLabel(
                    reco_frame,
                    text=f"💡 {item['recommendation']}",
                    font=("Segoe UI", 9),
                    text_color="#664400",
                    anchor="w",
                    wraplength=115,
                    justify="left"
                ).pack(anchor="w", padx=2, pady=0)

                # Ajouter bouton pour rapport batterie si disponible
                if 'battery_report_path' in item and item['battery_report_path']:
                    ctk.CTkButton(
                        issue_frame,
                        text="📄 Voir Rapport Batterie Complet",
                        command=lambda path=item['battery_report_path']: os.startfile(path),
                        width=200,
                        height=30,
                        font=("Segoe UI", 11)
                    ).pack(anchor="w", padx=10, pady=(0, 5))

                # Bouton CrystalDiskInfo pour problèmes disques
                if '💿' in item.get('category', '') or 'disque' in item.get('category', '').lower() or 'disk' in item.get('category', '').lower():
                    ctk.CTkButton(
                        issue_frame,
                        text="🔬 Lancer CrystalDiskInfo (Analyse complète)",
                        command=lambda: self._launch_crystaldiskinfo(),
                        width=250,
                        height=30,
                        font=("Segoe UI", 11),
                        fg_color="#2196F3",
                        hover_color="#1976D2"
                    ).pack(anchor="w", padx=10, pady=(0, 5))

        # AVERTISSEMENTS
        if scan_results['warning']:
            # Header de section
            warning_header = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#FFA500")
            warning_header.pack(fill=tk.X, pady=(10, 5))

            ctk.CTkLabel(
                warning_header,
                text="⚠️ AVERTISSEMENTS",
                font=("Segoe UI", 18, "bold"),
                text_color="white"
            ).pack(side=tk.LEFT, padx=20, pady=12)

            ctk.CTkLabel(
                warning_header,
                text="À SURVEILLER",
                font=("Segoe UI", 11),
                text_color="white"
            ).pack(side=tk.RIGHT, padx=20, pady=12)

            # Conteneur
            warning_card = ctk.CTkFrame(scroll_frame, corner_radius=10, border_width=2, border_color="#FFA500")
            warning_card.pack(fill=tk.X, pady=(0, 10))

            # Système de colonnes : 6 items par ligne (plus d'espace horizontal)
            items_per_row = 6
            row_frame = None

            for i, item in enumerate(scan_results['warning'], 1):
                # Créer une nouvelle ligne tous les 9 items
                if (i - 1) % items_per_row == 0:
                    row_frame = ctk.CTkFrame(warning_card, fg_color="transparent")
                    row_frame.pack(fill=tk.X, padx=2, pady=0)

                issue_frame = ctk.CTkFrame(row_frame, corner_radius=4, fg_color="white", border_width=1, border_color="#FFAA44")
                issue_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=0)

                # Numéro + Catégorie
                header_frame = ctk.CTkFrame(issue_frame, fg_color="#FFF4E5", corner_radius=3)
                header_frame.pack(fill=tk.X, padx=1, pady=0)

                ctk.CTkLabel(
                    header_frame,
                    text=f"#{i}",
                    font=("Segoe UI", 10, "bold"),
                    text_color="#CC6600",
                    width=20
                ).pack(side=tk.LEFT, padx=(1, 0), pady=0)

                ctk.CTkLabel(
                    header_frame,
                    text=item['category'],
                    font=("Segoe UI", 11, "bold"),
                    text_color="#994C00",
                    anchor="w",
                    wraplength=120
                ).pack(side=tk.LEFT, padx=1, pady=0)

                # Problème
                ctk.CTkLabel(
                    issue_frame,
                    text=f"⚠️ {item['issue']}",
                    font=("Segoe UI", 10),
                    text_color="#CC6600",
                    anchor="w",
                    wraplength=120,
                    justify="left"
                ).pack(anchor="w", padx=2, pady=(0, 0))

                # Recommandation
                reco_frame = ctk.CTkFrame(issue_frame, fg_color="#FFF8E5", corner_radius=3, border_width=1, border_color="#FFE5AA")
                reco_frame.pack(fill=tk.X, padx=1, pady=(0, 0))

                ctk.CTkLabel(
                    reco_frame,
                    text=f"💡 {item['recommendation']}",
                    font=("Segoe UI", 9),
                    text_color="#665500",
                    anchor="w",
                    wraplength=115,
                    justify="left"
                ).pack(anchor="w", padx=2, pady=0)

                # Ajouter bouton pour rapport batterie si disponible
                if 'battery_report_path' in item and item['battery_report_path']:
                    ctk.CTkButton(
                        issue_frame,
                        text="📄 Voir Rapport Batterie Complet",
                        command=lambda path=item['battery_report_path']: os.startfile(path),
                        width=200,
                        height=30,
                        font=("Segoe UI", 11)
                    ).pack(anchor="w", padx=10, pady=(0, 5))

                # Bouton CrystalDiskInfo pour problèmes disques
                if '💿' in item.get('category', '') or 'disque' in item.get('category', '').lower() or 'disk' in item.get('category', '').lower():
                    ctk.CTkButton(
                        issue_frame,
                        text="🔬 Lancer CrystalDiskInfo (Analyse complète)",
                        command=lambda: self._launch_crystaldiskinfo(),
                        width=250,
                        height=30,
                        font=("Segoe UI", 11),
                        fg_color="#2196F3",
                        hover_color="#1976D2"
                    ).pack(anchor="w", padx=10, pady=(0, 5))

        # STATUTS OK - VERSION AMÉLIORÉE AVEC MEILLEURE ORGANISATION
        if scan_results['ok']:
            # Header de section
            ok_header = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#4CAF50")
            ok_header.pack(fill=tk.X, pady=(10, 5))

            ctk.CTkLabel(
                ok_header,
                text="✅ STATUTS NORMAUX",
                font=("Segoe UI", 18, "bold"),
                text_color="white"
            ).pack(side=tk.LEFT, padx=20, pady=12)

            ctk.CTkLabel(
                ok_header,
                text="TOUT VA BIEN",
                font=("Segoe UI", 11),
                text_color="white"
            ).pack(side=tk.RIGHT, padx=20, pady=12)

            # Conteneur
            ok_card = ctk.CTkFrame(scroll_frame, corner_radius=10, border_width=2, border_color="#4CAF50")
            ok_card.pack(fill=tk.X, pady=(0, 10))

            # Système de colonnes : 6 items par ligne (plus d'espace horizontal)
            items_per_row = 6
            row_frame = None

            for i, item in enumerate(scan_results['ok'], 1):
                # Créer une nouvelle ligne tous les 9 items
                if (i - 1) % items_per_row == 0:
                    row_frame = ctk.CTkFrame(ok_card, fg_color="transparent")
                    row_frame.pack(fill=tk.X, padx=2, pady=0)

                # Item avec largeur proportionnelle
                item_frame = ctk.CTkFrame(row_frame, corner_radius=4, fg_color="white", border_width=1, border_color="#88DD88")
                item_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=0)

                # Header avec numéro + catégorie
                header_frame = ctk.CTkFrame(item_frame, fg_color="#E8F5E9", corner_radius=3)
                header_frame.pack(fill=tk.X, padx=1, pady=0)

                ctk.CTkLabel(
                    header_frame,
                    text=f"#{i}",
                    font=("Segoe UI", 10, "bold"),
                    text_color="#2E7D32",
                    width=20
                ).pack(side=tk.LEFT, padx=(1, 0), pady=0)

                ctk.CTkLabel(
                    header_frame,
                    text=item['category'],
                    font=("Segoe UI", 11, "bold"),
                    text_color="#1B5E20",
                    anchor="w",
                    wraplength=120
                ).pack(side=tk.LEFT, padx=1, pady=0)

                # Message
                ctk.CTkLabel(
                    item_frame,
                    text=f"✓ {item['message']}",
                    font=("Segoe UI", 10),
                    text_color="#2E7D32",
                    anchor="w",
                    wraplength=120,
                    justify="left"
                ).pack(anchor="w", padx=2, pady=(0, 1))

                # Boutons actions
                button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                button_frame.pack(fill=tk.X, padx=10, pady=(0, 4))

                # Ajouter bouton pour rapport batterie si disponible OU si catégorie batterie
                if 'battery_report_path' in item and item['battery_report_path']:
                    ctk.CTkButton(
                        button_frame,
                        text="📄 Voir Rapport Batterie HTML",
                        command=lambda path=item['battery_report_path']: os.startfile(path),
                        width=200,
                        height=28,
                        font=("Segoe UI", 11),
                        fg_color="#4CAF50",
                        hover_color="#45A049"
                    ).pack(side=tk.LEFT, padx=5)
                elif '🔋' in item.get('category', '') or 'batterie' in item.get('category', '').lower():
                    # Bouton pour générer le rapport si pas encore fait
                    def generate_battery_report():
                        import subprocess
                        # Path déjà importé en haut du fichier (ligne 19)
                        try:
                            temp_dir = Path(get_portable_temp_dir())
                            temp_dir.mkdir(parents=True, exist_ok=True)
                            report_path = temp_dir / "battery-report.html"
                            result = subprocess.run(
                                ['powercfg', '/batteryreport', '/output', str(report_path)],
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                timeout=30
                            )
                            if result.returncode == 0 and report_path.exists():
                                os.startfile(str(report_path))
                            else:
                                from tkinter import messagebox
                                # Analyser l'erreur
                                output = (result.stderr or "") + (result.stdout or "")
                                output_lower = output.lower()
                                if "0x422" in output or "service" in output_lower:
                                    messagebox.showwarning("Service de diagnostic désactivé",
                                        "Le service 'DPS' (Service de stratégie de diagnostic)\n"
                                        "est désactivé sur votre PC.\n\n"
                                        "Pour l'activer:\n"
                                        "1. Ouvrez services.msc\n"
                                        "2. Trouvez 'Service de stratégie de diagnostic'\n"
                                        "3. Double-cliquez → Type: Manuel ou Automatique\n"
                                        "4. Cliquez 'Démarrer'")
                                elif "accès" in output_lower or "access" in output_lower:
                                    messagebox.showwarning("Droits requis",
                                        "Droits administrateur requis.\n\n"
                                        "Relancez NiTriTe en tant qu'administrateur.")
                                else:
                                    messagebox.showerror("Erreur PowerCfg",
                                        f"Code erreur: {result.returncode}\n\n{output[:200] if output else 'Aucun détail'}")
                        except subprocess.TimeoutExpired:
                            from tkinter import messagebox
                            messagebox.showerror("Timeout", "La génération du rapport a pris trop de temps.")
                        except Exception as e:
                            from tkinter import messagebox
                            messagebox.showerror("Erreur", f"Impossible de générer le rapport batterie:\n{str(e)}")

                    ctk.CTkButton(
                        button_frame,
                        text="🔋 Générer Rapport Batterie",
                        command=generate_battery_report,
                        width=200,
                        height=28,
                        font=("Segoe UI", 11),
                        fg_color="#FF9800",
                        hover_color="#F57C00"
                    ).pack(side=tk.LEFT, padx=5)

                # Bouton CrystalDiskInfo pour infos disques
                if '💿' in item.get('category', '') or 'disque' in item.get('category', '').lower() or 'disk' in item.get('category', '').lower() or 'santé' in item.get('category', '').lower():
                    ctk.CTkButton(
                        button_frame,
                        text="🔬 Analyser avec CrystalDiskInfo",
                        command=lambda: self._launch_crystaldiskinfo(),
                        width=220,
                        height=28,
                        font=("Segoe UI", 11),
                        fg_color="#2196F3",
                        hover_color="#1976D2"
                    ).pack(side=tk.LEFT, padx=5)

        # Frame pour boutons export et fermer
        bottom_frame = ctk.CTkFrame(results_window, fg_color="transparent")
        bottom_frame.pack(pady=20)

        # Label export
        ctk.CTkLabel(
            bottom_frame,
            text="📤 Exporter le scan:",
            font=("Segoe UI", 12, "bold")
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Boutons export
        ctk.CTkButton(
            bottom_frame,
            text="💾 TXT",
            command=lambda: self._export_scan_to_txt(scan_results),
            width=100,
            height=35,
            font=("Segoe UI", 12)
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            bottom_frame,
            text="🌐 HTML",
            command=lambda: self._export_scan_to_html(scan_results),
            width=100,
            height=35,
            font=("Segoe UI", 12)
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            bottom_frame,
            text="📝 MD",
            command=lambda: self._export_scan_to_md(scan_results),
            width=100,
            height=35,
            font=("Segoe UI", 12)
        ).pack(side=tk.LEFT, padx=5)

        # Bouton fermer
        ctk.CTkButton(
            bottom_frame,
            text="✖️ Fermer",
            command=results_window.destroy,
            width=120,
            height=35,
            font=("Segoe UI", 12, "bold"),
            fg_color="#FF4444",
            hover_color="#CC0000"
        ).pack(side=tk.LEFT, padx=(20, 0))

    def _export_scan_to_txt(self, scan_results):
        """Exporter résultats scan en fichier TXT"""
        from tkinter import messagebox, filedialog
        from datetime import datetime
        from pathlib import Path

        try:
            # Créer le dossier exports si nécessaire
            export_dir = Path("temp/scan_exports")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Nom de fichier avec timestamp (proposition par défaut)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"scan_total_{timestamp}.txt"

            # Demander à l'utilisateur de choisir le nom et l'emplacement
            filename = filedialog.asksaveasfilename(
                initialdir=export_dir,
                initialfile=default_filename,
                title="Enregistrer le rapport TXT",
                defaultextension=".txt",
                filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
            )

            # Si l'utilisateur annule
            if not filename:
                return

            filename = Path(filename)

            # Générer contenu TXT
            content = []
            content.append("=" * 80)
            content.append("NITRITE V20.0 - SCAN TOTAL DU PC")
            content.append("=" * 80)
            content.append(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            content.append("=" * 80)
            content.append("")

            # Statistiques
            critical_count = len(scan_results['critical'])
            warning_count = len(scan_results['warning'])
            ok_count = len(scan_results['ok'])

            content.append("RÉSUMÉ:")
            content.append(f"  - Problèmes critiques: {critical_count}")
            content.append(f"  - Avertissements: {warning_count}")
            content.append(f"  - Statuts OK: {ok_count}")
            content.append("")
            content.append("=" * 80)

            # Problèmes critiques
            if scan_results['critical']:
                content.append("")
                content.append("❌ PROBLÈMES CRITIQUES (ACTION URGENTE REQUISE)")
                content.append("-" * 80)
                for item in scan_results['critical']:
                    content.append(f"\n[{item['category']}]")
                    content.append(f"  Problème: {item['issue']}")
                    content.append(f"  Recommandation: {item['recommendation']}")
                    content.append("")

            # Avertissements
            if scan_results['warning']:
                content.append("")
                content.append("⚠️ AVERTISSEMENTS (À SURVEILLER)")
                content.append("-" * 80)
                for item in scan_results['warning']:
                    content.append(f"\n[{item['category']}]")
                    content.append(f"  Problème: {item['issue']}")
                    content.append(f"  Recommandation: {item['recommendation']}")
                    content.append("")

            # Statuts OK
            if scan_results['ok']:
                content.append("")
                content.append("✅ TOUT VA BIEN")
                content.append("-" * 80)
                for item in scan_results['ok']:
                    content.append(f"[{item['category']}] {item['message']}")

            content.append("")
            content.append("=" * 80)
            content.append("Fin du rapport - NiTriTe V20.0")
            content.append("=" * 80)

            # Écrire fichier
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            messagebox.showinfo(
                "Export réussi",
                f"Scan exporté avec succès !\n\nFichier: {filename}"
            )

            # Ouvrir le fichier
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Erreur export", f"Impossible d'exporter: {str(e)}")

    def _get_battery_details_for_export(self, scan_results):
        """Extraire informations batterie détaillées pour export HTML depuis scan_results"""
        battery_info = {
            'has_battery': False,
            'design_capacity': 'N/A',
            'full_capacity': 'N/A',
            'wear_percent': 'N/A',
            'serial_number': 'N/A',
            'model': 'N/A',
            'manufacturer': 'N/A',
            'chemistry': 'N/A',
            'cycle_count': 'N/A'
        }

        try:
            # Chercher dans tous les résultats du scan
            all_results = scan_results['ok'] + scan_results['warning'] + scan_results['critical']

            for result in all_results:
                category = result.get('category', '')
                if '🔋' in category or 'batterie' in category.lower():
                    battery_info['has_battery'] = True

                    # Utiliser les données structurées si disponibles
                    if 'design_capacity' in result and 'full_capacity' in result:
                        design_cap = result['design_capacity']
                        full_cap = result['full_capacity']
                        wear = result.get('wear_percent', 0)

                        battery_info['design_capacity'] = f"{design_cap:,} mWh"
                        battery_info['full_capacity'] = f"{full_cap:,} mWh"
                        battery_info['wear_percent'] = f"{wear:.1f}%"

                        # Extraire aussi les nouvelles données
                        if 'name' in result:
                            battery_info['model'] = result['name']
                        if 'manufacturer' in result:
                            battery_info['manufacturer'] = result['manufacturer']
                        if 'serial_number' in result:
                            battery_info['serial_number'] = result['serial_number']
                        if 'chemistry' in result:
                            battery_info['chemistry'] = result['chemistry']
                        if 'cycle_count' in result:
                            battery_info['cycle_count'] = str(result['cycle_count'])

                        print(f"[DEBUG BATTERIE] Données complètes extraites: {result.get('name', 'N/A')} - {full_cap:,} / {design_cap:,} mWh")
                    else:
                        # Fallback: Extraire depuis le texte (ancienne méthode)
                        import re
                        text = result.get('message', '') or result.get('issue', '')
                        print(f"[DEBUG BATTERIE] Fallback - Texte extrait: {text}")

                        capacity_match = re.search(r'Capacité:\s*([0-9,]+)\s*mWh\s*/\s*([0-9,]+)\s*mWh', text)
                        wear_match = re.search(r'Usure:\s*([0-9.]+)%', text)

                        if capacity_match:
                            full_capacity = capacity_match.group(1)
                            design_capacity = capacity_match.group(2)
                            battery_info['full_capacity'] = f"{full_capacity} mWh"
                            battery_info['design_capacity'] = f"{design_capacity} mWh"
                            print(f"[DEBUG BATTERIE] Capacités extraites: {full_capacity} / {design_capacity}")

                        if wear_match:
                            battery_info['wear_percent'] = f"{wear_match.group(1)}%"
                            print(f"[DEBUG BATTERIE] Usure extraite: {wear_match.group(1)}%")

                    # Essayer d'extraire info supplémentaires via WMI (métadonnées uniquement)
                    try:
                        import wmi
                        w = wmi.WMI()

                        for bat in w.Win32_Battery():
                            device_id = getattr(bat, 'DeviceID', None)
                            if device_id:
                                battery_info['serial_number'] = device_id

                            name = getattr(bat, 'Name', None)
                            if name:
                                battery_info['model'] = name

                            caption = getattr(bat, 'Caption', None)
                            if caption:
                                battery_info['manufacturer'] = caption

                            chemistry = getattr(bat, 'Chemistry', None)
                            chemistry_types = {
                                1: "Autre", 2: "Inconnu", 3: "Lead Acid",
                                4: "Nickel Cadmium", 5: "Nickel Metal Hydride",
                                6: "Lithium-ion", 7: "Zinc air", 8: "Lithium Polymer"
                            }
                            if chemistry in chemistry_types:
                                battery_info['chemistry'] = chemistry_types[chemistry]

                            break
                    except:
                        pass

                    break

        except Exception as e:
            print(f"Erreur extraction batterie: {e}")

        return battery_info

    def _export_scan_to_html(self, scan_results):
        """Exporter résultats scan en fichier HTML stylisé"""
        from tkinter import messagebox, filedialog
        from datetime import datetime
        from pathlib import Path

        try:
            # Créer le dossier exports si nécessaire
            export_dir = Path("temp/scan_exports")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Nom de fichier avec timestamp (proposition par défaut)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"scan_total_{timestamp}.html"

            # Demander à l'utilisateur de choisir le nom et l'emplacement
            filename = filedialog.asksaveasfilename(
                initialdir=export_dir,
                initialfile=default_filename,
                title="Enregistrer le rapport HTML",
                defaultextension=".html",
                filetypes=[("Fichiers HTML", "*.html"), ("Tous les fichiers", "*.*")]
            )

            # Si l'utilisateur annule
            if not filename:
                return

            filename = Path(filename)

            # Statistiques
            critical_count = len(scan_results['critical'])
            warning_count = len(scan_results['warning'])
            ok_count = len(scan_results['ok'])

            # Informations batterie détaillées
            battery_details = self._get_battery_details_for_export(scan_results)

            # Générer HTML
            html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NiTriTe - Scan Total PC</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 3px solid #e9ecef;
        }}
        .stat-card {{
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            min-width: 150px;
        }}
        .stat-card.critical {{
            background: #ffe5e5;
            border: 2px solid #ff4444;
        }}
        .stat-card.warning {{
            background: #fff4e5;
            border: 2px solid #ffa500;
        }}
        .stat-card.ok {{
            background: #e5ffe5;
            border: 2px solid #00ff00;
        }}
        .stat-card h3 {{
            font-size: 2.5em;
            margin-bottom: 5px;
        }}
        .stat-card.critical h3 {{ color: #ff4444; }}
        .stat-card.warning h3 {{ color: #ffa500; }}
        .stat-card.ok h3 {{ color: #00aa00; }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid;
        }}
        .section-title.critical {{
            color: #ff4444;
            border-color: #ff4444;
        }}
        .section-title.warning {{
            color: #ffa500;
            border-color: #ffa500;
        }}
        .section-title.ok {{
            color: #00aa00;
            border-color: #00aa00;
        }}
        .item {{
            background: #f8f9fa;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 5px solid;
        }}
        .item.critical {{ border-color: #ff4444; }}
        .item.warning {{ border-color: #ffa500; }}
        .item.ok {{ border-color: #00aa00; }}
        .item-category {{
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .item-issue {{
            margin-bottom: 10px;
            white-space: pre-wrap;
        }}
        .item-recommendation {{
            color: #555;
            font-style: italic;
            padding: 10px;
            background: white;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 NiTriTe V20.0</h1>
            <p>Scan Total du PC - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card critical">
                <h3>{critical_count}</h3>
                <p>Problèmes Critiques</p>
            </div>
            <div class="stat-card warning">
                <h3>{warning_count}</h3>
                <p>Avertissements</p>
            </div>
            <div class="stat-card ok">
                <h3>{ok_count}</h3>
                <p>Statuts OK</p>
            </div>
        </div>

"""

            # Section Batterie (si disponible)
            if battery_details['has_battery']:
                html += f"""
        <div class="battery-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; margin: 20px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.2);">
            <h2 style="color: white; font-size: 1.8em; margin-bottom: 20px; text-align: center;">🔋 INFORMATIONS BATTERIE DÉTAILLÉES</h2>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Modèle / Référence</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #333;">{battery_details['model']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Fabricant</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #333;">{battery_details['manufacturer']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Numéro de Série / ID</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #333;">{battery_details['serial_number']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Type de Chimie</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #333;">{battery_details['chemistry']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Capacité Originale (Design)</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #4CAF50;">{battery_details['design_capacity']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Capacité Actuelle (Full Charge)</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #2196F3;">{battery_details['full_capacity']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px; border: 3px solid #FF9800;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Usure Totale</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #FF5722;">{battery_details['wear_percent']}</div>
                </div>

                <div style="background: rgba(255,255,255,0.95); padding: 20px; border-radius: 10px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 5px;">Nombre de Cycles</div>
                    <div style="font-size: 1.3em; font-weight: bold; color: #9C27B0;">{battery_details['cycle_count']}</div>
                </div>
            </div>

            <div style="background: rgba(255,255,255,0.9); padding: 15px; border-radius: 10px; margin-top: 15px; text-align: center; font-size: 0.9em; color: #555;">
                <strong>💡 Note:</strong> Ces informations proviennent du rapport batterie Windows (powercfg /batteryreport). L'usure augmente avec le temps et les cycles de charge.
            </div>
        </div>
"""

            html += """
        <div class="content">
"""

            # Problèmes critiques
            if scan_results['critical']:
                html += """
            <div class="section">
                <h2 class="section-title critical">❌ PROBLÈMES CRITIQUES (ACTION URGENTE REQUISE)</h2>
"""
                for item in scan_results['critical']:
                    issue = item['issue'].replace('\n', '<br>')
                    recommendation = item['recommendation'].replace('\n', '<br>')
                    html += f"""
                <div class="item critical">
                    <div class="item-category">{item['category']}</div>
                    <div class="item-issue">{issue}</div>
                    <div class="item-recommendation">💡 Recommandation: {recommendation}</div>
                </div>
"""
                html += "            </div>\n"

            # Avertissements
            if scan_results['warning']:
                html += """
            <div class="section">
                <h2 class="section-title warning">⚠️ AVERTISSEMENTS (À SURVEILLER)</h2>
"""
                for item in scan_results['warning']:
                    issue = item['issue'].replace('\n', '<br>')
                    recommendation = item['recommendation'].replace('\n', '<br>')
                    html += f"""
                <div class="item warning">
                    <div class="item-category">{item['category']}</div>
                    <div class="item-issue">{issue}</div>
                    <div class="item-recommendation">💡 Recommandation: {recommendation}</div>
                </div>
"""
                html += "            </div>\n"

            # Statuts OK
            if scan_results['ok']:
                html += """
            <div class="section">
                <h2 class="section-title ok">✅ TOUT VA BIEN</h2>
"""
                for item in scan_results['ok']:
                    message = item['message'].replace('\n', '<br>')
                    html += f"""
                <div class="item ok">
                    <div class="item-category">{item['category']}</div>
                    <div class="item-issue">{message}</div>
                </div>
"""
                html += "            </div>\n"

            html += """
        </div>

        <div class="footer">
            <p>📊 Rapport généré par NiTriTe V20.0 - L'outil ultime de maintenance PC</p>
        </div>
    </div>
</body>
</html>
"""

            # Écrire fichier
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)

            messagebox.showinfo(
                "Export réussi",
                f"Scan exporté avec succès en HTML !\n\nFichier: {filename}"
            )

            # Ouvrir le fichier dans le navigateur
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Erreur export", f"Impossible d'exporter en HTML: {str(e)}")

    def _export_scan_to_md(self, scan_results):
        """Exporter résultats scan en fichier Markdown"""
        from tkinter import messagebox, filedialog
        from datetime import datetime
        from pathlib import Path

        try:
            # Créer le dossier exports si nécessaire
            export_dir = Path("temp/scan_exports")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Nom de fichier avec timestamp (proposition par défaut)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"scan_total_{timestamp}.md"

            # Demander à l'utilisateur de choisir le nom et l'emplacement
            filename = filedialog.asksaveasfilename(
                initialdir=export_dir,
                initialfile=default_filename,
                title="Enregistrer le rapport Markdown",
                defaultextension=".md",
                filetypes=[("Fichiers Markdown", "*.md"), ("Tous les fichiers", "*.*")]
            )

            # Si l'utilisateur annule
            if not filename:
                return

            filename = Path(filename)

            # Statistiques
            critical_count = len(scan_results['critical'])
            warning_count = len(scan_results['warning'])
            ok_count = len(scan_results['ok'])

            # Générer Markdown
            md = []
            md.append("# 🔍 NiTriTe V20.0 - Scan Total du PC")
            md.append("")
            md.append(f"**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            md.append("")
            md.append("---")
            md.append("")

            # Résumé
            md.append("## 📊 Résumé")
            md.append("")
            md.append("| Catégorie | Nombre |")
            md.append("|-----------|--------|")
            md.append(f"| ❌ Problèmes Critiques | {critical_count} |")
            md.append(f"| ⚠️ Avertissements | {warning_count} |")
            md.append(f"| ✅ Statuts OK | {ok_count} |")
            md.append("")
            md.append("---")
            md.append("")

            # Problèmes critiques
            if scan_results['critical']:
                md.append("## ❌ PROBLÈMES CRITIQUES (ACTION URGENTE REQUISE)")
                md.append("")
                for i, item in enumerate(scan_results['critical'], 1):
                    md.append(f"### {i}. {item['category']}")
                    md.append("")
                    md.append(f"**Problème:**")
                    md.append(f"{item['issue']}")
                    md.append("")
                    md.append(f"**💡 Recommandation:**")
                    md.append(f"{item['recommendation']}")
                    md.append("")
                    md.append("---")
                    md.append("")

            # Avertissements
            if scan_results['warning']:
                md.append("## ⚠️ AVERTISSEMENTS (À SURVEILLER)")
                md.append("")
                for i, item in enumerate(scan_results['warning'], 1):
                    md.append(f"### {i}. {item['category']}")
                    md.append("")
                    md.append(f"**Problème:**")
                    md.append(f"{item['issue']}")
                    md.append("")
                    md.append(f"**💡 Recommandation:**")
                    md.append(f"{item['recommendation']}")
                    md.append("")
                    md.append("---")
                    md.append("")

            # Statuts OK
            if scan_results['ok']:
                md.append("## ✅ TOUT VA BIEN")
                md.append("")
                for item in scan_results['ok']:
                    md.append(f"- **{item['category']}:** {item['message']}")
                md.append("")

            md.append("---")
            md.append("")
            md.append("*📊 Rapport généré par NiTriTe V20.0 - L'outil ultime de maintenance PC*")

            # Écrire fichier
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(md))

            messagebox.showinfo(
                "Export réussi",
                f"Scan exporté avec succès en Markdown !\n\nFichier: {filename}"
            )

            # Ouvrir le fichier
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Erreur export", f"Impossible d'exporter en Markdown: {str(e)}")

    # === MÉTHODES MASTER OUTILS ===

    def _execute_tool(self, tool_name, tool_action):
        """Exécuter outil (commande ou URL)"""
        import subprocess
        import webbrowser

        print(f" Exécution: {tool_name}")
        print(f"   Action: {tool_action}")

        try:
            # Déterminer si c'est une URL ou une commande
            if tool_action.startswith(('http://', 'https://', 'ms-settings:', 'windowsdefender:')):
                # C'est une URL - ouvrir dans le navigateur
                print(f" Ouverture URL: {tool_action}")
                webbrowser.open(tool_action)

            else:
                # C'est une commande système - l'exécuter
                print(f" Exécution commande: {tool_action}")

                # Certaines commandes doivent être lancées directement
                direct_commands = [
                    'msinfo32', 'dxdiag', 'taskmgr', 'msconfig',
                    'resmon', 'diskmgmt.msc', 'compmgmt.msc', 'services.msc',
                    'dfrgui', 'regedit', 'winver', 'sysdm.cpl'
                ]

                # Vérifier si c'est une commande directe
                is_direct = any(cmd in tool_action for cmd in direct_commands)

                if is_direct:
                    # Lancer directement sans cmd
                    subprocess.Popen(tool_action, shell=True)
                else:
                    # Utiliser cmd.exe pour autres commandes
                    subprocess.Popen(
                        ['cmd.exe', '/c', 'start', tool_action],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

        except Exception as e:
            print(f" Erreur exécution {tool_name}: {e}")
            from tkinter import messagebox
            messagebox.showerror(
                "Erreur d'exécution",
                f"Impossible d'exécuter {tool_name}:\n\n{str(e)}"
            )

    def _launch_crystaldiskinfo(self):
        """Lancer CrystalDiskInfo en mode portable depuis logiciel/"""
        from tkinter import messagebox
        import subprocess
        from pathlib import Path

        try:
            # Chercher CrystalDiskInfo dans logiciel/ ET ses sous-dossiers
            logiciel_folder = Path("logiciel")

            # Lister tous les fichiers .exe
            crystaldisk_exe = None

            if logiciel_folder.exists() and logiciel_folder.is_dir():
                # PRIORITÉ 1 : Chercher dans logiciel/CrystalDisk/
                crystaldisk_subfolder = logiciel_folder / "CrystalDisk"
                if crystaldisk_subfolder.exists():
                    for exe_file in crystaldisk_subfolder.glob("*.exe"):
                        if 'disk' in exe_file.name.lower() or 'crystal' in exe_file.name.lower():
                            crystaldisk_exe = exe_file
                            print(f"🔬 CrystalDiskInfo trouvé dans CrystalDisk/: {crystaldisk_exe}")
                            break

                # PRIORITÉ 2 : Chercher récursivement dans tous les sous-dossiers
                if not crystaldisk_exe:
                    for exe_file in logiciel_folder.rglob("*.exe"):
                        if 'disk' in exe_file.name.lower() or 'crystal' in exe_file.name.lower():
                            crystaldisk_exe = exe_file
                            print(f"🔬 CrystalDiskInfo trouvé: {crystaldisk_exe}")
                            break

            if crystaldisk_exe:
                print(f"🔬 Lancement CrystalDiskInfo: {crystaldisk_exe}")
                subprocess.Popen(str(crystaldisk_exe), shell=True)
                messagebox.showinfo(
                    "CrystalDiskInfo",
                    f"CrystalDiskInfo lancé !\n\nCe logiciel analyse la santé de vos disques durs/SSD.\n\nVérifiez:\n• Health Status (Good/Caution/Bad)\n• Température\n• Heures d'utilisation\n• Secteurs réalloués"
                )
            else:
                # CrystalDiskInfo non trouvé - proposer de le télécharger
                response = messagebox.askyesnocancel(
                    "CrystalDiskInfo non trouvé",
                    "CrystalDiskInfo n'a pas été trouvé dans le dossier logiciel/.\n\n"
                    "Voulez-vous:\n"
                    "• OUI: Ouvrir la page de téléchargement CrystalDiskInfo\n"
                    "• NON: Aller dans Diagnostic pour télécharger via NiTriTe\n"
                    "• ANNULER: Fermer"
                )

                if response is True:
                    # Ouvrir page download
                    import webbrowser
                    webbrowser.open("https://crystalmark.info/en/software/crystaldiskinfo/")
                elif response is False:
                    # Message pour aller dans Diagnostic
                    messagebox.showinfo(
                        "Télécharger via NiTriTe",
                        "Allez dans:\n\nDiagnostic > CrystalDiskInfo\n\nPour télécharger et installer le logiciel."
                    )

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer CrystalDiskInfo:\n\n{str(e)}"
            )

    def _launch_benchmaster(self):
        """Lancer BenchMaster.AI - Sonde de diagnostic OrdiPlus"""
        import webbrowser
        from tkinter import messagebox

        # Instructions d'installation
        instructions = """BENCHMASTER.AI - Sonde de Diagnostic OrdiPlus

Le lien va s'ouvrir dans votre navigateur.

INSTRUCTIONS D'INSTALLATION:

1. Sur la page web, selectionnez votre version Windows

2. Deux fichiers vont se telecharger:
   • BenchMasterProbe.exe
   • BenchMasterProbe.bmat

3. IMPORTANT: Placez les 2 fichiers dans le MEME dossier

4. Double-cliquez sur BenchMasterProbe.exe

5. Si Windows SmartScreen apparait:
   • Cliquez sur "Plus d'infos"
   • Puis "Executer quand meme"

6. La sonde se connectera a votre compte OrdiPlus
   et effectuera le diagnostic automatiquement

Le diagnostic sera visible sur votre tableau de bord OrdiPlus.
"""

        # Afficher les instructions
        response = messagebox.showinfo(
            "BenchMaster.AI - Instructions",
            instructions
        )

        # Ouvrir le lien dans le navigateur
        webbrowser.open("https://diag.ordi-plus.fr/client/onboarding")

        messagebox.showinfo(
            "BenchMaster.AI",
            "La page de telechargement s'est ouverte dans votre navigateur.\n\n"
            "Suivez les instructions pour telecharger et installer la sonde."
        )

    def _activate_windows_office(self):
        """Activer Windows et Office"""
        from tkinter import messagebox
        response = messagebox.askyesno(
            "Activation Windows/Office",
            "Cette action va exécuter le script MAS (Microsoft Activation Scripts) depuis Internet.\n\n"
            " Assurez-vous de comprendre ce que vous faites.\n\n"
            "Continuer ?",
            icon='warning'
        )
        if not response:
            return
        try:
            import tempfile
            script_content = "irm https://get.activated.win | iex"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                f.write(script_content)
                script_path = f.name
            cmd = f'powershell -Command "Start-Process powershell -ArgumentList \'-ExecutionPolicy Bypass -File \"{script_path}\"\' -Verb RunAs"'
            subprocess.Popen(cmd, shell=True)
            messagebox.showinfo(
                "Activation lancée",
                "Le script MAS a été lancé en mode administrateur.\n\n"
                "Suivez les instructions dans la fenêtre PowerShell qui s'ouvre."
            )
            def cleanup():
                import time
                time.sleep(60)
                try:
                    os.remove(script_path)
                except:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer le script d'activation:\n\n{str(e)}")

    def _open_temp_folder(self):
        """Ouvrir le dossier Temp"""
        try:
            temp_path = os.path.expandvars("%TEMP%")
            subprocess.Popen(f'explorer "{temp_path}"', shell=True)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier Temp:\n\n{str(e)}")

    def _open_appdata_local(self):
        """Ouvrir le dossier LocalAppData"""
        try:
            appdata_path = os.path.expandvars("%LOCALAPPDATA%")
            subprocess.Popen(f'explorer "{appdata_path}"', shell=True)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible d'ouvrir AppData Local:\n\n{str(e)}")

    def _update_all_apps(self):
        """Mettre à jour toutes les applications via WinGet"""
        from tkinter import messagebox

        def run_update():
            try:
                # Demander confirmation
                result = messagebox.askyesno(
                    "Mise à jour globale",
                    "Voulez-vous mettre à jour toutes les applications installées via WinGet?\n\n"
                    "Cette opération peut prendre plusieurs minutes.",
                    icon='question'
                )

                if not result:
                    return

                messagebox.showinfo(
                    "Mise à jour en cours",
                    "La mise à jour a démarré.\n\n"
                    "Une fenêtre PowerShell va s'ouvrir pour afficher la progression.\n"
                    "Ne fermez pas cette fenêtre."
                )

                # Lancer winget upgrade --all dans PowerShell visible
                subprocess.Popen(
                    ['powershell', '-NoExit', '-Command',
                     'Write-Host "Mise a jour de toutes les applications..." -ForegroundColor Cyan; '
                     'winget upgrade --all --accept-source-agreements --accept-package-agreements; '
                     'Write-Host "`nTermine! Vous pouvez fermer cette fenetre." -ForegroundColor Green'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lancer la mise à jour:\n\n{str(e)}")

        # Lancer dans un thread pour ne pas bloquer l'UI
        threading.Thread(target=run_update, daemon=True).start()

    def _update_nvidia_drivers(self):
        """Ouvrir la page de téléchargement des drivers NVIDIA"""
        import webbrowser
        from tkinter import messagebox

        try:
            # Essayer d'ouvrir GeForce Experience si installé
            # Sinon ouvrir la page web de téléchargement
            try:
                subprocess.Popen(['C:\\Program Files\\NVIDIA Corporation\\NVIDIA GeForce Experience\\NVIDIA GeForce Experience.exe'])
                messagebox.showinfo(
                    "NVIDIA Drivers",
                    "GeForce Experience a été lancé.\n\n"
                    "Utilisez-le pour vérifier et installer les derniers drivers."
                )
            except:
                # GeForce Experience non installé, ouvrir le site web
                webbrowser.open('https://www.nvidia.com/Download/index.aspx?lang=fr')
                messagebox.showinfo(
                    "NVIDIA Drivers",
                    "La page de téléchargement des drivers NVIDIA a été ouverte dans votre navigateur.\n\n"
                    "Sélectionnez votre carte graphique pour télécharger les derniers drivers."
                )
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir les drivers NVIDIA:\n\n{str(e)}")

    def _update_amd_drivers(self):
        """Ouvrir la page de téléchargement des drivers AMD"""
        import webbrowser
        from tkinter import messagebox

        try:
            # Essayer d'ouvrir AMD Radeon Software si installé
            # Sinon ouvrir la page web de téléchargement
            try:
                subprocess.Popen(['C:\\Program Files\\AMD\\CNext\\CNext\\RadeonSoftware.exe'])
                messagebox.showinfo(
                    "AMD Drivers",
                    "AMD Radeon Software a été lancé.\n\n"
                    "Utilisez-le pour vérifier et installer les derniers drivers."
                )
            except:
                # Radeon Software non installé, ouvrir le site web
                webbrowser.open('https://www.amd.com/fr/support')
                messagebox.showinfo(
                    "AMD Drivers",
                    "La page de téléchargement des drivers AMD a été ouverte dans votre navigateur.\n\n"
                    "Utilisez l'outil de détection automatique ou sélectionnez votre carte graphique."
                )
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir les drivers AMD:\n\n{str(e)}")

    def _repair_windows_image(self):
        """Réparer l'image Windows avec DISM"""
        from tkinter import messagebox

        result = messagebox.askyesno(
            "Réparer l'image Windows",
            "Cette opération va réparer l'image système Windows avec DISM.\n\n"
            "Cela peut prendre 10-30 minutes.\n\n"
            "Une fenêtre PowerShell va s'ouvrir en mode Administrateur.\n\n"
            "Continuer ?",
            icon='question'
        )

        if not result:
            return

        try:
            messagebox.showinfo(
                "Réparation en cours",
                "La réparation de l'image Windows a démarré.\n\n"
                "Une fenêtre PowerShell admin va s'ouvrir.\n"
                "Ne la fermez pas pendant l'opération."
            )

            # Commande DISM
            dism_cmd = (
                'Write-Host "Reparation de l\'\'image Windows..." -ForegroundColor Cyan; '
                'Write-Host "Cette operation peut prendre 10-30 minutes." -ForegroundColor Yellow; '
                'Write-Host ""; '
                'DISM /Online /Cleanup-Image /RestoreHealth; '
                'Write-Host ""; '
                'Write-Host "Termine! Vous pouvez fermer cette fenetre." -ForegroundColor Green'
            )

            run_as_admin(dism_cmd)

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer DISM:\n\n{str(e)}")

    def _open_user_properties(self):
        """Ouvrir les propriétés du dossier utilisateur"""
        from tkinter import messagebox

        try:
            # Obtenir le chemin du dossier utilisateur
            user_folder = os.path.expandvars("%USERPROFILE%")

            # Ouvrir simplement l'explorateur sur le dossier Users
            users_folder = os.path.dirname(user_folder)
            subprocess.Popen(f'explorer "{users_folder}"', shell=True)

            messagebox.showinfo(
                "Dossier Utilisateurs",
                f"Dossier ouvert: {users_folder}\n\n"
                "Vous pouvez voir tous les utilisateurs et faire clic-droit > Propriétés\n"
                "sur n'importe quel dossier utilisateur."
            )

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n\n{str(e)}")

    def _run_chkdsk(self):
        """Lancer un CHKDSK complet"""
        from tkinter import messagebox

        result = messagebox.askyesno(
            "CHKDSK Complet",
            "Cette opération va analyser et réparer le disque C:\n\n"
            " Le PC devra redémarrer pour effectuer la vérification.\n\n"
            "Options:\n"
            "• /F : Corrige les erreurs sur le disque\n"
            "• /R : Recherche les secteurs défectueux et récupère les données\n\n"
            "Continuer ?",
            icon='warning'
        )

        if not result:
            return

        try:
            # Lancer CHKDSK avec /F /R dans PowerShell
            subprocess.Popen(
                ['powershell', '-NoExit', '-Command',
                 'Write-Host "Planification de CHKDSK au prochain redemarrage..." -ForegroundColor Cyan; '
                 'Write-Host ""; '
                 'chkdsk C: /F /R; '
                 'Write-Host ""; '
                 'Write-Host "Le CHKDSK s\'executera au prochain redemarrage." -ForegroundColor Green; '
                 'Write-Host "Tapez \'shutdown /r /t 60\' pour redemarrer dans 60 secondes." -ForegroundColor Yellow'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            messagebox.showinfo(
                "CHKDSK planifié",
                "CHKDSK a été planifié pour le prochain redémarrage.\n\n"
                "Le PC va redémarrer et effectuer la vérification complète du disque.\n\n"
                "Cela peut prendre 1-2 heures selon la taille du disque."
            )

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer CHKDSK:\n\n{str(e)}")

    # === CUSTOM PORTABLE APPS MANAGER ===

    def _get_custom_tools_json_path(self):
        """Retourne le chemin du fichier JSON de config des outils personnalisés"""
        try:
            # Utiliser le chemin portable si disponible
            if hasattr(sys, 'frozen'):
                # Mode PyInstaller
                app_dir = Path(sys.executable).parent
            else:
                # Mode développement
                app_dir = Path(__file__).parent.parent.parent

            json_path = app_dir / "data" / "custom_diagnostic_tools.json"
            return json_path
        except:
            # Fallback
            return Path("data/custom_diagnostic_tools.json")

    def _get_custom_folder_path(self):
        """Retourne le chemin du dossier logiciel/Custom"""
        try:
            if hasattr(sys, 'frozen'):
                app_dir = Path(sys.executable).parent
            else:
                app_dir = Path(__file__).parent.parent.parent

            custom_folder = app_dir / "logiciel" / "Custom"
            return custom_folder
        except:
            return Path("logiciel/Custom")

    def _load_custom_tools(self):
        """
        Charger les outils personnalisés depuis JSON + scan automatique du dossier Custom

        Returns:
            list: Liste des outils personnalisés
        """
        all_custom_tools = []

        try:
            json_path = self._get_custom_tools_json_path()

            # Charger le JSON
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Outils manuellement ajoutés
                manual_tools = config.get("custom_tools", [])
                all_custom_tools.extend(manual_tools)

                # Scanner le dossier si auto-scan activé
                if config.get("auto_scan_enabled", True):
                    scanned_tools = self._scan_custom_folder()

                    # Fusionner sans doublons (prioriser les manuels)
                    manual_ids = {tool['id'] for tool in manual_tools}
                    for scanned in scanned_tools:
                        if scanned['id'] not in manual_ids:
                            all_custom_tools.append(scanned)
            else:
                # Si JSON n'existe pas, juste scanner
                all_custom_tools = self._scan_custom_folder()

        except Exception as e:
            print(f"Erreur chargement custom tools: {e}")
            import traceback
            traceback.print_exc()

        return all_custom_tools

    def _scan_custom_folder(self):
        """
        Scanner le dossier logiciel/Custom pour auto-détecter les .exe

        Returns:
            list: Liste des outils auto-découverts
        """
        scanned_tools = []

        try:
            custom_folder = self._get_custom_folder_path()

            if not custom_folder.exists():
                # Créer le dossier s'il n'existe pas
                custom_folder.mkdir(parents=True, exist_ok=True)
                return []

            # Scanner tous les .exe dans le dossier (pas récursif)
            exe_files = list(custom_folder.glob("*.exe"))

            for exe_file in exe_files:
                # Créer un ID unique basé sur le nom du fichier
                tool_id = f"auto_{exe_file.stem.lower().replace(' ', '_')}"

                # Nom lisible
                tool_name = exe_file.stem

                # Emoji par défaut pour auto-découverts
                emoji = "📦"

                scanned_tools.append({
                    "id": tool_id,
                    "name": tool_name,
                    "emoji": emoji,
                    "exe_path": str(exe_file),
                    "auto_discovered": True,
                    "enabled": True,
                    "created_date": datetime.now().strftime("%Y-%m-%d")
                })

        except Exception as e:
            print(f"Erreur scan custom folder: {e}")

        return scanned_tools

    def _save_custom_tools(self, tools_list):
        """
        Sauvegarder les outils personnalisés dans le JSON

        Args:
            tools_list: Liste des outils à sauvegarder (seulement manuels, pas auto-découverts)
        """
        try:
            json_path = self._get_custom_tools_json_path()

            # Charger config existante
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {
                    "version": "1.0",
                    "auto_scan_enabled": True,
                    "custom_folder": "logiciel/Custom"
                }

            # Filtrer pour ne garder que les outils manuels (pas auto-discovered)
            manual_tools = [t for t in tools_list if not t.get("auto_discovered", False)]

            # Mettre à jour
            config["custom_tools"] = manual_tools

            # Sauvegarder
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Erreur sauvegarde custom tools: {e}")
            import traceback
            traceback.print_exc()

    def _add_custom_tool_dialog(self):
        """Dialog pour ajouter manuellement un outil personnalisé"""
        from tkinter import filedialog, messagebox

        # Créer fenêtre dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Ajouter une Application Portable")
        dialog.geometry("750x850")
        dialog.transient(self)
        dialog.grab_set()

        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (750 // 2)
        y = (dialog.winfo_screenheight() // 2) - (850 // 2)
        dialog.geometry(f"750x850+{x}+{y}")

        # Container principal (non-scrollable - dialog assez grand)
        main_container = ctk.CTkFrame(dialog, fg_color="transparent")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Titre
        title = ctk.CTkLabel(
            main_container,
            text="➕ Ajouter une Application Personnalisée",
            font=(DesignTokens.FONT_FAMILY, 18, "bold")
        )
        title.pack(pady=(0, 20))

        # Variable pour stocker le chemin
        exe_path_var = tk.StringVar()

        # Section fichier .exe
        exe_label = ctk.CTkLabel(
            main_container,
            text="Fichier exécutable (.exe):",
            font=(DesignTokens.FONT_FAMILY, 14)
        )
        exe_label.pack(anchor="w", pady=(0, 5))

        exe_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        exe_frame.pack(fill=tk.X, pady=(0, 15))

        exe_entry = ctk.CTkEntry(
            exe_frame,
            textvariable=exe_path_var,
            placeholder_text="Cliquez sur 'Parcourir' pour sélectionner...",
            height=40
        )
        exe_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        def browse_exe():
            filepath = filedialog.askopenfilename(
                title="Sélectionner l'application",
                filetypes=[("Exécutables", "*.exe"), ("Tous les fichiers", "*.*")]
            )
            if filepath:
                exe_path_var.set(filepath)
                # Auto-remplir le nom si vide
                if not name_entry.get():
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, Path(filepath).stem)

        browse_btn = ModernButton(
            exe_frame,
            text="📁 Parcourir",
            variant="outlined",
            size="md",
            command=browse_exe
        )
        browse_btn.pack(side=tk.RIGHT)

        # Section nom
        name_label = ctk.CTkLabel(
            main_container,
            text="Nom de l'application:",
            font=(DesignTokens.FONT_FAMILY, 14)
        )
        name_label.pack(anchor="w", pady=(0, 5))

        name_entry = ctk.CTkEntry(
            main_container,
            placeholder_text="Ex: Mon Outil de Diagnostic",
            height=40
        )
        name_entry.pack(fill=tk.X, pady=(0, 15))

        # Section emoji
        emoji_label = ctk.CTkLabel(
            main_container,
            text="Icône (emoji):",
            font=(DesignTokens.FONT_FAMILY, 14)
        )
        emoji_label.pack(anchor="w", pady=(0, 5))

        emoji_var = tk.StringVar(value="📊")

        emoji_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        emoji_frame.pack(fill=tk.X, pady=(0, 20))

        # Liste d'emojis prédéfinis
        emojis = ["📊", "🔧", "🛠️", "⚙️", "🔍", "📦", "💻", "🖥️", "⚡", "🎮", "📈", "🔬", "🧰", "🎯"]

        for emoji in emojis:
            btn = ctk.CTkButton(
                emoji_frame,
                text=emoji,
                width=45,
                height=45,
                font=(DesignTokens.FONT_FAMILY, 20),
                fg_color="transparent",
                hover_color=DesignTokens.ACCENT_PRIMARY,
                command=lambda e=emoji: emoji_var.set(e)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Emoji sélectionné (affichage)
        selected_label = ctk.CTkLabel(
            main_container,
            textvariable=emoji_var,
            font=(DesignTokens.FONT_FAMILY, 48)
        )
        selected_label.pack(pady=10)

        # Boutons action
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        def save_tool():
            exe_path = exe_path_var.get()
            name = name_entry.get()
            emoji = emoji_var.get()

            # Validation
            if not exe_path:
                messagebox.showerror("Erreur", "Veuillez sélectionner un fichier .exe")
                return

            if not name:
                messagebox.showerror("Erreur", "Veuillez entrer un nom")
                return

            if not Path(exe_path).exists():
                messagebox.showerror("Erreur", f"Le fichier n'existe pas:\n{exe_path}")
                return

            # Créer l'outil
            new_tool = {
                "id": f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": name,
                "emoji": emoji,
                "exe_path": exe_path,
                "auto_discovered": False,
                "enabled": True,
                "created_date": datetime.now().strftime("%Y-%m-%d")
            }

            # Charger outils existants
            existing_tools = self._load_custom_tools()
            # Filtrer pour garder seulement les manuels
            manual_tools = [t for t in existing_tools if not t.get("auto_discovered", False)]
            manual_tools.append(new_tool)

            # Sauvegarder
            self._save_custom_tools(manual_tools)

            # Rafraîchir l'affichage
            self._populate_tools()

            messagebox.showinfo("Succès", f"'{name}' a été ajouté avec succès!")
            dialog.destroy()

        save_btn = ModernButton(
            btn_frame,
            text="💾 Enregistrer",
            variant="filled",
            command=save_tool
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ModernButton(
            btn_frame,
            text="❌ Annuler",
            variant="outlined",
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def _remove_custom_tool(self, tool_id):
        """Supprimer un outil personnalisé"""
        from tkinter import messagebox

        result = messagebox.askyesno(
            "Supprimer l'outil",
            "Voulez-vous vraiment supprimer cet outil personnalisé?",
            icon='warning'
        )

        if not result:
            return

        try:
            # Charger tous les outils
            all_tools = self._load_custom_tools()

            # Filtrer pour retirer l'outil supprimé
            remaining_tools = [t for t in all_tools if t['id'] != tool_id]

            # Si c'était un outil auto-découvert, ne rien sauvegarder (il réapparaîtra au scan)
            # Sinon, sauvegarder la liste mise à jour
            tool_to_remove = next((t for t in all_tools if t['id'] == tool_id), None)

            if tool_to_remove and not tool_to_remove.get("auto_discovered", False):
                # C'est un outil manuel, le retirer du JSON
                manual_tools = [t for t in remaining_tools if not t.get("auto_discovered", False)]
                self._save_custom_tools(manual_tools)
            else:
                # Outil auto-découvert : informer l'utilisateur
                messagebox.showinfo(
                    "Outil auto-découvert",
                    "Cet outil a été détecté automatiquement dans logiciel/Custom/.\n\n"
                    "Pour le retirer définitivement, supprimez le fichier .exe du dossier."
                )
                return

            # Rafraîchir l'affichage
            self._populate_tools()

            messagebox.showinfo("Succès", "L'outil a été supprimé.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer l'outil:\n{str(e)}")

    def _launch_custom_tool(self, tool_config):
        """Lancer un outil personnalisé"""
        try:
            exe_path = tool_config.get("exe_path")

            if not exe_path or not Path(exe_path).exists():
                from tkinter import messagebox
                messagebox.showerror(
                    "Erreur",
                    f"Le fichier n'existe pas:\n{exe_path}\n\n"
                    "Il a peut-être été déplacé ou supprimé."
                )
                return

            # Lancer l'exe
            os.startfile(exe_path)
            print(f"Lancé: {tool_config['name']} ({exe_path})")

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible de lancer l'application:\n{str(e)}")


class OptimizationsPage(ctk.CTkFrame):
    """Page Optimisations avec vraies commandes"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)
        
        self._create_header()
        self._create_content()
    
    def _create_header(self):
        """Header"""
        header = ModernCard(self)
        header.pack(fill=tk.X, padx=20, pady=10)
        
        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)
        
        title_frame = SectionHeader(container, text="⚡ Optimisations")
        title_frame.pack(side=tk.LEFT)

        ModernButton(
            container,
            text="🚀 Optimiser Tout",
            variant="filled",
            command=self._optimize_all
        ).pack(side=tk.RIGHT)
    
    def _create_content(self):
        """Contenu"""
        scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
        scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self._create_cleanup_section(scroll)
        self._create_performance_section(scroll)
        self._create_services_section(scroll)
        self._create_startup_section(scroll)
    
    def _create_cleanup_section(self, parent):
        """Section nettoyage"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="🧹 Nettoyage")
        title.pack(fill=tk.X)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        actions = [
            ("🗑️ Vider la corbeille", "Libérer de l'espace", self._empty_recycle_bin),
            ("🗑️ Fichiers temporaires", "Supprimer fichiers temp", self._clean_temp_files),
            ("🌐 Cache navigateurs", "Nettoyer cache", self._clean_browser_cache),
            ("💿 Nettoyage disque Windows", "Outil système", self._clean_system_files),
        ]
        
        for text, desc, command in actions:
            self._create_action_row(content, text, desc, command)
    
    def _create_performance_section(self, parent):
        """Section performance"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="⚡ Performance")
        title.pack(fill=tk.X)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        actions = [
            ("💿 Optimiser disques", "Défragmentation/TRIM", self._defragment),
            ("📋 Gestionnaire des tâches", "Ouvrir Task Manager", self._optimize_boot),
            ("🧹 Nettoyeur de disque", "Outil Windows", self._clean_registry),
            ("🎮 Options performances", "Ajuster effets visuels", self._adjust_visual_effects),
            ("🖥️ AtlasOS", "OS optimisé performance gaming", lambda: self._open_url("https://atlasos.net")),
            ("🖥️ ReviOS", "Windows debloaté optimisé", lambda: self._open_url("https://www.revi.cc/")),
        ]

        for text, desc, command in actions:
            self._create_action_row(content, text, desc, command)
    
    def _create_services_section(self, parent):
        """Section services"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="⚙️ Services")
        title.pack(fill=tk.X)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        desc = ctk.CTkLabel(
            content,
            text="Gérer les services Windows",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=10)
        
        ModernButton(
            content,
            text="⚙️ Ouvrir Services",
            variant="outlined",
            command=self._manage_services
        ).pack(anchor="w")
    
    def _create_startup_section(self, parent):
        """Section démarrage"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)
        
        title = SectionHeader(card, text="🚀 Démarrage")
        title.pack(fill=tk.X)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        desc = ctk.CTkLabel(
            content,
            text="Gérer les programmes au démarrage",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=10)
        
        ModernButton(
            content,
            text="🚀 Gestionnaire Démarrage",
            variant="outlined",
            command=self._manage_startup
        ).pack(anchor="w")
    
    def _create_action_row(self, parent, text, description, command):
        """Ligne d'action"""
        row = ctk.CTkFrame(
            parent,
            fg_color=DesignTokens.BG_ELEVATED,
            corner_radius=DesignTokens.RADIUS_MD
        )
        row.pack(fill=tk.X, pady=5)
        
        container = ctk.CTkFrame(row, fg_color="transparent")
        container.pack(fill=tk.X, padx=15, pady=12)
        
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_label = ctk.CTkLabel(
            left,
            text=text,
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        text_label.pack(anchor="w")
        
        desc_label = ctk.CTkLabel(
            left,
            text=description,
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_TERTIARY,
            anchor="w"
        )
        desc_label.pack(anchor="w")
        
        ModernButton(
            container,
            text="▶️ Exécuter",
            variant="filled",
            size="sm",
            command=command
        ).pack(side=tk.RIGHT)
    
    # Callbacks avec vraies commandes
    def _optimize_all(self):
        """Optimisation complète"""
        print(" Optimisation complète...")
        self._empty_recycle_bin()
        self._clean_temp_files()
        print(" Optimisation terminée")
    
    def _empty_recycle_bin(self):
        """Vider corbeille"""
        try:
            subprocess.run('powershell -Command "Clear-RecycleBin -Force"', shell=True, check=True)
            print(" Corbeille vidée")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _clean_temp_files(self):
        """Nettoyer fichiers temporaires"""
        try:
            temp_dirs = [
                os.environ.get('TEMP'),
                os.environ.get('TMP'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp')
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        for item in os.listdir(temp_dir):
                            item_path = os.path.join(temp_dir, item)
                            try:
                                if os.path.isfile(item_path):
                                    os.unlink(item_path)
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                            except:
                                continue
                    except:
                        continue
            
            print(" Fichiers temporaires nettoyés")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _clean_browser_cache(self):
        """Nettoyer cache navigateurs"""
        print(" Ouverture gestionnaire stockage...")
        try:
            subprocess.Popen('ms-settings:storagesense', shell=True)
        except:
            print(" Impossible d'ouvrir les paramètres")
    
    def _clean_system_files(self):
        """Nettoyage disque Windows"""
        try:
            subprocess.Popen('cleanmgr', shell=True)
            print(" Nettoyage disque lancé")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _defragment(self):
        """Défragmentation"""
        try:
            subprocess.Popen('dfrgui', shell=True)
            print(" Défragmenteur lancé")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _optimize_boot(self):
        """Gestionnaire des tâches"""
        try:
            subprocess.Popen('taskmgr', shell=True)
            print(" Gestionnaire des tâches lancé")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _clean_registry(self):
        """Nettoyage disque"""
        try:
            subprocess.Popen('cleanmgr /sageset:1', shell=True)
            print(" Nettoyage disque configuré")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _adjust_visual_effects(self):
        """Ajuster effets visuels"""
        try:
            subprocess.Popen('SystemPropertiesPerformance.exe', shell=True)
            print(" Options de performances ouvertes")
        except Exception as e:
            print(f" Erreur: {e}")

    def _open_url(self, url):
        """Ouvrir une URL dans le navigateur"""
        import webbrowser
        try:
            webbrowser.open(url)
            print(f" Ouverture de {url}")
        except Exception as e:
            print(f" Erreur lors de l'ouverture de l'URL: {e}")

    def _manage_services(self):
        """Gérer services"""
        try:
            subprocess.Popen('services.msc', shell=True)
            print(" Gestionnaire de services ouvert")
        except Exception as e:
            print(f" Erreur: {e}")
    
    def _manage_startup(self):
        """Gérer démarrage"""
        try:
            subprocess.Popen('taskmgr /0 /startup', shell=True)
            print(" Gestionnaire de démarrage ouvert")
        except Exception as e:
            print(f" Erreur: {e}")