import os
from gtts import gTTS

def generate_voice(theses_list, output_audio="audio.mp3"):
    """
    Принимает список тезисов от ИИ, склеивает их в один текст
    и озвучивает роботом gTTS прямо в файл audio.mp3.
    """
    print("[ИИ Голос] Старт генерации аудиоозвучки...")

    # Жестко удаляем старый аудиофайл, если он остался от прошлого запроса
    if os.path.exists(output_audio):
        try:
            os.remove(output_audio)
        except Exception:
            pass

    # Соединяем все тезисы ИИ в один большой текст для озвучки
    full_text = " . ".join(theses_list)
    print(f"[ИИ Голос] Текст для озвучки: {full_text}")

    try:
        # Включаем русский голос от Google gTTS
        tts = gTTS(text=full_text, lang='ru', slow=False)
        tts.save(output_audio)

        if os.path.exists(output_audio):
            print(f"[ИИ Голос] Успех! Аудиофайл создан: {os.path.abspath(output_audio)}")
            return output_audio
        else:
            print("[Ошибка ИИ Голоса] Файл звука не создался.")
            return None
    except Exception as e:
        print(f"[Ошибка ИИ Голоса]: {e}")
        return None

if __name__ == "__main__":
    print("=== ТЕСТ АВТОНОМНОЙ ОЗВУЧКИ ===")
    generate_voice(["Тест авто озвучки", "Система чистый код 2026 работает"])
