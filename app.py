from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import json

# Подключаем наш ИИ-суммаризатор
try:
    from summarizer import generate_summary
except ImportError:
    print("[Ошибка] Не найден файл summarizer.py!")
    sys.exit(1)

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
                
                # Получаем НАСТОЯЩИЕ тезисы прямо от живого ИИ!
                live_theses = generate_summary(user_query)
                print(f"[СЕРВЕР] Получено тезисов: {len(live_theses)}")
                
                # Читаем оригинальный файл answer.html
                try:
                    with open("answer.html", "r", encoding="utf-8") as f:
                        html_content = f.read()
                    
                    # Магия: на лету заменяем демонстрационный текст в HTML на ответы ИИ!
                    thesis_blocks = "".join([f'<li class="thesis-item">{t}</li>' for t in live_theses])
                    
                    # Вживляем новые тезисы в структуру страницы
                    updated_html = html_content.replace(
                        '<ul class="thesis-list">', 
                        f'<ul class="thesis-list">{thesis_blocks}<!--'
                    ).replace(
                        '</ul>',
                        '--></ul>'
                    )
                    
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
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, AiServiceHandler)
    print("==================================================")
    print("🚀 ИИ-МОСТ ОБНОВЛЕН И ГОТОВ К ТЕСТУ GEMINI AI!")
    print("Адрес локального сайта: http://localhost:8000")
    print("==================================================")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[СЕРВЕР] Сервер остановлен.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
