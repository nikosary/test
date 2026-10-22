import os
import sys
import subprocess
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
    full_text = " . ".join([str(t) for t in theses_list])
    print(f"[ИИ Голос] Текст для озвучки: {full_text}")

    try:
        # Включаем русский голос от Google gTTS
        tts = gTTS(text=full_text, lang='ru', slow=False)
        tts.save(output_audio)

        if os.path.exists(output_audio) and os.path.getsize(output_audio) > 0:
            print(f"[ИИ Голос] Успех! Аудиофайл создан: {os.path.abspath(output_audio)}")
            return output_audio
        else:
            print("[ИИ Голос] Предупреждение: Файл звука создался пустым.")
    except Exception as e:
        print(f"[ИИ Голос] ⚠️ Интернет-сбой gTTS или нет связи с Google: {e}")
    
    # ЖЕЛЕЗОБЕТОННЫЙ ПЛАН Б: Если озвучка не скачалась, создаем тишину через FFmpeg, чтобы видео не ломалось!
    print("[ИИ Голос] ⚙️ Аварийный режим: создаю безопасный аудиофайл тишины для FFmpeg...")
    try:
        ffmpeg_path = "ffmpeg"
        if sys.platform.startswith("win") and os.path.exists("ffmpeg.exe"):
            ffmpeg_path = os.path.abspath("ffmpeg.exe")

        # Считаем примерную длину тишины по объему текста (около 15 секунд)
        duration = max(12, round(len(full_text) / 12, 1))
        
        # Команда создает файл тишины mp3 заданной длины
        cmd = [
            ffmpeg_path, "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(duration),
            "-c:a", "libmp3lame", "-b:a", "128k",
            output_audio
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        if os.path.exists(output_audio) and os.path.getsize(output_audio) > 0:
            print(f"[ИИ Голос] Аварийный аудиофайл тишины успешно подготовлен: {output_audio}")
            return output_audio
    except Exception as ffmpeg_err:
        print(f"[ИИ Голос] ❌ Не удалось создать даже файл тишины: {ffmpeg_err}")
    
    return None

if __name__ == "__main__":
    print("=== ТЕСТ АВТОНОМНОЙ ОЗВУЧКИ ===")
    generate_voice(["Тест авто озвучки", "Система чистый код 2026 работает"])
