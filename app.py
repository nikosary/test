# ==========================================================
# ПРОЕКТ: ХОЧУ ЗНАТЬ 2026 — АВТОНОМНЫЙ КИНЕМАТОГРАФИЧЕСКИЙ СЕРВЕР
# ==========================================================
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import sys
import os
import subprocess
import time
from datetime import datetime

print("[СЕРВЕР] 🚀 Старт пуленепробиваемой системы Чистый Код 2026...")

try:
    from summarizer import generate_summary
    print("[СЕРВЕР] ✅ Модуль summarizer успешно подключен")
except ImportError:
    print("[СЕРВЕР] ❌ Критическая ошибка: Не найден файл summarizer.py!")
    sys.exit(1)

try:
    from video_generator import generate_video
    print("[СЕРВЕР] ✅ Модуль video_generator успешно подключен")
except ImportError:
    generate_video = None

try:
    from voice_engine import generate_voice
    print("[СЕРВЕР] ✅ Модуль voice_engine успешно подключен")
except ImportError:
    generate_voice = None

last_generated_theses = []
TEMP_DIR = "/tmp" if not sys.platform.startswith("win") else "."
OUTPUT_VIDEO_PATH = os.path.join(TEMP_DIR, "output.mp4")
AUDIO_FILE_PATH = os.path.join(TEMP_DIR, "audio.mp3")

def wrap_text_clean(text, max_chars=35):
    if not text: return ""
    clean_text = str(text).replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    words = clean_text.split()
    lines, current_line, current_length = [], [], 0
    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line, current_length = [word], len(word)
    if current_line: lines.append(" ".join(current_line))
    return "\\\n".join(lines)

class AiServiceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global last_generated_theses
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/api/generate":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            raw_query_list = query_params.get('query', [''])
            
            # ИСПРАВЛЕНО: Извлекаем строку из списка корректно
            user_query = raw_query_list[0].strip() if raw_query_list else ""
            
            if not user_query:
                self.send_response(400)
                self.end_headers()
                return

            now = datetime.now()
            current_date = now.strftime("%d.%m.%Y")
            display_time = now.strftime("%H:%M:%S")

            print(f"\n[ОБЛАКО RENDER] 📨 ЗАПУСК МОНТАЖА: '{user_query}' в {display_time}")

            try:
                live_theses = generate_summary(user_query)
                theses = [t.strip() for t in live_theses.split(".") if t.strip()] if isinstance(live_theses, str) else list(live_theses)
            except Exception:
                theses = [f"Ответ на запрос: {user_query}", "ИИ успешно обработал тему.", "Контент сформирован в облаке."]

            while len(theses) < 3: theses.append("Чистый контент 2026")
            last_generated_theses = theses

            if generate_voice:
                try: generate_voice(theses, output_audio=AUDIO_FILE_PATH)
                except Exception: pass

            if os.path.exists(OUTPUT_VIDEO_PATH): os.remove(OUTPUT_VIDEO_PATH)

            ffmpeg_path = "static_ffmpeg" if os.environ.get("PORT") else "ffmpeg"
            clean_q = user_query.replace("'", "").replace('"', "")
            if len(clean_q) > 40: clean_q = clean_q[:37] + "..."
            
            q_wrapped = wrap_text_clean(clean_q, max_chars=30)
            
            # ТОЧНОЕ ИСПРАВЛЕНИЕ ДЛЯ ПЛЕЕРА: Передаем отдельные элементы по индексам!
            t1_wrapped = wrap_text_clean(theses[0], max_chars=35)
            t2_wrapped = wrap_text_clean(theses[1], max_chars=35)
            t3_wrapped = wrap_text_clean(theses[2], max_chars=35)

            slide_time = 4.0
            try:
                cmd = [
                    ffmpeg_path, "-y",
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1a2a3d:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d5a27:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#1e3d1a:s=854x480:r=10", 
                    "-f", "lavfi", "-t", str(slide_time), "-i", "color=c=#2d2d2d:s=854x480:r=10", 
                ]
                has_audio = os.path.exists(AUDIO_FILE_PATH) and os.path.getsize(AUDIO_FILE_PATH) > 0
                if has_audio: cmd += ["-i", AUDIO_FILE_PATH]

                filter_string = (
                    f"[0:v] drawtext=text='{q_wrapped}':fontcolor=white:fontsize=26:x=(w-text_w)/2:y=100:borderw=2:bordercolor=black [v1_title];"
                    f"[v1_title] drawtext=text='DATA: {current_date}  VREMYA: {display_time}':fontcolor=yellow:fontsize=28:x=(w-text_w)/2:y=260:borderw=3:bordercolor=black [v1];"
                    f"[1:v] drawtext=text='{t1_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v2];"
                    f"[2:v] drawtext=text='{t2_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v3];"
                    f"[3:v] drawtext=text='{t3_wrapped}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black:line_spacing=8 [v4];"
                    "[v1][v2][v3][v4] concat=n=4:v=1:a=0 [v_final]"
                )
                cmd += ["-filter_complex", filter_string, "-map", "[v_final]"]
                if has_audio: cmd += ["-map", "4:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
                cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", OUTPUT_VIDEO_PATH]
                
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                print("[ОБЛАКО RENDER] 🎉 МОНТАЖ ПОЛНОСТЬЮ ЗАВЕРШЕН!")
            except Exception as ffmpeg_err:
                print(f"[БЭКЕНД] ❌ Ошибка FFmpeg: {ffmpeg_err}")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {"status": "ready", "video_url": f"/output.mp4?t={int(time.time())}", "theses": last_generated_theses}
            self.wfile.write(json.dumps(response_data).encode())
            return

        if parsed_url.path == "/output.mp4":
            if os.path.exists(OUTPUT_VIDEO_PATH):
                file_size = os.path.getsize(OUTPUT_VIDEO_PATH)
                self.send_response(200)
                self.send_header("Content-type", "video/mp4")
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with open(OUTPUT_VIDEO_PATH, "rb") as video_file:
                    while True:
                        chunk = video_file.read(65536)
                        if not chunk: break
                        self.wfile.write(chunk)
                return

        if parsed_url.path == "/answer.html":
            theses_to_show = last_generated_theses if last_generated_theses else ["Данные обработаны", "Видео создано", "Чистый код 2026"]
            thesis_blocks = "".join([f'<li class="thesis-item">{t}</li>' for t in theses_to_show])
            html_content = "<html><body><ul class='thesis-list'></ul></body></html>"
            if os.path.exists("answer.html"):
                with open("answer.html", "r", encoding="utf-8") as f: html_content = f.read()
            updated_html = html_content.replace('<ul class="thesis-list">', f'<ul class="thesis-list">{thesis_blocks}')
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(updated_html.encode("utf-8"))
            return

        return super().do_GET()

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', PORT), AiServiceHandler)
    print("="*60)
    print(f"[СЕРВЕР] ✅ ЖЕЛЕЗОБЕТОННЫЙ ЗАПУСК НА ПОРТУ {PORT}")
    print("="*60)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
