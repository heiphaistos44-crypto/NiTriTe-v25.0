#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page Statistiques & Rapports - NiTriTe V20
Affichage centralisé de tous les rapports générés (HTML, TXT, MD, JSON)
Vue d'ensemble des rapports de Diagnostic, Scan Total, Batterie, etc.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import os
import sys
import subprocess
import webbrowser
from datetime import datetime
from v14_mvp.design_system import DesignTokens
from v14_mvp.components import ModernCard, ModernButton, SectionHeader, ModernStatsCard


class StatisticsReportsPage(ctk.CTkFrame):
    """Page Statistiques & Rapports - Centre de rapports système"""

    def __init__(self, parent):
        super().__init__(parent, fg_color=DesignTokens.BG_PRIMARY)

        try:
            # Déterminer le dossier racine de l'application
            if getattr(sys, 'frozen', False):
                # Mode PyInstaller
                app_root = Path(sys.executable).parent
            else:
                # Mode développement
                app_root = Path(__file__).parent.parent.parent

            # Dossiers de rapports (chemins dynamiques)
            self.reports_folders = [
                Path.home() / "Documents" / "NiTriTe_Reports",
                app_root / "data" / "logs",
                app_root / "data" / "reports",
                Path.home() / "Downloads",  # Pour rapports PowerCfg, etc.
                Path("C:/Windows/Temp"),  # Rapports temporaires
            ]

            # Créer dossier principal si inexistant
            self.main_reports_folder = self.reports_folders[0]
            self.main_reports_folder.mkdir(parents=True, exist_ok=True)

            self.all_reports = []

            # NOUVEAU : Un seul scrollable frame pour TOUTE la page
            self.scroll = ctk.CTkScrollableFrame(self, fg_color=DesignTokens.BG_PRIMARY)
            self.scroll.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

            self._create_header()
            self._create_content()
            self._scan_reports()

        except Exception as e:
            # Afficher l'erreur au lieu d'un écran noir
            import traceback
            error_msg = f"Erreur lors du chargement de la page:\n\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)

            # Afficher un message d'erreur visible
            error_frame = ctk.CTkFrame(self, fg_color=DesignTokens.BG_PRIMARY)
            error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            ctk.CTkLabel(
                error_frame,
                text="❌ Erreur de Chargement",
                font=(DesignTokens.FONT_FAMILY, 24, "bold"),
                text_color="#EF4444"
            ).pack(pady=(20, 10))

            error_text = ctk.CTkTextbox(
                error_frame,
                width=800,
                height=400,
                fg_color=DesignTokens.BG_SECONDARY
            )
            error_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
            error_text.insert("1.0", error_msg)
            error_text.configure(state="disabled")

    def _create_header(self):
        """Header de la page"""
        header = ModernCard(self.scroll)
        header.pack(fill=tk.X, padx=20, pady=10)

        container = ctk.CTkFrame(header, fg_color="transparent")
        container.pack(fill=tk.X, padx=20, pady=15)

        # Titre
        SectionHeader(container, text="📊 Statistiques & Rapports Système").pack(side=tk.LEFT)

        # Boutons d'action
        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(side=tk.RIGHT)

        ModernButton(
            actions,
            text="🔄 Actualiser",
            variant="outlined",
            command=self._refresh_reports
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            actions,
            text="📂 Ouvrir Dossier",
            variant="outlined",
            command=self._open_reports_folder
        ).pack(side=tk.LEFT, padx=5)

        ModernButton(
            actions,
            text="🗑️ Nettoyer Anciens",
            variant="outlined",
            command=self._cleanup_old_reports
        ).pack(side=tk.LEFT, padx=5)

    def _create_content(self):
        """Contenu de la page (rapports)"""
        # Info (self.scroll existe déjà depuis __init__)
        info_card = ModernCard(self.scroll)
        info_card.pack(fill=tk.X, padx=20, pady=10)

        info_text = ctk.CTkLabel(
            info_card,
            text="ℹ️ Cette page centralise tous les rapports système générés par NiTriTe.\n"
                 "Rapports de diagnostic, scan total, batterie, CrystalDiskInfo, etc.",
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            justify="left"
        )
        info_text.pack(padx=20, pady=15)

        # Container pour les rapports (sera rempli par _scan_reports)
        self.reports_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.reports_container.pack(fill=tk.BOTH, expand=True, padx=20)

    def _scan_reports(self):
        """Scanner tous les dossiers pour trouver les rapports"""
        self.all_reports = []

        # Extensions de rapports supportées (uniquement .txt et .html)
        report_extensions = ['.html', '.txt']

        for folder in self.reports_folders:
            if not folder.exists():
                continue

            try:
                for file_path in folder.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in report_extensions:
                        # Filtrer les rapports pertinents
                        file_name_lower = file_path.name.lower()
                        if any(keyword in file_name_lower for keyword in [
                            'rapport', 'report', 'scan', 'diagnostic', 'battery', 'batterie',
                            'crystal', 'disk', 'nitrite', 'system', 'log', 'powercfg'
                        ]):
                            stat = file_path.stat()
                            self.all_reports.append({
                                'path': file_path,
                                'name': file_path.name,
                                'size': stat.st_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime),
                                'type': file_path.suffix.upper()[1:]
                            })
            except Exception as e:
                print(f"Erreur scan dossier {folder}: {e}")

        # Trier par date (plus récent en premier)
        self.all_reports.sort(key=lambda x: x['modified'], reverse=True)

        # Afficher
        self._display_reports()

    def _format_size(self, size_bytes):
        """Formater la taille en unité lisible"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _display_reports(self):
        """Afficher les rapports trouvés"""
        # Nettoyer
        for widget in self.reports_container.winfo_children():
            widget.destroy()

        if not self.all_reports:
            # Aucun rapport
            no_reports = ModernCard(self.reports_container)
            no_reports.pack(fill=tk.X, pady=20)

            ctk.CTkLabel(
                no_reports,
                text="📭 Aucun rapport trouvé\n\nLancez des diagnostics ou scans pour générer des rapports",
                font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_MD),
                text_color=DesignTokens.TEXT_SECONDARY,
                justify="center"
            ).pack(pady=30)
            return

        # Statistiques globales
        stats_card = ModernCard(self.reports_container)
        stats_card.pack(fill=tk.X, pady=10)

        stats_title = SectionHeader(stats_card, text=f"📈 Statistiques - {len(self.all_reports)} rapports trouvés")
        stats_title.pack(pady=10)

        # Compter par type
        type_counts = {}
        total_size = 0
        for report in self.all_reports:
            type_counts[report['type']] = type_counts.get(report['type'], 0) + 1
            total_size += report['size']

        stats_frame = ctk.CTkFrame(stats_card, fg_color="transparent")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        stats_text = f"📌 Rapports par type: "
        for rtype, count in sorted(type_counts.items()):
            stats_text += f"{rtype}({count})  "
        stats_text += f"\n💾 Taille totale: {self._format_size(total_size)}"

        ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=(DesignTokens.FONT_FAMILY, DesignTokens.FONT_SIZE_SM),
            text_color=DesignTokens.TEXT_SECONDARY,
            justify="left"
        ).pack(anchor="w")

        # Liste des rapports organisés par catégories déroulantes
        reports_card = ModernCard(self.reports_container)
        reports_card.pack(fill=tk.X, pady=10)

        reports_title = SectionHeader(reports_card, text="📄 Rapports par Catégories")
        reports_title.pack(pady=10)

        # Frame pour les catégories
        categories_container = ctk.CTkFrame(reports_card, fg_color=DesignTokens.BG_SECONDARY, corner_radius=12)
        categories_container.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Catégoriser les rapports et créer les accordéons
        self._create_categorized_accordions(categories_container)

        # Section logs catégorisés et redimensionnables
        self._create_categorized_logs()

    def _create_categorized_accordions(self, parent):
        """Créer les accordéons par catégorie de rapports"""
        # Définir les catégories avec leurs critères de filtrage
        categories = [
            {
                'id': 'backup',
                'title': '💾 Sauvegardes',
                'icon': '💾',
                'color': '#10B981',
                'keywords': ['backup', 'sauvegarde']
            },
            {
                'id': 'diagnostic',
                'title': '🔍 Rapports de Diagnostic',
                'icon': '🔍',
                'color': '#3B82F6',
                'keywords': ['diagnostic', 'diag', 'report']
            },
            {
                'id': 'virus',
                'title': '🛡️ Scans de Virus & Sécurité',
                'icon': '🛡️',
                'color': '#EF4444',
                'keywords': ['virus', 'scan', 'malware', 'security', 'threat', 'securite']
            },
            {
                'id': 'update',
                'title': '⬆️ Mises à Jour',
                'icon': '⬆️',
                'color': '#F59E0B',
                'keywords': ['update', 'maj', 'upgrade']
            },
            {
                'id': 'application',
                'title': '📱 Logs d\'Application',
                'icon': '📱',
                'color': '#8B5CF6',
                'keywords': ['app', 'log', 'application']
            },
            {
                'id': 'system',
                'title': '⚙️ Système',
                'icon': '⚙️',
                'color': '#6366F1',
                'keywords': ['system', 'hardware', 'driver', 'device', 'systeme']
            },
            {
                'id': 'performance',
                'title': '⚡ Performance',
                'icon': '⚡',
                'color': '#EC4899',
                'keywords': ['perf', 'monitor', 'benchmark', 'speed']
            },
            {
                'id': 'other',
                'title': '📄 Autres Rapports',
                'icon': '📄',
                'color': '#64748B',
                'keywords': []  # Tout ce qui ne correspond à aucune catégorie
            }
        ]

        # Catégoriser les rapports
        categorized_reports = {cat['id']: [] for cat in categories}

        for report in self.all_reports:
            report_name_lower = report['name'].lower()
            categorized = False

            # Vérifier chaque catégorie (sauf 'other')
            for cat in categories[:-1]:  # Exclure 'other' de la boucle
                if any(keyword in report_name_lower for keyword in cat['keywords']):
                    categorized_reports[cat['id']].append(report)
                    categorized = True
                    break

            # Si non catégorisé, mettre dans 'other'
            if not categorized:
                categorized_reports['other'].append(report)

        # Créer les accordéons
        self.accordion_states = {}  # Stocker l'état expanded/collapsed
        self.accordion_contents = {}  # Stocker les frames de contenu

        for cat in categories:
            cat_id = cat['id']
            reports = categorized_reports[cat_id]

            # Ne créer la section que si elle contient des rapports
            if reports:
                self._create_accordion_section(parent, cat, reports)

    def _create_accordion_section(self, parent, category, reports):
        """Créer une section déroulante pour une catégorie"""
        cat_id = category['id']

        # Frame principal de la section
        section_frame = ctk.CTkFrame(parent, fg_color=DesignTokens.BG_PRIMARY, corner_radius=8)
        section_frame.pack(fill=tk.X, pady=5, padx=5)

        # Header cliquable
        header_frame = ctk.CTkFrame(section_frame, fg_color=DesignTokens.BG_SECONDARY, corner_radius=8)
        header_frame.pack(fill=tk.X, padx=2, pady=2)

        # État initial: collapsed (False) ou expanded (True)
        self.accordion_states[cat_id] = False

        # Icône d'expansion (▶ collapsed, ▼ expanded)
        expand_icon = ctk.CTkLabel(
            header_frame,
            text="▶",
            font=(DesignTokens.FONT_FAMILY, 14, "bold"),
            text_color=category['color'],
            width=30
        )
        expand_icon.pack(side=tk.LEFT, padx=(10, 5), pady=10)

        # Titre de la catégorie
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{category['icon']} {category['title']} ({len(reports)})",
            font=(DesignTokens.FONT_FAMILY, 14, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=10)

        # Frame pour le contenu (initialement caché)
        content_frame = ctk.CTkFrame(section_frame, fg_color=DesignTokens.BG_SECONDARY, corner_radius=8)
        self.accordion_contents[cat_id] = content_frame

        # Remplir le contenu avec les rapports
        for i, report in enumerate(reports[:50]):  # Limiter à 50 pour performance
            self._create_report_item(content_frame, report, i+1)

        # Fonction toggle pour expand/collapse
        def toggle_accordion():
            is_expanded = self.accordion_states[cat_id]

            if is_expanded:
                # Collapse
                content_frame.pack_forget()
                expand_icon.configure(text="▶")
                self.accordion_states[cat_id] = False
            else:
                # Expand
                content_frame.pack(fill=tk.X, padx=2, pady=(0, 2))
                expand_icon.configure(text="▼")
                self.accordion_states[cat_id] = True

        # Bind click events sur le header
        for widget in [header_frame, expand_icon, title_label]:
            widget.bind('<Button-1>', lambda e: toggle_accordion())
            widget.configure(cursor="hand2")

    def _create_report_item(self, parent, report, num):
        """Créer un item de rapport"""
        item_frame = ctk.CTkFrame(parent, fg_color=DesignTokens.BG_PRIMARY, corner_radius=8)
        item_frame.pack(fill=tk.X, pady=5, padx=5)

        # Numéro
        num_label = ctk.CTkLabel(
            item_frame,
            text=f"#{num}",
            font=(DesignTokens.FONT_FAMILY, 12, "bold"),
            text_color=DesignTokens.ACCENT_PRIMARY,
            width=50
        )
        num_label.pack(side=tk.LEFT, padx=10, pady=10)

        # Info rapport
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

        # Icône selon type
        type_icons = {
            'HTML': '🌐',
            'TXT': '📝',
            'MD': '📄',
            'JSON': '🔧',
            'LOG': '📋',
            'XML': '📑'
        }
        icon = type_icons.get(report['type'], '📄')

        ctk.CTkLabel(
            info_frame,
            text=f"{icon} {report['name']}",
            font=(DesignTokens.FONT_FAMILY, 14, "bold"),
            text_color=DesignTokens.TEXT_PRIMARY,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text=f"Type: {report['type']}  •  Taille: {self._format_size(report['size'])}  •  Modifié: {report['modified'].strftime('%d/%m/%Y %H:%M')}",
            font=(DesignTokens.FONT_FAMILY, 11),
            text_color=DesignTokens.TEXT_SECONDARY,
            anchor="w"
        ).pack(anchor="w", pady=(3, 0))

        # Boutons d'action
        actions_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        actions_frame.pack(side=tk.RIGHT, padx=10)

        ModernButton(
            actions_frame,
            text="📖 Ouvrir",
            variant="filled",
            width=100,
            command=lambda p=report['path']: self._open_report(p)
        ).pack(side=tk.LEFT, padx=3)

        ModernButton(
            actions_frame,
            text="📂 Dossier",
            variant="outlined",
            width=100,
            command=lambda p=report['path']: self._open_report_folder(p)
        ).pack(side=tk.LEFT, padx=3)

        ModernButton(
            actions_frame,
            text="🗑️",
            variant="outlined",
            width=50,
            command=lambda p=report['path']: self._delete_report(p)
        ).pack(side=tk.LEFT, padx=3)

    def _format_size(self, size_bytes):
        """Formater la taille en KB/MB"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _open_report(self, file_path):
        """Ouvrir un rapport"""
        try:
            if file_path.suffix.lower() == '.html':
                webbrowser.open(str(file_path))
            else:
                os.startfile(str(file_path))
            print(f"✓ Rapport ouvert: {file_path.name}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le rapport:\n\n{str(e)}")

    def _open_report_folder(self, file_path):
        """Ouvrir le dossier contenant le rapport"""
        try:
            subprocess.run(['explorer', '/select,', str(file_path)])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n\n{str(e)}")

    def _delete_report(self, file_path):
        """Supprimer un rapport"""
        response = messagebox.askyesno(
            "Supprimer le rapport",
            f"Êtes-vous sûr de vouloir supprimer ce rapport ?\n\n{file_path.name}"
        )

        if response:
            try:
                file_path.unlink()
                messagebox.showinfo("Succès", "Rapport supprimé avec succès")
                self._refresh_reports()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le rapport:\n\n{str(e)}")

    def _refresh_reports(self):
        """Rafraîchir la liste des rapports"""
        self._scan_reports()

    def _open_reports_folder(self):
        """Ouvrir le dossier principal des rapports"""
        try:
            os.startfile(str(self.main_reports_folder))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n\n{str(e)}")

    def _cleanup_old_reports(self):
        """Nettoyer les anciens rapports (>30 jours)"""
        response = messagebox.askyesno(
            "Nettoyer les Anciens Rapports",
            "Cette opération va supprimer tous les rapports de plus de 30 jours.\n\n"
            "Continuer ?"
        )

        if not response:
            return

        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 jours

        for report in self.all_reports:
            if report['modified'].timestamp() < cutoff_date:
                try:
                    report['path'].unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Erreur suppression {report['name']}: {e}")

        messagebox.showinfo(
            "Nettoyage Terminé",
            f"✅ {deleted_count} rapport(s) ancien(s) supprimé(s)"
        )

        self._refresh_reports()

    def _create_categorized_logs(self):
        """Section logs catégorisés et redimensionnables"""
        logs_container = ModernCard(self.scroll)
        logs_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Header avec titre et boutons de redimensionnement
        header_frame = ctk.CTkFrame(logs_container, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        SectionHeader(header_frame, text="📋 Logs Détaillés par Catégorie").pack(side=tk.LEFT)

        # Boutons de redimensionnement
        resize_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        resize_frame.pack(side=tk.RIGHT)

        ctk.CTkButton(
            resize_frame,
            text="▲",
            width=40,
            height=30,
            font=(DesignTokens.FONT_FAMILY, 16, "bold"),
            fg_color=DesignTokens.ACCENT_PRIMARY,
            hover_color=DesignTokens.ACCENT_HOVER,
            command=lambda: self._resize_logs(100)
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            resize_frame,
            text="▼",
            width=40,
            height=30,
            font=(DesignTokens.FONT_FAMILY, 16, "bold"),
            fg_color=DesignTokens.ACCENT_PRIMARY,
            hover_color=DesignTokens.ACCENT_HOVER,
            command=lambda: self._resize_logs(-100)
        ).pack(side=tk.LEFT, padx=2)

        # Boutons de catégories
        categories_frame = ctk.CTkFrame(logs_container, fg_color="transparent")
        categories_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        self.current_log_category = "diagnostic"
        self.category_buttons = {}

        categories = [
            ("diagnostic", "🔍 Diagnostic", "#3B82F6"),
            ("application", "📱 Application", "#10B981"),
            ("system", "⚙️ Système", "#F59E0B"),
            ("security", "🔒 Sécurité", "#EF4444"),
            ("performance", "⚡ Performance", "#8B5CF6")
        ]

        for i, (cat_id, cat_label, cat_color) in enumerate(categories):
            btn = ctk.CTkButton(
                categories_frame,
                text=cat_label,
                font=(DesignTokens.FONT_FAMILY, 14, "bold"),
                fg_color=cat_color if cat_id == "diagnostic" else DesignTokens.BG_TERTIARY,
                hover_color=cat_color,
                command=lambda c=cat_id, col=cat_color: self._switch_log_category(c, col)
            )
            btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
            self.category_buttons[cat_id] = {"button": btn, "color": cat_color}

        # Zone de texte redimensionnable
        self.logs_text_categorized = ctk.CTkTextbox(
            logs_container,
            font=("Consolas", 11),  # Police monospace pour logs
            fg_color=DesignTokens.BG_SECONDARY,
            text_color=DesignTokens.TEXT_PRIMARY,
            height=400,
            wrap=tk.WORD
        )
        self.logs_text_categorized.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        # Charger la catégorie par défaut
        self._load_diagnostic_logs()

    def _resize_logs(self, delta):
        """Redimensionner la zone de logs"""
        if hasattr(self, 'logs_text_categorized'):
            current_height = self.logs_text_categorized.cget("height")
            new_height = max(200, min(800, current_height + delta))
            self.logs_text_categorized.configure(height=new_height)

    def _switch_log_category(self, category, color):
        """Changer de catégorie de logs"""
        # Mettre à jour l'apparence des boutons
        for cat_id, btn_data in self.category_buttons.items():
            if cat_id == category:
                btn_data["button"].configure(fg_color=btn_data["color"])
            else:
                btn_data["button"].configure(fg_color=DesignTokens.BG_TERTIARY)

        self.current_log_category = category

        # Charger les logs de la catégorie
        if category == "diagnostic":
            self._load_diagnostic_logs()
        elif category == "application":
            self._load_application_logs()
        elif category == "system":
            self._load_system_logs()
        elif category == "security":
            self._load_security_logs()
        elif category == "performance":
            self._load_performance_logs()

    def _load_diagnostic_logs(self):
        """Charger les logs de diagnostic"""
        if not hasattr(self, 'logs_text_categorized'):
            return

        self.logs_text_categorized.delete("1.0", tk.END)
        self.logs_text_categorized.insert("1.0", "=== 🔍 LOGS DIAGNOSTIC ===\n\n")

        # Filtrer les rapports de diagnostic
        diagnostic_reports = [
            r for r in self.all_reports
            if any(keyword in r['name'].lower() for keyword in ['diagnostic', 'scan', 'test', 'check'])
        ]

        if diagnostic_reports:
            self.logs_text_categorized.insert("end", f"Nombre de rapports: {len(diagnostic_reports)}\n\n")
            for report in diagnostic_reports[:50]:  # Limiter à 50
                self.logs_text_categorized.insert(
                    "end",
                    f"📄 {report['name']}\n"
                    f"   📅 Date: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"   📁 Catégorie: {report.get('category', 'N/A')}\n"
                    f"   💾 Taille: {self._format_size(report['size'])}\n\n"
                )
        else:
            self.logs_text_categorized.insert("end", "Aucun rapport de diagnostic trouvé.\n")

    def _load_application_logs(self):
        """Charger les logs d'application"""
        if not hasattr(self, 'logs_text_categorized'):
            return

        self.logs_text_categorized.delete("1.0", tk.END)
        self.logs_text_categorized.insert("1.0", "=== 📱 LOGS APPLICATION ===\n\n")

        # Filtrer les rapports d'application
        app_reports = [
            r for r in self.all_reports
            if any(keyword in r['name'].lower() for keyword in ['app', 'install', 'winget', 'portable'])
        ]

        if app_reports:
            self.logs_text_categorized.insert("end", f"Nombre de rapports: {len(app_reports)}\n\n")
            for report in app_reports[:50]:
                self.logs_text_categorized.insert(
                    "end",
                    f"📄 {report['name']}\n"
                    f"   📅 Date: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"   📁 Catégorie: {report.get('category', 'N/A')}\n"
                    f"   💾 Taille: {self._format_size(report['size'])}\n\n"
                )
        else:
            self.logs_text_categorized.insert("end", "Aucun rapport d'application trouvé.\n")

    def _load_system_logs(self):
        """Charger les logs système"""
        if not hasattr(self, 'logs_text_categorized'):
            return

        self.logs_text_categorized.delete("1.0", tk.END)
        self.logs_text_categorized.insert("1.0", "=== ⚙️ LOGS SYSTÈME ===\n\n")

        # Filtrer les rapports système
        system_reports = [
            r for r in self.all_reports
            if any(keyword in r['name'].lower() for keyword in ['system', 'hardware', 'driver', 'device'])
        ]

        if system_reports:
            self.logs_text_categorized.insert("end", f"Nombre de rapports: {len(system_reports)}\n\n")
            for report in system_reports[:50]:
                self.logs_text_categorized.insert(
                    "end",
                    f"📄 {report['name']}\n"
                    f"   📅 Date: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"   📁 Catégorie: {report.get('category', 'N/A')}\n"
                    f"   💾 Taille: {self._format_size(report['size'])}\n\n"
                )
        else:
            self.logs_text_categorized.insert("end", "Aucun rapport système trouvé.\n")

    def _load_security_logs(self):
        """Charger les logs de sécurité"""
        if not hasattr(self, 'logs_text_categorized'):
            return

        self.logs_text_categorized.delete("1.0", tk.END)
        self.logs_text_categorized.insert("1.0", "=== 🔒 LOGS SÉCURITÉ ===\n\n")

        # Filtrer les rapports de sécurité
        security_reports = [
            r for r in self.all_reports
            if any(keyword in r['name'].lower() for keyword in ['security', 'virus', 'scan', 'malware', 'threat'])
        ]

        if security_reports:
            self.logs_text_categorized.insert("end", f"Nombre de rapports: {len(security_reports)}\n\n")
            for report in security_reports[:50]:
                self.logs_text_categorized.insert(
                    "end",
                    f"📄 {report['name']}\n"
                    f"   📅 Date: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"   📁 Catégorie: {report.get('category', 'N/A')}\n"
                    f"   💾 Taille: {self._format_size(report['size'])}\n\n"
                )
        else:
            self.logs_text_categorized.insert("end", "Aucun rapport de sécurité trouvé.\n")

    def _load_performance_logs(self):
        """Charger les logs de performance"""
        if not hasattr(self, 'logs_text_categorized'):
            return

        self.logs_text_categorized.delete("1.0", tk.END)
        self.logs_text_categorized.insert("1.0", "=== ⚡ LOGS PERFORMANCE ===\n\n")

        # Filtrer les rapports de performance
        perf_reports = [
            r for r in self.all_reports
            if any(keyword in r['name'].lower() for keyword in ['perf', 'speed', 'benchmark', 'monitor'])
        ]

        if perf_reports:
            self.logs_text_categorized.insert("end", f"Nombre de rapports: {len(perf_reports)}\n\n")
            for report in perf_reports[:50]:
                self.logs_text_categorized.insert(
                    "end",
                    f"📄 {report['name']}\n"
                    f"   📅 Date: {report['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"   📁 Catégorie: {report.get('category', 'N/A')}\n"
                    f"   💾 Taille: {self._format_size(report['size'])}\n\n"
                )
        else:
            self.logs_text_categorized.insert("end", "Aucun rapport de performance trouvé.\n")
