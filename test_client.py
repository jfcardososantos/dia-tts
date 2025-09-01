import requests
import json
import base64

# Configuração da API
API_URL = "http://localhost:5000"

def test_health():
    """Testa se a API está funcionando"""
    print("🔍 Testando saúde da API...")
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    print("-" * 50)

def test_tts_file(text: str):
    """Testa o endpoint /tts que retorna arquivo MP3"""
    print(f"🎵 Testando TTS (arquivo) com texto: '{text}'")
    
    payload = {
        "text": text,
        "sample_rate": 22050
    }
    
    response = requests.post(
        f"{API_URL}/tts", 
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        # Salva o arquivo MP3
        filename = f"output_{hash(text) % 10000}.mp3"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Áudio salvo como: {filename}")
        print(f"Tamanho do arquivo: {len(response.content)} bytes")
    else:
        print(f"❌ Erro: {response.status_code}")
        try:
            print(f"Resposta: {response.json()}")
        except:
            print(f"Resposta raw: {response.text}")
    
    print("-" * 50)

def test_tts_json(text: str):
    """Testa o endpoint /tts/stream que retorna JSON com base64"""
    print(f"🎵 Testando TTS (JSON/base64) com texto: '{text}'")
    
    payload = {
        "text": text,
        "sample_rate": 22050
    }
    
    response = requests.post(
        f"{API_URL}/tts/stream", 
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Resposta recebida!")
        print(f"Formato: {data.get('format')}")
        print(f"Sample rate: {data.get('sample_rate')}")
        print(f"Tamanho do base64: {len(data.get('audio_base64', ''))} chars")
        
        # Opcionalmente, decodifica e salva o arquivo
        audio_base64 = data.get('audio_base64', '')
        if audio_base64.startswith('data:audio/mpeg;base64,'):
            audio_data = base64.b64decode(audio_base64.split(',')[1])
            filename = f"output_base64_{hash(text) % 10000}.mp3"
            with open(filename, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Arquivo decodificado salvo como: {filename}")
    else:
        print(f"❌ Erro: {response.status_code}")
        try:
            print(f"Resposta: {response.json()}")
        except:
            print(f"Resposta raw: {response.text}")
    
    print("-" * 50)

def main():
    print("🚀 Testando API TTS com modelo Alissonerdx/Dia1.6-pt_BR-v1")
    print("=" * 60)
    
    # Testa saúde da API
    test_health()
    
    # Textos para teste
    textos_teste = [
        "Olá, mundo! Esta é uma API de texto para fala em português brasileiro.",
        "O gato subiu no telhado para ver a lua brilhante.",
        "Inteligência artificial está revolucionando o mundo da tecnologia."
    ]
    
    for texto in textos_teste:
        # Testa ambos os endpoints
        test_tts_file(texto)
        test_tts_json(texto)
    
    print("🎉 Testes concluídos!")
    print("\n📁 Arquivos gerados:")
    print("- output_*.mp3 (do endpoint /tts)")
    print("- output_base64_*.mp3 (do endpoint /tts/stream)")

if __name__ == "__main__":
    main()