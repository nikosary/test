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

def find_font():
    """Ищет доступный шрифт в системе"""
    font_candidates = [
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "Roboto-Regular.ttf"
    ]

    # Проверяем в текущей папке
    for font in font_candidates:
        if os.path.exists(font):
            print(f"[ИИ Видео] ✅ Найден шрифт: {font}")
            return font

    # На Windows ищем системные шрифты
    if sys.platform.startswith("win"):
        windows_fonts = [
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\Arial.ttf",
            "C:\\Windows\\Fonts\\Arialbd.ttf"
        ]
        for font in windows_fonts:
            if os.path.exists(font):
                print(f"[ИИ Видео] ✅ Найден системный шрифт: {font}")
                return font

    # На Linux/Mac ищем системные шрифты
    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Arial.ttf"
    ]
    for font in linux_fonts:
        if os.path.exists(font):
            print(f"[ИИ Видео] ✅ Найден системный шрифт: {font}")
            return font

    print("[ИИ Видео] ❌ Шрифт не найден!")
    return None

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] 🎬 Запуск генерации видео...")

    # Проверяем аудиофайл
    if not os.path.exists(audio_file):
        print(f"[ИИ Видео] ❌ Аудиофайл '{audio_file}' не найден!")
        print("[ИИ Видео] ⚠️  Видео будет создано без звука")
        # Создадим пустой аудиофайл
        subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "anullsrc", "-t", "21", audio_file], capture_output=True)

    # Находим шрифт
    font_path = find_font()
    if not font_path:
        print("[ИИ Видео] ❌ Шрифт не найден! Видео не будет создано.")
        return None

    # Используем реальную дату и время
    now = datetime.now()
    current_date = now.strftime("%d.%m.%Y")
    current_time = now.strftime("%H-%M-%S")

    # Пытаемся получить тезисы из summarizer
    try:
        from summarizer import generate_summary
        theses = generate_summary(query_text)
        print(f"[ИИ Видео] ✅ Получены тезисы для видео: {len(theses)}")
    except Exception as e:
        print(f"[ИИ Видео] ⚠️  Не удалось получить тезисы: {e}")
        print("[ИИ Видео] Использую заглушки...")
        theses = ["Первый тезис от ИИ", "Второй тезис от ИИ", "Третий тезис от ИИ"]

    # Гарантируем наличие ровно 3 элементов
    while len(theses) < 3:
        theses.append("Чистый код 2026")

    # Очищаем тезисы от спецсимволов
    t1_raw = str(theses[0]).replace("'", "").replace('"', '').replace(':', '').strip()
    t2_raw = str(theses[1]).replace("'", "").replace('"', '').replace(':', '').strip()
    t3_raw = str(theses[2]).replace("'", "").replace('"', '').replace(':', '').strip()

    # Очищаем тему вопроса
    clean_query = query_text.replace("'", "").replace('"', '').replace(':', '').strip()
    if len(clean_query) > 30:
        clean_query = clean_query[:27] + "..."

    # Текст для титульного слайда
    title_text = f"ZAPROS  {clean_query}   --   DATA  {current_date}   --   VREMYA  {current_time}"

    # Перенос строк
    t1_wrapped = wrap_text(t1_raw)
    t2_wrapped = wrap_text(t2_raw)
    t3_wrapped = wrap_text(t3_raw)

    # Определяем путь к FFmpeg
    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path):
            print("[ИИ Видео] ❌ ffmpeg.exe не найден в текущей папке!")
            return None
    else:
        ffmpeg_path = "ffmpeg"

    # Проверяем FFmpeg
    try:
        subprocess.run([ffmpeg_path, "-version"], capture_output=True, check=True)
        print(f"[ИИ Видео] ✅ FFmpeg доступен: {ffmpeg_path}")
    except Exception:
        print(f"[ИИ Видео] ❌ FFmpeg не доступен: {ffmpeg_path}")
        return None

    # Удаляем старый файл если есть
    if os.path.exists(output_video):
        try:
            os.remove(output_video)
            print(f"[ИИ Видео] 🗑️  Удален старый файл: {output_video}")
        except Exception as e:
            print(f"[ИИ Видео] ⚠️  Не удалось удалить старый файл: {e}")

    # Команда FFmpeg
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1e3d1a:s=854x480:r=10",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1a2a3d:s=854x480:r=10",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#2d2d2d:s=854x480:r=10",
        "-i", audio_file,

        "-filter_complex",
        f"[0:v] drawtext=fontfile={font_path}:text='{title_text}':fontcolor=white:fontsize=18:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black [v1];"

        f"[1:v] drawtext=fontfile={font_path}:text='{t1_wrapped}':fontcolor=white:fontsize=22:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black:line_spacing=5 [v2];"

        f"[2:v] drawtext=fontfile={font_path}:text='{t2_wrapped}':fontcolor=white:fontsize=22:"
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
        print("[ИИ Видео] ⏳ Запуск FFmpeg...")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

        if result.stderr:
            # Показываем последние 500 символов логов
            logs = result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
            print(f"[ИИ Видео] 📋 Логи FFmpeg: {logs}")

        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024 * 1024)
            print(f"[ИИ Видео] ✅ Успех! Видео создано: {output_video} ({file_size:.2f} MB)")
            return output_video
        else:
            print("[ИИ Видео] ❌ Файл не создался, хотя FFmpeg отработал.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"[ИИ Видео] ❌ Ошибка FFmpeg. Код возврата: {e.returncode}")
        if e.stderr:
            error_logs = e.stderr[-1000:] if len(e.stderr) > 1000 else e.stderr
            print(f"[ИИ Видео] 📋 Ошибка FFmpeg: {error_logs}")
        return None
    except Exception as e:
        print(f"[ИИ Видео] ❌ Неизвестная ошибка: {e}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("Тестовый запуск генератора видео")
    print("="*60)

    test_query = "Зачем кошке усы"
    print(f"\nЗапрос: {test_query}\n")

    result = generate_video(test_query)

    if result:
        print(f"\n✅ Готово! Видео: {result}")
    else:
        print("\n❌ Не удалось создать видео. Проверьте ошибки выше.")
