# 🎬 Video AI Enhancer

<p align="center">
  <img src="static/logo.png" alt="Video AI Enhancer Official Logo" width="350">
</p>

> Améliorez n'importe quelle vidéo floue, sombre ou saccadée avec l'IA — localement, gratuitement, et en un seul clic.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20UI-black?logo=flask)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

---

## ✨ Qu'est-ce que c'est ?

**Video AI Enhancer** est un outil open-source qui améliore automatiquement vos vidéos basse qualité en les traitant image par image grâce au réseau de neurones [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN).

Il s'utilise via une **interface graphique locale** (page web dans votre navigateur) et s'installe en **une seule commande**.

### Ce qu'il fait concrètement :

| Fonctionnalité | Détail |
|---|---|
| 🤖 **Upscaling IA × 4** | Chaque image est agrandie ×4 par le réseau de neurones RRDB, qui reconstitue les détails (visages, textures, cheveux) |
| ☀️ **Correction de luminosité** | Éclaircit les vidéos trop sombres sans brûler les zones claires, via une courbe photoshop-style |
| 🎞️ **Lissage du mouvement** | Convertit une vidéo saccadée (ex: 13 fps) vers 30 fps de manière fluide |
| 🔄 **Correction de rotation** | Détecte et corrige automatiquement les vidéos mal orientées |
| 🔊 **Audio préservé** | La piste audio originale est conservée sans ré-encodage |

---

## 📊 Avant / Après

| Propriété | Vidéo originale | Vidéo améliorée |
|-----------|-----------------|-----------------|
| Résolution | 640 × 368 | **2560 × 1472** (× 4 IA) |
| FPS | ~13.81 fps (saccadé) | **30 fps** (fluide) |
| Débit vidéo | 465 kb/s | ~13 000 kb/s |
| Luminosité | Sombre / illisible | Naturelle et nette |
| Orientation | Rotation incorrecte | Corrigée automatiquement |

---

## 🚀 Installation et Lancement (1 seule commande)

### Étape 1 — Cloner le projet

```bash
# Via SSH (recommandé)
git clone git@github.com:elhamdiabderrahim8/video-enhancer.git
cd video-enhancer

# Ou via HTTPS
git clone https://github.com/elhamdiabderrahim8/video-enhancer.git
cd video-enhancer
```

### Étape 2 — Lancer le script d'installation

```bash
./setup.sh
```

> **C'est tout.** Le script s'occupe automatiquement de :
> - ✅ Vérifier et installer `ffmpeg` si nécessaire
> - ✅ Télécharger le binaire `realesrgan-ncnn-vulkan` (~11 Mo)
> - ✅ Télécharger les modèles IA (~35 Mo)
> - ✅ Créer un environnement virtuel Python et installer Flask
> - ✅ Ouvrir l'interface graphique dans votre navigateur automatiquement

### Accès manuel à l'interface (si le navigateur ne s'ouvre pas)

```
http://localhost:5000
```

---

## 🖥️ Interface Graphique

L'interface web locale permet de :

- **Sélectionner** la vidéo d'entrée en saisissant son chemin (le chemin de sortie est suggéré automatiquement)
- **Choisir le mode IA :**
  - ⚡ **Mode Rapide** (`realesr-animevideov3`) — Idéal pour une amélioration générale, environ 2× plus rapide
  - 🐢 **Mode Lent / Ultra-réaliste** (`realesrgan-x4plus`) — Meilleur pour les visages et les détails photographiques
- **Sélectionner le matériel de calcul :** GPU (Vulkan, recommandé) ou CPU
- **Ajuster la luminosité** (gamma) et la qualité de compression (CRF)
- **Voir une estimation précise du temps** calculée selon votre GPU/CPU et le nombre de frames
- **Suivre l'avancement** en temps réel via une console de logs interactive

---

## 🧠 Comment ça fonctionne — Pipeline technique

```
Vidéo d'entrée
      │
      ▼  [Étape 1 — FFmpeg]
Extraction des frames en PNG
(vsync=0, sans doublons)
      │
      ▼  [Étape 2 — Real-ESRGAN NCNN Vulkan]
Amélioration IA × 4 par frame
  ┌────────────────────────────────┐
  │ Réseau RRDB (23 blocs denses)  │
  │  Input :  640 × 368 px        │
  │  ↓ Encode le contexte         │
  │  ↓ Reconstruit les détails    │
  │  Output : 2560 × 1472 px      │
  └────────────────────────────────┘
      │
      ▼  [Étape 3 — FFmpeg]
Réassemblage final :
  - fps=30 (lissage)
  - correction de luminosité (curves)
  - encodage libx264 CRF 15 (haute qualité)
  - audio original réintégré
      │
      ▼
Vidéo finale améliorée ✅
```

---

## ⏱️ Temps de traitement estimé

Le temps dépend de votre matériel :

| Matériel | Temps par frame (mode rapide) | Temps par frame (mode lent) |
|----------|-------------------------------|------------------------------|
| NVIDIA RTX 3080 | ~0.5 sec | ~2 sec |
| NVIDIA GTX 1060 | ~1.5 sec | ~8 sec |
| Intel Iris Xe (intégré) | ~5 sec | ~67 sec |
| CPU uniquement | ~12 sec | ~5 min |

> 💡 **Conseil :** Pour une vidéo de 300 frames avec un GPU intégré Intel, comptez environ 30 minutes en mode Rapide et 6 heures en mode Lent.

---

## 📋 Prérequis système

### Requis automatiquement par `setup.sh`
- `ffmpeg` (installé via `dnf`, `apt` ou `brew` selon votre OS)
- `realesrgan-ncnn-vulkan` v0.2.0 (téléchargé et extrait automatiquement)
- Les modèles IA (téléchargés automatiquement dans `bin/models/`)
- `Flask` (installé via pip dans un environnement virtuel isolé)

### Requis manuellement par l'utilisateur
- Python 3.8 ou supérieur
- Git

### Installation de FFmpeg (si vous préférez le faire manuellement)

#### Linux — Fedora / RHEL
```bash
sudo dnf install -y ffmpeg ffmpeg-libs
```

#### Linux — Ubuntu / Debian
```bash
sudo apt update && sudo apt install -y ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
- Via Winget : `winget install "FFmpeg (Essentials)"`
- Via Chocolatey : `choco install ffmpeg`
- Manuellement : [ffmpeg.org/download.html](https://ffmpeg.org/download.html)

---

## 📁 Structure du projet

```
video-enhancer/
├── app.py                  # Serveur web local Flask (API + streaming de logs)
├── enhance_video.py        # Script principal d'amélioration vidéo (portable)
├── setup.sh                # Script d'installation automatique (1 seule commande)
├── requirements.txt        # Dépendances Python (Flask uniquement)
├── LICENSE                 # Licence MIT
├── README.md               # Ce fichier
├── templates/
│   └── index.html          # Structure HTML de l'interface graphique
└── static/
    ├── css/
    │   └── style.css       # Feuille de style Dark Glassmorphism avec animations
    └── js/
        └── app.js          # Logique JavaScript (diagnostic, estimation, logs SSE)
```

---

## 🙏 Crédits et remerciements

Ce projet est un **wrapper d'automatisation** construit au-dessus de ces excellents projets open-source :

| Projet | Auteurs | Licence |
|--------|---------|---------|
| [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | Xinntao Wang — Tencent ARC Lab | BSD-3-Clause |
| [Real-ESRGAN-ncnn-vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan) | nihui | MIT |
| [FFmpeg](https://ffmpeg.org) | L'équipe FFmpeg | LGPL / GPL |

> ⚠️ Ce projet **ne contient aucun poids de modèle IA**. Les modèles sont téléchargés directement depuis le dépôt officiel de Real-ESRGAN au moment de l'installation.

---

## 📄 Licence

Le code de ce projet (script d'automatisation et interface web) est sous **licence MIT** — voir [LICENSE](LICENSE) pour les détails.

Les modèles IA Real-ESRGAN sont soumis à leurs propres licences. Consultez le [dépôt officiel Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) pour les conditions d'utilisation commerciale.

---

## 🌟 Si ce projet vous a aidé, laissez une étoile !
