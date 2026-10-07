import requests


class SummaryService:
    def __init__(self, model_name: str = "openai"):
        self.model_name = model_name

    def summarize(self, transcript_text: str) -> str:
        """
        Возвращает краткий, живой пересказ аудиозаписи без лишней воды.
        """
        if not transcript_text.strip():
            return "Текст пуст, нечего пересказывать."

        print(f"\n🧠 Генерируем краткий пересказ...")

        system_prompt = (
            "Ты — ассистент, который кратко и емко пересказывает голосовые сообщения и аудиозаписи.\n"
            "Правила:\n"
            "1. Никакой лишней воды, длинных вступлений и канцелярщины.\n"
            "2. Выдели ГЛАВНОЕ: в чем суть, о чем человек говорит, ключевой контекст.\n"
            "3. Если есть конкретные договоренности, вопросы или просьбы — выдели их отдельно.\n\n"
            "Формат ответа:\n"
            "**О чем речь (в 2-3 предложениях):** ...\n\n"
            "**Главные мысли:**\n"
            "- Тезис 1\n"
            "- Тезис 2\n\n"
            "**Что нужно сделать / итог (если есть):**\n"
            "- Действие/вывод\n"
        )

        url = "https://text.pollinations.ai/"
        
        # Защита от переполнения контекста: берем до ~30 000 символов (этого за глаза для любого аудио)
        safe_transcript = transcript_text[:35000]

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Вот текст голосового:\n\n{safe_transcript}"}
            ],
            "model": self.model_name,
            "seed": 42
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                print("✅ Краткий пересказ готов!")
                return response.text.strip()
            else:
                raise RuntimeError(f"Ошибка сервера ({response.status_code})")
        except Exception as e:
            raise RuntimeError(f"Не удалось получить саммари: {e}")