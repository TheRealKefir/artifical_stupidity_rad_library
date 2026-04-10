import re
from typing import Optional, Tuple


def normalize_query(query: str) -> str:
    """
    Нормализует пользовательский запрос:
    - Удаляет лишние спецсимволы и пробелы
    - Сохраняет буквы, цифры, базовую пунктуацию
    """
    # Удаляем лишние символы (оставляем буквы, цифры, базовую пунктуацию)
    query = re.sub(r'[^\w\s.,!?;:()\-«»""]', '', query, flags=re.UNICODE)
    # Нормализуем пробелы
    query = re.sub(r'\s+', ' ', query).strip()
    return query


def truncate_context(context: str, max_length: int = 4000) -> Tuple[str, bool]:
    """
    Обрезает контекст до максимальной длины, сохраняя целостность предложений.
    Возвращает обрезанный контекст и флаг обрезки.
    """
    if len(context) <= max_length:
        return context, False

    # Пытаемся обрезать на границе предложения
    truncated = context[:max_length]
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclamation = truncated.rfind('!')

    # Находим последнюю границу предложения
    sentence_end = max(last_period, last_question, last_exclamation)

    if sentence_end > max_length * 0.5:  # Если есть предложение хотя бы в 50% текста
        truncated = truncated[:sentence_end + 1]

    return truncated.rstrip() + " [...]", True


def build_prompt(
        user_query: str,
        context: str,
        system_instruction: Optional[str] = None,
        max_context_length: int = 4000
) -> str:
    """
    Формирует промпт для модели на основе контекста и вопроса.
    
    Args:
        user_query: Исходный вопрос пользователя
        context: Текст контекста (например, чанки из базы знаний)
        system_instruction: Системная инструкция для модели (опционально)
        max_context_length: Максимальная длина контекста в символах
    
    Returns:
        Сформированный промпт
    """
    cleaned_query = normalize_query(user_query)

    if system_instruction is None:
        system_instruction = (
            "Ты — ассистент, анализирующий загруженные книги. "
            "Отвечай на вопросы, используя только информацию из предоставленного контекста. "
            "Если ответ невозможно найти в контексте, честно скажи, что не знаешь."
        )

    # Обрезаем контекст с сохранением целостности предложений
    truncated_context, was_truncated = truncate_context(context, max_context_length)

    # Формируем структурированный промпт
    prompt = (
        f"{system_instruction}\n\n"
        f"=== КОНТЕКСТ ===\n"
        f"{truncated_context}\n"
        f"=== КОНТЕКСТ ЗАВЕРШЁН ===\n\n"
        f"ВОПРОС: {cleaned_query}\n\n"
        f"ОТВЕТ:"
    )

    return prompt


def build_comparison_prompt(
        user_query: str,
        contexts: list[str],
        system_instruction: Optional[str] = None
) -> str:
    """
    Формирует промпт для сравнения нескольких контекстов.
    
    Args:
        user_query: Вопрос пользователя
        contexts: Список контекстов для сравнения
        system_instruction: Системная инструкция (опционально)
    
    Returns:
        Промпт для сравнения
    """
    cleaned_query = normalize_query(user_query)

    if system_instruction is None:
        system_instruction = (
            "Ты — аналитическая система поиска по книгам. Твоя задача: дать точный ответ на основе нескольких источников.\n\n"
            "ПРАВИЛА:\n"
            "1. Сравнивай информацию из всех предоставленных источников.\n"
            "2. В конце каждого утверждения обязательно указывай номер источника, например: [1] или [1, 2].\n"
            "3. Если источники противоречат друг другу, назови это прямо.\n"
            "4. Используй только предоставленные данные. Не придумывай ничего от себя."
        )

    # Собираем блоки источников
    context_blocks = []
    for i, ctx in enumerate(contexts, 1):
        truncated, _ = truncate_context(ctx)
        context_blocks.append(f"<source id='{i}'>\n{truncated}\n</source>")

    # Финальный промпт
    prompt = (
        f"{system_instruction}\n\n"
        f"Ниже представлены фрагменты из разных книг:\n\n"
        f"{chr(10).join(context_blocks)}\n\n"  # chr(10) это \n, чтобы не ломать f-строку
        f"ЗАДАНИЕ:\n"
        f"На основе вышеуказанных источников ответь на вопрос: \"{cleaned_query}\"\n"
        f"Если в источниках нет ответа, напиши 'Информация не найдена'.\n\n"
        f"ОТВЕТ:"
    )
    return prompt
