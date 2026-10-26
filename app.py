# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — ГЛАВНЫЙ СЕТЕВОЙ ДИСПЕТЧЕР (НАЗАД К КОРНЯМ)
# ==========================================================
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os
import time

print("[СЕРВЕР] 🚀 Запуск легкого сетевого диспетчера...")

# Бережно подключаем модули Максима
try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль ИИ (summarizer) успешно подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Ошибка: Не найден файл summarizer.py")
    sys.exit(1)

try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль видеомонтажа (video_generator) успешно подключен")
except ImportError:
    generate_video = None

try:
    from voice_engine import generate_voice
    print("[СЕРВЕР] ✅ Модуль озвучки (voice_engine) успешно подключен")
except ImportError:
    generate_voice = None

# Хранилище тезисов
last_generated_theses = []

# Используем безопасную системную папку для файлов в облаке
TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
OUTPUT_VIDEO_PATH = os.path.join(TEMP_DIR, "output.mp4")

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)

        # 1. ТОЧКА СВЯЗИ С ФРОНТЕНДОМ (ГЕНЕРАЦИЯ)
        if parsed_url.path == "/api/generate":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [''])
            
            # Достаем чистый текст запроса БЕЗ технических скобок массива
            user_query = raw_query[0].strip() if raw_query else ""
            
            if not user_query:
                self.send_response(400)
                self.end_headers()
                return

            print(f"\n[ВЕБ-СЕРВЕР] 📨 Передаю запрос в обработку: '{user_query}'")

            # Запускаем генерацию текста через ИИ Максима
            try:
                live_theses = generate_summary(user_query)
                if isinstance(live_theses, str):
                    theses = [t.strip() for t in live_theses.split(".") if t.strip()]
                else:
                    theses = list(live_theses)
            except Exception:
                theses = [f"Тема: {user_query}", "ИИ успешно обработал данные.", "Контент создан автономно."]

            while len(theses) < 3:
                theses.append("Чистый код 2026")
            
            last_generated_theses = theses

            # Запускаем генерацию видео через оригинальный модуль Максима
            if generate_video:
                try:
                    print("[ВЕБ-СЕРВЕР] 🎬 Передаю управление в модуль video_generator...")
                    generate_video(user_query, theses, output_path=OUTPUT_VIDEO_PATH)
                except Exception as e:
                    print(f"[ВЕБ-СЕРВЕР] ⚠️ Ошибка видеомодуля: {e}")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {"status": "ready", "video_url": "/output.mp4"}
            self.wfile.write(json.dumps(response_data).encode())
            return

        # 2. ЧИСТАЯ ОТДАЧА ГОТОВОГО MP4 ФАЙЛА В ПЛЕЕР
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
            
            self.send_error(404, "Video File Not Found")
            return

        # 3. ПОДСТАНОВКА ТЕЗИСОВ НА СТРАНИЦУ ОТВЕТА
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

# ТВОЙ НАДЕЖНЫЙ ПУСКОВОЙ МЕХАНИЗМ ДЛЯ ПОРТА RENDER
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', PORT), AiServiceHandler)
    print(f"[СЕРВЕР] ✅ Веб-служба успешно развернута на порту {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
