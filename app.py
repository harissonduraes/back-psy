from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import openai
from elevenlabs.client import ElevenLabs
from io import BytesIO
import tempfile
import base64
import os

app = Flask(__name__)
CORS(app)

client = openai.OpenAI(
    api_key="3uYH4b-u9f5UqafLGpqrCG_VLjhPwyixTdmhAtYmXrc",
    base_url="https://api.poe.com/v1",
)

elevenlabs_client = ElevenLabs(
  api_key="sk_b5562e737fe0a85859c9f3d574437eb872ac7ef960f3d99d",
)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "Nenhum arquivo de áudio fornecido"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "Nenhum arquivo de áudio selecionado"}), 400

    temp_file_path = None # Inicializa para garantir que esteja definido
    try:
        # Salva o arquivo de áudio temporariamente para processamento
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_audio_file:
            audio_file.save(tmp_audio_file.name)
            temp_file_path = tmp_audio_file.name

        print(f"Arquivo de áudio temporário salvo em: {temp_file_path}")

        # 1. Transcrição de Fala para Texto (STT) com ElevenLabs
        transcription_text = ""
        try:
            with open(temp_file_path, "rb") as file_to_transcribe:
                transcription_response = elevenlabs_client.speech_to_text.convert(
                    file=file_to_transcribe,
                    model_id="scribe_v1",
                    language_code="pt",
                    diarize=False,
                )
            transcription_text = transcription_response.text
            print(f"Transcrição concluída: {transcription_text}")
        except Exception as e:
            print(f"Erro na transcrição: {e}")
            raise Exception(f"Erro na transcrição: {e}") # Propaga o erro para o bloco principal

        # 2. Interação com o Modelo de Linguagem (LLM)
        chat_response = client.chat.completions.create(
            model="Therabot-GPT",
            messages=[{"role": "user", "content": transcription_text}],
        )
        llm_response_content = chat_response.choices[0].message.content
        print(f"Resposta do LLM: {llm_response_content}")

        # 3. Conversão de Texto para Fala (TTS) usando o modelo ElevenLabs-v3 via Poe
        chat_tts_response = client.chat.completions.create(
            model="ElevenLabs-v3",
            messages=[{"role": "user", "content": llm_response_content}],
        )
        audio_url = chat_tts_response.choices[0].message.content
        print(f"URL do áudio gerado: {audio_url}")

        # 4. Baixar o Áudio Gerado e codificar em base64
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()

        audio_buffer = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            audio_buffer.write(chunk)
        audio_buffer.seek(0)

        # Codifica o áudio em Base64
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')
        audio_mimetype = "audio/mpeg" # Assumindo MP3 do ElevenLabs-v3

        # Limpa o arquivo de áudio temporário de entrada
        os.remove(temp_file_path)

        # Retorna um JSON com todos os dados
        return jsonify({
            "transcription": transcription_text,
            "llm_response": llm_response_content,
            "audio_data": f"data:{audio_mimetype};base64,{audio_base64}"
        })

    except Exception as e:
        print(f"Ocorreu um erro inesperado no backend: {e}")
        # Limpa o arquivo temporário se um erro ocorrer após sua criação
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)