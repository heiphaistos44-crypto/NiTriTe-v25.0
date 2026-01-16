#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Composants avec Icônes Colorées - NiTriTe V20.0
Versions améliorées des composants avec support des icônes colorées
"""

import customtkinter as ctk
import tkinter as tk
from v14_mvp.design_system import DesignTokens
from v14_mvp.icons_system import ColoredIconsManager


class ModernButtonColored(ctk.CTkButton):
    """Bouton moderne avec icône colorée"""

    def __init__(self, parent, emoji=None, text="", variant="filled", size="md", **kwargs):
        """
        Créer un bouton avec icône colorée

        Args:
            parent: Widget parent
            emoji: Emoji à afficher (sera converti en icône colorée)
            text: Texte du bouton (sans l'emoji)
            variant: "filled", "outlined", "text"
            size: "sm", "md", "lg"
            **kwargs: Arguments supplémentaires pour CTkButton
        """
        # Déterminer les tailles
        sizes = {
            "sm": {"height": 32, "font_size": 12, "icon_size": 18},
            "md": {"height": 40, "font_size": 13, "icon_size": 20},
            "lg": {"height": 48, "font_size": 14, "icon_size": 22}
        }
        size_config = sizes.get(size, sizes["md"])

        # Déterminer les couleurs selon le variant
        if variant == "filled":
            fg_color = DesignTokens.ACCENT_PRIMARY
            hover_color = DesignTokens.ACCENT_HOVER
            text_color = "white"
            border_width = 0
        elif variant == "outlined":
            fg_color = "transparent"
            hover_color = DesignTokens.BG_HOVER
            text_color = DesignTokens.TEXT_PRIMARY
            border_width = 2
            kwargs['border_color'] = DesignTokens.ACCENT_PRIMARY
        else:  # text
            fg_color = "transparent"
            hover_color = DesignTokens.BG_HOVER
            text_color = DesignTokens.TEXT_PRIMARY
            border_width = 0

        # Si un emoji est fourni, créer l'icône colorée
        if emoji:
            icon_image = ColoredIconsManager.create_colored_icon(emoji, size=size_config["icon_size"])
            kwargs['image'] = icon_image
            kwargs['compound'] = "left"

        # Initialiser le bouton
        super().__init__(
            parent,
            text=text,
            height=size_config["height"],
            font=(DesignTokens.FONT_FAMILY, size_config["font_size"]),
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            border_width=border_width,
            corner_radius=DesignTokens.RADIUS_MD,
            cursor="hand2",
            **kwargs
        )


class ModernCardColored(ctk.CTkFrame):
    """Carte moderne avec support pour titre avec icône colorée"""

    def __init__(self, parent, title_emoji=None, title_text=None, **kwargs):
        """
        Créer une carte avec titre optionnel avec icône colorée

        Args:
            parent: Widget parent
            title_emoji: Emoji pour le titre (sera converti en icône colorée)
            title_text: Texte du titre
            **kwargs: Arguments supplémentaires pour CTkFrame
        """
        super().__init__(
            parent,
            fg_color=DesignTokens.BG_ELEVATED,
            corner_radius=DesignTokens.RADIUS_MD,
            **kwargs
        )

        # Si un titre est fourni, l'ajouter
        if title_text:
            self._create_title(title_emoji, title_text)

    def _create_title(self, emoji, text):
        """Créer un titre avec icône colorée"""
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill=tk.X, padx=20, pady=15)

        if emoji:
            # Icône colorée
            icon = ColoredIconsManager.create_colored_icon(emoji, size=24)
            icon_label = ctk.CTkLabel(title_frame, image=icon, text="")
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Texte
        text_label = ctk.CTkLabel(
            title_frame,
            text=text,
            font=(DesignTokens.FONT_FAMILY, 18, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)


class SectionHeaderColored(ctk.CTkFrame):
    """En-tête de section avec icône colorée"""

    def __init__(self, parent, emoji, text, **kwargs):
        """
        Créer un en-tête de section

        Args:
            parent: Widget parent
            emoji: Emoji (sera converti en icône colorée)
            text: Texte de l'en-tête
            **kwargs: Arguments supplémentaires
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Icône colorée
        icon = ColoredIconsManager.create_colored_icon(emoji, size=28)
        icon_label = ctk.CTkLabel(self, image=icon, text="")
        icon_label.image = icon
        icon_label.pack(side=tk.LEFT, padx=(0, 12))

        # Texte
        text_label = ctk.CTkLabel(
            self,
            text=text,
            font=(DesignTokens.FONT_FAMILY, 24, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)


class IconTextLabel(ctk.CTkFrame):
    """Label avec icône colorée et texte"""

    def __init__(self, parent, emoji, text, icon_size=20, font_size=13, **kwargs):
        """
        Créer un label avec icône colorée

        Args:
            parent: Widget parent
            emoji: Emoji (sera converti en icône colorée)
            text: Texte
            icon_size: Taille de l'icône
            font_size: Taille de la police
            **kwargs: Arguments supplémentaires
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Icône colorée
        icon = ColoredIconsManager.create_colored_icon(emoji, size=icon_size)
        icon_label = ctk.CTkLabel(self, image=icon, text="")
        icon_label.image = icon
        icon_label.pack(side=tk.LEFT, padx=(0, 8))

        # Texte
        text_label = ctk.CTkLabel(
            self,
            text=text,
            font=(DesignTokens.FONT_FAMILY, font_size),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)


class ActionRowColored(ctk.CTkFrame):
    """Ligne d'action avec icône colorée, description et bouton"""

    def __init__(self, parent, emoji, title, description, button_text, command, **kwargs):
        """
        Créer une ligne d'action

        Args:
            parent: Widget parent
            emoji: Emoji pour l'icône
            title: Titre de l'action
            description: Description
            button_text: Texte du bouton
            command: Fonction à exécuter
            **kwargs: Arguments supplémentaires
        """
        super().__init__(
            parent,
            fg_color=DesignTokens.BG_ELEVATED,
            corner_radius=DesignTokens.RADIUS_MD,
            **kwargs
        )

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill=tk.X, padx=15, pady=12)

        # Icône colorée
        icon = ColoredIconsManager.create_colored_icon(emoji, size=32)
        icon_label = ctk.CTkLabel(container, image=icon, text="")
        icon_label.image = icon
        icon_label.pack(side=tk.LEFT, padx=(0, 15))

        # Texte (titre + description)
        text_frame = ctk.CTkFrame(container, fg_color="transparent")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            font=(DesignTokens.FONT_FAMILY, 14, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.pack(anchor="w")

        desc_label = ctk.CTkLabel(
            text_frame,
            text=description,
            font=(DesignTokens.FONT_FAMILY, 11),
            text_color=DesignTokens.TEXT_TERTIARY,
            anchor="w"
        )
        desc_label.pack(anchor="w")

        # Bouton
        button = ModernButtonColored(
            container,
            emoji="▶️",
            text=button_text,
            variant="filled",
            size="sm",
            command=command
        )
        button.pack(side=tk.RIGHT)


class StatsCardColored(ctk.CTkFrame):
    """Carte de statistiques avec icône colorée"""

    def __init__(self, parent, emoji, title, value, subtitle="", **kwargs):
        """
        Créer une carte de stats

        Args:
            parent: Widget parent
            emoji: Emoji pour l'icône
            title: Titre
            value: Valeur à afficher
            subtitle: Sous-titre optionnel
            **kwargs: Arguments supplémentaires
        """
        super().__init__(
            parent,
            fg_color=DesignTokens.BG_ELEVATED,
            corner_radius=DesignTokens.RADIUS_MD,
            **kwargs
        )

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Icône colorée
        icon = ColoredIconsManager.create_colored_icon(emoji, size=36)
        icon_label = ctk.CTkLabel(container, image=icon, text="")
        icon_label.image = icon
        icon_label.pack(pady=(0, 10))

        # Titre
        title_label = ctk.CTkLabel(
            container,
            text=title,
            font=(DesignTokens.FONT_FAMILY, 12),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        title_label.pack()

        # Valeur
        value_label = ctk.CTkLabel(
            container,
            text=str(value),
            font=(DesignTokens.FONT_FAMILY, 28, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY
        )
        value_label.pack(pady=(5, 0))

        # Sous-titre
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                container,
                text=subtitle,
                font=(DesignTokens.FONT_FAMILY, 10),
                text_color=DesignTokens.TEXT_TERTIARY
            )
            subtitle_label.pack(pady=(5, 0))


# Fonctions helpers pour faciliter l'utilisation
def colored_button(parent, emoji=None, text="", **kwargs):
    """Créer rapidement un bouton coloré"""
    return ModernButtonColored(parent, emoji=emoji, text=text, **kwargs)

def colored_card(parent, title_emoji=None, title_text=None, **kwargs):
    """Créer rapidement une carte colorée"""
    return ModernCardColored(parent, title_emoji=title_emoji, title_text=title_text, **kwargs)

def section_header(parent, emoji, text, **kwargs):
    """Créer rapidement un en-tête de section"""
    return SectionHeaderColored(parent, emoji, text, **kwargs)

def icon_text(parent, emoji, text, **kwargs):
    """Créer rapidement un label icône+texte"""
    return IconTextLabel(parent, emoji, text, **kwargs)

# Alias pour compatibilité
create_colored_card = colored_card
