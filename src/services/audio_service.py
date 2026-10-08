import sys
import os
import shutil
import tempfile
from pathlib import Path
from pydub import AudioSegment


def get_ffmpeg_path() -> str:
    """
    Возвращает путь к FFmpeg:
    - Если запущено из скомпилированного .exe (Windows), ищет в упакованных ресурсах.
    - Если запущено в режиме разработки (Mac/Win), полагается на системный ffmpeg.
    """
    if getattr(sys, 'frozen', False):
        # Режим PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        ffmpeg_exe = bundle_dir / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            return str(ffmpeg_exe)
    
    # Режим разработки
    return "ffmpeg"


# Указываем pydub точный путь к ffmpeg
AudioSegment.converter = get_ffmpeg_path()


class AudioService:
    def __init__(self):
        # Используем безопасную системную временную папку ОС
        self.temp_dir = Path(tempfile.gettempdir()) / "audio_summarizer_chunks"

    def prepare_audio(self, input_file_path: str, chunk_duration_min: int = 5) -> list[str]:
        """
        Принимает путь к аудиофайлу, нарезает его на кусочки
        и сохраняет во временную папку.
        """
        input_path = Path(input_file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {input_file_path}")

        self.cleanup_temp_dir()
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"🔄 Загрузка аудиофайла: {input_path.name}...")
        audio = AudioSegment.from_file(str(input_path))
        audio = audio.set_channels(1)  # моно

        chunk_length_ms = chunk_duration_min * 60 * 1000
        total_duration_ms = len(audio)
        chunk_paths = []

        print(f"⏱ Общая длительность: {total_duration_ms // 1000} сек. Нарезка...")

        chunk_index = 0
        for start_ms in range(0, total_duration_ms, chunk_length_ms):
            end_ms = min(start_ms + chunk_length_ms, total_duration_ms)
            chunk = audio[start_ms:end_ms]

            chunk_filename = self.temp_dir / f"chunk_{chunk_index:03d}.mp3"
            chunk.export(
                str(chunk_filename),
                format="mp3",
                bitrate="64k",
                parameters=["-ar", "16000"]
            )

            chunk_paths.append(str(chunk_filename))
            chunk_index += 1

        return chunk_paths

    def cleanup_temp_dir(self):
        """Гарантированно удаляет временную папку"""
        if self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                print("🧹 Временные аудиофайлы удалены.")
            except Exception as e:
                print(f"⚠️ Предупреждение при очистке: {e}")