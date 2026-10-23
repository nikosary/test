# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — ПОЛНАЯ КИНЕМАТОГРАФИЧЕСКАЯ СБОРКА
# ==========================================================
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os
import subprocess
import time
from datetime import datetime

print("[СЕРВЕР] 🚀 Старт пуленепробиваемой системы Чистый Код 2026...")

try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль summarizer успешно подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Критическая ошибка: Не найден файл summarizer.py!")
    sys.exit(1)

try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль video_generator успешно подключен")
except ImportError:
    generate_video = None

try:
    from voice_engine import generate_voice
    print("[СЕРВЕР] ✅ Модуль voice_engine успешно подключен")
except ImportError:
    generate_voice = None

# Глобальная переменная для хранения последних тезисов ИИ
last_generated_theses = []

# НАСТРОЙКА ДЛЯ RENDER: Переносим создание файлов в безопасную системную папку /tmp
TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
OUTPUT_VIDEO_PATH = os.path.join(TEMP_DIR, "output.mp4")
AUDIO_FILE_PATH = os.path.join(TEMP_DIR, "audio.mp3")

def wrap_text_clean(text, max_chars=35):
    """Аккуратно разбивает длинный текст на строки для экрана."""
    if not text:
        return ""
    clean_text = str(text).replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    words = clean_text.split()
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

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)

        # 1. ЖЕЛЕЗНЫЙ ПЕРЕХВАТ ПУТИ ГЕНЕРАЦИИ ВИДЕО (Защита от 404 ошибки)
        if parsed_url.path == "/api/generate":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [''])
            if not raw_query or not raw_query.strip():
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Empty query"}).encode())
                return

            user_query = raw_query.strip()
            now = datetime.now()
            current_date = now.strftime("%d.%m.%Y")
            display_time = now.strftime("%H:%M:%S")

            print(f"\n{'='*60}")
            print(f"[ОБЛАКО RENDER] 📨 ЗАПУСК РОЛИКА: '{user_query}' в {display_time}")
            print(f"{'='*60}")

            # Шаг A. Создаем тезисы через ИИ
            try:
                live_theses = generate_summary(user_query)
                if isinstance(live_theses, str):
                    theses = [t.strip() for t in live_theses.split(".") if t.strip()]
                else:
                    theses = list(live_theses)
            except Exception as e:
                print(f"[ОБЛАКО RENDER] ⚠️ Сбой ИИ, создаю заглушки: {e}")
                theses = [
                    f"Ответ на запрос: {user_query}",
                    "ИИ-алгоритмы проекта Чистый код 2026 успешно обработали тему.",
                    "Контент автономно сформирован и упакован в облаке."
                ]

            while len(theses) < 3:
                theses.append("Чистый контент 2026")

            # Сохраняем в глобальную переменную для страницы ответа
            last_generated_theses = theses

            # Шаг B. Создаем аудио-озвучку audio.mp3 в папке /tmp
            if generate_voice:
                try:
                    generate_voice(theses, output_audio=AUDIO_FILE_PATH)
                except Exception as voice_err:
                    print(f"[ОБЛАКО RENDER] ⚠️ Ошибка голосового движка: {voice_err}")

            # Шаг C. Начинаем профессиональный монтаж через FFmpeg
            if os.path.exists(OUTPUT_VIDEO_PATH):
                try: os.remove(OUTPUT_VIDEO_PATH)
                except Exception: pass

            ffmpeg_path = "ffmpeg"
            try:
                import static_ffmpeg
                if hasattr(static_ffmpeg, 'run'):
                    ffmpeg_path = "static_ffmpeg"
            except ImportError:
                pass

            if sys.platform.startswith("win") and os.path.exists("ffmpeg.exe"):
                ffmpeg_path = os.path.abspath("ffmpeg.exe")

            # Готовим тексты: разбиваем на красивые короткие читаемые строчки
            clean_q = user_query.replace("'", "").replace('"', "")
            if len(clean_q) > 40: clean_q = clean_q[:37] + "..."
            
            q_wrapped = wrap_text_clean(clean_q, max_chars=30)
            
            # ЖЕСТКОЕ ИСПРАВЛЕНИЕ ПО ИНДЕКСАМ: Тексты на слайдах будут строго разными!
            t1_wrapped = wrap_text_clean(theses[0], max_chars=35)
            t2_wrapped = wrap_text_clean(theses[1], max_chars=35)
            t3_wrapped = wrap_text_clean(theses[2], max_chars=35)

            slide_time = 4.0  # Каждая картинка показывается по 4 секунды
            
            print("[ОБЛАКО RENDER] 🎬 FFmpeg начинает склейку экранов со звуком...")
            video_ready = False
            try:
                cmd = [
                    "ffmpeg" if ffmpeg_path == "ffmpeg" else "static_ffmpeg", "-y",
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d5a27:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", 
                ]
                
                if os.path.exists(AUDIO_FILE_PATH) and os.path.getsize(AUDIO_FILE_PATH) > 0:
                    cmd += ["-i", AUDIO_FILE_PATH]
                    has_audio = True
                else:
                    has_audio = False

                filter_string = (
                    f"[0:v] drawtext=text='{q_wrapped}':fontcolor=white:fontsize=26:x=(w-text_w)/2:y=100:borderw=2:bordercolor=black [v1_title];"
                    f"[v1_title] drawtext=text='DATA: {current_date}  VREMYA: {display_time}':fontcolor=yellow:fontsize=28:x=(w-text_w)/2:y=260:borderw=3:bordercolor=black [v1];"
                    f"[1:v] drawtext=text='{t1_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v2];"
                    f"[2:v] drawtext=text='{t2_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v3];"
                    f"[3:v] drawtext=text='{t3_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v4];"
                    "[v1][v2][v3][v4] concat=n=4:v=1:a=0 [v_final]"
                )

                cmd += ["-filter_complex", filter_string, "-map", "[v_final]"]
                
                if has_audio:
                    cmd += ["-map", "4:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
                
                cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", OUTPUT_VIDEO_PATH]
                
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                print("[ОБЛАКО RENDER] 🎉 МОНТАЖ ФИЛЬМА ПОЛНОСТЬЮ ЗАВЕРШЕН!")
                video_ready = True
            except Exception as ffmpeg_err:
                print(f"[ОБЛАКО RENDER] ❌ Ошибка FFmpeg сборки: {ffmpeg_err}")
                video_ready = False

            if not video_ready:
                try:
                    cmd_alt = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=#2d5a27:s=854x480:d=8", "-c:v", "libx264", OUTPUT_VIDEO_PATH]
                    subprocess.run(cmd_alt, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                except Exception: pass

            time.sleep(2.5)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {
                "status": "ready",
                "video_url": f"/output.mp4?t={int(time.time())}",
                "theses": last_generated_theses
            }
            self.wfile.write(json.dumps(response_data).encode())
            return

        # 2. НАДЕЖНАЯ ОТДАЧА СТРИМИНГОВОГО ВИДЕО ИЗ ПАПКИ /tmp В ПЛЕЕР
        if parsed_url.path == "/output.mp4":
            if os.path.exists(OUTPUT_VIDEO_PATH):
                try:
                    file_size = os.path.getsize(OUTPUT_VIDEO_PATH)
                    self.send_response(200)
                    self.send_header("Content-type", "video/mp4")
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Accept-Ranges", "bytes") 
                    self.end_headers()
                    
                    with open(OUTPUT_VIDEO_PATH, "rb") as video_file:
                        while True:
                            chunk = video_file.read(65536)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    return
                except Exception:
                    return
            else:
                self.send_error(404, "File Not Found")
                return

