#!/bin/bash

echo "🚀 Instalando TTS API com modelo Dia português..."

# Instala a versão dev do transformers (necessária para Dia)
echo "📦 Instalando transformers dev..."
pip install git+https://github.com/huggingface/transformers.git

# Instala outras dependências
echo "📦 Instalando outras dependências..."
pip install -r requirements.txt

echo "✅ Instalação concluída!"
echo ""
echo "🧪 Para testar:"
echo "  python app.py"
echo ""
echo "🐳 Ou com Docker:"
echo "  docker-compose up --build"