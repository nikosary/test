from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
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

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/output.mp4":
            if os.path.exists("output.mp4"):
                try:
                    self.send_response(200)
                    self.send_header("Content-type", "video/mp4")
                    self.send_header("Content-Length", str(os.path.getsize("output.mp4")))
                    self.end_headers()
                    with open("output.mp4", "rb") as video_file:
                        self.wfile.write(video_file.read())
                    return
                except Exception as ev_err:
                    print(f"[СЕРВЕР] ❌ Ошибка отдачи видео: {ev_err}")
            else:
                print(f"[СЕРВЕР] ❌ Файл output.mp4 не найден на диске!")

        if parsed_url.path == "/answer.html":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [''])
            
            # СТРОГО: Извлекаем чистый текст из списка, чтобы не сломать FFmpeg
            if raw_query:
                user_query = raw_query[0].strip()
                
                print(f"\n{'='*60}")
                print(f"[СЕРВЕР] 📨 НОВЫЙ ЗАПРОС ОТ ПОЛЬЗОВАТЕЛЯ: '{user_query}'")
                print(f"{'='*60}")

                # 1. Тезисы ИИ
                try:
                    live_theses = generate_summary(user_query)
                except Exception as e:
                    print(f"[СЕРВЕР] ❌ Ошибка ИИ: {e}")
                    live_theses = ["Ошибка получения тезисов", "Попробуйте позже", "Технический сбой"]

                # 2. Озвучка роботом
                if generate_voice:
                    try:
                        generate_voice(live_theses)
                    except Exception as voice_err:
                        print(f"[СЕРВЕР] ❌ Ошибка авто-озвучки: {voice_err}")

                # 3. Видеомонтаж (FFmpeg запустится в фоновом режиме, пока крутится процесс загрузки)
                if generate_video:
                    try:
                        generate_video(user_query)
                    except Exception as ev:
                        print(f"[СЕРВЕР] ❌ Ошибка генерации видео: {ev}")
                else:
                    with open("output.mp4", "wb") as f: f.write(b"")

                # 4. Подмена контента на странице ответа
                try:
                    with open("answer.html", "r", encoding="utf-8") as f:
                        html_content = f.read()

                    thesis_blocks = "".join([f'<li class="thesis-item">{t}</li>' for t in live_theses])

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
                    print(f"[СЕРВЕР] ❌ Ошибка верстки: {e}")

        return super().do_GET()

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, AiServiceHandler)
    print("="*60)
    print("🚀 ИИ-МОСТ ПЕРЕНЕСЕН В ПАПКУ TEST И ГОТОВ К СБОРКЕ!")
    print(f"🌐 Сервер запущен на порту: {port}")
    print("="*60)
    try: httpd.serve_forever()
    except KeyboardInterrupt: httpd.server_close()

if __name__ == "__main__":
    run_server()
