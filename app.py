from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import os
import time  # Добавили для фиксации задержки монтажа

# Подключаем наш ИИ-суммаризатор
try:
    from summarizer import generate_summary
except ImportError:
    print("[Ошибка] Не найден файл summarizer.py!")
    sys.exit(1)

# Подключаем наш видеогенератор
try:
    from video_generator import generate_video
except ImportError:
    generate_video = None

# Подключаем наш модуль авто-озвучки
try:
    from voice_engine import generate_voice
except ImportError:
    generate_voice = None

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Если браузер запрашивает само видео output.mp4
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
                    print(f"[Ошибка отдачи видеофайла]: {ev_err}")
            else:
                print("[Ошибка] Файл output.mp4 не найден на диске сервера!")
        
        # Перехватываем переход на страницу результатов
        if parsed_url.path == "/answer.html":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            user_query = query_params.get('query', [''])
            
            if user_query:
                print(f"\n[СЕРВЕР] Запрос от пользователя: '{user_query}'")
                
                # 1. Получаем тезисы от ИИ
                print("[СЕРВЕР] Обращение к нейросети Google Gemini AI...")
                live_theses = generate_summary(user_query)
                print(f"[СЕРВЕР] Получено тезисов: {len(live_theses)}")
                
                # 2. Запускаем авто-озвучку
                if generate_voice:
                    try:
                        print("[СЕРВЕР] Отправка тезисов ИИ на озвучку роботом...")
                        generate_voice(live_theses)
                    except Exception as voice_err:
                        print(f"[Ошибка в блоке авто-озвучки]: {voice_err}")
                
                # 3. Запускаем генерацию видеоролика
                print("[СЕРВЕР] Запуск видеогенератора для создания output.mp4...")
                if generate_video:
                    try:
                        generate_video(user_query) 
                        print("[СЕРВЕР] Ожидание финальной записи видеофайла на диск...")
                        # Даем серверу честные 4 секунды на то, чтобы FFmpeg успел закрыть файл
                        time.sleep(4)
                        print("[СЕРВЕР] Видео успешно сохранено и готово к отдаче!")
                    except Exception as ev:
                        print(f"[Ошибка генерации видео]: {ev}")
                else:
                    with open("output.mp4", "wb") as f:
                        f.write(b"")
                
                # 4. Читаем оригинальный файл answer.html и подставляем тезисы
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
                    
                    # Отправляем обновленную страницу в браузер
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(updated_html.encode("utf-8"))
                    return
                except Exception as e:
                    print(f"[Ошибка подмены контента]: {e}")

        return super().do_GET()

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server_address = ('', port)
    
    httpd = HTTPServer(server_address, AiServiceHandler)
    print("==================================================")
    print("🚀 ИИ-МОСТ ОБНОВЛЕН И ПОДСТРОЕН ПОД РЕНДЕР!")
    print(f"Сервер запущен на порту: {port}")
    print("==================================================")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[СЕРВЕР] Сервер остановлен.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
