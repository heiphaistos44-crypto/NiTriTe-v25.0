#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page Utilitaires Système Avancés - NiTriTe V20
Gestionnaire complet: Partitions, ISO, VirtualBox, Dual-boot, Clonage, Récupération, etc.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import webbrowser
from pathlib import Path
from v14_mvp.design_system import DesignTokens
from v14_mvp.components import ModernCard, ModernButton, SectionHeader


class SystemUtilitiesPage(ctk.CTkFrame):
    """Page Utilitaires Système Avancés - Outils système complets"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        self._create_header()
        self._create_content()

    def _create_header(self):
        """Header de la page"""
        header = ModernCard(self)
        header.pack(fill=tk.X, padx=20, pady=10)

        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)

        title_frame = SectionHeader(container, text="💿 Utilitaires Système Avancés")
        title_frame.pack(side=tk.LEFT)

        subtitle = ctk.CTkLabel(
            container,
            text="Partitions • ISO • VM • Dual-Boot • Clonage • Récupération • Réseau",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        subtitle.pack(side=tk.RIGHT)

    def _create_content(self):
        """Contenu scrollable"""
        scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
        scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Toutes les sections
        self._create_partition_section(scroll)
        self._create_iso_section(scroll)
        self._create_vm_section(scroll)
        self._create_dualboot_section(scroll)
        self._create_cloning_section(scroll)
        self._create_recovery_section(scroll)
        self._create_network_section(scroll)
        self._create_system_info_section(scroll)
        self._create_performance_section(scroll)
        self._create_security_section(scroll)
        self._create_cleanup_section(scroll)

    def _create_partition_section(self, parent):
        """Section gestion des partitions"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="💾 Gestion des Partitions")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Créer, redimensionner, formater et gérer vos partitions de disque",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🪟 Gestion des disques Windows",
            variant="filled",
            command=self._open_disk_management
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💿 MiniTool Partition Wizard",
            variant="outlined",
            command=lambda: self._download_tool("MiniTool")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔧 EaseUS Partition Master",
            variant="outlined",
            command=lambda: self._download_tool("EaseUS")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🎯 AOMEI Partition Assistant",
            variant="outlined",
            command=lambda: self._download_tool("AOMEI")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_iso_section(self, parent):
        """Section montage ISO"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="💿 Montage & Gravure ISO")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Monter, graver et créer des images ISO",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="📁 Monter ISO (Windows)",
            variant="filled",
            command=self._mount_iso
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💿 Rufus (USB Bootable)",
            variant="outlined",
            command=lambda: self._download_tool("Rufus")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔥 ImgBurn",
            variant="outlined",
            command=lambda: self._download_tool("ImgBurn")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="⚡ Ventoy",
            variant="outlined",
            command=lambda: self._download_tool("Ventoy")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_vm_section(self, parent):
        """Section machines virtuelles"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="🖥️ Machines Virtuelles")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Installer et gérer des machines virtuelles (VM)",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="📦 VirtualBox (Gratuit)",
            variant="filled",
            command=lambda: self._download_tool("VirtualBox")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💼 VMware Workstation",
            variant="outlined",
            command=lambda: self._download_tool("VMware")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🪟 Hyper-V (Windows)",
            variant="outlined",
            command=self._enable_hyperv
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🐧 QEMU",
            variant="outlined",
            command=lambda: self._download_tool("QEMU")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_dualboot_section(self, parent):
        """Section dual-boot"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="⚡ Dual-Boot & Bootloaders")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Gérer plusieurs systèmes d'exploitation sur un même PC",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🪟 Configuration Boot Windows",
            variant="filled",
            command=self._open_msconfig
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🐧 EasyBCD",
            variant="outlined",
            command=lambda: self._download_tool("EasyBCD")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="📚 Guide Dual-Boot",
            variant="outlined",
            command=self._open_dualboot_guide
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔧 GRUB Customizer",
            variant="outlined",
            command=lambda: self._download_tool("GRUB")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_cloning_section(self, parent):
        """Section clonage disque"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="💽 Clonage & Migration de Disque")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Cloner votre disque dur vers un SSD ou faire une image complète du système",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🎯 Macrium Reflect",
            variant="filled",
            command=lambda: self._download_tool("Macrium")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💿 Clonezilla",
            variant="outlined",
            command=lambda: self._download_tool("Clonezilla")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔧 EaseUS Todo Backup",
            variant="outlined",
            command=lambda: self._download_tool("EaseUS_Backup")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="⚡ Acronis True Image",
            variant="outlined",
            command=lambda: self._download_tool("Acronis")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_recovery_section(self, parent):
        """Section récupération de données"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="♻️ Récupération de Données")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Récupérer des fichiers supprimés ou depuis un disque endommagé",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🔍 Recuva",
            variant="filled",
            command=lambda: self._download_tool("Recuva")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💎 TestDisk & PhotoRec",
            variant="outlined",
            command=lambda: self._download_tool("TestDisk")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🌟 R-Studio",
            variant="outlined",
            command=lambda: self._download_tool("R-Studio")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🎯 Disk Drill",
            variant="outlined",
            command=lambda: self._download_tool("DiskDrill")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_network_section(self, parent):
        """Section outils réseau"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="🌐 Outils Réseau Avancés")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Analyse réseau, transfert de fichiers, partage réseau",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🔍 Wireshark",
            variant="filled",
            command=lambda: self._download_tool("Wireshark")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="📡 Advanced IP Scanner",
            variant="outlined",
            command=lambda: self._download_tool("IPScanner")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🌍 NetSetMan",
            variant="outlined",
            command=lambda: self._download_tool("NetSetMan")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="⚡ PuTTY",
            variant="outlined",
            command=lambda: self._download_tool("PuTTY")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_system_info_section(self, parent):
        """Section informations système"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="🔎 Informations Système Détaillées")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Obtenir des informations détaillées sur votre matériel et système",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🪟 Informations système Windows",
            variant="filled",
            command=self._open_system_info
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💻 CPU-Z",
            variant="outlined",
            command=lambda: self._download_tool("CPU-Z")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🎮 GPU-Z",
            variant="outlined",
            command=lambda: self._download_tool("GPU-Z")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔧 HWiNFO",
            variant="outlined",
            command=lambda: self._download_tool("HWiNFO")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="📊 Speccy",
            variant="outlined",
            command=lambda: self._download_tool("Speccy")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💻 AIDA64",
            variant="outlined",
            command=lambda: self._download_tool("AIDA64")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💾 CrystalDiskInfo",
            variant="outlined",
            command=lambda: self._download_tool("CrystalDiskInfo")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🎮 MSI Afterburner",
            variant="outlined",
            command=lambda: self._download_tool("MSI_Afterburner")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_performance_section(self, parent):
        """Section tests de performance"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="⚡ Tests de Performance & Benchmark")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Tester les performances de votre CPU, GPU, RAM, SSD",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🎯 3DMark",
            variant="filled",
            command=lambda: self._download_tool("3DMark")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💾 CrystalDiskMark",
            variant="outlined",
            command=lambda: self._download_tool("CrystalDiskMark")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔧 Prime95 (CPU)",
            variant="outlined",
            command=lambda: self._download_tool("Prime95")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🎮 FurMark (GPU)",
            variant="outlined",
            command=lambda: self._download_tool("FurMark")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="📊 UserBenchmark",
            variant="outlined",
            command=lambda: self._download_tool("UserBenchmark")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🎬 Cinebench",
            variant="outlined",
            command=lambda: self._download_tool("Cinebench")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💾 Memtest86+",
            variant="outlined",
            command=lambda: self._download_tool("Memtest86")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="📊 AS SSD Benchmark",
            variant="outlined",
            command=lambda: self._download_tool("AS_SSD")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_security_section(self, parent):
        """Section sécurité avancée"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="🛡️ Sécurité & Chiffrement")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Chiffrer vos données, gérer les mots de passe, sécuriser le système",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🔐 VeraCrypt",
            variant="filled",
            command=lambda: self._download_tool("VeraCrypt")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔑 KeePass",
            variant="outlined",
            command=lambda: self._download_tool("KeePass")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🛡️ BitLocker (Windows)",
            variant="outlined",
            command=self._enable_bitlocker
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🗑️ Eraser (Suppression sécurisée)",
            variant="outlined",
            command=lambda: self._download_tool("Eraser")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🔐 Bitwarden",
            variant="outlined",
            command=lambda: self._download_tool("Bitwarden")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    def _create_cleanup_section(self, parent):
        """Section nettoyage et optimisation"""
        card = ModernCard(parent)
        card.pack(fill=tk.X, pady=10)

        title = SectionHeader(card, text="🧹 Nettoyage & Optimisation")
        title.pack(fill=tk.X)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill=tk.X, padx=20, pady=(0, 15))

        desc = ctk.CTkLabel(
            content,
            text="Nettoyer fichiers temporaires, optimiser le système, supprimer programmes inutiles",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        )
        desc.pack(anchor="w", pady=(10, 15))

        tools_frame = ctk.CTkFrame(content, fg_color="transparent")
        tools_frame.pack(fill=tk.X)

        ModernButton(
            tools_frame,
            text="🧹 CCleaner",
            variant="filled",
            command=lambda: self._download_tool("CCleaner")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🗑️ BleachBit",
            variant="outlined",
            command=lambda: self._download_tool("BleachBit")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="⚙️ Glary Utilities",
            variant="outlined",
            command=lambda: self._download_tool("GlaryUtilities")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="💎 Wise Care 365",
            variant="outlined",
            command=lambda: self._download_tool("WiseCare365")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ModernButton(
            tools_frame,
            text="🛠️ Revo Uninstaller",
            variant="outlined",
            command=lambda: self._download_tool("RevoUninstaller")
        ).pack(side=tk.LEFT, padx=5, pady=5)

    # === MÉTHODES D'ACTION ===

    def _open_disk_management(self):
        """Ouvrir Gestion des disques Windows"""
        try:
            subprocess.Popen(["diskmgmt.msc"])
            print("✅ Gestion des disques ouverte")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la gestion des disques:\n\n{str(e)}")

    def _open_system_info(self):
        """Ouvrir Informations système Windows"""
        try:
            subprocess.Popen(["msinfo32"])
            print("✅ Informations système ouvertes")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir les informations système:\n\n{str(e)}")

    def _mount_iso(self):
        """Monter un fichier ISO"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier ISO",
            filetypes=[("Fichiers ISO", "*.iso"), ("Tous les fichiers", "*.*")]
        )

        if not file_path:
            return

        try:
            subprocess.run(
                ['powershell', '-Command', f'Mount-DiskImage -ImagePath "{file_path}"'],
                check=True
            )
            messagebox.showinfo("Succès", f"ISO monté avec succès:\n\n{Path(file_path).name}")
            print(f"✅ ISO monté: {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de monter l'ISO:\n\n{str(e)}")

    def _open_msconfig(self):
        """Ouvrir MSCONFIG pour gérer le boot"""
        try:
            subprocess.Popen(["msconfig"])
            print("✅ MSCONFIG ouvert")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir MSCONFIG:\n\n{str(e)}")

    def _enable_hyperv(self):
        """Guide pour activer Hyper-V"""
        messagebox.showinfo(
            "Activer Hyper-V",
            "Pour activer Hyper-V sur Windows:\n\n"
            "1. Ouvrir 'Activer ou désactiver des fonctionnalités Windows'\n"
            "2. Cocher 'Hyper-V'\n"
            "3. Redémarrer le PC\n\n"
            "Note: Nécessite Windows 10/11 Pro ou Enterprise"
        )

    def _enable_bitlocker(self):
        """Guide pour activer BitLocker"""
        messagebox.showinfo(
            "Activer BitLocker",
            "Pour activer BitLocker:\n\n"
            "1. Panneau de configuration > Système et sécurité > Chiffrement de lecteur BitLocker\n"
            "2. Cliquer sur 'Activer BitLocker' sur le lecteur souhaité\n"
            "3. Suivre l'assistant\n\n"
            "Note: Nécessite Windows Pro ou Enterprise + TPM"
        )

    def _open_dualboot_guide(self):
        """Ouvrir guide Dual-Boot"""
        webbrowser.open("https://itsfoss.com/install-ubuntu-dual-boot-mode-windows/")

    def _download_tool(self, tool_name):
        """Ouvrir la page de téléchargement d'un outil"""
        tool_urls = {
            "MiniTool": "https://www.partitionwizard.com/free-partition-manager.html",
            "EaseUS": "https://www.easeus.com/partition-manager/epm-free.html",
            "AOMEI": "https://www.diskpart.com/",
            "Rufus": "https://rufus.ie/",
            "ImgBurn": "https://www.imgburn.com/",
            "Ventoy": "https://www.ventoy.net/",
            "VirtualBox": "https://www.virtualbox.org/",
            "VMware": "https://www.vmware.com/products/workstation-player.html",
            "QEMU": "https://www.qemu.org/download/",
            "EasyBCD": "https://neosmart.net/EasyBCD/",
            "GRUB": "https://launchpad.net/grub-customizer",
            "Macrium": "https://www.macrium.com/reflectfree",
            "Clonezilla": "https://clonezilla.org/",
            "EaseUS_Backup": "https://www.easeus.com/backup-software/tb-free.html",
            "Acronis": "https://www.acronis.com/",
            "Recuva": "https://www.ccleaner.com/recuva",
            "TestDisk": "https://www.cgsecurity.org/wiki/TestDisk",
            "R-Studio": "https://www.r-studio.com/",
            "DiskDrill": "https://www.cleverfiles.com/",
            "Wireshark": "https://www.wireshark.org/",
            "IPScanner": "https://www.advanced-ip-scanner.com/",
            "NetSetMan": "https://www.netsetman.com/",
            "PuTTY": "https://www.putty.org/",
            "CPU-Z": "https://www.cpuid.com/softwares/cpu-z.html",
            "GPU-Z": "https://www.techpowerup.com/gpuz/",
            "HWiNFO": "https://www.hwinfo.com/",
            "Speccy": "https://www.ccleaner.com/speccy",
            "3DMark": "https://www.3dmark.com/",
            "CrystalDiskMark": "https://crystalmark.info/en/software/crystaldiskmark/",
            "Prime95": "https://www.mersenne.org/download/",
            "FurMark": "https://geeks3d.com/furmark/",
            "UserBenchmark": "https://www.userbenchmark.com/",
            "VeraCrypt": "https://www.veracrypt.fr/",
            "KeePass": "https://keepass.info/",
            "Eraser": "https://eraser.heidi.ie/"
        }

        url = tool_urls.get(tool_name, "https://www.google.com/search?q=" + tool_name)
        webbrowser.open(url)
        print(f"✓ Ouverture de {tool_name}")
