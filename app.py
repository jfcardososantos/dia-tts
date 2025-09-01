from flask import Flask, request, jsonify, send_file
from transformers import pipeline
import torch
import io
import numpy as np
from scipy.io.wavfile import write
import tempfile
import os
from pydub import AudioSegment
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TTSService:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Carrega o modelo TTS do Hugging Face"""
        try:
            logger.info("Carregando modelo Alissonerdx/Dia1.6-pt_BR-v1...")
            
            # Verifica se CUDA está disponível
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Usando device: {device}")
            
            # Carrega o pipeline TTS
            self.model = pipeline(
                "text-to-speech",
                model="Alissonerdx/Dia1.6-pt_BR-v1",
                device=0 if device == "cuda" else -1
            )
            
            logger.info("Modelo carregado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            self.model = None
    
    def text_to_speech(self, text: str, sample_rate: int = 22050) -> bytes:
        """
        Converte texto em fala e retorna bytes do áudio em MP3
        
        Args:
            text (str): Texto para converter
            sample_rate (int): Taxa de amostragem do áudio
            
        Returns:
            bytes: Áudio em formato MP3
        """
        if not self.model:
            raise Exception("Modelo não carregado")
        
        try:
            # Gera o áudio usando o modelo
            logger.info(f"Gerando áudio para texto: '{text[:50]}...'")
            result = self.model(text)
            
            # Extrai os dados de áudio
            audio_data = result["audio"]
            
            # Se o áudio está em formato tensor, converte para numpy
            if torch.is_tensor(audio_data):
                audio_data = audio_data.cpu().numpy()
            
            # Normaliza o áudio para o range [-1, 1]
            audio_data = np.array(audio_data)
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normaliza se necessário
            if np.abs(audio_data).max() > 1.0:
                audio_data = audio_data / np.abs(audio_data).max()
            
            # Converte para int16 para compatibilidade com WAV
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Cria arquivo WAV temporário em memória
            wav_buffer = io.BytesIO()
            write(wav_buffer, sample_rate, audio_int16)
            wav_buffer.seek(0)
            
            # Converte WAV para MP3 usando pydub
            audio_segment = AudioSegment.from_wav(wav_buffer)
            mp3_buffer = io.BytesIO()
            audio_segment.export(mp3_buffer, format="mp3", bitrate="128k")
            mp3_buffer.seek(0)
            
            logger.info("Áudio gerado com sucesso!")
            return mp3_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao gerar áudio: {str(e)}")
            raise

# Inicializa o serviço TTS
tts_service = TTSService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    if tts_service.model is None:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Modelo não carregado'
        }), 503
    
    return jsonify({
        'status': 'healthy',
        'message': 'API TTS funcionando',
        'model': 'Alissonerdx/Dia1.6-pt_BR-v1'
    })

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Endpoint principal para conversão de texto em fala
    
    Esperado JSON:
    {
        "text": "Texto para converter em fala",
        "sample_rate": 22050  // opcional, padrão 22050
    }
    
    Retorna: Arquivo MP3 com o áudio gerado
    """
    try:
        # Verifica se o modelo está carregado
        if tts_service.model is None:
            return jsonify({
                'error': 'Modelo não está carregado'
            }), 503
        
        # Obtém dados do request
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Campo "text" é obrigatório'
            }), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({
                'error': 'Texto não pode estar vazio'
            }), 400
        
        # Limita o tamanho do texto (opcional)
        if len(text) > 1000:
            return jsonify({
                'error': 'Texto muito longo (máximo 1000 caracteres)'
            }), 400
        
        sample_rate = data.get('sample_rate', 22050)
        
        # Gera o áudio
        audio_bytes = tts_service.text_to_speech(text, sample_rate)
        
        # Cria arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(audio_bytes)
        temp_file.close()
        
        # Retorna o arquivo MP3
        return send_file(
            temp_file.name,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='tts_output.mp3'
        )
        
    except Exception as e:
        logger.error(f"Erro no endpoint /tts: {str(e)}")
        return jsonify({
            'error': f'Erro interno: {str(e)}'
        }), 500
    
    finally:
        # Remove arquivo temporário se existir
        try:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except:
            pass

@app.route('/tts/stream', methods=['POST'])
def text_to_speech_json():
    """
    Endpoint alternativo que retorna o áudio como base64 em JSON
    
    Esperado JSON:
    {
        "text": "Texto para converter em fala",
        "sample_rate": 22050  // opcional
    }
    
    Retorna JSON:
    {
        "audio_base64": "data:audio/mpeg;base64,UklGRn...",
        "format": "mp3",
        "sample_rate": 22050
    }
    """
    try:
        # Verifica se o modelo está carregado
        if tts_service.model is None:
            return jsonify({
                'error': 'Modelo não está carregado'
            }), 503
        
        # Obtém dados do request
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Campo "text" é obrigatório'
            }), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({
                'error': 'Texto não pode estar vazio'
            }), 400
        
        if len(text) > 1000:
            return jsonify({
                'error': 'Texto muito longo (máximo 1000 caracteres)'
            }), 400
        
        sample_rate = data.get('sample_rate', 22050)
        
        # Gera o áudio
        audio_bytes = tts_service.text_to_speech(text, sample_rate)
        
        # Converte para base64
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            'audio_base64': f'data:audio/mpeg;base64,{audio_base64}',
            'format': 'mp3',
            'sample_rate': sample_rate,
            'text': text
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /tts/stream: {str(e)}")
        return jsonify({
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint não encontrado',
        'available_endpoints': [
            'GET /health - Verificar status da API',
            'POST /tts - Converter texto em áudio (retorna MP3)',
            'POST /tts/stream - Converter texto em áudio (retorna base64)'
        ]
    }), 404

if __name__ == '__main__':
    # Configurações para desenvolvimento
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Desabilita debug em produção
        threaded=True
    )