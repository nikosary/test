from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import os
import sys

# Импортируем нашу готовую цепочку генерации видео
try:
    from video_generator import generate_video
    from summarizer import generate_summary
    from search import search_internet
except ImportError:
    print("[Ошибка] Не найдены файлы search.py, summarizer.py или video_generator.py!")
    print("Убедитесь, что запускаете app.py прямо из папки test.")
    sys.exit(1)

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Разбираем адрес запроса
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Если пользователь отправляет форму со страницы ожидания (process.html)
        if parsed_url.path == "/process.html" or parsed_url.path == "/answer.html":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            user_query = query_params.get('query', [''])[0]
            
            if user_query:
                print(f"\n[СЕРВЕР] Получен новый поисковый запрос: '{user_query}'")
                
                # Запускаем полный цикл нашего автономного ИИ-движка!
                print("[СЕРВЕР] Шаг 1: Запуск автономного поиска...")
                raw_info = search_internet(user_query)
                
                print("[СЕРВЕР] Шаг 2: Анализ текста и создание тезисов...")
                ready_theses = generate_summary(raw_info)
                
                print("[СЕРВЕР] Шаг 3: Монтаж нового MP4 видеоролика...")
                generate_video(ready_theses, user_query)
                
                print("[СЕРВЕР] Успех! Видео перегенерировано под текущий запрос.")

        # Отдаем файлы (html, css, mp4) браузеру как обычный веб-сервер
        return super().do_GET()

def run_server():
    # Запускаем сервер на порту 8000
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, AiServiceHandler)
    print("==================================================")
    print("🚀 ИИ-МОСТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    print("Адрес локального сайта: http://localhost:8000")
    print("Чтобы остановить сервер, нажмите Ctrl + C в терминале")
    print("==================================================")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[СЕРВЕР] Работа завершена. До встречи!")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
