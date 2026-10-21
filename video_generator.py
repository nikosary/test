import subprocess
import os
import sys

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] Запуск динамического монтажа с РУССКИМИ тезисами ИИ...")
    
    # Подключаем наш суммаризатор, чтобы взять живой текст для титров
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = ["Первый тезис проекта", "Второй тезис проекта", "Третий тезис проекта"]

    # Гарантируем, что у нас ровно 3 тезиса (дописываем заглушки, если ИИ дал меньше)
    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Очищаем текст от кавычек и опасных символов, которые могут сломать FFmpeg
    t1 = theses[0].replace("'", "").replace('"', '')
    t2 = theses[1].replace("'", "").replace('"', '')
    t3 = theses[2].replace("'", "").replace('"', '')

    # Умная проверка путей FFmpeg
    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path):
            print("[Ошибка] Файл ffmpeg.exe не найден!")
            return None
    else:
        ffmpeg_path = "ffmpeg"

    # Жестко удаляем старое видео
    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    # Проверяем наш файл шрифта
    font_path = "arial.ttf"
    if not os.path.exists(font_path):
        print("[Предупреждение] Шрифт arial.ttf не найден в папке проекта!")

    print("[ИИ Видео] Компиляция видеопотоков и наложение русских титров...")
    
    # Команда генерирует 3 цветных экрана и накладывает на КАЖДЫЙ свой собственный тезис ИИ!
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1e3d1a:s=854x480:r=10", # Зеленый фон
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1a2a3d:s=854x480:r=10", # Синий фон
        "-f", "lavfi", "-t", "7", "-i", "color=c=#2d2d2d:s=854x480:r=10", # Серый фон
        "-i", audio_file,                                                 # Наш ИИ-голос
        
        # Сложнейшая магия фильтров: накладываем русский текст со шрифтом Arial
        "-filter_complex", 
        f"[0:v] drawtext=fontfile={font_path}:text='{t1}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black [v1];"
        
        f"[1:v] drawtext=fontfile={font_path}:text='{t2}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black [v2];"
        
        f"[2:v] drawtext=fontfile={font_path}:text='{t3}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black [v3];"
        
        "[v1][v2][v3] concat=n=3:v=1:a=0 [v_final]",
        
        "-map", "[v_final]",                  # Забираем готовое видео с русскими титрам
        "-map", "3:a",                        # Забираем звук из аудиофайла
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",                          # Обрезаем по длине звука
        output_video
    ]

    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(output_video):
            print(f"[ИИ Видео] Успех! Настоящий фильм с русскими титрами смонтирован!")
            return output_video
        else:
            return None
    except Exception as e:
        print(f"[Ошибка монтажа]: {e}")
        return None

if __name__ == "__main__":
    generate_video("Тест")
