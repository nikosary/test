import os
from gtts import gTTS

def generate_voice(theses_list, output_audio="audio.mp3"):
    """Создает аудиофайл MP3 на основе списка тезисов."""
    try:
        full_text = " ".join(theses_list)
        print(f"[ГОЛОС] 🎙️ Синтезирую русскую речь для: {full_text[:30]}...")
        
        # Генерируем чистый голос через gTTS
        tts = gTTS(text=full_text, lang='ru')
        tts.save(output_audio)
        print(f"[ГОЛОС] ✅ Файл {output_audio} успешно записан")
        return True
    except Exception as e:
        print(f"[ГОЛОС] ❌ Ошибка голосового движка: {e}")
        return False
