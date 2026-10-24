# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — АВТОНОМНЫЙ КИНЕМАТОГРАФИЧЕСКИЙ СЕРВЕР
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
print(f"[DEBUG] Python version: {sys.version}")
print(f"[DEBUG] Working directory: {os.getcwd()}")
print(f"[DEBUG] PLATFORM: {sys.platform}")

# Проверка модулей
try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль summarizer успешно подключен")
except ImportError as e:
    print(f"[СЕРВЕР] ❌ Критическая ошибка: Не найден файл summarizer.py! {e}")
    sys.exit(1)

try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль video_generator успешно подключен")
except ImportError as e:
    print(f"[СЕРВЕР] ⚠️ Модуль video_generator не найден: {e}")
    generate_video = None

try:
    from voice_engine import generate_voice
    print("[СЕРВЕР] ✅ Модуль voice_engine успешно подключен")
except ImportError as e:
    print(f"[СЕРВЕР] ⚠️ Модуль voice_engine не найден: {e}")
    generate_voice = None

# Глобальные переменные
last_generated_theses = []
TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
OUTPUT_VIDEO_PATH = os.path.join(TEMP_DIR, "output.mp4")
AUDIO_FILE_PATH = os.path.join(TEMP_DIR, "audio.mp3")

print(f"[DEBUG] TEMP_DIR: {TEMP_DIR}")
print(f"[DEBUG] OUTPUT_VIDEO_PATH: {OUTPUT_VIDEO_PATH}")
print(f"[DEBUG] AUDIO_FILE_PATH: {AUDIO_FILE_PATH}")

def wrap_text_clean(text, max_chars=35):
    if not text: return ""
    clean_text = str(text).replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    words = clean_text.split()
    lines, current_line, current_length = [], [], 0
    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line, current_length = [word], len(word)
    if current_line: lines.append(" ".join(current_line))
    return "\\\n".join(lines)

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)
        
        print(f"[DEBUG] Received request: {parsed_url.path}")

        # 1. ГЕНЕРАЦИЯ ВИДЕО
        if parsed_url.path == "/api/generate":
            print("[DEBUG] =========== /api/generate START ===========")
            
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query_list = query_params.get('query', [])
            
            print(f"[DEBUG] raw_query_list: {raw_query_list}")
            
            user_query = ""
            if raw_query_list and len(raw_query_list) > 0:
                user_query = str(raw_query_list[0]).strip()
            
            print(f"[DEBUG] user_query: '{user_query}'")
            
            if not user_query:
                print("[DEBUG] Empty query, returning 400")
                self.send_response(400)
                self.end_headers()
                return

            now = datetime.now()
            current_date = now.strftime("%d.%m.%Y")
            display_time = now.strftime("%H:%M:%S")

            print(f"[ОБЛАКО RENDER] 📨 ЗАПУСК МОНТАЖА ДЛЯ: '{user_query}' в {display_time}")

            # Шаг A: Генерация тезисов
            print("[DEBUG] Вызываю generate_summary...")
            try:
                live_theses = generate_summary(user_query)
                print(f"[DEBUG] generate_summary вернул: {live_theses}")
                theses = [t.strip() for t in live_theses.split(".") if t.strip()] if isinstance(live_theses, str) else list(live_theses)
            except Exception as e:
                print(f"[DEBUG] Ошибка generate_summary: {e}")
                theses = [f"Ответ на запрос: {user_query}", "ИИ успешно обработал тему.", "Контент сформирован в облаке."]

            print(f"[DEBUG] Тезисы: {theses}")
            
            while len(theses) < 3: 
                theses.append("Чистый контент 2026")
            
            last_generated_theses = theses
            print(f"[DEBUG] last_generated_theses: {last_generated_theses}")

            # Шаг B: Генерация аудио
            print("[DEBUG] Проверяю generate_voice...")
            if generate_voice:
                try:
                    print(f"[DEBUG] Вызываю generate_voice с {AUDIO_FILE_PATH}")
                    generate_voice(theses, output_audio=AUDIO_FILE_PATH)
                    print(f"[DEBUG] Аудио создано: {os.path.exists(AUDIO_FILE_PATH)}")
                except Exception as e:
                    print(f"[DEBUG] Ошибка generate_voice: {e}")
            else:
                print("[DEBUG] generate_voice = None, пропускаем")

            # Шаг C: Удаление старого видео
            if os.path.exists(OUTPUT_VIDEO_PATH): 
                try: 
                    os.remove(OUTPUT_VIDEO_PATH)
                    print(f"[DEBUG] Удален старый файл: {OUTPUT_VIDEO_PATH}")
                except Exception as e:
                    print(f"[DEBUG] Ошибка удаления старого файла: {e}")

            # Шаг D: Настройка FFmpeg движка
            ffmpeg_path = "static_ffmpeg"
            if sys.platform.startswith("win"):
                ffmpeg_path = "ffmpeg"
            print(f"[DEBUG] Выбран движок ffmpeg_path: {ffmpeg_path}")
            
            # Проверка FFmpeg
            try:
                result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
                print(f"[DEBUG] FFmpeg version check: {result.stdout[:100]}")
            except Exception as e:
                print(f"[DEBUG] FFmpeg не найден через вызов: {e}")

            clean_q = user_query.replace("'", "").replace('"', "")
            if len(clean_q) > 40: clean_q = clean_q[:37] + "..."
            
            q_wrapped = wrap_text_clean(clean_q, max_chars=30)
            t1_wrapped = wrap_text_clean(theses[0] if len(theses) > 0 else "Тезис 1", max_chars=35)
            t2_wrapped = wrap_text_clean(theses[1] if len(theses) > 1 else "Тезис 2", max_chars=35)
            t3_wrapped = wrap_text_clean(theses[2] if len(theses) > 2 else "Тезис 3", max_chars=35)

            print(f"[DEBUG] q_wrapped: {q_wrapped}")
            print(f"[DEBUG] t1_wrapped: {t1_wrapped}")
            print(f"[DEBUG] t2_wrapped: {t2_wrapped}")
            print(f"[DEBUG] t3_wrapped: {t3_wrapped}")

            slide_time = 4.0
            
            # Шаг E: Генерация видео через FFmpeg
            print("[DEBUG] Начинаю генерацию видео...")
            try:
                cmd = [
                    ffmpeg_path, "-y",
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d5a27:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", 
                ]
                
                has_audio = os.path.exists(AUDIO_FILE_PATH) and os.path.getsize(AUDIO_FILE_PATH) > 0
                print(f"[DEBUG] has_audio: {has_audio}")
                
                if has_audio: 
                    cmd += ["-i", AUDIO_FILE_PATH]

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
                
                print(f"[DEBUG] Вызываю subprocess для FFmpeg...")
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                print("[ОБЛАКО RENDER] 🎉 МОНТАЖ ПОЛНОСТЬЮ ЗАВЕРШЕН!")
            except Exception as ffmpeg_err:
                print(f"[DEBUG] Критическая ошибка сборки ролика через FFmpeg: {ffmpeg_err}")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {"status": "ready", "video_url": f"/output.mp4?t={int(time.time())}", "theses": last_generated_theses}
            self.wfile.write(json.dumps(response_data).encode())
            return

        # 2. ОТДАЧА ВИДЕОПОТОКА В ПЛЕЕР (С ФИКСАЦИЕЙ СОЕДИНЕНИЯ)
        if parsed_url.path == "/output.mp4":
            print(f"[DEBUG] Запрос потока /output.mp4. Проверяю путь: {OUTPUT_VIDEO_PATH}")
            if os.path.exists(OUTPUT_VIDEO_PATH):
                file_size = os.path.getsize(OUTPUT_VIDEO_PATH)
                print(f"[DEBUG] Видео найдено! Размер: {file_size} байт. Отдаю...")
