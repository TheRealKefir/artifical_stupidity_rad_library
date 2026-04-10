from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Dict, List
from app.utils.helpers import clear_hardware_cache
import os
import re
from langchain_core.documents import Document
from flask import current_app
from langchain_huggingface import HuggingFaceEndpointEmbeddings


def get_embeddings():
    """
    Получение модели эмбеддингов через Hugging Face Inference API.
    Это не скачивает модель целиком, а отправляет текст на API HF.
    """
    return HuggingFaceEndpointEmbeddings(
        model=current_app.config,
        task="feature-extraction",
        huggingfacehub_api_token=current_app.config
    )


def _chunk_text(text: str, max_length: int = 2000):
    """
    Генератор, эффективно разбивающий текст на смысловые фрагменты (чанки) заданного размера.

    Алгоритм работы:
    1. Текст разделяется на абзацы по двойному переносу строки.
    2. Каждый абзац разбивается на предложения с помощью `smart_sentence_split`.
    3. Предложения последовательно объединяются в чанк, пока его длина не превысит `max_length`.
    4. Как только лимит достигнут, генератор возвращает (yield) текущий собранный текст
        и начинает формирование нового чанка с текущего предложения.

    Это обеспечивает «мягкое» разбиение: чанк никогда не оборвется на середине слова
    или предложения, если само предложение не превышает `max_length`.

    Args:
        text (str): Входной текст для обработки.
        max_length (int): Максимально допустимое количество символов в одном чанке.
                          По умолчанию 2000.

    Yields:
        str: Очередной сформированный текстовый фрагмент.
    """
    if not text.strip():
        return

    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    current_chunk = []
    current_length = 0

    for paragraph in paragraphs:
        for sentence in smart_sentence_split(paragraph):
            sentence_len = len(sentence) + 1  # +1 для пробела при join

            if current_length + sentence_len > max_length and current_chunk:
                yield " ".join(current_chunk)
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += sentence_len

    if current_chunk:
        yield " ".join(current_chunk)


def smart_sentence_split(text: str) -> List[str]:
    """
    Интеллектуально разделяет текст на отдельные предложения, учитывая специфику русского языка.

    В отличие от обычного разделения по точкам, эта функция:
    1. Идентифицирует распространенные сокращения (т.д., и т.п., ул., гл.) и временно заменяет их
       плейсхолдерами, чтобы избежать ложных разрывов.
    2. Корректно обрабатывает инициалы, номера (№) и параграфы (§).
    3. Использует регулярные выражения для поиска границ предложений (. ! ?), за которыми следует пробел.
    4. Восстанавливает сокращения в финальном списке предложений.

    Args:
        text (str): Исходный текст для разделения.

    Returns:
        List[str]: Список очищенных предложений. Если разделение невозможно,
                   возвращает список из одного элемента (исходный текст).
    """
    abbreviations = [
        r'т\.д\.?', r'т\.п\.?', r'и т\.д\.?', r'и т\.п\.?',
        r'др\.?', r'ул\.?', r'г\.?', r'гг\.?', r'см\.?', r'см\.?',
        r'рис\.?', r'табл\.?', r'гл\.?', r'стр\.?', r'им\.?',
        r'№\s*\d+', r'§\s*\d+', r'академик\s+[А-Я]\.\s*[А-Я]\.',
        r'[А-Я]\.\s*[А-Я]\.\s*[А-Я][а-я]+',
    ]

    placeholders = {}
    for i, abbr_pattern in enumerate(abbreviations):
        matches = re.finditer(abbr_pattern, text, flags=re.IGNORECASE)
        for match in matches:
            placeholder = f"__ABBR{i}_{match.start()}__"
            placeholders[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    restored_sentences = []
    for sentence in sentences:
        for placeholder, original in placeholders.items():
            sentence = sentence.replace(placeholder, original)
        if sentence.strip():
            restored_sentences.append(sentence.strip())

    return restored_sentences if restored_sentences else [text]


def get_metadata_from_filename(path: str) -> Dict[str, str]:
    """
    Извлекает метаданные книги (автор и название) из имени файла.

    Ожидаемый формат имени файла: 'Имя Автора - Название Книги.txt'.
    Если разделитель '-' отсутствует, имя файла целиком принимается за название.

    Args:
        path (str): Полный путь к файлу или только имя файла.

    Returns:
        Dict[str, str]: Словарь с ключами "author" и "title".
    """
    basename = os.path.basename(path).replace('.txt', '')

    if "-" in basename:
        parts = basename.split("-", 1)
        author = parts[0].strip().title()
        title = parts[1].strip().title()
    else:
        author = "Неизвестен"
        title = basename.replace('-', ' ').strip().title()

    return {"author": author, "title": title}


def ingest_book(path: str, db, user_id: str, chunk_size: int = 2000, chunk_overlap: int = 200):
    """
        Разбивает книгу на главы и чанки, затем индексирует их в векторной базе данных.

        Функция выполняет интеллектуальное разбиение:
        1. Определяет структуру глав с помощью регулярных выражений.
        2. Сохраняет контекст каждой главы в метаданных.
        3. Использует RecursiveCharacterTextSplitter для создания перекрывающихся чанков.
        4. Привязывает каждый фрагмент к конкретному user_id для изоляции данных.

        Args:
            path (str): Путь к текстовому файлу книги.
            db (Chroma): Объект векторного хранилища (например, ChromaDB).
            user_id (str): Уникальный идентификатор владельца книги.
            chunk_size (int): Максимальный размер одного текстового фрагмента (в символах).
            chunk_overlap (int): Размер перекрытия между соседними чанками.

        Raises:
            FileNotFoundError: Если файл по указанному пути не существует.
        """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    meta = get_metadata_from_filename(path)

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""],

    )

    chapter_pattern = r'(?i)^\s*(?:Глава\s+)?(?:[IVXLCDM0-9]+|[а-яё]+\s*(?:ая|ье))\s*[\.:\-]?\s*$'
    chapter_matches = list(re.finditer(chapter_pattern, full_text, flags=re.MULTILINE))

    sections = []

    if not chapter_matches:
        sections.append(("Вступление", full_text))
    else:
        intro_text = full_text[:chapter_matches[0].start()].strip()
        if intro_text:
            sections.append(("Вступление", intro_text))

        for idx, match in enumerate(chapter_matches):
            raw_title = match.group().strip()
            chapter_title = raw_title.title() if raw_title else f"Глава {idx + 1}"

            start_pos = match.end()
            end_pos = chapter_matches[idx + 1].start() if idx + 1 < len(chapter_matches) else len(full_text)

            chapter_content = full_text[start_pos:end_pos].strip()
            if chapter_content:
                sections.append((chapter_title, chapter_content))

    final_docs = []

    for chapter_title, content in sections:
        docs = text_splitter.create_documents([content])

        for doc in docs:
            doc.metadata.update({
                "author": meta["author"],
                "book": meta["title"],
                "chapter": chapter_title,
                "user_id": user_id
            })
        final_docs.extend(docs)
    if final_docs:
        db.add_documents(final_docs)
        clear_hardware_cache()


def vector_search(query_text: str, db, user_id: str, k: int = 5) -> List[Document]:
    """
    Выполняет семантический поиск в векторном хранилище с жесткой фильтрацией по пользователю.

    Процесс работы:
    1. Текст запроса преобразуется в вектор (embedding) с помощью модели, привязанной к `db`.
    2. В базе данных ищутся `k` наиболее близких векторов.
    3. Применяется фильтр `where={"user_id": user_id}`, который гарантирует, что
       система не вернет документы, принадлежащие другим пользователям.

    Args:
        query_text (str): Текст вопроса пользователя.
        db (Chroma): Объект векторной базы данных.
        user_id (str): Идентификатор пользователя для изоляции контекста.
        k (int): Количество возвращаемых наиболее релевантных фрагментов.

    Returns:
        List[Document]: Список найденных документов LangChain с их контентом и метаданными.
    """
    results = db.similarity_search(
        query_text,
        k=k,
        filter={"user_id": user_id}
    )

    return results
