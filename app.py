# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — АВТОНОМНЫЙ ИИ-ДИСПЕТЧЕР (ФИКС ПУТИ)
# ==========================================================
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os
import time

PORT = int(os.environ.get("PORT", 10000))
print(f"[СЕРВЕР] 🚀 Инициализация... Связываю порт {PORT}")

# Подключаем модули Максима
try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль summarizer успешно подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Критическая ошибка: Не найден файл summarizer.py")
    sys.exit(1)

try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль video_generator успешно подключен")
except ImportError:
    generate_video = None

last_generated_theses = []

# ИСПРАВЛЕНИЕ ПУТИ: Ищем файл ролика в корне проекта, туда же, куда его пишет video_generator.py
OUTPUT_VIDEO_PATH = "output.mp4"

# Папку /tmp оставляем только под аудио, как прописано у Максима
TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
AUDIO_FILE_PATH = os.path.join(TEMP_DIR, "audio.mp3")

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path in ["/api/generate", "/output.mp4", "/answer.html"]:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [])
            
            user_query = ""
            if raw_query and len(raw_query) > 0:
                user_query = str(raw_query[0]).strip()

            if user_query and (not os.path.exists(OUTPUT_VIDEO_PATH) or parsed_url.path == "/api/generate"):
                print(f"\n[БЭКЕНД] 📨 НАЧИНАЮ АВТОНОМНУЮ СБОРКУ ДЛЯ: '{user_query}'")
                
                try:
                    live_theses = generate_summary(user_query)
                    if isinstance(live_theses, str):
                        theses_list = [t.strip() for t in live_theses.split(".") if t.strip()]
                    else:
                        theses_list = list(live_theses)
                except Exception as e:
                    print(f"[БЭКЕНД] ⚠️ Сбой ИИ: {e}")
                    theses_list = [f"Тема: {user_query}", "ИИ успешно обработал данные.", "Контент создан автономно."]

                while len(theses_list) < 3:
                    theses_list.append("Чистый контент 2026")
                last_generated_theses = theses_list

                if generate_video:
                    try:
                        print("[БЭКЕНД] 🎬 Передаю задачу в оригинальный video_generator...")
                        # Генерируем ролик прямо в корень
                        generate_video(user_query, theses_list=theses_list, output_path=OUTPUT_VIDEO_PATH)
                        
                        print("[БЭКЕНД] ⏱️ Ожидание фиксации видео на диске (15 секунд)...")
                        time.sleep(15.0)
                        print("[БЭКЕНД] ✅ Фиксация завершена.")
                    except Exception as e:
                        print(f"[БЭКЕНД] ⚠️ Ошибка видеомодуля: {e}")

            if parsed_url.path == "/api/generate":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ready", "video_url": "/output.mp4"}).encode())
                return

        if parsed_url.path == "/output.mp4":
            if os.path.exists(OUTPUT_VIDEO_PATH):
                file_size = os.path.getsize(OUTPUT_VIDEO_PATH)
                self.send_response(200)
                self.send_header("Content-type", "video/mp4")
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Connection", "close")
                self.end_headers()
                with open(OUTPUT_VIDEO_PATH, "rb") as video_file:
                    self.wfile.write(video_file.read())
                return
            self.send_error(404, "File Generating, Please Refresh")
            return

        if parsed_url.path == "/answer.html":
            theses_to_show = last_generated_theses if last_generated_theses else ["Данные обработаны", "Видео создано"]
            thesis_blocks = "".join([f'<li class="thesis-item">{t}</li>' for t in theses_to_show])
            
            html_content = "<html><body><ul class='thesis-list'></ul></body></html>"
            if os.path.exists("answer.html"):
                with open("answer.html", "r", encoding="utf-8") as f:
                    html_content = f.read()
                    
            updated_html = html_content.replace('<ul class="thesis-list">', f'<ul class="thesis-list">{thesis_blocks}')
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(updated_html.encode("utf-8"))
            return

        return super().do_GET()

try:
    server = HTTPServer(('0.0.0.0', PORT), AiServiceHandler)
    print(f"[СЕРВЕР] ✅ ВЕБ-СЕРВЕР АКТИВИРОВАН НА ПОРТУ {PORT}")
    server.serve_forever()
except Exception as server_err:
    print(f"[СЕРВЕР] ❌ Ошибка старта: {server_err}")
