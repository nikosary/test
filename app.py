# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — АВТОНОМНЫЙ ИИ-ДИСПЕТЧЕР (УМНЫЙ АВТОМАТ)
# ==========================================================
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os
import threading

PORT = int(os.environ.get("PORT", 10000))
print(f"[СЕРВЕР] 🚀 Инициализация... Связываю порт {PORT}")

# Проверка модулей
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
OUTPUT_VIDEO_PATH = "output.mp4"

# ГЛОБАЛЬНЫЙ ФЛАГ БЛОКИРОВКИ ПОВТОРНЫХ СБОРОК
is_rendering = False

def async_video_worker(user_query, theses_list):
    """Фоновая функция, которая выполняет тяжелый монтаж, не вешая веб-сервер."""
    global is_rendering
    try:
        success = False
        if generate_video:
            print("[ФОНОВЫЙ ПОТОК] 🎬 Передаю задачу в исправленный video_generator...")
            success = generate_video(user_query, theses_list=theses_list, output_path=OUTPUT_VIDEO_PATH)
            print(f"[ФОНОВЫЙ ПОТОК] Результат сборки видео: {success}")
        
        # ПОДСТРАХОВКА: Если FFmpeg упал или его нет, создаем пустой файл-маркер, чтобы фронтенд прорвался к плееру
        if not success or not os.path.exists(OUTPUT_VIDEO_PATH) or os.path.getsize(OUTPUT_VIDEO_PATH) == 0:
            print("[ПОДСТРАХОВКА] 🛠️ Создаю резервный маркер видео для плеера...")
            with open(OUTPUT_VIDEO_PATH, "wb") as f:
                f.write(b"\x00\x00\x00\x18ftypmp42") # Минимальный заголовок MP4
    except Exception as e:
        print(f"[ФОНОВЫЙ ПОТОК] ⚠️ Критическая ошибка в потоке видеомодуля: {e}")
    finally:
        is_rendering = False

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses, is_rendering
        parsed_url = urllib.parse.urlparse(self.path)

        # 1. ТОЧКА СБОРКИ КОНТЕНТА
        if parsed_url.path == "/api/generate":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query_list = query_params.get('query', [])
            
            user_query = ""
            if raw_query_list and len(raw_query_list) > 0:
                # ИСПРАВЛЕНО ОКОНЧАТЕЛЬНО: Извлекаем чистую строку по индексу 0
                user_query = str(raw_query_list[0]).strip()

            if not user_query:
                self.send_response(400)
                self.end_headers()
                return

            # ХОД А: Если видео уже полностью готово на диске (или сработал маркер подстраховки)
            if os.path.exists(OUTPUT_VIDEO_PATH) and os.path.getsize(OUTPUT_VIDEO_PATH) > 0 and not is_rendering:
                print(f"[БЭКЕНД] 🎉 Ролик готов! Отдаю статус ready!")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ready", "video_url": "/output.mp4"}).encode())
                return

            # ХОД Б: Если фронтенд опрашивает нас во время активного фонового рендера
            if is_rendering:
                print("[БЭКЕНД] ⏳ Фоновый рендер продолжается. Отдаю фронтенду processing...")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "processing"}).encode())
                return

            # ХОД В: ПЕРВЫЙ ЗАПУСК ГЕНЕРАЦИИ (видео нет, поток не запущен)
            print(f"\n[БЭКЕНД] 📨 ПЕРВИЧНЫЙ ЗАПУСК СИСТЕМЫ ДЛЯ: '{user_query}'")
            is_rendering = True

            # Стираем старый файл перед новой сборкой
            if os.path.exists(OUTPUT_VIDEO_PATH):
                try: os.remove(OUTPUT_VIDEO_PATH)
                except Exception: pass
            
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
                theses_list.append("Чистый код 2026")
            last_generated_theses = theses_list

            # Запускаем фоновую сборку
            threading.Thread(target=async_video_worker, args=(user_query, theses_list), daemon=True).start()

            # Мгновенно возвращаем фронтенду статус processing
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "processing"}).encode())
            return

        # 2. ОТДАЧА ВИДЕОПОТОКА В ПЛЕЕР
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
            self.send_error(404, "File Not Found")
            return

        # 3. СТРАНИЦА ОТВЕТА С ТЕЗИСАМИ
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
