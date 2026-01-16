# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_all

# Ajouter src/ au path pour que les imports fonctionnent
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

# Imports caches critiques pour NiTriTe V25
hiddenimports = [
    # Systeme et monitoring
    'psutil', 'requests', 'webbrowser', 'html',
    # Interface graphique
    'customtkinter', 'tkinter', 'tkinter.ttk', 'tkinter.font',
    # Images
    'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL._tkinter_finder',
    # Modules internes
    'importlib', 'importlib.util',
    # Cryptographie (dechiffrement mots de passe navigateurs)
    'Crypto', 'Crypto.Cipher', 'Crypto.Cipher.AES',
    # Google Generative AI pour l'agent IA
    'google.generativeai', 'google.ai.generativelanguage',
    # Sklearn pour AI knowledge base
    'sklearn', 'sklearn.feature_extraction', 'sklearn.feature_extraction.text',
    'sklearn.metrics', 'sklearn.metrics.pairwise',
    # Nouvelles pages V25
    'v14_mvp.page_drivers', 'v14_mvp.page_scanvirus',
    'v14_mvp.page_advanced_driver_scanner', 'v14_mvp.pages_full',
]

# Ajouter les modules v14_mvp dynamiquement
import glob
v14_mvp_files = glob.glob(os.path.join('src', 'v14_mvp', '*.py'))
for file in v14_mvp_files:
    module_name = os.path.splitext(os.path.basename(file))[0]
    if module_name != '__init__':
        hiddenimports.append(f'v14_mvp.{module_name}')

# Ajouter les modules src/ dynamiquement
src_files = glob.glob(os.path.join('src', '*.py'))
for file in src_files:
    module_name = os.path.splitext(os.path.basename(file))[0]
    if module_name != '__init__':
        hiddenimports.append(module_name)

# Ajouter win32com seulement sur Windows
if sys.platform == 'win32':
    try:
        hiddenimports += ['wmi', 'win32com', 'win32com.client', 'pythoncom']
        hiddenimports += collect_submodules('win32com')
        hiddenimports += collect_submodules('pythoncom')
    except:
        pass  # Ignorer si non disponible

# Ajouter customtkinter submodules
try:
    hiddenimports += collect_submodules('customtkinter')
except:
    pass

# Ajouter sklearn submodules
try:
    hiddenimports += collect_submodules('sklearn')
except:
    pass

# Construction de la liste des datas
datas_list = [
    ('data', 'data'),
    ('assets', 'assets'),
    ('config', 'config'),
    ('src', 'src'),
]

# Ajouter les dossiers optionnels s'ils existent
optional_folders = [
    ('Script Windows', 'Script Windows'),
    ('Windows Scripts', 'Windows Scripts'),
    ('logiciel', 'logiciel'),
    ('Drivers', 'Drivers'),
]

for src_folder, dst_folder in optional_folders:
    if os.path.exists(src_folder):
        datas_list.append((src_folder, dst_folder))
        print(f"[SPEC] Dossier inclus: {src_folder}")

a = Analysis(
    [os.path.join('src', 'v14_mvp', 'main_app.py')],
    pathex=[os.path.join(os.getcwd(), 'src')],
    binaries=[],
    datas=datas_list,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy.testing', 'pandas', 'scipy', 'IPython'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NiTriTe_V25_Portable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='assets/Nitrite_icon1.ico' if os.path.exists('assets/Nitrite_icon1.ico') else None,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NiTriTe_V25_Portable'
)
