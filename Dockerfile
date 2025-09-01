FROM python:3.10-slim

# Instalar dependências do sistema incluindo git
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .

# Instalar dependências em etapas para melhor cache
RUN pip install --no-cache-dir --upgrade pip

# Instalar transformers do GitHub (versão dev necessária para Dia)
RUN pip install --no-cache-dir git+https://github.com/huggingface/transformers.git

# Instalar outras dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .

# Expor porta
EXPOSE 5000

# Comando para executar a aplicação
CMD ["python", "app.py"]