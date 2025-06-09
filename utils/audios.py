import os
from gtts import gTTS

# Tenta importar ElevenLabs
try:
    from elevenlabs import generate, save, set_api_key
    from dotenv import load_dotenv
    load_dotenv()
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
    ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")
    if ELEVEN_API_KEY and ELEVEN_VOICE_ID:
        set_api_key(ELEVEN_API_KEY)
        USE_ELEVEN = True
    else:
        USE_ELEVEN = False
except Exception:
    USE_ELEVEN = False


def gerar_audio(texto, arquivo="saida.mp3"):
    """
    Gera áudio a partir do texto usando ElevenLabs se disponível,
    senão usa gTTS.
    """
    if USE_ELEVEN:
        try:
            print("🎙️ Usando ElevenLabs")
            audio = generate(
                text=texto,
                voice=ELEVEN_VOICE_ID,
                model="eleven_multilingual_v2"
            )
            save(audio, arquivo)
            return
        except Exception as e:
            print(f"❌ Erro na ElevenLabs: {e}")
            print("➡️ Usando fallback para gTTS")

    # gTTS (fallback)
    print("🎙️ Usando gTTS")
    tts = gTTS(text=texto, lang="pt")
    tts.save(arquivo)