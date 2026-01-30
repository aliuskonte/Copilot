"""Сервис ответов на вопросы через OpenAI Chat API."""

from openai import AsyncOpenAI

from copilot.config import get_settings


SYSTEM_PROMPT = """Ты помощник на созвоне. Собеседник задаёт вопросы, ты отвечаешь кратко и по делу.
Отвечай на том же языке, что и вопрос. Будь лаконичен (1-3 предложения)."""

IS_QUESTION_PROMPT = """Определи, является ли следующий текст вопросом (прямым или косвенным).
Ответь только "да" или "нет".
Текст: {text}"""


class LLMService:
    """Ответы на вопросы через GPT."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_llm_model

    async def is_question(self, text: str) -> bool:
        """Определяет, является ли текст вопросом."""
        if not text.strip():
            return False
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "user", "content": IS_QUESTION_PROMPT.format(text=text)},
            ],
            max_tokens=10,
        )
        answer = response.choices[0].message.content or ""
        return "да" in answer.lower() or "yes" in answer.lower()

    async def answer_question(self, question: str) -> str:
        """Отвечает на вопрос собеседника."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            max_tokens=500,
        )
        return (response.choices[0].message.content or "").strip()


llm_service = LLMService()
