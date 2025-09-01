from flask import Flask, request, jsonify, send_file
import torch
import io
import tempfile
import os
import logging
import base64
from transformers import AutoProcessor, DiaForConditionalGeneration

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class DiaPortugueseTTSService:
    def __init__(self):
        self.processor = None
        self.model = None
        self.device = None
        self.available = False
        self.load_model()
    
    def load_model(self):
        """Carrega o modelo Dia TTS em português"""
        try:
            logger.info("🚀 Carregando modelo Alissonerdx/Dia1.6-pt_BR-v1...")
            
            # Define dispositivo
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"📱 Usando device: {self.device}")
            
            # Carrega o processador
            logger.info("📥 Carregando processador...")
            self.processor = AutoProcessor.from_pretrained("Alissonerdx/Dia1.6-pt_BR-v1")
            
            # Carrega o modelo
            logger.info("🧠 Carregando modelo...")
            self.model = DiaForConditionalGeneration.from_pretrained("Alissonerdx/Dia1.6-pt_BR-v1")
            self.model = self.model.to(self.device)
            
            # Configura para modo de inferência
            self.model.eval()
            
            self.available = True
            logger.info("✅ Modelo Dia TTS português carregado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo Dia: {str(e)}")
            logger.error(f"🔍 Tipo do erro: {type(e).__name__}")
            self.available = False
            
            # Fallback para Google TTS
            try:
                from gtts import gTTS
                self.model = "gtts_fallback"
                self.available = True
                logger.warning("⚠️ Usando Google TTS como fallback")
            except:
                logger.error("❌ Fallback também falhou")
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Converte texto em fala usando o modelo Dia português
        """
        if not self.available:
            raise Exception("Serviço TTS não disponível")
        
        try:
            logger.info(f"🎵 Gerando áudio para: '{text[:50]}...'")
            
            # Se estiver usando fallback Google TTS
            if self.model == "gtts_fallback":
                from gtts import gTTS
                tts = gTTS(text=text, lang='pt-br', slow=False)
                mp3_buffer = io.BytesIO()
                tts.write_to_fp(mp3_buffer)
                mp3_buffer.seek(0)
                logger.info("✅ Áudio gerado com Google TTS!")
                return mp3_buffer.getvalue()
            
            # Usando modelo Dia português
            # Formato correto: precisa do token de speaker [S1]
            formatted_text = f"[S1] {text}"
            
            # Processa o texto
            inputs = self.processor(
                text=[formatted_text], 
                padding=True, 
                return_tensors="pt"
            ).to(self.device)
            
            # Gera o áudio
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=3072,
                    guidance_scale=3.0,
                    temperature=1.8,
                    top_p=0.90,
                    top_k=45,
                    do_sample=True
                )
            
            # Decodifica o áudio
            audio_outputs = self.processor.batch_decode(outputs)
            
            # Salva como arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            
            # Usa o método save_audio do processador
            self.processor.save_audio(audio_outputs, temp_file.name)
            
            # Lê o arquivo gerado
            with open(temp_file.name, 'rb') as f:
                audio_bytes = f.read()
            
            # Remove arquivo temporário
            os.unlink(temp_file.name)
            
            logger.info("✅ Áudio gerado com modelo Dia português!")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio: {str(e)}")
            logger.error(f"🔍 Detalhes: {type(e).__name__}")
            raise

# Inicializa o serviço TTS
tts_service = DiaPortugueseTTSService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    model_name = "Dia TTS Português" if tts_service.model != "gtts_fallback" else "Google TTS (Fallback)"
    
    return jsonify({
        'status': 'healthy' if tts_service.available else 'unhealthy',
        'message': 'API TTS funcionando',
        'model': model_name,
        'language': 'pt-br',
        'device': tts_service.device,
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
        
        model_name = "Dia TTS Português" if tts_service.model != "gtts_fallback" else "Google TTS (Fallback)"
        
        return jsonify({
            'audio_base64': f'data:audio/mpeg;base64,{audio_base64}',
            'format': 'mp3',
            'text': text,
            'model': model_name,
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