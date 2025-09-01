from flask import Flask, request, jsonify, send_file
import io
import tempfile
import os
import logging
import base64
from gtts import gTTS

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TTSService:
    def __init__(self):
        self.available = True
        logger.info("✅ Serviço TTS com Google TTS inicializado")
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Converte texto em fala usando Google TTS
        """
        try:
            logger.info(f"Gerando áudio para texto: '{text[:50]}...'")
            
            # Usa Google TTS em português brasileiro
            tts = gTTS(text=text, lang='pt-br', slow=False)
            
            # Salva em buffer de memória
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            
            logger.info("✅ Áudio gerado com sucesso!")
            return mp3_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio: {str(e)}")
            raise

# Inicializa o serviço TTS
tts_service = TTSService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return jsonify({
        'status': 'healthy',
        'message': 'API TTS funcionando',
        'model': 'Google TTS',
        'language': 'pt-br',
        'available': tts_service.available
    })

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Endpoint principal para conversão de texto em fala
    """
    try:
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
        
        # Limita o tamanho do texto
        if len(text) > 1000:
            return jsonify({
                'error': 'Texto muito longo (máximo 1000 caracteres)'
            }), 400
        
        # Gera o áudio
        audio_bytes = tts_service.text_to_speech(text)
        
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
    Endpoint que retorna o áudio como base64 em JSON
    """
    try:
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
        
        # Gera o áudio
        audio_bytes = tts_service.text_to_speech(text)
        
        # Converte para base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            'audio_base64': f'data:audio/mpeg;base64,{audio_base64}',
            'format': 'mp3',
            'text': text,
            'model': 'Google TTS',
            'language': 'pt-br'
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
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Converte texto em fala usando Google TTS
        """
        try:
            logger.info(f"Gerando áudio para texto: '{text[:50]}...'")
            
            # Usa Google TTS em português brasileiro
            tts = gTTS(text=text, lang='pt-br', slow=False)
            
            # Salva em buffer de memória
            mp3_buffer = io.BytesIO()
            tts.write_to_fp(mp3_buffer)
            mp3_buffer.seek(0)
            
            logger.info("✅ Áudio gerado com sucesso!")
            return mp3_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio: {str(e)}")
            raise

# Inicializa o serviço TTS
tts_service = TTSService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return jsonify({
        'status': 'healthy',
        'message': 'API TTS funcionando',
        'model': 'Google TTS',
        'language': 'pt-br',
        'available': tts_service.available
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
        # Verifica se o serviço está disponível
        if not tts_service.available:
            return jsonify({
                'error': 'Serviço TTS não disponível'
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
        
        sample_rate = data.get('sample_rate', 16000)
        
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
        # Verifica se o serviço está disponível
        if not tts_service.available:
            return jsonify({
                'error': 'Serviço TTS não disponível'
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
        
        sample_rate = data.get('sample_rate', 16000)
        
        # Gera o áudio
        audio_bytes = tts_service.text_to_speech(text, sample_rate)
        
        # Converte para base64
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            'audio_base64': f'data:audio/mpeg;base64,{audio_base64}',
            'format': 'mp3',
            'text': text,
            'model': 'Google TTS',
            'language': 'pt-br'
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