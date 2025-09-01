from flask import Flask, request, jsonify, send_file
import torch
import io
import tempfile
import os
import logging
import base64
from TTS.api import TTS
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class TTSService:
    def __init__(self):
        self.tts_model = None
        self.device = None
        self.load_model()
    
    def load_model(self):
        """Carrega um modelo TTS funcional em português"""
        try:
            logger.info("Carregando modelo TTS em português brasileiro...")
            
            # Define dispositivo
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Usando device: {self.device}")
            
            # Lista modelos disponíveis em português
            try:
                # Tenta carregar modelo Coqui TTS em português
                self.tts_model = TTS(model_name="tts_models/pt/cv/vits", progress_bar=False)
                logger.info("✅ Modelo Coqui TTS (pt/cv/vits) carregado com sucesso!")
                
            except Exception as e1:
                logger.warning(f"Modelo Coqui não disponível: {e1}")
                try:
                    # Fallback para modelo multilingual
                    self.tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", progress_bar=False)
                    logger.info("✅ Modelo multilingual YourTTS carregado com sucesso!")
                    
                except Exception as e2:
                    logger.warning(f"Modelo multilingual não disponível: {e2}")
                    # Último fallback - Google TTS
                    from gtts import gTTS
                    self.tts_model = "gtts"
                    logger.info("✅ Usando Google TTS como fallback")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar qualquer modelo: {str(e)}")
            self.tts_model = None
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Converte texto em fala e retorna bytes do áudio em MP3
        """
        if not self.tts_model:
            raise Exception("Nenhum modelo TTS está carregado")
        
        try:
            logger.info(f"Gerando áudio para texto: '{text[:50]}...'")
            
            # Se estiver usando Google TTS como fallback
            if self.tts_model == "gtts":
                from gtts import gTTS
                tts = gTTS(text=text, lang='pt-br', slow=False)
                mp3_buffer = io.BytesIO()
                tts.write_to_fp(mp3_buffer)
                mp3_buffer.seek(0)
                logger.info("✅ Áudio gerado com Google TTS!")
                return mp3_buffer.getvalue()
            
            # Se estiver usando modelo Coqui TTS
            else:
                # Gera arquivo WAV temporário
                temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_wav.close()
                
                # Gera o áudio
                self.tts_model.tts_to_file(text=text, file_path=temp_wav.name)
                
                # Converte WAV para MP3
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(temp_wav.name)
                mp3_buffer = io.BytesIO()
                audio.export(mp3_buffer, format="mp3", bitrate="128k")
                mp3_buffer.seek(0)
                
                # Remove arquivo temporário
                os.unlink(temp_wav.name)
                
                logger.info("✅ Áudio gerado com Coqui TTS!")
                return mp3_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio: {str(e)}")
            raise

# Inicializa o serviço TTS
tts_service = TTSService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    if tts_service.tts_model is None:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Nenhum modelo TTS carregado'
        }), 503
    
    model_info = "Coqui TTS" if tts_service.tts_model != "gtts" else "Google TTS"
    
    return jsonify({
        'status': 'healthy',
        'message': 'API TTS funcionando',
        'model': model_info,
        'device': tts_service.device,
        'language': 'pt-br'
    })

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """
    Endpoint principal para conversão de texto em fala
    """
    try:
        # Verifica se o modelo está carregado
        if tts_service.tts_model is None:
            return jsonify({
                'error': 'Nenhum modelo TTS está carregado'
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
        # Verifica se o modelo está carregado
        if tts_service.tts_model is None:
            return jsonify({
                'error': 'Nenhum modelo TTS está carregado'
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
        
        # Gera o áudio
        audio_bytes = tts_service.text_to_speech(text)
        
        # Converte para base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        model_info = "Coqui TTS" if tts_service.tts_model != "gtts" else "Google TTS"
        
        return jsonify({
            'audio_base64': f'data:audio/mpeg;base64,{audio_base64}',
            'format': 'mp3',
            'text': text,
            'model': model_info,
            'language': 'pt-br'
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /tts/stream: {str(e)}")
        return jsonify({
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/models', methods=['GET'])
def list_models():
    """Lista modelos TTS disponíveis"""
    try:
        available_models = []
        
        # Verifica modelos Coqui TTS
        try:
            from TTS.api import TTS
            coqui_models = TTS.list_models()
            pt_models = [m for m in coqui_models if 'pt' in m or 'portuguese' in m.lower()]
            available_models.extend(pt_models)
        except:
            pass
        
        # Sempre tem Google TTS disponível
        available_models.append("Google TTS (gtts)")
        
        return jsonify({
            'available_models': available_models,
            'current_model': "Coqui TTS" if tts_service.tts_model != "gtts" else "Google TTS",
            'status': 'healthy' if tts_service.tts_model else 'no_model_loaded'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Erro ao listar modelos: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint não encontrado',
        'available_endpoints': [
            'GET /health - Verificar status da API',
            'GET /models - Listar modelos disponíveis',
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