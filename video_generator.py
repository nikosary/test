import subprocess
import os
import sys
from datetime import datetime

def wrap_text(text, max_chars=40):
    """
    Автоматически разбивает длинный русский текст на несколько строк,
    чтобы он красиво ложился по центру экрана видео.
    """
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
    """Умный поиск шрифта Arial: проверяет проект и системные папки Windows/Linux/Mac."""
    font_candidates = [
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "Roboto-Regular.ttf"
    ]

    for font in font_candidates:
        if os.path.exists(font):
            print(f"[ИИ Видео] ✅ Найден шрифт в папке проекта: {font}")
            return font

    if sys.platform.startswith("win"):
        windows_fonts = [
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\Arial.ttf",
            "C:\\Windows\\Fonts\\Arialbd.ttf"
        ]
        for font in windows_fonts:
            if os.path.exists(font):
                print(f"[ИИ Видео] ✅ Найден системный шрифт Windows: {font}")
                return font

    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Arial.ttf"
    ]
    for font in linux_fonts:
        if os.path.exists(font):
            print(f"[ИИ Видео] ✅ Найден системный шрифт Linux/Mac: {font}")
            return font

    print("[ИИ Видео] ❌ Шрифт не найден!")
    return None

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] 🎬 Запуск сверхнадежной генерации видео...")

    # ИСПРАВЛЕНО: Гарантируем, что запрос преобразован в чистую текстовую строку
    if isinstance(query_text, list):
        query_text = " ".join([str(x) for x in query_text])
    else:
        query_text = str(query_text)

    # Проверяем аудиофайл
    if not os.path.exists(audio_file):
        print(f"[ИИ Видео] ❌ Аудиофайл '{audio_file}' не найден!")
        print("[ИИ Видео] ⚠️  Создаю временный пустой аудио-фон для проверки...")
        subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "anullsrc", "-t", "21", audio_file], capture_output=True)

    font_path = find_font()
    if not font_path:
        print("[ИИ Видео] ❌ Монтаж невозможен без файла шрифта.")
        return None

    # Считываем реальную текущую дату и время
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time = now.strftime("%H:%M:%S")

    # Пытаемся получить тезисы из summarizer
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
        print(f"[ИИ Видео] ✅ Получены тезисы для видео: {len(theses)}")
    except Exception as e:
        print(f"[ИИ Видео] ⚠️  Не удалось получить тезисы: {e}")
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Очищаем тезисы строго по номерам из списка
    t1_raw = str(theses[0]).replace("'", "").replace('"', '').replace(':', ' ').strip()
    t2_raw = str(theses[1]).replace("'", "").replace('"', '').replace(':', ' ').strip()
    t3_raw = str(theses[2]).replace("'", "").replace('"', '').replace(':', ' ').strip()

    # Очищаем тему вопроса пользователя для первой строки
    clean_query = query_text.replace("'", "").replace('"', '').replace(':', ' ').strip()
    if len(clean_query) > 30:
        clean_query = clean_query[:27] + "..."

    # Текст для титульного слайда (без запрещенных для FFmpeg вертикальных палочек)
    title_text = f"ZAPROS  {clean_query}   --   DATA  {current_date}   --   VREMYA  {current_time}"

    t1_wrapped = wrap_text(t1_raw)
    t2_wrapped = wrap_text(t2_raw)
    t3_wrapped = wrap_text(t3_raw)

    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path):
            ffmpeg_path = "ffmpeg"
    else:
        ffmpeg_path = "ffmpeg"

    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    # Высчитываем тайминги динамически на базе объема букв (скорость 12 симв/сек)
    full_length = len(" ".join([str(t) for t in theses]))
    audio_duration = max(12, round(full_length / 12, 1))
    slide_time = round(audio_duration / 3, 1)
    print(f"[ИИ Видео] Расчетная длина слайда: {slide_time} сек. Итого ролик: {audio_duration} сек.")

    # Пуленепробиваемая команда FFmpeg с крупными часами и исправленным третьим слайдом
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10",
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10",
        "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10",
        "-i", audio_file,

        "-filter_complex",
        # Слайд 1: Вопрос сверху, а по центру КРУПНО желтая дата и время
        f"[0:v] drawtext=fontfile='{font_path}':text='{wrap_text(clean_query, max_chars=30)}':fontcolor=white:fontsize=24:"
        f"x=(w-text_w)/2:y=50:borderw=3:bordercolor=black [v1_title];"
        f"[v1_title] drawtext=fontfile='{font_path}':text='{current_date}  {current_time}':fontcolor=yellow:fontsize=32:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=4:bordercolor=black [v1];"

        # Слайд 2: Первый тезис ИИ
        f"[1:v] drawtext=fontfile='{font_path}':text='{t1_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v2];"

        # Слайд 3: ИСПРАВЛЕНО: Теперь выводится строго третий тезис t3_wrapped вместо дубликата второго!
        f"[2:v] drawtext=fontfile='{font_path}':text='{t3_wrapped}':fontcolor=white:fontsize=22:"
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
        print("[ИИ Видео] ⏳ Запуск стабильного FFmpeg монтажа...")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            print(f"[ИИ Видео] ✅ Успех! Фильм с часами смонтирован: {output_video} ({file_size:.2f} MB)")
            return output_video
        else:
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ИИ Видео] ❌ Ошибка FFmpeg. Код: {e.returncode}")
        if e.stderr: print(f"[ИИ Видео] 📋 Логи: {e.stderr[-500:]}")
        return None
    except Exception as e:
        print(f"[ИИ Видео] ❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    generate_video("Зачем кошке усы")
