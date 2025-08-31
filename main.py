
import io
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch
from transformers import pipeline
import scipy.io.wavfile

# --- 1. Carregamento do Modelo ---
# Carregamos o pipeline de text-to-speech do Hugging Face.
# Isso é feito globalmente para que o modelo seja carregado apenas uma vez
# quando a aplicação iniciar, e não a cada requisição.
print("Carregando o modelo TTS...")
# O argumento `trust_remote_code=True` é necessário para que modelos da comunidade
# que definem sua própria arquitetura em código possam ser carregados.
synthesizer = pipeline("text-to-speech", "Alissonerdx/Dia1.6-pt_BR-v1", trust_remote_code=True)
print("Modelo carregado com sucesso!")


# --- 2. Definição do App FastAPI ---
app = FastAPI(
    title="API de Geração de Voz",
    description="Uma API para gerar áudio a partir de texto usando o modelo Alissonerdx/Dia1.6-pt_BR-v1.",
    version="1.0.0",
)

# --- 3. Modelo de Requisição (Pydantic) ---
# Define a estrutura do corpo da requisição JSON que esperamos.
# Ex: {"text": "seu texto aqui"}
class TextToSpeechRequest(BaseModel):
    text: str


# --- 4. Endpoint da API ---
@app.post("/generate-audio/",
          tags=["Geração de Áudio"],
          summary="Gera um arquivo de áudio a partir de um texto.",
          response_description="O arquivo de áudio no formato WAV.")
async def generate_audio(request: TextToSpeechRequest):
    """
    Recebe um texto e retorna o áudio correspondente em formato WAV.

    - **text**: O texto que você deseja converter em voz.
    """
    # Gera a forma de onda (waveform) a partir do texto usando o modelo
    speech = synthesizer(request.text)

    # O pipeline retorna um dicionário. O áudio está na chave 'audio' (como um array NumPy)
    # e a taxa de amostragem em 'sampling_rate'.
    audio_array = speech["audio"]
    sampling_rate = speech["sampling_rate"]

    # --- 5. Conversão para o formato WAV em memória ---
    # Criamos um buffer de bytes em memória para não precisar salvar o arquivo em disco.
    buffer = io.BytesIO()
    # Usamos a biblioteca SciPy para escrever o array NumPy no buffer como um arquivo WAV.
    scipy.io.wavfile.write(buffer, rate=sampling_rate, data=audio_array)
    # Reposicionamos o cursor do buffer para o início.
    buffer.seek(0)

    # --- 6. Retorno da Resposta ---
    # Retornamos uma StreamingResponse, que é eficiente para enviar arquivos.
    # O media_type "audio/wav" informa ao navegador ou cliente como tratar o arquivo.
    return StreamingResponse(buffer, media_type="audio/wav")

