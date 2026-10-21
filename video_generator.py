import subprocess
import os
import sys

def generate_video(query_text, audio_file="audio.mp3", output_video="output.mp4"):
    print("[ИИ Видео] Запуск динамического монтажа с авто-генерацией цветных фонов...")
    
    # Умная проверка путей FFmpeg
    if sys.platform.startswith("win"):
        ffmpeg_path = os.path.abspath("ffmpeg.exe")
        if not os.path.exists(ffmpeg_path):
            print("[Ошибка] Файл ffmpeg.exe не найден!")
            return None
    else:
        ffmpeg_path = "ffmpeg"

    # Жестко удаляем старое видео
    if os.path.exists(output_video):
        try: os.remove(output_video)
        except Exception: pass

    print("[ИИ Видео] Настройка генераторов цвета и бегущих строк...")
    
    # Магия FFmpeg: Мы создаем 3 разных виртуальных фона без использования физических картинок!
    # 1-й фон: Темно-зеленый (Эко-стиль проекта) на первые 7 секунд
    # 2-й фон: Приглушенный синий на следующие 7 секунд
    # 3-й фон: Серый графитовый на финальные 7 секунд
    command = [
        ffmpeg_path, "-y",
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1e3d1a:s=854x480:r=10", # Зеленый (0-7 сек)
        "-f", "lavfi", "-t", "7", "-i", "color=c=#1a2a3d:s=854x480:r=10", # Синий (7-14 сек)
        "-f", "lavfi", "-t", "7", "-i", "color=c=#2d2d2d:s=854x480:r=10", # Серый (14-21 сек)
        "-i", audio_file,                                                 # Наш ИИ-голос
        
        # Фильтр склейки фонов и наложения крупного белого текста по центру экрана
        "-filter_complex", 
        "[0:v][1:v][2:v] concat=n=3:v=1:a=0 [v_init];"
        "[v_init] drawtext=text='CHISTYI KOD 2026 . CLOUD FINAL':fontcolor=white:fontsize=42:"
        "x=(w-text_w)/2:y=(h-text_h)/2:borderw=4:bordercolor=black [v_final]",
        
        "-map", "[v_final]",                  # Забираем готовое смонтированное видео со сменой цветов
        "-map", "3:a",                        # Забираем звук из аудиофайла
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",                          # Обрезаем ролик строго по длине звука
        output_video
    ]

    try:
        # Запускаем автоматический монтаж фильма в облаке
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) // 1024
            print(f"[ИИ Видео] Успех! Цветной ИИ-фильм смонтирован: {os.path.abspath(output_video)}")
            return output_video
        else:
            print("[Ошибка] Фильм не создался.")
            return None
    except Exception as e:
        print(f"[Ошибка монтажа цветного видео]: {e}")
        return None

if __name__ == "__main__":
    print("=== ГЕНЕРАЛЬНЫЙ ТЕСТ ЦВЕТНОГО КИНОТЕАТРА ===")
    generate_video("Тест")
