# NiTriTe V25.0

**Application de Maintenance Informatique Professionnelle pour Windows**

NiTriTe est une boîte à outils complète pour les techniciens informatiques, offrant une interface moderne pour la maintenance, le diagnostic et l'optimisation des systèmes Windows.

## Fonctionnalités

### Maintenance Système
- **Diagnostic complet** : Analyse CPU, RAM, disques et réseau
- **Optimisation Windows** : Scripts de nettoyage et d'optimisation
- **Gestion des pilotes** : Scanner et installer les pilotes manquants
- **Scan antivirus** : Intégration d'outils de détection de malwares

### Outils Intégrés
- **Applications portables** : Collection d'outils portables prêts à l'emploi
- **Installateur Master** : Installation en lot de logiciels essentiels
- **Scripts Windows** : Bibliothèque de tweaks et scripts d'optimisation
- **Terminal intégré** : Exécution de commandes système

### Intelligence Artificielle
- **Assistant IA** : Aide contextuelle avec Ollama (local)
- **Base de connaissances** : Documentation technique intégrée
- **Système RAG** : Recherche sémantique dans la documentation

### Interface
- **Design moderne** : Interface CustomTkinter avec thèmes personnalisables
- **Multi-thèmes** : Plusieurs palettes de couleurs disponibles
- **100% Portable** : Aucune installation requise

## Installation

### Option 1 : Version Portable (Recommandée)

1. **Cloner avec Git LFS** (important pour les gros fichiers) :
   ```bash
   git lfs install
   git clone https://github.com/heiphaistos44-crypto/NiTriTe-v25.0.git
   ```

2. Lancer `NiTriTe_V25_Portable.exe` depuis le dossier `release/NiTriTe_V25_Portable/`

### Option 2 : Depuis les sources

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/heiphaistos44-crypto/NiTriTe-v25.0.git
   cd NiTriTe-v25.0
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Lancer l'application :
   ```bash
   python src/v14_mvp/main_app.py
   ```

### Option 3 : Créer l'exécutable portable

```bash
python build_portable.py
```

Ou utiliser le script batch :
```bash
BUILD_PORTABLE.bat
```

## Configuration requise

- **OS** : Windows 10/11 (64-bit)
- **Python** : 3.10+ (pour exécution depuis les sources)
- **RAM** : 4 Go minimum
- **Espace disque** : 2 Go pour la version portable complète

## Structure du projet

```
NiTriTe-v25.0/
├── src/                    # Code source Python
│   ├── v14_mvp/           # Modules principaux de l'application
│   └── *.py               # Utilitaires et gestionnaires
├── config/                 # Fichiers de configuration
├── data/                   # Données et base de connaissances
├── logiciel/              # Outils et logiciels portables intégrés
├── Drivers/               # Pilotes et runtimes
├── Script Windows/        # Scripts d'optimisation Windows
├── dist/                  # Build de développement
├── release/               # Version portable finale
└── requirements.txt       # Dépendances Python
```

## Technologies utilisées

- **Python 3.10+**
- **CustomTkinter** - Interface graphique moderne
- **PyInstaller** - Création d'exécutables
- **Pillow** - Traitement d'images
- **psutil** - Monitoring système
- **requests** - Téléchargements HTTP

## Avertissement

Ce logiciel est fourni "tel quel" à des fins de maintenance informatique. Utilisez-le de manière responsable et uniquement sur des systèmes pour lesquels vous avez les autorisations nécessaires.

## Licence

Projet personnel - Tous droits réservés

## Auteur

**heiphaistos44-crypto**

---

*NiTriTe V25.0 - Votre boîte à outils pour la maintenance informatique professionnelle*
