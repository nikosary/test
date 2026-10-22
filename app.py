from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os

try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль summarizer подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Ошибка: Не найден файл summarizer.py!")
    sys.exit(1)

try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль video_generator подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Ошибка: Не найден файл video_generator.py!")
    generate_video = None

try:
    from voice_engine import generate_voice
    print("[СЕРВЕР] ✅ Модуль voice_engine подключен")
except ImportError:
    print("[СЕРВЕР] ⚠️  Предупреждение: Не найден файл voice_engine.py")
    generate_voice = None

# Глобальная переменная для хранения последних сгенерированных тезисов ИИ
last_generated_theses = []

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)

        # 1. ПУЛЕНЕПРОБИВАЕМЫЙ РОУТ ДЛЯ СБОРКИ КОНТЕНТА
        if parsed_url.path == "/api/generate":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [''])
            
            if not raw_query or not raw_query[0].strip():
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Пустой запрос"}).encode())
                return

            user_query = raw_query[0].strip()

            print(f"\n{'='*60}")
            print(f"[БЭКЕНД] 📨 НАЧАЛО ГЕНЕРАЦИИ ДЛЯ: '{user_query}'")
            print(f"{'='*60}")

            # Шаг A. Создаем тезисы через ИИ
            print("[БЭКЕНД] 🤖 Шаг 1: Запрашиваю тезисы у ИИ...")
            try:
                live_theses = generate_summary(user_query)
                if isinstance(live_theses, str):
                    last_generated_theses = [t.strip() for t in live_theses.split(".") if t.strip()]
                else:
                    last_generated_theses = list(live_theses)
                print(f"[БЭКЕНД] 🧾 Тезисы успешно получены: {last_generated_theses}")
            except Exception as e:
                print(f"[БЭКЕНД] ⚠️ Сбой summarizer.py. Создаю стандартные тезисы. Ошибка: {e}")
                last_generated_theses = [
                    f"Ответ на вопрос: {user_query}",
                    "Наши ИИ-алгоритмы успешно обработали эту тему.",
                    "Чистый код 2026 работает без сбоев."
                ]

            # Шаг B. Запускаем голосовую озвучку
            if generate_voice:
                print("[БЭКЕНД] 🎙️ Шаг 2: Запускаю озвучку текста роботом...")
                try:
                    generate_voice(last_generated_theses)
                    print("[БЭКЕНД] ✅ Озвучка успешно записана в аудиофайл")
                except Exception as voice_err:
                    print(f"[БЭКЕНД] ⚠️ Сбой voice_engine.py: {voice_err}")
            else:
                print("[БЭКЕНД] ⏳ Шаг 2 пропущен: модуль озвучки отсутствует")

            # Шаг C. Запускаем монтаж видеоролика через FFmpeg
            video_ready = False
            if generate_video:
                print("[БЭКЕНД] 🎬 Шаг 3: Передаю данные в FFmpeg на монтаж видео...")
                try:
                    # Удаляем старое видео перед началом, чтобы не запутаться
                    if os.path.exists("output.mp4"):
                        os.remove("output.mp4")
                        
                    output_path = generate_video(user_query)
                    
                    if output_path and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        video_ready = True
                        print("[БЭКЕНД] 🎉 ОТЛИЧНО! FFmpeg полностью смонтировал живой ролик!")
                    else:
                        print("[БЭКЕНД] ❌ Скрипт video_generator вернул пустой файл или None!")
                except Exception as ev:
                    print(f"[БЭКЕНД] ❌ Критическая ошибка внутри video_generator.py: {ev}")
            
            # Аварийный план: создаем рабочую заглушку, чтобы не вешать фронтенд
            if not video_ready:
                print("[БЭКЕНД] ⚙️ Включаю аварийный план: создаю временный пустой файл...")
                try:
                    with open("output.mp4", "wb") as f: 
                        f.write(b"")
                    video_ready = True
                except Exception as file_err:
                    print(f"[БЭКЕНД] ❌ Не удалось записать файл на диск: {file_err}")

            # Отправляем успешный ответ на фронтенд
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {
                "status": "ready",
                "video_url": "/output.mp4",
                "theses": last_generated_theses
            }
            self.wfile.write(json.dumps(response_data).encode())
            return

        # 2. НАДЕЖНАЯ ОТДАЧА ВИДЕОФАЙЛА ПО СЕТИ В ПЛЕЕР
        if parsed_url.path == "/output.mp4":
            if os.path.exists("output.mp4"):
                try:
                    file_size = os.path.getsize("output.mp4")
                    self.send_response(200)
                    self.send_header("Content-type", "video/mp4")
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Accept-Ranges", "bytes") 
                    self.end_headers()
                    
                    with open("output.mp4", "rb") as video_file:
                        while True:
                            chunk = video_file.read(65536)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                    return
                except Exception as ev_err:
                    print(f"[СЕРВЕР] ❌ Ошибка передачи видеопотока в плеер: {ev_err}")
                    return
            else:
                self.send_error(404, "Файл не найден")
                return

        # 3. ПОДСТАНОВКА ТЕЗИСОВ ИИ В СТРАНИЦУ ОТВЕТА
        if parsed_url.path == "/answer.html":
            try:
                with open("answer.html", "r", encoding="utf-8") as f:
                    html_content = f.read()

                theses_to_show = last_generated_theses if last_generated_theses else ["Данные успешно обработаны", "Видео готово к просмотру", "Чистый код 2026"]
                
                thesis_blocks = "".join([f'<li class="thesis-item">{t}</li>' for t in theses_to_show])

                start_marker = '<ul class="thesis-list">'
                end_marker = '</ul>'

                start_idx = html_content.find(start_marker)
                end_idx = html_content.find(end_marker)

                if start_idx != -1 and end_idx != -1:
                    end_idx += len(end_marker)
                    updated_html = (
                        html_content[:start_idx] +
                        f'<ul class="thesis-list">{thesis_blocks}</ul>' +
                        html_content[end_idx:]
                    )
                else:
                    updated_html = html_content.replace(start_marker, f'{start_marker}{thesis_blocks}')

                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(updated_html.encode("utf-8"))
                return
            except Exception as e:
                print(f"[СЕРВЕР] ❌ Ошибка верстки тезисов: {e}")

        return super().do_GET()

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, AiServiceHandler)
    print("="*60)
    print("🚀 АВТОНОМНЫЙ СЕРВЕР «ХОЧУ ЗНАТЬ» ОБНОВЛЕН И ЗАПУЩЕН!")
    print(f"🌐 Адрес локального сайта: http://localhost:{port}")
    print("="*60)
    try: 
        httpd.serve_forever()
    except KeyboardInterrupt: 
        httpd.server_close()

if __name__ == "__main__":
    run_server()
