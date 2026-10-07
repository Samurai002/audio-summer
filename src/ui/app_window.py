import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.services.audio_service import AudioService
from src.services.transcription_service import TranscriptionService
from src.services.summary_service import SummaryService


# Настройка внешнего вида (современная темная тема)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Audio Summarizer")
        self.geometry("780x680")
        self.minsize(650, 550)

        # Сервисы
        self.audio_service = AudioService()
        self.transcription_service = TranscriptionService(model_size="small")
        self.summary_service = SummaryService()

        self.selected_file_path = None

        # Сборка интерфейса
        self._create_widgets()

    def _create_widgets(self):
        # 1. Верхняя панель: Заголовок
        self.header_label = ctk.CTkLabel(
            self, text="🎙 Аудио Саммаризатор", font=ctk.CTkFont(size=22, weight="bold")
        )
        self.header_label.pack(pady=(15, 10))

        # 2. Фрейм выбора файла
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(fill="x", padx=20, pady=5)

        self.btn_select_file = ctk.CTkButton(
            self.file_frame, text="📁 Выбрать аудио", command=self._select_file, width=140
        )
        self.btn_select_file.pack(side="left", padx=10, pady=10)

        self.lbl_file_name = ctk.CTkLabel(
            self.file_frame, text="Файл не выбран", text_color="gray", anchor="w"
        )
        self.lbl_file_name.pack(side="left", fill="x", expand=True, padx=10)

        # 3. Кнопка запуска
        self.btn_start = ctk.CTkButton(
            self,
            text="🚀 Начать обработку",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_processing_thread,
            state="disabled",
            height=40
        )
        self.btn_start.pack(fill="x", padx=20, pady=10)

        # 4. Статус процесса
        self.lbl_status = ctk.CTkLabel(
            self, text="Готов к работе", font=ctk.CTkFont(size=13, slant="italic")
        )
        self.lbl_status.pack(pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))

        # 5. Вкладки с результатами
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)

        self.tab_summary = self.tabview.add("📌 Краткий пересказ")
        self.tab_transcript = self.tabview.add("📝 Полный текст")

        # Текстовые поля
        self.txt_summary = ctk.CTkTextbox(self.tab_summary, wrap="word", font=ctk.CTkFont(size=14))
        self.txt_summary.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_transcript = ctk.CTkTextbox(self.tab_transcript, wrap="word", font=ctk.CTkFont(size=13))
        self.txt_transcript.pack(fill="both", expand=True, padx=5, pady=5)

        # 6. Нижняя панель действий
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(fill="x", padx=20, pady=10)

        self.btn_copy = ctk.CTkButton(
            self.bottom_frame, text="📋 Скопировать пересказ", command=self._copy_to_clipboard, width=170
        )
        self.btn_copy.pack(side="left")

        self.btn_clear_cache = ctk.CTkButton(
            self.bottom_frame,
            text="🧹 Очистить кэш модели (~450MB)",
            fg_color="#8B0000",
            hover_color="#5B0000",
            command=self._clear_cache,
            width=210
        )
        self.btn_clear_cache.pack(side="right")

    def _select_file(self):
        filetypes = [
            ("Аудиофайлы", "*.mp3 *.ogg *.wav *.m4a *.aac *.flac *.wma"),
            ("Все файлы", "*.*")
        ]
        path = filedialog.askopenfilename(title="Выберите аудиофайл", filetypes=filetypes)
        if path:
            self.selected_file_path = path
            self.lbl_file_name.configure(text=Path(path).name, text_color="white")
            self.btn_start.configure(state="normal")
            self._set_status("Файл выбран. Нажмите «Начать обработку».", 0)

    def _set_status(self, text: str, progress: float):
        self.lbl_status.configure(text=text)
        self.progress_bar.set(progress)
        self.update_idletasks()

    def _start_processing_thread(self):
        # Запускаем в отдельном потоке, чтобы окно программы не висло
        thread = threading.Thread(target=self._process_pipeline, daemon=True)
        thread.start()

    def _process_pipeline(self):
        self.btn_start.configure(state="disabled")
        self.btn_select_file.configure(state="disabled")

        try:
            # Шаг 1: Нарезка и сжатие
            self._set_status("⏳ [1/3] Подготовка и нарезка аудио...", 0.2)
            chunk_paths = self.audio_service.prepare_audio(self.selected_file_path, chunk_duration_min=5)

            # Шаг 2: Расшифровка
            self._set_status("⏳ [2/3] Расшифровка через Whisper (может занять пару минут)...", 0.5)
            transcript = self.transcription_service.transcribe_chunks(chunk_paths, language="ru")

            # Выводим транскрипт сразу
            self.txt_transcript.delete("1.0", "end")
            self.txt_transcript.insert("1.0", transcript)

            # Шаг 3: Саммари
            self._set_status("⏳ [3/3] Создание краткого пересказа...", 0.8)
            summary = self.summary_service.summarize(transcript)

            # Выводим саммари
            self.txt_summary.delete("1.0", "end")
            self.txt_summary.insert("1.0", summary)

            self._set_status("✅ Обработка успешно завершена!", 1.0)
            self.tabview.set("📌 Краткий пересказ")

        except Exception as e:
            self._set_status(f"❌ Ошибка: {str(e)}", 0)
            messagebox.showerror("Ошибка обработки", f"Произошла ошибка:\n{e}")
        finally:
            # Чистим временные куски звука
            self.audio_service.cleanup_temp_dir()
            self.btn_start.configure(state="normal")
            self.btn_select_file.configure(state="normal")

    def _copy_to_clipboard(self):
        summary_text = self.txt_summary.get("1.0", "end").strip()
        if summary_text:
            self.clipboard_clear()
            self.clipboard_append(summary_text)
            messagebox.showinfo("Успех", "Краткий пересказ скопирован в буфер обмена!")
        else:
            messagebox.showwarning("Внимание", "Поле пересказа пустое.")

    def _clear_cache(self):
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите удалить файлы модели Whisper?\n"
            "Это освободит около 450 МБ на диске, но при следующем запуске модель скачается заново."
        )
        if confirm:
            deleted = self.transcription_service.delete_cached_model()
            if deleted:
                messagebox.showinfo("Очищено", "Файлы модели успешно удалены с диска!")
            else:
                messagebox.showinfo("Инфо", "Кэш уже пуст, удалять нечего.")