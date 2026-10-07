import gc
import shutil
from pathlib import Path
from faster_whisper import WhisperModel


class TranscriptionService:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        
        # Задаем изолированную папку для кэша в домашней директории пользователя
        # (будет работать одинаково и на macOS, и на Windows)
        self.cache_dir = Path.home() / ".audio_summarizer_cache" / "whisper"
        self.model = None

    def load_model(self):
        """Загружает модель в память (если еще не загружена)"""
        if self.model is None:
            print(f"🧠 Загрузка модели Whisper ({self.model_size})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(self.cache_dir)  # сохраняем именно в нашу папку
            )
            print("✅ Модель загружена!")

    def transcribe_chunks(self, chunk_paths: list[str], language: str = "ru") -> str:
        """Расшифровывает чанки и склеивает текст"""
        # Убедимся, что модель инициализирована
        self.load_model()

        full_transcript = []
        total_chunks = len(chunk_paths)

        print(f"\n🎙 Начинаем транскрибацию ({total_chunks} чанков)...")

        for index, chunk_path in enumerate(chunk_paths, start=1):
            path = Path(chunk_path)
            print(f"  [{index}/{total_chunks}] Обработка {path.name}...")

            segments, _ = self.model.transcribe(
                str(path),
                language=language,
                beam_size=5,
                vad_filter=True
            )

            chunk_text = " ".join([segment.text.strip() for segment in segments])
            full_transcript.append(chunk_text)

        result_text = "\n\n".join(full_transcript)
        print("✅ Расшифровка завершена!")
        return result_text

    def delete_cached_model(self) -> bool:
        """
        Выгружает модель из RAM и удаляет скачанные файлы с диска.
        Возвращает True в случае успеха.
        """
        print("🧹 Очистка следов и удаление модели...")
        
        # 1. Выгружаем из оперативной памяти (критично для Windows)
        if self.model is not None:
            del self.model
            self.model = None
            gc.collect()

        # 2. Удаляем папку с весами модели с диска
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            print("✅ Файлы модели успешно удалены с диска.")
            return True
        else:
            print("ℹ️ Кэш модели уже был пуст.")
            return False

    def is_model_cached(self) -> bool:
        """Проверяет, скачана ли модель сейчас на диске (для UI)"""
        return self.cache_dir.exists() and any(self.cache_dir.iterdir())