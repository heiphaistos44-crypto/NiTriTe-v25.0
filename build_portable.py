#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de build multi-plateforme pour NiTriTe V25
Fonctionne sur Windows, Linux et macOS
Version corrigee avec support d'encodage ameliore
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration de l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Ignorer si déjà configuré

def print_header(text):
    """Afficher un header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def force_remove_readonly(func, path, exc_info):
    """Fonction pour forcer la suppression de fichiers en lecture seule"""
    import stat
    try:
        # Changer les permissions
        os.chmod(path, stat.S_IWUSR | stat.S_IWRITE | stat.S_IREAD)
        func(path)
    except Exception:
        # Si ça ne marche toujours pas, passer silencieusement
        pass

def clean_build():
    """Nettoyer les anciens builds"""
    print("[*] Nettoyage des anciens builds...")
    print("    (Les fichiers verrouilles seront ignores)")

    import time
    import subprocess

    # Tuer les processus qui pourraient bloquer
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'NiTriTe_V25_Portable.exe'],
                      capture_output=True, timeout=5)
        time.sleep(1)
    except:
        pass

    dirs_to_clean = ['dist', 'build', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"    Suppression: {dir_name}/")
            # Utiliser rmdir /S /Q de Windows qui est plus robuste
            if sys.platform == 'win32':
                try:
                    subprocess.run(['cmd', '/c', 'rmdir', '/S', '/Q', dir_name],
                                  capture_output=True, timeout=30)
                    time.sleep(0.5)
                except:
                    pass

            # Tentative avec shutil si le dossier existe toujours
            if os.path.exists(dir_name):
                for attempt in range(3):
                    try:
                        shutil.rmtree(dir_name, onerror=force_remove_readonly)
                        break
                    except Exception as e:
                        if attempt < 2:
                            time.sleep(1)
                        else:
                            # Ignorer silencieusement - PyInstaller gérera
                            pass

    # Nettoyer aussi les __pycache__ dans src/
    for root, dirs, files in os.walk('src'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path, onerror=force_remove_readonly)
            except:
                pass

    print("[OK] Nettoyage termine\n")

def check_python_version():
    """Vérifier la version de Python"""
    print("[*] Verification de Python...")
    py_version = sys.version_info

    if py_version.major != 3 or py_version.minor < 8:
        print(f"[X] ERREUR: Python {py_version.major}.{py_version.minor} detecte")
        print("[!] Python 3.8+ requis")
        return False

    print(f"[OK] Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    return True

def check_dependencies():
    """Vérifier les dépendances"""
    print("\n[*] Verification des dependances...")

    # Mapping package pip -> module Python
    required = {
        'customtkinter': 'customtkinter',
        'Pillow': 'PIL',
        'requests': 'requests',
        'psutil': 'psutil',
        'pyinstaller': 'PyInstaller'
    }

    missing = []
    for package, module in required.items():
        try:
            __import__(module)
            print(f"    [OK] {package}")
        except ImportError:
            print(f"    [X] {package} - MANQUANT")
            missing.append(package)

    if missing:
        print(f"\n[!] Dependances manquantes: {', '.join(missing)}")
        print("[*] Installation automatique...")

        for package in missing:
            print(f"    Installation de {package}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"    [OK] {package} installe")
            else:
                print(f"    [X] Erreur lors de l'installation de {package}")
                return False

        print("[OK] Installation terminee")

    return True

def check_files():
    """Vérifier que tous les fichiers nécessaires existent"""
    print("\n[*] Verification des fichiers...")

    required_files = [
        'src/v14_mvp/main_app.py',
        'data/programs.json',
        'NiTriTe_V25_Portable.spec',
        'config/app_config.json',
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"    [OK] {file_path}")
        else:
            print(f"    [X] {file_path} - MANQUANT")
            all_exist = False

    # Assets optionnels
    if os.path.exists('assets/Nitrite_icon1.ico'):
        print(f"    [OK] assets/Nitrite_icon1.ico (icone)")
    else:
        print(f"    [!] assets/Nitrite_icon1.ico - optionnel (pas d'icone)")

    return all_exist

def build_executable():
    """Builder l'exécutable avec PyInstaller"""
    print("\n[*] Build de l'executable avec PyInstaller...")
    print("    Cette operation peut prendre plusieurs minutes...\n")

    try:
        # Utiliser python -m PyInstaller pour compatibilité Windows
        # Note: --clean retiré car il cause des problèmes de permissions sur Windows
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--noconfirm', 'NiTriTe_V25_Portable.spec'],
            check=True,
            capture_output=False,
            text=True
        )

        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[X] ERREUR lors du build:")
        print(f"    Code de sortie: {e.returncode}")
        return False

    except FileNotFoundError:
        print("\n[X] ERREUR: PyInstaller non trouve")
        print("    Installation: pip install pyinstaller")
        return False

def verify_build():
    """Vérifier que le build a réussi"""
    print("\n[*] Verification du build...")

    # Chercher l'exécutable (extension dépend de l'OS)
    exe_name = 'NiTriTe_V25_Portable.exe' if sys.platform == 'win32' else 'NiTriTe_V25_Portable'
    exe_dir = Path('dist') / 'NiTriTe_V25_Portable'
    exe_path = exe_dir / exe_name

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Executable cree: {exe_path}")
        print(f"    Taille: {size_mb:.1f} MB")
        return True
    else:
        print(f"[X] Executable non trouve: {exe_path}")
        return False

def copy_essential_folders_to_dist():
    """Copier les dossiers essentiels vers dist/"""
    print("\n[*] Copie des dossiers essentiels vers dist/...")

    dist_dir = Path('dist') / 'NiTriTe_V25_Portable'

    # Liste des dossiers a copier
    folders_to_copy = [
        ('Script Windows', 'Script Windows'),
        ('Windows Scripts', 'Windows Scripts'),
        ('logiciel', 'logiciel'),
        ('Drivers', 'Drivers'),
        ('config', 'config'),
    ]

    import time
    success_count = 0

    for src_name, dst_name in folders_to_copy:
        src_path = Path(src_name)
        dst_path = dist_dir / dst_name

        # Si le dossier source n'existe pas, créer un dossier vide avec README
        if not src_path.exists():
            print(f"[!] Dossier '{src_name}' non trouve - Creation d'un dossier vide...")
            src_path.mkdir(exist_ok=True)

            readme_content = f"Dossier {src_name}\n{'='*40}\n\n"
            if src_name == 'Windows Scripts':
                readme_content += "Placez vos scripts Windows (.bat, .cmd, .ps1) ici.\n"
                readme_content += "Ils seront accessibles depuis la categorie 'Scripts Windows' de NiTriTe.\n"
            elif src_name == 'logiciel':
                readme_content += "Placez vos logiciels portables ici.\n"
                readme_content += "Ils seront accessibles depuis NiTriTe.\n"
            elif src_name == 'Drivers':
                readme_content += "Placez vos drivers ici.\n"
                readme_content += "Ils seront accessibles depuis le gestionnaire de pilotes de NiTriTe.\n"

            readme_path = src_path / "README.txt"
            readme_path.write_text(readme_content, encoding='utf-8')
            print(f"[OK] Dossier '{src_name}' cree avec README.txt")

        try:
            # Supprimer l'ancien dossier s'il existe
            if dst_path.exists():
                print(f"    Suppression de l'ancien dossier {dst_name}...")
                shutil.rmtree(dst_path, ignore_errors=True)

            time.sleep(0.3)

            # Copier le nouveau dossier
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

            # Compter les éléments copiés
            items_count = len(list(dst_path.rglob('*')))
            size_mb = sum(f.stat().st_size for f in dst_path.rglob('*') if f.is_file()) / (1024 * 1024)

            print(f"[OK] '{src_name}' copie vers dist/ ({items_count} elements, {size_mb:.1f} MB)")
            success_count += 1

        except Exception as e:
            print(f"[!] Erreur copie {src_name}: {e}")

    print(f"\n[*] {success_count}/{len(folders_to_copy)} dossiers copies avec succes")
    return success_count > 0

def create_launcher_batch():
    """Créer un fichier batch de lancement dans dist/"""
    print("\n[*] Creation du fichier de lancement...")

    dist_dir = Path('dist') / 'NiTriTe_V25_Portable'
    launcher_path = dist_dir / 'Lancer_NiTriTe_V20.bat'

    launcher_content = '''@echo off
chcp 65001 >nul
title NiTriTe V25 - Lancement

echo ================================================
echo   NiTriTe V25 - Lancement en cours...
echo ================================================
echo.

start "" "NiTriTe_V25_Portable.exe"

timeout /t 2 >nul
exit
'''

    try:
        launcher_path.write_text(launcher_content, encoding='utf-8')
        print(f"[OK] Fichier de lancement cree: {launcher_path}")
        return True
    except Exception as e:
        print(f"[!] Erreur creation launcher: {e}")
        return False

def create_readme():
    """Créer un README dans dist/"""
    print("\n[*] Creation du README...")

    dist_dir = Path('dist') / 'NiTriTe_V25_Portable'
    readme_path = dist_dir / 'README.txt'

    readme_content = """NiTriTe V25 - Version Portable
====================================

Installation:
1. Extraire tous les fichiers dans un dossier
2. Double-cliquer sur Lancer_NiTriTe_V20.bat (ou NiTriTe_V25_Portable.exe)

Configuration requise:
- Windows 10/11 (64-bit)
- Aucune installation requise
- Tous les composants sont embarques

Nouveautes V20:
- Interface modernisee avec CustomTkinter
- Scanner de virus avance avec multiples moteurs
- Gestionnaire de pilotes ameliore
- Utilitaires systeme integres
- Base de connaissances interactive
- Statistiques et rapports detailles
- Windows Update Manager
- Activation Windows et Office
- Et bien plus...

Structure des dossiers:
- data/           : Donnees de configuration et programmes
- assets/         : Ressources graphiques
- src/            : Code source embarque
- Windows Scripts/: Scripts Windows personnalisables

Support:
Pour toute question ou probleme, consultez la documentation dans l'application
ou visitez le depot GitHub du projet.

(c) 2024 NiTriTe Team
"""

    try:
        readme_path.write_text(readme_content, encoding='utf-8')
        print(f"[OK] README cree: {readme_path}")
        return True
    except Exception as e:
        print(f"[!] Erreur creation README: {e}")
        return False

def create_portable_package():
    """Créer un package portable complet dans release/"""
    print("\n[*] Creation du package portable de distribution...")

    dist_dir = Path('dist') / 'NiTriTe_V25_Portable'
    release_dir = Path('release')

    if not dist_dir.exists():
        print("[X] Dossier dist/ non trouve, impossible de creer le package")
        return False

    try:
        # Créer dossier de release
        if release_dir.exists():
            print("    Suppression de l'ancien package...")
            shutil.rmtree(release_dir, ignore_errors=True)

        import time
        time.sleep(0.5)

        release_dir.mkdir(exist_ok=True)
        release_app_dir = release_dir / 'NiTriTe_V25_Portable'

        print(f"    Copie de l'application complete vers release/...")
        shutil.copytree(dist_dir, release_app_dir, dirs_exist_ok=True)

        # Compter les elements copies
        items_count = len(list(release_app_dir.rglob('*')))
        size_mb = sum(f.stat().st_size for f in release_app_dir.rglob('*') if f.is_file()) / (1024 * 1024)

        print(f"[OK] Package portable cree dans: release/")
        print(f"    Elements: {items_count}")
        print(f"    Taille totale: {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"[!] Erreur creation package: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print_header("NiTriTe V25 - Build Portable")

    # 1. Vérifier Python
    if not check_python_version():
        return 1

    # 2. Vérifier dépendances
    if not check_dependencies():
        return 1

    # 3. Vérifier fichiers
    if not check_files():
        print("\n[X] Fichiers manquants - Impossible de continuer")
        return 1

    # 4. Nettoyer
    clean_build()

    # 5. Builder
    print_header("Demarrage du Build")

    if not build_executable():
        print("\n[X] BUILD ECHOUE")
        return 1

    # 6. Vérifier
    if not verify_build():
        print("\n[X] BUILD ECHOUE - Executable non cree")
        return 1

    # 7. Copier dossiers essentiels (Script Windows, logiciel, Drivers) vers dist/
    copy_essential_folders_to_dist()

    # 8. Créer fichier de lancement
    create_launcher_batch()

    # 9. Créer README
    create_readme()

    # 10. Créer package portable pour distribution
    if not create_portable_package():
        print("\n[!] Package portable non cree, mais executable disponible dans dist/")

    # Succès !
    print_header("BUILD REUSSI !")

    exe_name = 'NiTriTe_V25_Portable.exe' if sys.platform == 'win32' else 'NiTriTe_V25_Portable'
    print(f"[OK] Executable pret: dist/NiTriTe_V25_Portable/{exe_name}")
    print(f"[OK] Package portable: release/NiTriTe_V25_Portable/")
    print(f"\n[*] Pour distribuer:")
    print(f"    1. Testez l'executable: dist/NiTriTe_V25_Portable/{exe_name}")
    print(f"    2. Verifiez toutes les fonctionnalites")
    print(f"    3. Compressez et distribuez: release/NiTriTe_V25_Portable/")
    print("\n" + "="*60 + "\n")

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Build annule par l'utilisateur (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
