#!/bin/bash
# -----------------------------------------------------------------------------
# Video AI Enhancer — Script d'installation et de lancement automatique
# -----------------------------------------------------------------------------

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}🎬  Initialisation de Video AI Enhancer${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Vérification / Installation de FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️ FFmpeg est manquant. Tentative d'installation...${NC}"
    
    # Détection de la distribution Linux
    if [ -f /etc/fedora-release ]; then
        echo -e "${BLUE}OS détecté : Fedora. Installation via DNF...${NC}"
        sudo dnf install -y ffmpeg ffmpeg-libs
    elif [ -f /etc/debian_version ]; then
        echo -e "${BLUE}OS détecté : Debian/Ubuntu. Installation via APT...${NC}"
        sudo apt update && sudo apt install -y ffmpeg
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${BLUE}OS détecté : macOS. Installation via Homebrew...${NC}"
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo -e "${RED}❌ Homebrew n'est pas installé. Veuillez installer FFmpeg manuellement.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Système d'exploitation non reconnu automatiquement.${NC}"
        echo -e "Veuillez installer FFmpeg manuellement pour votre système."
        exit 1
    fi
else
    echo -e "${GREEN}✅ FFmpeg est déjà installé.${NC}"
fi

# 2. Téléchargement de Real-ESRGAN Vulkan Portable
mkdir -p bin
cd bin

if [ ! -f "realesrgan-ncnn-vulkan" ]; then
    echo -e "${YELLOW}⚙️ Récupération du binaire Real-ESRGAN NCNN Vulkan...${NC}"
    
    # Choix de l'URL selon l'OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        URL="https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases/download/v0.1.0/realesrgan-ncnn-vulkan-20220315-macos.zip"
    else
        URL="https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases/download/v0.1.0/realesrgan-ncnn-vulkan-20220315-ubuntu.zip"
    fi
    
    echo -e "Téléchargement depuis : $URL"
    curl -L -o realesrgan.zip "$URL"
    
    echo -e "Extraction des fichiers..."
    unzip -q realesrgan.zip
    rm realesrgan.zip
    
    # Rendre le binaire exécutable
    chmod +x realesrgan-ncnn-vulkan
    echo -e "${GREEN}✅ Real-ESRGAN configuré avec succès dans le dossier bin/${NC}"
else
    echo -e "${GREEN}✅ Real-ESRGAN est déjà configuré.${NC}"
fi

cd ..

# 3. Création de l'environnement virtuel Python
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Création de l'environnement virtuel Python (.venv)...${NC}"
    python3 -m venv .venv
fi

# Activation de l'environnement virtuel
source .venv/bin/activate

echo -e "Installation des dépendances Python (Flask)..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Lancement de l'application et ouverture du navigateur
echo -e "${GREEN}🚀 Lancement du serveur Web local (port 5000)...${NC}"

# Lancer l'ouverture du navigateur en arrière-plan après 2 secondes
(
    sleep 2
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:5000"
    elif command -v open &> /dev/null; then
        open "http://localhost:5000"
    else
        echo -e "${YELLOW}👉 Veuillez ouvrir manuellement : http://localhost:5000 dans votre navigateur.${NC}"
    fi
) &

# Lancement du serveur Flask
python3 app.py
