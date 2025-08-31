# ---- Base Stage ----
# Usamos uma imagem base slim do Python para manter o tamanho final menor.
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema que podem ser necessárias para bibliotecas de áudio.
# libsndfile1 é usada por bibliotecas como a SciPy para processar arquivos de áudio.
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 && rm -rf /var/lib/apt/lists/*

# ---- Dependencies Stage ----
# Copia o arquivo de dependências primeiro.
# Esta camada do Docker só será reconstruída se o arquivo requirements.txt mudar.
COPY requirements.txt .

# Instala as dependências do Python.
# --no-cache-dir: Não armazena o cache do pip, mantendo a imagem menor.
# --prefer-binary: Prefere pacotes binários a compilar do código-fonte, acelerando a instalação.
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# ---- Application Stage ----
# Agora copia o código da aplicação.
# Esta camada será reconstruída se os arquivos .py mudarem.
COPY main.py .

# Expõe a porta em que a aplicação irá rodar.
EXPOSE 8000

# ---- Run Stage ----
# O comando para iniciar a aplicação quando o container for executado.
# Usamos --host 0.0.0.0 para tornar a API acessível de fora do container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
