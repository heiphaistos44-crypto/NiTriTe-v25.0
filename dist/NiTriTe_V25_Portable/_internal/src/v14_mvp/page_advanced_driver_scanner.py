#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page Scanner Pilotes Avancé - NiTriTe V20
Scanner complet des drivers système comme Snappy Driver
Analyse tous les drivers installés et propose les mises à jour
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import json
from pathlib import Path
from datetime import datetime
from v14_mvp.design_system import DesignTokens
from v14_mvp.components import ModernCard, ModernButton, SectionHeader


class AdvancedDriverScannerPage(ctk.CTkFrame):
    """Page Scanner de Pilotes Avancé - Analyse système complète"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        self.drivers_found = []
        self.scanning = False
        self.backup_folder = Path.home() / "Documents" / "NiTriTe_Driver_Backups"
        self.backup_folder.mkdir(parents=True, exist_ok=True)

        # Détecter type de PC
        self.is_laptop = self._detect_laptop()

        # Configurer grid layout
        self.grid_rowconfigure(0, weight=0)  # Header fixe
        self.grid_rowconfigure(1, weight=0)  # Stats fixe (rempli après scan)
        self.grid_rowconfigure(2, weight=1)  # Contenu scrollable
        self.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_stats_section()  # Section stats fixe
        self._create_content()

    def _detect_laptop(self):
        """Détecter si c'est un portable ou un PC de bureau"""
        try:
            import psutil
            battery = psutil.sensors_battery()
            return battery is not None
        except:
            return False

    def _get_driver_status(self, driver_date_str):
        """Calculer le statut du driver basé sur sa date"""
        try:
            # Parse la date du driver (format: YYYYMMDD, DD/MM/YYYY ou YYYY-MM-DD)
            if not driver_date_str or driver_date_str == "N/A" or driver_date_str == "":
                return "❓ INCONNU", "#64748B", False  # Gris

            # Convertir la date
            if len(driver_date_str) == 8 and driver_date_str.isdigit():
                # Format YYYYMMDD
                driver_date = datetime.strptime(driver_date_str, "%Y%m%d")
            elif "/" in driver_date_str:
                # Format DD/MM/YYYY ou MM/DD/YYYY
                driver_date = datetime.strptime(driver_date_str[:10], "%d/%m/%Y")
            elif "-" in driver_date_str and len(driver_date_str) >= 10:
                # Format YYYY-MM-DD (format WMI/ISO)
                driver_date = datetime.strptime(driver_date_str[:10], "%Y-%m-%d")
            else:
                return "❓ INCONNU", "#64748B", False

            # Calculer l'âge en jours
            age_days = (datetime.now() - driver_date).days
            age_months = age_days / 30

            # Déterminer le statut
            if age_months < 6:
                return "✅ RÉCENT", "#10B981", False  # Vert - Pas de mise à jour nécessaire
            elif age_months < 12:
                return "⚠️ À VÉRIFIER", "#F59E0B", True  # Orange - Vérifier si mise à jour dispo
            else:
                return "❌ ANCIEN", "#EF4444", True  # Rouge - Mise à jour recommandée

        except Exception as e:
            print(f"Erreur parsing date driver: {e}")
            return "❓ INCONNU", "#64748B", False

    def _create_header(self):
        """Header de la page"""
        header = ModernCard(self)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)

        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)

        # Titre avec icône
        title_container = ctk.CTkFrame(container, fg_color="transparent")
        title_container.pack(side=tk.LEFT)

        SectionHeader(title_container, text="🔬 Scanner de Pilotes Avancé").pack(side=tk.LEFT)

        pc_type = ctk.CTkLabel(
            title_container,
            text=f"  {'💻 Portable' if self.is_laptop else '🖥️ Bureau'}",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
            text_color=DesignTokens.ACCENT_PRIMARY
        )
        pc_type.pack(side=tk.LEFT, padx=10)

        # Boutons d'action
        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(side=tk.RIGHT)

        ModernButton(
            actions,
            text="🔍 Scanner Maintenant",
            variant="filled",
            command=self._start_scan
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            actions,
            text="💾 Sauvegarder Pilotes",
            variant="outlined",
            command=self._backup_all_drivers
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            actions,
            text="♻️ Restaurer Sauvegarde",
            variant="outlined",
            command=self._restore_drivers
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            actions,
            text="📊 Exporter Liste",
            variant="outlined",
            command=self._export_drivers_list
        ).pack(side=tk.LEFT, padx=5)

    def _create_stats_section(self):
        """Section statistiques fixe (affichée après scan)"""
        # Container pour les stats (caché par défaut, affiché après scan)
        self.stats_container = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_container.grid(row=1, column=0, sticky="ew", padx=20, pady=0)
        self.stats_container.grid_remove()  # Caché par défaut

    def _create_content(self):
        """Contenu scrollable"""
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=DesignTokens.BG_PRIMARY,
            height=600  # Hauteur minimale pour meilleure visibilité
        )
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # Info message
        info_card = ModernCard(self.scroll)
        info_card.pack(fill=tk.X, pady=10)

        info_text = ctk.CTkLabel(
            info_card,
            text="ℹ️ Ce scanner analyse TOUS les pilotes installés sur votre PC et détecte les pilotes obsolètes ou manquants.\n"
                 "Similaire à Snappy Driver, il identifie les mises à jour disponibles via Windows Update.",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            justify="left",
            wraplength=800
        )
        info_text.pack(padx=20, pady=15)

        # Zone de résultats (sera remplie lors du scan)
        self.results_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.results_container.pack(fill=tk.BOTH, expand=True)

        self._show_welcome_message()

    def _show_welcome_message(self):
        """Message de bienvenue"""
        welcome = ModernCard(self.results_container)
        welcome.pack(fill=tk.BOTH, expand=True, pady=20)

        icon = ctk.CTkLabel(
            welcome,
            text="🔬",
            font=(DesignTokens.FONT_FAMILY, 64)
        )
        icon.pack(pady=20)

        title = ctk.CTkLabel(
            welcome,
            text="Prêt à scanner votre système",
            font=(DesignTokens.FONT_FAMILY, 24, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY
        )
        title.pack(pady=10)

        desc = ctk.CTkLabel(
            welcome,
            text="Cliquez sur 'Scanner Maintenant' pour analyser tous vos pilotes\n"
                 "et détecter les mises à jour disponibles",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
            text_color=DesignTokens.TEXT_SECONDARY,
            justify="center"
        )
        desc.pack(pady=(10, 30), padx=20)

    def _start_scan(self):
        """Démarrer le scan des pilotes"""
        if self.scanning:
            messagebox.showinfo("Scan en cours", "Un scan est déjà en cours. Veuillez patienter...")
            return

        # Nettoyer résultats précédents
        for widget in self.results_container.winfo_children():
            widget.destroy()

        # Afficher indicateur de chargement
        loading_card = ModernCard(self.results_container)
        loading_card.pack(fill=tk.X, pady=10)

        loading_label = ctk.CTkLabel(
            loading_card,
            text="🔄 Analyse en cours...\n\nScanning du système pour détecter tous les pilotes installés\nCette opération peut prendre 1-2 minutes",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
            text_color=DesignTokens.TEXT_PRIMARY,
            justify="center"
        )
        loading_label.pack(pady=30)

        # Lancer scan dans un thread
        self.scanning = True
        thread = threading.Thread(target=self._perform_scan, daemon=True)
        thread.start()

    def _deduplicate_drivers(self, drivers):
        """Dédupliquer les pilotes basés sur DeviceName + ClassName

        Stratégie:
        - Groupe par (DeviceName, ClassName)
        - Pour chaque groupe, garde la version la plus récente ou la plus complète
        - Préfère les entrées signées
        """
        from datetime import datetime

        seen = {}  # Key: (DeviceName, ClassName), Value: driver dict

        for driver in drivers:
            device_name = driver.get('DeviceName', '').strip()
            class_name = driver.get('ClassName', '').strip()

            if not device_name:  # Skip invalid
                continue

            key = (device_name.lower(), class_name.lower())

            if key not in seen:
                # Premier occurence, garder
                seen[key] = driver
            else:
                # Doublon détecté - garder le meilleur
                existing = seen[key]

                # Critère 1: Préférer les signés
                existing_signed = existing.get('IsSigned', 'Non') == 'Oui'
                new_signed = driver.get('IsSigned', 'Non') == 'Oui'

                if new_signed and not existing_signed:
                    seen[key] = driver
                    continue
                elif existing_signed and not new_signed:
                    continue  # Garder existing

                # Critère 2: Préférer version la plus complète (pas "N/A")
                existing_version = existing.get('Version', 'N/A')
                new_version = driver.get('Version', 'N/A')

                if new_version != 'N/A' and existing_version == 'N/A':
                    seen[key] = driver
                    continue
                elif existing_version != 'N/A' and new_version == 'N/A':
                    continue

                # Critère 3: Préférer date la plus récente
                try:
                    existing_date = existing.get('Date', '1900-01-01')
                    new_date = driver.get('Date', '1900-01-01')

                    if existing_date != 'N/A' and new_date != 'N/A':
                        if new_date > existing_date:
                            seen[key] = driver
                except:
                    pass  # En cas d'erreur de comparaison, garder existing

        return list(seen.values())

    def _perform_scan(self):
        """Effectuer le scan (dans un thread séparé) - SANS ADMIN via WMI"""
        try:
            drivers = []

            # NOUVELLE MÉTHODE: WMI (Windows Management Instrumentation) - PAS BESOIN D'ADMIN!
            print("Scan drivers via WMI...")

            # 1. Scanner via WMI Win32_PnPSignedDriver
            try:
                cmd = """
Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, DriverDate,
Manufacturer, DeviceClass, InfName, IsSigned, DriverProviderName, Location | ConvertTo-Json
                """.strip()

                result = subprocess.run(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='ignore',
                    timeout=90,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )

                if result.returncode == 0 and result.stdout:
                    drivers_data = json.loads(result.stdout)
                    if isinstance(drivers_data, list):
                        for d in drivers_data:
                            if d and d.get('DeviceName'):
                                drivers.append({
                                    'Driver': d.get('InfName', 'N/A'),
                                    'DeviceName': d.get('DeviceName', 'N/A'),
                                    'ProviderName': d.get('DriverProviderName') or d.get('Manufacturer', 'N/A'),
                                    'ClassName': d.get('DeviceClass', 'N/A'),
                                    'Version': d.get('DriverVersion', 'N/A'),
                                    # Format WMI: YYYYMMDDHHMMSS.microseconds+timezone → Extraire YYYYMMDD (8 chars)
                                    'Date': d.get('DriverDate', '')[:8] if (d.get('DriverDate') and len(str(d.get('DriverDate', ''))) >= 8) else 'N/A',
                                    'Location': d.get('Location', 'N/A'),
                                    'IsSigned': 'Oui' if d.get('IsSigned') else 'Non'
                                })
                    print(f"✓ WMI: {len(drivers)} drivers trouvés")
            except Exception as e:
                print(f"Erreur WMI scan: {e}")

            # 2. NE PAS ajouter les périphériques PnP génériques
            # (ils ajoutent trop de faux positifs - drivers système intégrés)
            # On garde uniquement les drivers tiers de Win32_PnPSignedDriver

            # Filtrer les drivers système Microsoft qui ne nécessitent pas de mise à jour manuelle
            microsoft_system_drivers = [
                'microsoft', 'windows', '(microsoft)', 'generic', 'standard',
                'système', 'system', '(standard', 'usb hub', 'pci express',
                'high definition audio', 'composite', 'racine', 'root'
            ]

            filtered_drivers = []
            for driver in drivers:
                provider = (driver.get('ProviderName') or '').lower()
                device_name = (driver.get('DeviceName') or '').lower()
                class_name = (driver.get('ClassName') or '').lower()

                # Garder si:
                # 1. Pas un driver Microsoft/Windows générique
                # 2. Ou si c'est un driver avec un fabricant tiers identifié
                is_microsoft_generic = any(ms in provider for ms in microsoft_system_drivers)
                is_generic_device = any(gen in device_name for gen in ['generic', 'standard', 'root', 'racine'])

                # Toujours garder les drivers de ces catégories importantes
                important_classes = ['display', 'net', 'media', 'audio', 'bluetooth', 'biometric', 'camera', 'printer']
                is_important = any(imp in class_name for imp in important_classes)

                # Garder si driver tiers OU catégorie importante
                if not is_microsoft_generic or is_important or (not is_generic_device and driver.get('Version') != 'N/A'):
                    filtered_drivers.append(driver)

            drivers = filtered_drivers
            print(f"✓ Après filtrage Microsoft/Générique: {len(drivers)} pilotes tiers pertinents")

            # DÉDUPLICATION: Supprimer les doublons basés sur DeviceName + ClassName
            drivers = self._deduplicate_drivers(drivers)
            print(f"✓ Après déduplication: {len(drivers)} pilotes uniques")

            self.drivers_found = drivers

            # Afficher résultats dans l'UI (thread-safe)
            self.after(0, self._display_scan_results)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erreur de scan", f"Erreur lors du scan:\n\n{str(e)}"))
        finally:
            self.scanning = False

    def _display_scan_results(self):
        """Afficher les résultats du scan"""
        # Nettoyer stats et résultats
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        for widget in self.results_container.winfo_children():
            widget.destroy()

        if not self.drivers_found:
            # Cacher stats et afficher erreur
            self.stats_container.grid_remove()

            no_result = ModernCard(self.results_container)
            no_result.pack(fill=tk.X, pady=20)

            ctk.CTkLabel(
                no_result,
                text="⚠️ Aucun pilote détecté\n\nLe scan n'a trouvé aucun pilote. Cela peut arriver si:\n• Les commandes PowerShell sont bloquées\n• Droits administrateur nécessaires",
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                text_color=DesignTokens.TEXT_SECONDARY,
                justify="center"
            ).pack(pady=30, padx=20)
            return

        # Afficher la section stats
        self.stats_container.grid()

        # Résumé (dans stats_container - fixe)
        summary_card = ModernCard(self.stats_container)
        summary_card.pack(fill=tk.X, pady=(0, 10), padx=0)

        summary_title = SectionHeader(summary_card, text=f"📊 Résultat du Scan - {len(self.drivers_found)} pilotes trouvés")
        summary_title.pack(pady=10)

        # Grouper les pilotes par catégorie
        drivers_by_category = {}
        category_icons = {
            "Audio": "🔊",
            "Display": "🖥️",
            "Network": "🌐",
            "System": "⚙️",
            "USB": "🔌",
            "Human Interface Devices": "🖱️",
            "Disk drives": "💾",
            "Monitor": "🖥️",
            "Keyboard": "⌨️",
            "Mouse": "🖱️",
            "Bluetooth": "📶",
            "Imaging devices": "📷",
            "Printer": "🖨️",
            "SCSI": "💿",
            "Sound": "🔊",
            "Video": "🎬",
            "Storage": "💾"
        }

        for driver in self.drivers_found:
            class_name = driver.get('DeviceClass', driver.get('ClassName', 'Autres'))
            if class_name not in drivers_by_category:
                drivers_by_category[class_name] = []
            drivers_by_category[class_name].append(driver)

        # Trier par nombre de pilotes (décroissant)
        sorted_categories = sorted(drivers_by_category.items(), key=lambda x: len(x[1]), reverse=True)

        # Statistiques par catégorie
        stats_text = f"✅ Scan terminé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n"
        stats_text += f"📌 {len(self.drivers_found)} pilotes répartis en {len(sorted_categories)} catégories"

        summary_text = ctk.CTkLabel(
            summary_card,
            text=stats_text,
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY
        )
        summary_text.pack(pady=10, padx=20)

        # Cartes de statistiques par catégorie (top 5) - dans stats_container (fixe)
        stats_row = ctk.CTkFrame(self.stats_container, fg_color="transparent")
        stats_row.pack(fill=tk.X, pady=(0, 10), padx=0)

        for i, (cat_name, drivers) in enumerate(sorted_categories[:5]):
            icon = category_icons.get(cat_name, "📦")
            stat_card = ModernCard(stats_row)
            stat_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            container = ctk.CTkFrame(stat_card, fg_color="transparent")
            container.pack(padx=15, pady=12)

            ctk.CTkLabel(
                container,
                text=icon,
                font=(DesignTokens.FONT_FAMILY, 24)
            ).pack(side=tk.LEFT, padx=(0, 10))

            info = ctk.CTkFrame(container, fg_color="transparent")
            info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            ctk.CTkLabel(
                info,
                text=cat_name,
                font=(DesignTokens.FONT_FAMILY, 11),
                text_color=DesignTokens.TEXT_SECONDARY,
                anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=str(len(drivers)),
                font=(DesignTokens.FONT_FAMILY, 20, "bold"),
                text_color=DesignTokens.TEXT_PRIMARY,
                anchor="w"
            ).pack(anchor="w")

        # Liste des pilotes par catégories (dans results_container - scrollable)
        drivers_title = SectionHeader(self.results_container, text="🔧 Pilotes par Catégorie")
        drivers_title.pack(pady=10)

        # Container pour les catégories (directement dans results_container qui est déjà scrollable)
        categories_container = ctk.CTkFrame(
            self.results_container,
            fg_color=DesignTokens.BG_SECONDARY,
            corner_radius=DesignTokens.RADIUS_LG
        )
        categories_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Créer une section repliable pour chaque catégorie
        # Catégories fermées par défaut (comme préféré par l'utilisateur)
        self.expanded_driver_categories = set()
        self.driver_category_frames = {}
        self.driver_category_buttons = {}

        for cat_name, drivers in sorted_categories:
            icon = category_icons.get(cat_name, "📦")
            is_expanded = cat_name in self.expanded_driver_categories
            arrow = "▼" if is_expanded else "▶"

            # Compter les pilotes par statut pour afficher un indicateur visuel
            old_count = 0      # ❌ ANCIEN (rouge)
            verify_count = 0   # ⚠️ À VÉRIFIER (orange)
            recent_count = 0   # ✅ RÉCENT (vert)
            unknown_count = 0  # ❓ INCONNU (gris)

            for driver in drivers:
                driver_date = driver.get('Date', 'N/A')
                status_badge, status_color, needs_update = self._get_driver_status(driver_date)
                if "ANCIEN" in status_badge:
                    old_count += 1
                elif "VÉRIFIER" in status_badge:
                    verify_count += 1
                elif "RÉCENT" in status_badge:
                    recent_count += 1
                else:
                    unknown_count += 1

            # Créer le badge de statut pour la catégorie (priorité: rouge > orange > gris > vert)
            status_indicator = ""
            if old_count > 0:
                status_indicator = f"  🔴 {old_count} ancien{'s' if old_count > 1 else ''}"
            elif verify_count > 0:
                status_indicator = f"  🟠 {verify_count} à vérifier"
            elif unknown_count == len(drivers):
                status_indicator = f"  ⚪ Dates inconnues"
            elif recent_count == len(drivers):
                status_indicator = f"  🟢 Tous récents"

            # Bouton catégorie (repliable) avec indicateur visuel
            cat_button = ctk.CTkButton(
                categories_container,
                text=f"{arrow} {icon} {cat_name} ({len(drivers)} pilotes){status_indicator}",
                font=(DesignTokens.FONT_FAMILY, 13, "bold"),
                text_color=DesignTokens.ACCENT_PRIMARY,
                fg_color=DesignTokens.BG_ELEVATED,
                hover_color=DesignTokens.BG_HOVER,
                anchor="w",
                command=lambda c=cat_name: self._toggle_driver_category(c)
            )
            cat_button.pack(fill=tk.X, pady=(10, 2), padx=5)
            self.driver_category_buttons[cat_name] = cat_button

            # Frame pour les pilotes de cette catégorie
            drivers_frame = ctk.CTkFrame(categories_container, fg_color="transparent")
            self.driver_category_frames[cat_name] = drivers_frame

            # Afficher les pilotes de la catégorie
            for i, driver in enumerate(drivers):
                driver_frame = ctk.CTkFrame(drivers_frame, fg_color=DesignTokens.BG_PRIMARY, corner_radius=8)
                driver_frame.pack(fill=tk.X, pady=3, padx=10)

                # Info driver (version compacte)
                info_frame = ctk.CTkFrame(driver_frame, fg_color="transparent")
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=10)

                device_name = driver.get('DeviceName', driver.get('Driver', 'Inconnu'))
                provider = driver.get('ProviderName', driver.get('Manufacturer', 'N/A'))
                version = driver.get('DriverVersion', driver.get('Version', 'N/A'))
                driver_date = driver.get('Date', 'N/A')  # CORRECTION: 'Date' au lieu de 'DriverDate'

                # Calculer le statut du driver basé sur son âge
                status_badge, status_color, needs_update = self._get_driver_status(driver_date)

                # Ligne 1 : Nom + Badge de statut
                name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
                name_row.pack(anchor="w", fill=tk.X)

                ctk.CTkLabel(
                    name_row,
                    text=f"📦 {device_name}",
                    font=(DesignTokens.FONT_FAMILY, 12, "bold"),
                    text_color=DesignTokens.TEXT_PRIMARY,
                    anchor="w"
                ).pack(side=tk.LEFT)

                # Badge de statut
                ctk.CTkLabel(
                    name_row,
                    text=status_badge,
                    font=(DesignTokens.FONT_FAMILY, 9, "bold"),
                    text_color="#FFFFFF",
                    fg_color=status_color,
                    corner_radius=4,
                    padx=8,
                    pady=2
                ).pack(side=tk.LEFT, padx=10)

                # Ligne 2 : Info fabricant et version
                info_text = f"Fabricant: {provider}  •  Version: {version}"
                if driver_date:
                    info_text += f"  •  Date: {driver_date}"

                ctk.CTkLabel(
                    info_frame,
                    text=info_text,
                    font=(DesignTokens.FONT_FAMILY, 10),
                    text_color=DesignTokens.TEXT_SECONDARY,
                    anchor="w"
                ).pack(anchor="w", pady=(2, 0))

                # Boutons d'action
                buttons_frame = ctk.CTkFrame(driver_frame, fg_color="transparent")
                buttons_frame.pack(side=tk.RIGHT, padx=10)

                # Bouton Mettre à jour - Apparence selon le statut
                maj_text = "⚠️ MAJ" if needs_update else "🔄 MAJ"
                maj_btn = ModernButton(
                    buttons_frame,
                    text=maj_text,
                    variant="filled",
                    size="sm",
                    width=90,
                    command=lambda d=driver: self._update_driver(d)
                )
                # Si mise à jour recommandée, bouton orange/rouge, sinon gris
                if needs_update:
                    maj_btn.configure(fg_color="#F59E0B", hover_color="#EF4444")
                maj_btn.pack(side=tk.LEFT, padx=3)

                # Bouton détails (avec couleur visible et taille suffisante)
                detail_btn = ModernButton(
                    buttons_frame,
                    text="ℹ️ Info",
                    variant="outlined",
                    size="sm",
                    width=80,
                    command=lambda d=driver: self._show_driver_details(d)
                )
                detail_btn.configure(
                    text_color=DesignTokens.ACCENT_PRIMARY,
                    border_color=DesignTokens.ACCENT_PRIMARY,
                    fg_color=DesignTokens.BG_ELEVATED,
                    hover_color=DesignTokens.BG_HOVER
                )
                detail_btn.pack(side=tk.LEFT, padx=3)

            # Afficher la frame si catégorie ouverte
            if is_expanded:
                drivers_frame.pack(fill=tk.X, pady=(0, 5))

    def _toggle_driver_category(self, category):
        """Ouvrir/Fermer une catégorie de pilotes (accordéon)"""
        if category in self.expanded_driver_categories:
            # Fermer la catégorie
            self.expanded_driver_categories.remove(category)
            self.driver_category_frames[category].pack_forget()
        else:
            # Ouvrir la catégorie
            self.expanded_driver_categories.add(category)
            # Remettre la frame APRÈS le bouton pour maintenir l'ordre
            self.driver_category_frames[category].pack(fill=tk.X, pady=(0, 5), after=self.driver_category_buttons[category])

        # Rafraîchir les flèches de toutes les catégories
        self._refresh_driver_categories()

    def _refresh_driver_categories(self):
        """Rafraîchir les flèches des catégories de pilotes"""
        for category, button in self.driver_category_buttons.items():
            is_expanded = category in self.expanded_driver_categories
            arrow = "▼" if is_expanded else "▶"
            text = button.cget("text")
            if text.startswith("▶") or text.startswith("▼"):
                parts = text.split(" ", 1)
                if len(parts) > 1:
                    button.configure(text=f"{arrow} {parts[1]}")

    def _backup_all_drivers(self):
        """Sauvegarder tous les pilotes du système"""
        response = messagebox.askyesno(
            "Sauvegarder les Pilotes",
            f"Cette opération va sauvegarder TOUS les pilotes tiers installés.\n\n"
            f"Dossier de sauvegarde:\n{self.backup_folder}\n\n"
            f"Cette opération peut prendre plusieurs minutes.\n\nContinuer ?"
        )

        if not response:
            return

        # Créer dossier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_folder / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Lancer sauvegarde dans un thread
        def perform_backup():
            try:
                # Utiliser DISM pour exporter les pilotes
                result = subprocess.run(
                    ['dism', '/online', '/export-driver', f'/destination:{backup_path}'],
                    capture_output=True,
                    text=True, encoding='utf-8', errors='ignore',
                    timeout=300  # 5 minutes max
                )

                if result.returncode == 0:
                    self.after(0, lambda: messagebox.showinfo(
                        "Sauvegarde Réussie",
                        f"✅ Tous les pilotes ont été sauvegardés avec succès!\n\n"
                        f"Dossier: {backup_path}\n\n"
                        f"Vous pouvez restaurer cette sauvegarde à tout moment."
                    ))
                else:
                    self.after(0, lambda: messagebox.showerror(
                        "Erreur",
                        f"Erreur lors de la sauvegarde:\n\n{result.stderr}"
                    ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde:\n\n{str(e)}"))

        thread = threading.Thread(target=perform_backup, daemon=True)
        thread.start()

    def _restore_drivers(self):
        """Restaurer les pilotes depuis une sauvegarde"""
        # Lister les sauvegardes disponibles
        backups = sorted(self.backup_folder.glob("backup_*"), reverse=True)

        if not backups:
            messagebox.showinfo(
                "Aucune Sauvegarde",
                "Aucune sauvegarde de pilotes trouvée.\n\n"
                "Utilisez 'Sauvegarder Pilotes' pour créer une sauvegarde d'abord."
            )
            return

        # TODO: Afficher dialogue de sélection de sauvegarde
        # Pour l'instant, utiliser la plus récente
        latest_backup = backups[0]

        response = messagebox.askyesno(
            "Restaurer les Pilotes",
            f"Restaurer la sauvegarde du {latest_backup.name.replace('backup_', '')}?\n\n"
            f"⚠️ ATTENTION: Cette opération nécessite un redémarrage du PC.\n\n"
            f"Continuer ?"
        )

        if not response:
            return

        messagebox.showinfo(
            "Restauration Manuelle",
            f"Pour restaurer les pilotes:\n\n"
            f"1. Ouvrez le Gestionnaire de périphériques\n"
            f"2. Clic droit sur un périphérique > Mettre à jour le pilote\n"
            f"3. Choisissez 'Parcourir mon ordinateur'\n"
            f"4. Sélectionnez le dossier:\n   {latest_backup}\n\n"
            f"Répétez pour chaque périphérique à restaurer."
        )

    def _update_driver(self, driver):
        """Mettre à jour un pilote via Windows Update ou Gestionnaire de périphériques"""
        device_name = driver.get('DeviceName', driver.get('Driver', 'Inconnu'))
        device_id = driver.get('DeviceID', driver.get('InstanceId', ''))

        # Fenêtre de choix
        choice_dialog = ctk.CTkToplevel(self)
        choice_dialog.title("Mise à jour du pilote")
        choice_dialog.geometry("500x380")
        choice_dialog.transient(self)
        choice_dialog.grab_set()
        choice_dialog.resizable(False, False)

        # Centrer
        choice_dialog.update_idletasks()
        x = (choice_dialog.winfo_screenwidth() // 2) - 250
        y = (choice_dialog.winfo_screenheight() // 2) - 190
        choice_dialog.geometry(f"500x380+{x}+{y}")

        ctk.CTkLabel(
            choice_dialog,
            text="🔄 Mettre à jour le pilote",
            font=(DesignTokens.FONT_FAMILY, 18, "bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            choice_dialog,
            text=device_name[:60] + "..." if len(device_name) > 60 else device_name,
            font=(DesignTokens.FONT_FAMILY, 12),
            text_color="#888"
        ).pack(pady=(0, 20))

        # Option 1: Windows Update
        def open_windows_update():
            choice_dialog.destroy()
            try:
                # Ouvrir Windows Update directement sur la page des mises à jour optionnelles
                subprocess.Popen(['start', 'ms-settings:windowsupdate-optionalupdates'], shell=True)
                messagebox.showinfo(
                    "Windows Update",
                    "Windows Update s'est ouvert.\n\n"
                    "1. Cliquez sur 'Mises à jour de pilotes'\n"
                    "2. Cochez les pilotes à mettre à jour\n"
                    "3. Cliquez sur 'Télécharger et installer'"
                )
            except Exception as e:
                # Fallback: ouvrir Windows Update classique
                subprocess.Popen(['start', 'ms-settings:windowsupdate'], shell=True)

        ctk.CTkButton(
            choice_dialog,
            text="📡 Ouvrir Windows Update",
            command=open_windows_update,
            width=400,
            height=45,
            font=(DesignTokens.FONT_FAMILY, 14),
            fg_color="#0078D4",
            hover_color="#106EBE"
        ).pack(pady=8)

        ctk.CTkLabel(
            choice_dialog,
            text="Recherche automatique des mises à jour Microsoft",
            font=(DesignTokens.FONT_FAMILY, 10),
            text_color="#666"
        ).pack()

        # Option 2: Gestionnaire de périphériques
        def open_device_manager():
            choice_dialog.destroy()
            try:
                # Ouvrir le gestionnaire de périphériques
                subprocess.Popen(['devmgmt.msc'], shell=True)
                messagebox.showinfo(
                    "Gestionnaire de périphériques",
                    f"Le Gestionnaire de périphériques s'est ouvert.\n\n"
                    f"1. Trouvez le périphérique:\n   {device_name[:50]}\n\n"
                    f"2. Clic droit → 'Mettre à jour le pilote'\n"
                    f"3. Choisissez 'Rechercher automatiquement'"
                )
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le gestionnaire: {e}")

        ctk.CTkButton(
            choice_dialog,
            text="⚙️ Gestionnaire de périphériques",
            command=open_device_manager,
            width=400,
            height=45,
            font=(DesignTokens.FONT_FAMILY, 14),
            fg_color="#4CAF50",
            hover_color="#45A049"
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            choice_dialog,
            text="Mise à jour manuelle via Windows",
            font=(DesignTokens.FONT_FAMILY, 10),
            text_color="#666"
        ).pack()

        # Option 3: Recherche web fabricant
        def search_manufacturer():
            choice_dialog.destroy()
            provider = driver.get('ProviderName', driver.get('Manufacturer', ''))
            search_query = f"{device_name} driver download {provider}".replace(' ', '+')
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q={search_query}")

        ctk.CTkButton(
            choice_dialog,
            text="🌐 Rechercher sur le site du fabricant",
            command=search_manufacturer,
            width=400,
            height=45,
            font=(DesignTokens.FONT_FAMILY, 14),
            fg_color="#FF9800",
            hover_color="#F57C00"
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            choice_dialog,
            text="Télécharger la dernière version officielle",
            font=(DesignTokens.FONT_FAMILY, 10),
            text_color="#666"
        ).pack()

        # Bouton Annuler
        ctk.CTkButton(
            choice_dialog,
            text="Annuler",
            command=choice_dialog.destroy,
            width=150,
            height=35,
            font=(DesignTokens.FONT_FAMILY, 12),
            fg_color="#607D8B",
            hover_color="#546E7A"
        ).pack(pady=(25, 10))

    def _show_driver_details(self, driver):
        """Afficher les détails complets d'un driver dans une fenêtre popup"""
        # Récupérer les informations du driver
        device_name = driver.get('DeviceName', driver.get('Driver', 'Inconnu'))
        provider = driver.get('ProviderName', driver.get('Manufacturer', 'N/A'))
        class_name = driver.get('ClassName', driver.get('DeviceClass', 'N/A'))
        version = driver.get('Version', driver.get('DriverVersion', 'N/A'))
        driver_date = driver.get('Date', 'N/A')
        inf_file = driver.get('Driver', driver.get('InfName', 'N/A'))
        location = driver.get('Location', 'N/A')
        is_signed = driver.get('IsSigned', 'N/A')

        # Calculer le statut
        status_badge, status_color, needs_update = self._get_driver_status(driver_date)

        # Créer fenêtre de dialogue
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails du Pilote - {device_name[:50]}")
        dialog.geometry("750x550")
        dialog.configure(fg_color=DesignTokens.BG_PRIMARY)

        # Forcer la fenêtre au premier plan
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))

        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (750 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"750x550+{x}+{y}")

        # Header avec icône et nom
        header_frame = ctk.CTkFrame(dialog, fg_color=DesignTokens.ACCENT_PRIMARY, corner_radius=10)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header_frame,
            text=f"📦 {device_name}",
            font=(DesignTokens.FONT_FAMILY, 18, "bold"),
            text_color="#FFFFFF"
        ).pack(pady=15, padx=20)

        # Badge de statut
        status_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        status_frame.pack(fill=tk.X, padx=20, pady=5)

        ctk.CTkLabel(
            status_frame,
            text=f"Statut: {status_badge}",
            font=(DesignTokens.FONT_FAMILY, 14, "bold"),
            text_color=status_color
        ).pack(side=tk.LEFT)

        # Contenu scrollable
        content_frame = ctk.CTkScrollableFrame(dialog, fg_color=DesignTokens.BG_SECONDARY, corner_radius=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Informations principales
        info_items = [
            ("🏢 Fabricant", provider),
            ("📂 Catégorie", class_name),
            ("🔢 Version", version),
            ("📅 Date du pilote", driver_date if driver_date != 'N/A' else "Non disponible"),
            ("📄 Fichier INF", inf_file),
            ("📍 Emplacement", location),
            ("✅ Signé numériquement", is_signed),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(content_frame, fg_color=DesignTokens.BG_PRIMARY, corner_radius=8)
            row.pack(fill=tk.X, pady=5, padx=10)

            ctk.CTkLabel(
                row,
                text=label,
                font=(DesignTokens.FONT_FAMILY, 12, "bold"),
                text_color=DesignTokens.TEXT_PRIMARY,
                width=200,
                anchor="w"
            ).pack(side=tk.LEFT, padx=15, pady=10)

            ctk.CTkLabel(
                row,
                text=str(value) if value else "N/A",
                font=(DesignTokens.FONT_FAMILY, 12),
                text_color=DesignTokens.TEXT_SECONDARY,
                anchor="w",
                wraplength=400
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

        # Section informations techniques (autres clés)
        other_keys = {k: v for k, v in driver.items()
                      if k not in ['DeviceName', 'Driver', 'ProviderName', 'Manufacturer',
                                   'ClassName', 'DeviceClass', 'Version', 'DriverVersion',
                                   'Date', 'DriverDate', 'InfName', 'Location', 'IsSigned']}

        if other_keys:
            tech_label = ctk.CTkLabel(
                content_frame,
                text="🔧 Informations Techniques",
                font=(DesignTokens.FONT_FAMILY, 14, "bold"),
                text_color=DesignTokens.ACCENT_PRIMARY
            )
            tech_label.pack(anchor="w", padx=10, pady=(15, 5))

            for key, value in other_keys.items():
                if value and str(value) != 'N/A':
                    row = ctk.CTkFrame(content_frame, fg_color=DesignTokens.BG_PRIMARY, corner_radius=8)
                    row.pack(fill=tk.X, pady=3, padx=10)

                    ctk.CTkLabel(
                        row,
                        text=key,
                        font=(DesignTokens.FONT_FAMILY, 11),
                        text_color=DesignTokens.TEXT_SECONDARY,
                        width=200,
                        anchor="w"
                    ).pack(side=tk.LEFT, padx=15, pady=8)

                    ctk.CTkLabel(
                        row,
                        text=str(value)[:100],
                        font=(DesignTokens.FONT_FAMILY, 11),
                        text_color=DesignTokens.TEXT_PRIMARY,
                        anchor="w"
                    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=8)

        # Boutons en bas
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)

        ModernButton(
            buttons_frame,
            text="🔄 Mettre à jour ce pilote",
            variant="filled" if needs_update else "outlined",
            command=lambda: [dialog.destroy(), self._update_driver(driver)]
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            buttons_frame,
            text="✖️ Fermer",
            variant="outlined",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _export_drivers_list(self):
        """Exporter la liste des drivers en TXT/CSV"""
        if not self.drivers_found:
            messagebox.showinfo("Aucun Driver", "Veuillez d'abord effectuer un scan avant d'exporter.")
            return

        from tkinter import filedialog

        # Demander format
        format_choice = messagebox.askquestion(
            "Format d'Export",
            "Exporter en format CSV ?\n\nOui = CSV (Excel)\nNon = TXT (Texte)"
        )

        if format_choice == 'yes':
            default_ext = ".csv"
            file_types = [("CSV files", "*.csv"), ("All files", "*.*")]
        else:
            default_ext = ".txt"
            file_types = [("Text files", "*.txt"), ("All files", "*.*")]

        # Demander emplacement
        filename = filedialog.asksaveasfilename(
            title="Enregistrer la liste des drivers",
            defaultextension=default_ext,
            filetypes=file_types,
            initialfile=f"drivers_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}{default_ext}"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if format_choice == 'yes':
                    # Format CSV
                    f.write("Numéro;Driver;Fabricant;Classe;Version;Date;Fichier;Boot Critical\n")
                    for i, driver in enumerate(self.drivers_found, 1):
                        f.write(f"{i};"
                                f"{driver.get('Driver', 'N/A')};"
                                f"{driver.get('ProviderName', 'N/A')};"
                                f"{driver.get('ClassName', 'N/A')};"
                                f"{driver.get('Version', 'N/A')};"
                                f"{driver.get('Date', 'N/A')};"
                                f"{driver.get('OriginalFileName', 'N/A')};"
                                f"{'Oui' if driver.get('BootCritical') else 'Non'}\n")
                else:
                    # Format TXT
                    f.write("═══════════════════════════════════════════════════════════\n")
                    f.write("     LISTE COMPLÈTE DES PILOTES INSTALLÉS\n")
                    f.write(f"     Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
                    f.write(f"     Total: {len(self.drivers_found)} pilotes\n")
                    f.write("═══════════════════════════════════════════════════════════\n\n")

                    for i, driver in enumerate(self.drivers_found, 1):
                        f.write(f"[{i}] {driver.get('Driver', 'N/A')}\n")
                        f.write(f"    Fabricant:     {driver.get('ProviderName', 'N/A')}\n")
                        f.write(f"    Classe:        {driver.get('ClassName', 'N/A')}\n")
                        f.write(f"    Version:       {driver.get('Version', 'N/A')}\n")
                        f.write(f"    Date:          {driver.get('Date', 'N/A')}\n")
                        f.write(f"    Fichier:       {driver.get('OriginalFileName', 'N/A')}\n")
                        f.write(f"    Boot Critical: {'Oui' if driver.get('BootCritical') else 'Non'}\n")
                        f.write("───────────────────────────────────────────────────────────\n\n")

            messagebox.showinfo(
                "Export Réussi",
                f"✅ Liste exportée avec succès!\n\n"
                f"Fichier: {filename}\n"
                f"Pilotes exportés: {len(self.drivers_found)}"
            )

            # Ouvrir le fichier
            if messagebox.askyesno("Ouvrir le fichier", "Voulez-vous ouvrir le fichier exporté ?"):
                subprocess.run(['notepad.exe', filename])

        except Exception as e:
            messagebox.showerror("Erreur d'Export", f"Erreur lors de l'export:\n\n{str(e)}")
