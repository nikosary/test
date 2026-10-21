import subprocess
import os
import sys
from datetime import datetime  # Добавили встроенные часы

def wrap_text(text, max_chars=40):
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
    if current_line:
        lines.append(" ".join(current_line))
    return "\\\n".join(lines)

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] Запуск монтажа с авто-датой, временем и вопросом...")
    
    # СЧИТЫВАЕМ ВРЕМЯ: Автоматически берем текущую дату и время на сервере
    now = datetime.now()
    current_date = now.strftime("%d.10.2026") # Жестко фиксируем победный октябрь 2026
    current_time = now.strftime("%H:%M:%S")    # Точное время до секунд (например, 19:01:15)
    
    # Подключаем суммаризатор для получения тезисов ИИ
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Форматируем тексты для слайдов
    # Первый слайд: выводим сам вопрос пользователя и время старта
    q_wrapped = wrap_text(query_text.replace("'", "").replace('"', ''))
    title_text = f"ВОПРОС: {q_wrapped}\\\n\\\nДата: {current_date}\\\nВремя: {current_time}"
    
    # Второй и третий слайды: выводим тезисы ответов
    t2 = wrap_text(theses[0].replace("'", "").replace('"', ''))
    t3 = wrap_text(theses[1].replace("'", "").replace('"', ''))

    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path): return None
    else:
        ffmpeg_path = "ffmpeg"

    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    font_path = "arial.ttf"
    
    # Команда FFmpeg: Слайд 1 (Зеленый) показывает вопрос и время. Слайды 2 и 3 показывают ответы!
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1e3d1a:s=854x480:r=10", # 1. Зеленый
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1a2a3d:s=854x480:r=10", # 2. Синий
        "-f", "lavfi", "-t", "7", "-i", "color=c=#2d2d2d:s=854x480:r=10", # 3. Серый
        "-i", audio_file,
        
        "-filter_complex", 
        f"[0:v] drawtext=fontfile={font_path}:text='{title_text}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=6 [v1];"
        
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
            print(f"[ИИ Видео] Фильм с часами и вопросом успешно смонтирован!")
            return output_video
        else: return None
    except Exception as e:
        print(f"[Ошибка монтажа]: {e}")
        return None

if __name__ == "__main__":
    generate_video("Зачем кошке усы")
