# API de Geração de Voz com Dia1.6-pt_BR

Esta é uma API simples criada com FastAPI para gerar áudio a partir de texto usando o modelo de Text-to-Speech (TTS) `Alissonerdx/Dia1.6-pt_BR-v1`.

O projeto inclui um `Dockerfile` para facilitar a execução em um ambiente containerizado.

## Como Executar com Docker (Recomendado)

Com o Docker instalado, siga os passos abaixo.

### 1. Construa a Imagem Docker

No terminal, na raiz do projeto, execute o comando abaixo. Isso irá criar uma imagem chamada `tts-api`.

```bash
docker build -t tts-api .
```

*Nota: O primeiro build pode demorar bastante, pois o Docker precisa baixar a imagem base do Python, instalar as dependências e o `transformers` irá baixar o modelo de TTS. Graças ao cache do Docker, os builds seguintes serão muito mais rápidos.*

### 2. Execute o Container

Após o build ser concluído, inicie um container a partir da imagem criada:

```bash
docker run -d -p 8000:8000 --name tts-container tts-api
```
- `-d`: Executa o container em modo "detached" (em segundo plano).
- `-p 8000:8000`: Mapeia a porta 8000 do seu computador para a porta 8000 do container.
- `--name tts-container`: Dá um nome fácil de lembrar ao seu container.

Sua API agora está rodando dentro do container!

### 3. Teste a API

Você pode testar usando `curl` da mesma forma que antes:

```bash
curl -X POST "http://127.0.0.1:8000/generate-audio/" \
     -H "Content-Type: application/json" \
     -d '{"text": "Olá mundo, rodando dentro de um container Docker."}' \
     --output output_docker.wav
```

Ou acesse a documentação interativa no seu navegador: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Parando o Container

Para parar o container, use o comando:
```bash
docker stop tts-container
```

---

## Como Executar Localmente (Sem Docker)

### 1. Instalação

Primeiro, certifique-se de que você tem o Python 3.8+ instalado. Depois, instale as dependências:

```bash
pip install -r requirements.txt
```

### 2. Executando a API

Para iniciar o servidor da API, execute:

```bash
uvicorn main:app --reload
```

A API estará disponível em [http://127.0.0.1:8000](http://127.0.0.1:8000).

```