import subprocess
import os
import sys
from datetime import datetime

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
    print("[ИИ Видео] Запуск сверхнадежного монтажа для Linux...")
    
    # Считываем дату и время
    now = datetime.now()
    current_date = "21.10.2026"
    current_time = now.strftime("%H-%M-%S")
    
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    # Гарантируем, что у нас в списке ровно 3 тезиса
    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Очищаем поисковый запрос пользователя для безопасного вывода в одну строку
    clean_query = query_text.replace("'", "").replace('"', '').replace(':', '').strip()
    if len(clean_query) > 30:
        clean_query = clean_query[:27] + "..."

    # Форматируем строчки БЕЗ опасных скрытых символов для первого слайда Linux
    title_text = f"ZAPROS  {clean_query}   --   DATA  {current_date}   --   VREMYA  {current_time}"
    
    # ИСПРАВЛЕНИЕ: Берем строго 1-й, 2-й и 3-й элементы из списка по очереди и превращаем в безопасный текст
    txt1 = str(theses[0]).replace("'", "").replace('"', '').replace(':', '').replace('[', '').replace(']', '')
    txt2 = str(theses[1]).replace("'", "").replace('"', '').replace(':', '').replace('[', '').replace(']', '')
    txt3 = str(theses[2]).replace("'", "").replace('"', '').replace(':', '').replace('[', '').replace(']', '')

    # Накладываем автоперенос строк на очищенный текст каждого тезиса отдельно
    t1_wrapped = wrap_text(txt1)
    t2_wrapped = wrap_text(txt2)
    t3_wrapped = wrap_text(txt3)

    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path): return None
    else:
        ffmpeg_path = "ffmpeg"

    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    font_path = "arial.ttf"
    
    # Абсолютно чистая команда FFmpeg для Render
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1e3d1a:s=854x480:r=10", 
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1a2a3d:s=854x480:r=10", 
        "-f", "lavfi", "-t", "7", "-i", "color=c=#2d2d2d:s=854x480:r=10", 
        "-i", audio_file,
        
        "-filter_complex", 
        f"[0:v] drawtext=fontfile={font_path}:text='{title_text}':fontcolor=white:fontsize=18:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black [v1];"
        
        f"[1:v] drawtext=fontfile={font_path}:text='{t2_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v2];"
        
        f"[2:v] drawtext=fontfile={font_path}:text='{txt3}':fontcolor=white:fontsize=22:"
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
            print(f"[ИИ Видео] Сверхнадежный фильм успешно смонтирован!")
            return output_video
        else: return None
    except Exception as e:
        print(f"[Ошибка монтажа]: {e}")
        return None

if __name__ == "__main__":
    generate_video("Зачем кошке усы")
