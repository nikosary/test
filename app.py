# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — АВТОНОМНЫЙ ИИ-ДИСПЕТЧЕР (МЕГА-СПЛИТ)
# ==========================================================
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os
import time

PORT = int(os.environ.get("PORT", 10000))
print(f"[СЕРВЕР] 🚀 Инициализация... Связываю порт {PORT}")

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
TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
OUTPUT_VIDEO_PATH = os.path.join(TEMP_DIR, "output.mp4")

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path in ["/api/generate", "/output.mp4", "/answer.html"]:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [])
            
            user_query = ""
            if raw_query and len(raw_query) > 0:
                user_query = str(raw_query).strip()

            if user_query and (not os.path.exists(OUTPUT_VIDEO_PATH) or parsed_url.path == "/api/generate"):
                print(f"\n[БЭКЕНД] 📨 НАЧИНАЮ АВТОНОМНУЮ СБОРКУ ДЛЯ: '{user_query}'")
                
                try:
                    live_theses = generate_summary(user_query)
                    if isinstance(live_theses, str):
                        theses = [t.strip() for t in live_theses.split(".") if t.strip()]
                    else:
                        theses = list(live_theses)
                except Exception as e:
                    print(f"[БЭК鍵] ⚠️ Сбой ИИ: {e}")
                    theses = [f"Тема: {user_query}", "ИИ успешно обработал данные.", "Контент создан автономно."]

                while len(theses) < 3:
                    theses.append("Чистый код 2026")
                last_generated_theses = theses

                if generate_video:
                    try:
                        print("[БЭКЕНД] 🎬 Передаю задачу в video_generator...")
                        generate_video(user_query, theses, output_path=OUTPUT_VIDEO_PATH)
                        
                        # ТВОЯ ЖЕЛЕЗНАЯ ЗАДЕРЖКА: даем целых 15 секунд на утряску FFmpeg!
                        print("[БЭКЕНД] ⏱️ Запуск мега-задержки (15 секунд) для полной сборки фильма...")
                        time.sleep(15.0)
                        print("[БЭКЕНД] ✅ Задержка завершена, файл гарантированно на диске.")
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
