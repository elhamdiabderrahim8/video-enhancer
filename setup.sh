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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
mkdir -p "$BIN_DIR"

if [ ! -f "$BIN_DIR/realesrgan-ncnn-vulkan" ]; then
    echo -e "${YELLOW}⚙️ Récupération du binaire Real-ESRGAN NCNN Vulkan...${NC}"
    
    # Choix de l'URL selon l'OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        URL="https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases/download/v0.2.0/realesrgan-ncnn-vulkan-v0.2.0-macos.zip"
        SUBFOLDER="realesrgan-ncnn-vulkan-v0.2.0-macos"
    else
        URL="https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases/download/v0.2.0/realesrgan-ncnn-vulkan-v0.2.0-ubuntu.zip"
        SUBFOLDER="realesrgan-ncnn-vulkan-v0.2.0-ubuntu"
    fi
    
    echo -e "Téléchargement depuis : $URL"
    curl -L -o "$BIN_DIR/realesrgan.zip" "$URL"
    
    echo -e "Extraction des fichiers..."
    unzip -q "$BIN_DIR/realesrgan.zip" -d "$BIN_DIR"
    rm "$BIN_DIR/realesrgan.zip"
    
    # Move binary from subfolder to bin/ root
    mv "$BIN_DIR/$SUBFOLDER/realesrgan-ncnn-vulkan" "$BIN_DIR/realesrgan-ncnn-vulkan"
    rm -rf "$BIN_DIR/$SUBFOLDER"
    
    chmod +x "$BIN_DIR/realesrgan-ncnn-vulkan"
    echo -e "${GREEN}✅ Binaire Real-ESRGAN installé dans bin/${NC}"
else
    echo -e "${GREEN}✅ Binaire Real-ESRGAN déjà présent.${NC}"
fi

# 2b. Récupération des fichiers de modèles IA
mkdir -p "$BIN_DIR/models"

# Check if models are already present
if [ ! -f "$BIN_DIR/models/realesrgan-x4plus.bin" ]; then
    echo -e "${YELLOW}🧠 Téléchargement des modèles IA (Real-ESRGAN)...${NC}"
    
    # List of models needed
    MODEL_NAMES=(
        "realesrgan-x4plus.bin"
        "realesrgan-x4plus.param"
        "realesr-animevideov3-x4.bin"
        "realesr-animevideov3-x4.param"
    )
    
    MODEL_BASE_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0"
    
    for MODEL in "${MODEL_NAMES[@]}"; do
        if [ ! -f "$BIN_DIR/models/$MODEL" ]; then
            echo -e "  → Téléchargement : $MODEL"
            curl -L -o "$BIN_DIR/models/$MODEL" "$MODEL_BASE_URL/$MODEL"
        fi
    done
    
    echo -e "${GREEN}✅ Modèles IA installés dans bin/models/${NC}"
else
    echo -e "${GREEN}✅ Modèles IA déjà présents.${NC}"
fi


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
