# 🎤 TTS API Brazil

Uma API moderna de Text-to-Speech (TTS) em português brasileiro usando o modelo [Alissonerdx/Dia1.6-pt_BR-v1](https://huggingface.co/Alissonerdx/Dia1.6-pt_BR-v1) do Hugging Face.

## ✨ Características

- 🇧🇷 **Português Brasileiro** - Otimizado para PT-BR
- 🎵 **Saída MP3** - Áudio de alta qualidade em formato MP3
- ⚡ **API RESTful** - Endpoints simples e intuitivos
- 🐳 **Docker Ready** - Containerizado para deploy fácil
- 🔧 **Configurável** - Suporte a diferentes sample rates
- 📊 **Monitoramento** - Logs estruturados e health check
- 🚀 **GPU Support** - Aceleração com CUDA quando disponível

## 🚀 Quick Start

### Usando Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/tts-api-brazil.git
cd tts-api-brazil

# Execute com Docker Compose
docker-compose up --build
```

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/tts-api-brazil.git
cd tts-api-brazil

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python -m app.main
```

## 📋 API Endpoints

### Health Check
```http
GET /health
```

**Resposta:**
```json
{
  "status": "healthy",
  "message": "API TTS funcionando",
  "model": "Alissonerdx/Dia1.6-pt_BR-v1"
}
```

### Text-to-Speech (Arquivo MP3)
```http
POST /tts
Content-Type: application/json

{
  "text": "Olá, mundo! Esta é uma demonstração de TTS.",
  "sample_rate": 22050
}
```

**Resposta:** Arquivo MP3 para download

### Text-to-Speech (Base64 JSON)
```http
POST /tts/stream
Content-Type: application/json

{
  "text": "Texto para converter em fala",
  "sample_rate": 22050
}
```

**Resposta:**
```json
{
  "audio_base64": "data:audio/mpeg;base64,UklGRn...",
  "format": "mp3",
  "sample_rate": 22050,
  "text": "Texto para converter em fala"
}
```

## 🛠️ Exemplos de Uso

### cURL
```bash
# Download direto do MP3
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Olá, esta é uma demonstração!"}' \
  --output audio.mp3

# Resposta em JSON
curl -X POST http://localhost:5000/tts/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "Texto de exemplo"}'
```

### Python
```python
import requests

# Fazendo requisição
response = requests.post('http://localhost:5000/tts', 
    json={"text": "Olá, mundo!"})

# Salvando arquivo MP3
with open('output.mp3', 'wb') as f:
    f.write(response.content)
```

### JavaScript
```javascript
// Usando fetch API
const response = await fetch('http://localhost:5000/tts/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: 'Olá, JavaScript!'})
});

const data = await response.json();
console.log('Áudio Base64:', data.audio_base64);
```

## ⚙️ Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```env
# Configurações da aplicação
FLASK_ENV=production
LOG_LEVEL=INFO

# Configurações do modelo
MODEL_NAME=Alissonerdx/Dia1.6-pt_BR-v1
DEFAULT_SAMPLE_RATE=22050
MAX_TEXT_LENGTH=1000

# Configurações do servidor
HOST=0.0.0.0
PORT=5000
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  tts-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./logs:/app/logs
```

## 🧪 Testes

```bash
# Executar testes unitários
python -m pytest tests/

# Testar API com cliente de exemplo
python scripts/test_client.py

# Benchmark de performance
python scripts/benchmark.py
```

## 📦 Deployment

### Docker Hub
```bash
# Build e push
docker build -t seu-usuario/tts-api-brazil .
docker push seu-usuario/tts-api-brazil
```

### Kubernetes
```yaml
# Exemplo de deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tts-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tts-api
  template:
    metadata:
      labels:
        app: tts-api
    spec:
      containers:
      - name: tts-api
        image: seu-usuario/tts-api-brazil:latest
        ports:
        - containerPort: 5000
```

## 🔧 Desenvolvimento

### Setup do ambiente de desenvolvimento
```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Executar em modo debug
python -m app.main --debug
```

### Estrutura do projeto
```
app/            # Código principal
├── main.py     # Entrada da aplicação
├── config.py   # Configurações
└── services/   # Lógica de negócio

api/            # Endpoints
tests/          # Testes automatizados
docs/           # Documentação
examples/       # Exemplos de uso
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

Veja [CONTRIBUTING.md](docs/CONTRIBUTING.md) para mais detalhes.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [Alissonerdx](https://huggingface.co/Alissonerdx) pelo modelo TTS
- [Hugging Face](https://huggingface.co/) pela plataforma
- Comunidade open source

## 📞 Suporte

- 📧 Email: seu-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/tts-api-brazil/issues)
- 💬 Discussões: [GitHub Discussions](https://github.com/seu-usuario/tts-api-brazil/discussions)

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!** ⭐