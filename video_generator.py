import subprocess
import os
import sys

def wrap_text(text, max_chars=40):
    """
    Умная функция: разбивает длинную строку текста на несколько строк
    по пробелам, чтобы текст не вылетал за края экрана видеоплеера.
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        # Считаем длину слова (+1 за пробел)
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    if current_line:
        lines.append(" ".join(current_line))
        
    # Возвращаем текст, где вместо бесконечной строки вставлены переносы \n
    return "\\\n".join(lines)

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] Запуск монтажа с АВТОМАТИЧЕСКИМ переносом русских строк...")
    
    # Подключаем наш суммаризатор, чтобы взять живой текст для титров
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = [
            "Глубокий анализ данных выявил ключевые закономерности по теме.",
            "Технология сборки контента работает полностью автономно без плагинов.",
            "Эко-стиль и лаконичная подача информации увеличивают удержание."
        ]

    # Гарантируем, что у нас ровно 3 тезиса
    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Обрабатываем каждый тезис функцией переноса строк и очищаем от опасных кавычек
    t1 = wrap_text(theses[0].replace("'", "").replace('"', ''))
    t2 = wrap_text(theses[1].replace("'", "").replace('"', ''))
    t3 = wrap_text(theses[2].replace("'", "").replace('"', ''))

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

    font_path = "arial.ttf"
    print("[ИИ Видео] Компиляция видеопотоков и наложение многострочных титров...")
    
    # Команда генерирует 3 цветных экрана и накладывает красиво разбитый текст по центру
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1e3d1a:s=854x480:r=10", # Зеленый фон
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1a2a3d:s=854x480:r=10", # Синий фон
        "-f", "lavfi", "-t", "7", "-i", "color=c=#2d2d2d:s=854x480:r=10", # Серый фон
        "-i", audio_file,                                                 # Наш ИИ-голос
        
        # Специфический фильтр FFmpeg для многострочного текста (text='...')
        "-filter_complex", 
        f"[0:v] drawtext=fontfile={font_path}:text='{t1}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v1];"
        
        f"[1:v] drawtext=fontfile={font_path}:text='{t2}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v2];"
        
        f"[2:v] drawtext=fontfile={font_path}:text='{t3}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v3];"
        
        "[v1][v2][v3] concat=n=3:v=1:a=0 [v_final]",
        
        "-map", "[v_final]",                  
        "-map", "3:a",                        
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",                          
        output_video
    ]

    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(output_video):
            print(f"[ИИ Видео] Успех! Видео с аккуратными переносами строк смонтировано!")
            return output_video
        else:
            return None
    except Exception as e:
        print(f"[Ошибка монтажа]: {e}")
        return None

if __name__ == "__main__":
    generate_video("Тест")
