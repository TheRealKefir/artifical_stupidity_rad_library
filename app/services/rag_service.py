import logging
import os
import re
from typing import Dict, List

from flask import current_app
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.helpers import clear_hardware_cache

logger = logging.getLogger(__name__)


class RagService:
    @staticmethod
    def get_embeddings():
        """
        Получение модели эмбеддингов через Hugging Face Inference API.
        Это не скачивает модель целиком, а отправляет текст на API HF.
        """
        logger.info("Инициализация HuggingFaceEndpointEmbeddings")
        return HuggingFaceEndpointEmbeddings(
            model=current_app.config,
            task="feature-extraction",
            huggingfacehub_api_token=current_app.config
        )

    @staticmethod
    def _chunk_text(text: str, max_length: int = 2000):
        """
        Генератор, эффективно разбивающий текст на смысловые фрагменты (чанки) заданного размера.
        ...
        """
        if not text.strip():
            logger.debug("Передан пустой текст для чанкинга, пропускаем.")
            return

        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            for sentence in RagService.smart_sentence_split(paragraph):
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

    @staticmethod
    def smart_sentence_split(text: str) -> List[str]:
        """
        Интеллектуально разделяет текст на отдельные предложения, учитывая специфику русского языка.
        ...
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

    @staticmethod
    def get_metadata_from_filename(path: str) -> Dict[str, str]:
        """
        Извлекает метаданные книги (автор и название) из имени файла.
        ...
        """
        basename = os.path.basename(path).replace('.txt', '')

        if "-" in basename:
            parts = basename.split("-", 1)
            author = parts[0].strip().title()
            title = parts[1].strip().title()
        else:
            author = "Неизвестен"
            title = basename.replace('-', ' ').strip().title()

        logger.debug(f"Извлечены метаданные из файла '{basename}': Автор='{author}', Название='{title}'")
        return {"author": author, "title": title}

    @staticmethod
    def ingest_book(path: str, db, user_id: str, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Разбивает книгу на главы и чанки, затем индексирует их в векторной базе данных.
        ...
        """
        logger.info(f"Начало обработки книги: {path} (user_id: {user_id})")

        if not os.path.exists(path):
            logger.error(f"Файл не найден: {path}")
            raise FileNotFoundError(f"File not found: {path}")

        meta = RagService.get_metadata_from_filename(path)

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            full_text = f.read()

        logger.debug(f"Файл успешно прочитан. Длина текста: {len(full_text)} символов.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "?", "!", " ", ""],
        )

        chapter_pattern = r'(?i)^\s*(?:Глава\s+)?(?:[IVXLCDM0-9]+|[а-яё]+\s*(?:ая|ье))\s*[\.:\-]?\s*$'
        chapter_matches = list(re.finditer(chapter_pattern, full_text, flags=re.MULTILINE))

        sections = []

        if not chapter_matches:
            logger.info("Главы не найдены. Книга будет обработана как единая секция 'Вступление'.")
            sections.append(("Вступление", full_text))
        else:
            logger.info(f"Найдено глав: {len(chapter_matches)}.")
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

        logger.info(f"Разбиение {len(sections)} секций на чанки...")
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
            logger.info(f"Добавление {len(final_docs)} документов в векторную БД...")
            db.add_documents(final_docs)
            clear_hardware_cache()
            logger.info(f"Успешная индексация книги: {meta['title']}. Кэш очищен.")
        else:
            logger.warning(f"Документы для книги {path} не были сформированы (возможно, файл пуст).")

    @staticmethod
    def vector_search(query_text: str, db, user_id: str, k: int = 5) -> List[Document]:
        """
        Выполняет семантический поиск в векторном хранилище с жесткой фильтрацией по пользователю.
        ...
        """
        logger.info(f"Векторный поиск (user_id: {user_id}, k: {k}) | Запрос: '{query_text}'")

        results = db.similarity_search(
            query_text,
            k=k,
            filter={"user_id": user_id}
        )

        logger.info(f"Найдено документов: {len(results)}")
        return results
