#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pages Complètes avec Icônes Colorées - NiTriTe V20.0
Version améliorée avec toutes les icônes en couleur
"""

import customtkinter as ctk
import tkinter as tk
import subprocess
import threading
import os
import sys
from pathlib import Path
from datetime import datetime

# Import des modules originaux pour hériter
from v14_mvp.pages_full import (
    UpdatesPage as UpdatesPageOriginal,
    BackupPage as BackupPageOriginal,
    DiagnosticPage as DiagnosticPageOriginal,
    OptimizationsPage as OptimizationsPageOriginal
)

from v14_mvp.design_system import DesignTokens
from v14_mvp.components_colored import (
    ModernButtonColored,
    ModernCardColored,
    SectionHeaderColored,
    StatsCardColored,
    colored_button,
    colored_card
)
from v14_mvp.icons_system import ColoredIconsManager


class UpdatesPageColored(ctk.CTkFrame):
    """Page Mises à jour avec icônes colorées"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        # Utiliser les méthodes de la classe originale
        self._original = UpdatesPageOriginal(parent)

        # Remplacer par notre version colorée
        self._create_header_colored()
        self._create_terminal()
        self._create_content_colored()

    def _create_header_colored(self):
        """Header avec icônes colorées"""
        header_card = colored_card(self)
        header_card.pack(fill=tk.X, padx=20, pady=10)

        container = ctk.CTkFrame(header_card, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)

        # Titre avec icône colorée
        title_frame = ctk.CTkFrame(container, fg_color="transparent")
        title_frame.pack(side=tk.LEFT)

        icon = ColoredIconsManager.create_colored_icon("⬆️", size=28)
        icon_label = ctk.CTkLabel(title_frame, image=icon, text="")
        icon_label.image = icon
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        title = ctk.CTkLabel(
            title_frame,
            text="Mises à Jour",
            font=(DesignTokens.FONT_FAMILY, 24, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY
        )
        title.pack(side=tk.LEFT)

        # Actions avec icônes colorées
        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(side=tk.RIGHT)

        colored_button(
            actions,
            emoji="🔎",
            text="Rechercher",
            variant="filled",
            command=self._original._check_updates
        ).pack(side=tk.LEFT, padx=5)

        colored_button(
            actions,
            emoji="⚡",
            text="Tout Mettre à Jour",
            variant="outlined",
            command=self._original._update_all
        ).pack(side=tk.LEFT, padx=5)

    def _create_terminal(self):
        """Utiliser le terminal de la version originale"""
        self._original.terminal_card.pack_forget()
        self._original.terminal_card.pack(in_=self, fill=tk.X, padx=20, pady=10)

        # Stocker la référence
        self.terminal_card = self._original.terminal_card
        self.terminal_output = self._original.terminal_output

    def _create_content_colored(self):
        """Contenu avec icônes colorées"""
        # Créer un frame scrollable
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
        self.main_scroll.pack(fill=tk.BOTH, expand=True)

        # Stats avec icônes colorées
        stats_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        self.stats_installed = StatsCardColored(
            stats_frame,
            emoji="📦",
            title="Installées",
            value="..."
        )
        self.stats_installed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.stats_uptodate = StatsCardColored(
            stats_frame,
            emoji="✅",
            title="À jour",
            value="..."
        )
        self.stats_uptodate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.stats_updates = StatsCardColored(
            stats_frame,
            emoji="⬆️",
            title="Mises à jour",
            value="..."
        )
        self.stats_updates.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Section Gestionnaires de paquets
        self._create_package_managers_colored()

        # Section Outils constructeurs
        self._create_manufacturer_tools_colored()

        # Section Pilotes
        self._create_windows_drivers_colored()

        # Section Snappy
        self._create_snappy_colored()

    def _create_package_managers_colored(self):
        """Gestionnaires de paquets avec icônes colorées"""
        card = colored_card(
            self.main_scroll,
            title_emoji="📦",
            title_text="Gestionnaires de Paquets"
        )
        card.pack(fill=tk.X, padx=20, pady=10)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Grid layout
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill=tk.X, pady=5)

        colored_button(
            row1,
            emoji="🔄",
            text="WinGet (Scan + Update)",
            variant="outlined",
            command=self._original._update_winget
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        colored_button(
            row1,
            emoji="🍫",
            text="Chocolatey (Auto-install + Update)",
            variant="outlined",
            command=self._original._update_chocolatey
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill=tk.X, pady=5)

        colored_button(
            row2,
            emoji="🪣",
            text="Scoop (Auto-install + Update)",
            variant="outlined",
            command=self._original._update_scoop
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        colored_button(
            row2,
            emoji="🐍",
            text="pip (Python packages)",
            variant="outlined",
            command=self._original._update_pip
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        row3 = ctk.CTkFrame(content, fg_color="transparent")
        row3.pack(fill=tk.X, pady=5)

        colored_button(
            row3,
            emoji="📦",
            text="npm (Node.js packages)",
            variant="outlined",
            command=self._original._update_npm
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _create_manufacturer_tools_colored(self):
        """Outils constructeurs avec icônes colorées"""
        card = colored_card(
            self.main_scroll,
            title_emoji="🏭",
            title_text="Outils de Mise à Jour Constructeurs"
        )
        card.pack(fill=tk.X, padx=20, pady=10)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        button_grid = ctk.CTkFrame(content, fg_color="transparent")
        button_grid.pack(fill=tk.X)

        manufacturers = [
            ("💻", "Dell SupportAssist", "https://www.dell.com/support/home/"),
            ("🖨️", "HP Support Assistant", "https://support.hp.com/drivers"),
            ("💼", "Lenovo Vantage", "https://support.lenovo.com/solutions/ht505081"),
            ("⚡", "Intel Driver Assistant", "https://www.intel.com/content/www/us/en/support/detect.html"),
            ("🎮", "NVIDIA GeForce Experience", "https://www.nvidia.com/geforce/geforce-experience/"),
            ("🔴", "AMD Software Adrenalin", "https://www.amd.com/support"),
            ("⚙️", "ASUS MyASUS", "https://www.asus.com/support/download-center/"),
            ("🐉", "MSI Center", "https://www.msi.com/Landing/msi-center"),
            ("🌟", "Acer Care Center", "https://www.acer.com/ac/en/US/content/software-download"),
        ]

        row = 0
        col = 0
        for emoji, text, url in manufacturers:
            btn = colored_button(
                button_grid,
                emoji=emoji,
                text=text,
                variant="outlined",
                command=lambda u=url: self._original._open_url(u)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1
            if col > 2:
                col = 0
                row += 1

        for i in range(3):
            button_grid.grid_columnconfigure(i, weight=1, uniform="manufacturer")

    def _create_windows_drivers_colored(self):
        """Pilotes Windows avec icônes colorées"""
        card = colored_card(
            self.main_scroll,
            title_emoji="🪟",
            title_text="Pilotes Génériques Windows"
        )
        card.pack(fill=tk.X, padx=20, pady=10)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        # Row 1
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill=tk.X, pady=5)

        colored_button(
            row1,
            emoji="🌐",
            text="Installer Pilotes Réseau",
            variant="outlined",
            command=self._original._install_network_drivers
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        colored_button(
            row1,
            emoji="🔊",
            text="Installer Pilotes Audio",
            variant="outlined",
            command=self._original._install_audio_drivers
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Row 2
        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill=tk.X, pady=5)

        colored_button(
            row2,
            emoji="🎮",
            text="Installer Pilotes Vidéo",
            variant="outlined",
            command=self._original._install_video_drivers
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        colored_button(
            row2,
            emoji="🎯",
            text="Installer TOUS les Pilotes",
            variant="filled",
            command=self._original._install_all_generic_drivers
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _create_snappy_colored(self):
        """Snappy avec icônes colorées"""
        card = colored_card(
            self.main_scroll,
            title_emoji="💿",
            title_text="Snappy Driver Installer"
        )
        card.pack(fill=tk.X, padx=20, pady=10)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill=tk.X)

        colored_button(
            btn_frame,
            emoji="⬇️",
            text="Télécharger Snappy Full (~40 GB)",
            variant="filled",
            command=self._original._download_snappy_full
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        colored_button(
            btn_frame,
            emoji="⬇️",
            text="Télécharger Snappy Lite (~2 GB)",
            variant="outlined",
            command=self._original._download_snappy_lite
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _log_to_terminal(self, message):
        """Rediriger vers la version originale"""
        self._original._log_to_terminal(message)


# Alias pour faciliter l'import
ColoredUpdatersPage = UpdatesPageColored
