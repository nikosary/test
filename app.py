from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import os

# Подключаем наш ИИ-суммаризатор
try:
    from summarizer import generate_summary
except ImportError:
    print("[Ошибка] Не найден файл summarizer.py!")
    sys.exit(1)

# ПОДКЛЮЧАЕМ НАШ ВИДЕОГЕНЕРАТОР
try:
    from video_generator import generate_video  # Предполагаем, что функция там называется так
except ImportError:
    # Если функция называется иначе, сервер создаст пустой файл, чтобы плеер не выдавал 404
    generate_video = None

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Перехватываем переход на страницу результатов
        if parsed_url.path == "/answer.html":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            user_query = query_params.get('query', [''])[0]
            
            if user_query:
                print(f"\n[СЕРВЕР] Запрос от пользователя: '{user_query}'")
                print("[СЕРВЕР] Обращение к нейросети Google Gemini AI...")
                
                # 1. Получаем тезисы от ИИ
                live_theses = generate_summary(user_query)
                print(f"[СЕРВЕР] Получено тезисов: {len(live_theses)}")
                
                # 2. ЗАПУСКАЕМ ГЕНЕРАЦИЮ ВИДЕОРОЛИКА!
                print("[СЕРВЕР] Запуск видеогенератора для создания output.mp4...")
                if generate_video:
                    try:
                        # Передаем запрос или тезисы в твой генератор видео
                        generate_video(user_query) 
                        print("[СЕРВЕР] Видео output.mp4 успешно сгенерировано!")
                    except Exception as ev:
                        print(f"[Ошибка генерации видео]: {ev}")
                else:
                    # Если генератор не импортировался, создаем временную «заглушку»
                    with open("output.mp4", "wb") as f:
                        f.write(b"")
                
                # 3. Читаем оригинальный файл answer.html и подставляем тезисы
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
