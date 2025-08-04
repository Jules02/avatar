#!/bin/bash

echo "🚀 Démarrage de l'interface MCP Client avec Streamlit..."
echo "📦 Installation des dépendances..."

# Installer les dépendances
pip3 install -r requirements.txt

echo "✅ Dépendances installées!"
echo "🌐 Lancement de l'interface web..."
echo "📍 L'interface sera disponible à l'adresse: http://localhost:8501"
echo ""
echo "Pour arrêter l'application, appuyez sur Ctrl+C"
echo ""

# Lancer Streamlit
streamlit run streamlit_interface.py --server.port 8501 --server.address 0.0.0.0

