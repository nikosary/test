from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import os
import time

# Подключаем наш ИИ-суммаризатор
try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль summarizer подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Ошибка: Не найден файл summarizer.py!")
    sys.exit(1)

# Подключаем наш видеогенератор
try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль video_generator подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Ошибка: Не найден файл video_generator.py!")
    generate_video = None

# Подключаем наш модуль авто-озвучки
try:
    from voice_engine import generate_voice
    print("[СЕРВЕР] ✅ Модуль voice_engine подключен")
except ImportError:
    print("[СЕРВЕР] ⚠️  Предупреждение: Не найден файл voice_engine.py")
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
                    print(f"[СЕРВЕР] ✅ Видео output.mp4 успешно отдано браузеру")
                    return
                except Exception as ev_err:
                    print(f"[СЕРВЕР] ❌ Ошибка отдачи videoфайла: {ev_err}")
            else:
                print(f"[СЕРВЕР] ❌ Файл output.mp4 не найден на диске сервера!")

        # Перехватываем переход на страницу результатов
        if parsed_url.path == "/answer.html":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query = query_params.get('query', [''])
            
            # ИСПРАВЛЕНО: Надежно извлекаем чистый текст запроса из списка (массива)
            if raw_query and raw_query[0].strip():
                user_query = raw_query[0].strip()
                
                print(f"\n{'='*60}")
                print(f"[СЕРВЕР] 📨 НОВЫЙ ЗАПРОС ОТ ПОЛЬЗОВАТЕЛЯ: '{user_query}'")
                print(f"{'='*60}")

                # 1. Получаем тезисы от ИИ
                print("[СЕРВЕР] 🔍 Обращение к нейросети Google Gemini AI...")
                try:
                    live_theses = generate_summary(user_query)
                    print(f"[СЕРВЕР] ✅ Получено тезисов: {len(live_theses)}")
                    for i, thesis in enumerate(live_theses, 1):
                        print(f"   Тезис {i}: {thesis}")
                except Exception as e:
                    print(f"[СЕРВЕР] ❌ Ошибка при получении тезисов: {e}")
                    live_theses = ["Ошибка при получении ответа", "Попробуйте другой запрос", "Техническая проблема"]

                # 2. Запускаем авто-озвучку
                if generate_voice:
                    try:
                        print("[СЕРВЕР] 🎤 Отправка тезисов ИИ на озвучку роботом...")
                        generate_voice(live_theses)
                        print("[СЕРВЕР] ✅ Озвучка завершена")
                    except Exception as voice_err:
                        print(f"[СЕРВЕР] ❌ Ошибка в блоке авто-озвучки: {voice_err}")

                # 3. Запускаем генерацию видеоролика
                print("[СЕРВЕР] 🎬 Запуск видеогенератора для создания output.mp4...")
                if generate_video:
                    try:
                        # Передаем строго чистый отформатированный текст (строку)
                        result = generate_video(user_query)
                        if result:
                            print(f"[СЕРВЕР] ✅ Видео успешно создано: {result}")
                        else:
                            print("[СЕРВЕР] ❌ Видеогенератор вернул None (ошибка генерации)")
                    except Exception as ev:
                        print(f"[СЕРВЕР] ❌ Ошибка генерации видео: {ev}")
                else:
                    print("[СЕРВЕР] ⚠️  Видеогенератор недоступен, создаю пустой файл...")
                    with open("output.mp4", "wb") as f:
                        f.write(b"")

                # ИСПРАВЛЕНО: Даем серверу Render честные 12 секунд, чтобы FFmpeg успел смонтировать и закрыть файл
                print("[СЕРВЕР] ⏳ Ожидание завершения записи файла на диск хостинга...")
                time.sleep(12)
                print("[СЕРВЕР] ✅ Видео готово к отдаче!")

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
                    print(f"[СЕРВЕР] ✅ Страница answer.html отправлена пользователю")
                    return
                except Exception as e:
                    print(f"[СЕРВЕР] ❌ Ошибка подмены контента: {e}")

        return super().do_GET()

def run_server():
    port = int(os.environ.get("PORT", 8000))
    server_address = ('', port)

    httpd = HTTPServer(server_address, AiServiceHandler)
    print("="*60)
    print("🚀 ИИ-МОСТ ОБНОВЛЕН И ПОДСТРОЕН ПОД РЕНДЕР!")
    print(f"🌐 Сервер запущен на порту: {port}")
    print("="*60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[СЕРВЕР] Сервер остановлен.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
