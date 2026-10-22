import subprocess
import os
import sys
from datetime import datetime

def wrap_text(text, max_chars=35):
    """Разбивает длинный текст на аккуратные строки для экрана видео."""
    if not text:
        return ""
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

def find_font():
    """Ищет шрифт Arial в системе Windows или Linux."""
    if os.path.exists("arial.ttf"):
        return "arial.ttf"
    if sys.platform.startswith("win"):
        win_font = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf")
        if os.path.exists(win_font): return win_font.replace("\\", "/")
    else:
        linux_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
        ]
        for font in linux_fonts:
            if os.path.exists(font): return font
    return "arial.ttf"

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] Запуск автономного монтажа с поштучным выбором тезисов...")
    
    # Считываем реальное время и дату
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    display_time = now.strftime("%H:%M:%S")  
    
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
    except Exception:
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    # Гарантируем наличие ровно 3 элементов в списке
    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Очищаем тему вопроса пользователя
    clean_query = query_text.replace("'", "").replace('"', '').replace(':', ' ').strip()
    if len(clean_query) > 40: clean_query = clean_query[:37] + "..."
    
    q_wrapped = wrap_text(clean_query, max_chars=30)
    
    # Считаем длину аудио математически по объёму текста
    full_text_length = len(" ".join([str(t) for t in theses]))
    audio_duration = max(12, round(full_text_length / 12, 1))
    
    # Делим время звука на 3 равных слайда для идеальной синхронизации
    slide_time = round(audio_duration / 3, 1)
    print(f"[ИИ Видео] Расчетная длина звука: {audio_duration} сек. Слайд: {slide_time} сек.")

    # Извлекаем тезисы строго поштучно по их индексам (0, 1, 2) из списка
    txt1 = str(theses[0]).replace("'", "").replace('"', '').replace(':', ' ').strip()
    txt2 = str(theses[1]).replace("'", "").replace('"', '').replace(':', ' ').strip()
    txt3 = str(theses[2]).replace("'", "").replace('"', '').replace(':', ' ').strip()

    t1_wrapped = wrap_text(txt1)
    t2_wrapped = wrap_text(txt2)
    t3_wrapped = wrap_text(txt3)

    # Безопасный текст для титульного слайда
    title_text = f"ZAPROS  {clean_query}   --   DATA  {current_date}   --   VREMYA  {display_time}"

    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path): ffmpeg_path = "ffmpeg"
    else:
        ffmpeg_path = "ffmpeg"

    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    font_path = find_font()
    
    # ИСПРАВЛЕНО: Полностью убрали опасные одинарные кавычки вокруг путей шрифтов для Linux!
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", 
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", 
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", 
        "-i", audio_file,
        
        "-filter_complex", 
        f"[0:v] drawtext=fontfile={font_path}:text='{q_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=50:borderw=3:bordercolor=black [v1_title];"
        f"[v1_title] drawtext=fontfile={font_path}:text='{current_date}  {display_time}':fontcolor=yellow:fontsize=32:x=(w-text_w)/2:y=(h-text_h)/2:borderw=4:bordercolor=black [v1];"
        
        f"[1:v] drawtext=fontfile={font_path}:text='{t1_wrapped}':fontcolor=white:fontsize=22:x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=6 [v2];"
        
        f"[2:v] drawtext=fontfile={font_path}:text='{t3_wrapped}':fontcolor=white:fontsize=22:x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=6 [v3];"
        
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
            print(f"[ИИ Видео] Сверхточный фильм с крупными часами успешно смонтирован!")
            return output_video
        else: return None
    except Exception as e:
        print(f"[Ошибка монтажа]: {e}")
        return None

if __name__ == "__main__":
    generate_video("Зачем кошке усы")
