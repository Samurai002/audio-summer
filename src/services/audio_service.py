import os
import shutil
from pathlib import Path
from pydub import AudioSegment


class AudioService:
    def __init__(self, temp_dir: str = "temp_chunks"):
        self.temp_dir = Path(temp_dir)

    def prepare_audio(self, input_file_path: str, chunk_duration_min: int = 10) -> list[str]:
        """
        Принимает путь к аудиофайлу, нарезает его на кусочки
        и сохраняет во временную папку в формате легкого mp3.
        Возвращает список путей к созданным чанкам.
        """
        input_path = Path(input_file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {input_file_path}")

        # Создаем чистую временную папку
        self.cleanup_temp_dir()
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"🔄 Загрузка аудиофайла: {input_path.name}...")
        # pydub сам определит формат файла через ffmpeg
        audio = AudioSegment.from_file(str(input_path))

        # Приводим к моно (1 канал) для уменьшения веса
        audio = audio.set_channels(1)

        chunk_length_ms = chunk_duration_min * 60 * 1000
        total_duration_ms = len(audio)
        chunk_paths = []

        print(f"⏱ Общая длительность: {total_duration_ms // 1000} сек. Нарезка на части по {chunk_duration_min} мин...")

        # Нарезка
        chunk_index = 0
        for start_ms in range(0, total_duration_ms, chunk_length_ms):
            end_ms = min(start_ms + chunk_length_ms, total_duration_ms)
            chunk = audio[start_ms:end_ms]

            chunk_filename = self.temp_dir / f"chunk_{chunk_index:03d}.mp3"
            
            # Экспортируем в легкий mp3 с низким битрейтом
            chunk.export(
                str(chunk_filename),
                format="mp3",
                bitrate="64k",
                parameters=["-ar", "16000"]  # 16 kHz частота дискретизации идеальна для Whisper
            )
            
            chunk_paths.append(str(chunk_filename))
            print(f"  ✅ Создан чанк: {chunk_filename.name} ({(end_ms - start_ms) // 1000} сек)")
            chunk_index += 1

        return chunk_paths

    def cleanup_temp_dir(self):
        """Удаляет временную папку со всеми чанками"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print("🧹 Временные файлы удалены.")