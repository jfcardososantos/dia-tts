from flask import Flask, request, jsonify, send_file
import torch
import io
import tempfile
import os
import logging
import base64
from gtts import gTTS
import scipy.io.wavfile

# Importa as classes corretas para o modelo VITS
from transformers import VitsTokenizer, VitsModel

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class DiaPortugueseTTSService:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = None
        self.available = False
        self.load_model()
    
    def load_model(self):
        """Carrega o modelo VITS TTS em português"""
        try:
            MODEL_ID = "Alissonerdx/Dia1.6-pt_BR-v1"
            logger.info(f"🚀 Carregando modelo {MODEL_ID}...")
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"📱 Usando device: {self.device}")
            
            # Carrega o tokenizer e o modelo VITS diretamente (a forma correta)
            logger.info("📥 Carregando tokenizer VITS...")
            self.tokenizer = VitsTokenizer.from_pretrained(MODEL_ID)
            
            logger.info("🧠 Carregando modelo VITS...")
            self.model = VitsModel.from_pretrained(MODEL_ID)
            self.model = self.model.to(self.device)
            
            self.model.eval()
            
            self.available = True
            logger.info("✅ Modelo VITS TTS português carregado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo VITS: {str(e)}")
            self.available = False
            
            # Fallback para Google TTS
            try:
                self.model = "gtts_fallback"
                self.available = True
                logger.warning("⚠️ Usando Google TTS como fallback")
            except Exception as fallback_error:
                logger.error(f"❌ Fallback também falhou: {fallback_error}")
    
    def text_to_speech(self, text: str) -> bytes:
        """
        Converte texto em fala usando o modelo VITS ou Google TTS
        """
        if not self.available:
            raise Exception("Serviço TTS não disponível")
        
        try:
            logger.info(f"🎵 Gerando áudio para: '{text[:50]}...'")
            
            if self.model == "gtts_fallback":
                tts = gTTS(text=text, lang='pt-br', slow=False)
                mp3_buffer = io.BytesIO()
                tts.write_to_fp(mp3_buffer)
                mp3_buffer.seek(0)
                logger.info("✅ Áudio gerado com Google TTS!")
                return mp3_buffer.getvalue(), 'audio/mpeg'
            
            # Lógica de inferência correta para VITS
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                output = self.model(**inputs).waveform

            audio_array = output.cpu().squeeze().numpy()
            sampling_rate = self.model.config.sampling_rate
            
            # Salva o áudio em um buffer de bytes no formato WAV
            wav_buffer = io.BytesIO()
            scipy.io.wavfile.write(wav_buffer, rate=sampling_rate, data=audio_array)
            wav_buffer.seek(0)
            
            logger.info("✅ Áudio gerado com modelo VITS português!")
            return wav_buffer.getvalue(), 'audio/wav'
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio: {str(e)}")
            raise

# Inicializa o serviço TTS
tts_service = DiaPortugueseTTSService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    model_name = "VITS (Alissonerdx/Dia1.6-pt_BR-v1)" if tts_service.model != "gtts_fallback" else "Google TTS (Fallback)"
    return jsonify({
        'status': 'healthy' if tts_service.available else 'unhealthy',
        'model': model_name,
        'device': tts_service.device if hasattr(tts_service, 'device') else 'cpu',
        'available': tts_service.available
    })

@app.route('/tts', methods=['POST'])
def text_to_speech_endpoint():
    """Endpoint principal para conversão de texto em fala"""
    temp_file_path = None
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Campo "text" é obrigatório'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Texto não pode estar vazio'}), 400
        
        if len(text) > 1000:
            return jsonify({'error': 'Texto muito longo (máximo 1000 caracteres)'}), 400
        
        audio_bytes, mimetype = tts_service.text_to_speech(text)
        
        suffix = '.wav' if mimetype == 'audio/wav' else '.mp3'
        download_name = 'tts_output' + suffix
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        return send_file(
            temp_file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        logger.error(f"Erro no endpoint /tts: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.route('/tts/stream', methods=['POST'])
def text_to_speech_json():
    """Endpoint que retorna o áudio como base64 em JSON"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Campo "text" é obrigatório'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Texto não pode estar vazio'}), 400
        
        if len(text) > 1000:
            return jsonify({'error': 'Texto muito longo (máximo 1000 caracteres)'}), 400
        
        audio_bytes, mimetype = tts_service.text_to_speech(text)
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        model_name = "VITS (Alissonerdx/Dia1.6-pt_BR-v1)" if tts_service.model != "gtts_fallback" else "Google TTS (Fallback)"
        
        return jsonify({
            'audio_base64': f'data:{mimetype};base64,{audio_base64}',
            'format': mimetype.split("/")[1],
            'text': text,
            'model': model_name
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint /tts/stream: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint não encontrado',
        'available_endpoints': [
            'GET /health',
            'POST /tts',
            'POST /tts/stream'
        ]
    }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
