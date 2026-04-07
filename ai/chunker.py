import os
import re
import gc
import torch
from typing import Dict, List
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

device = 'cuda' if torch.cuda.is_available() else 'cpu'
text_embedder = HuggingFaceEmbeddings(
    model_name='intfloat/multilingual-e5-large',
    model_kwargs={'device': device}
)


def get_metadata_from_filename(path: str) -> Dict[str, str]:
    """
    Извлекает метаданные из формата 'Имя Автора-Название Книги.txt'
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


def smart_sentence_split(text: str) -> List[str]:
    """
    Умное разделение текста на предложения с учётом особенностей русского языка.
    Сохраняет целостность предложений, сокращений (т.д., и т.п., др., ул.)
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


def ingest_book(path: str, db: Chroma):
    meta = get_metadata_from_filename(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        full_text = f.read()

    chapter_pattern = r'(?i)^\s*(?:Глава\s+)?(?:[IVXLCDM0-9]+|[а-яё]+\s*(?:ая|ье))\s*[\.:\-]?\s*$'

    chapter_matches = list(re.finditer(chapter_pattern, full_text, flags=re.MULTILINE))

    final_docs = []

    if not chapter_matches:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', full_text) if p.strip()]
        chunks_content = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            sentences = smart_sentence_split(paragraph)
            for sentence in sentences:
                sentence_len = len(sentence) + 1
                if current_length + sentence_len > 2000 and current_chunk:
                    chunks_content.append(" ".join(current_chunk))
                    current_chunk = [sentence]
                    current_length = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_len

        if current_chunk:
            chunks_content.append(" ".join(current_chunk))

        for content in chunks_content:
            doc = Document(page_content=content)
            doc.metadata.update({
                "author": meta["author"],
                "book": meta["title"],
                "chapter": "Вступление"
            })
            final_docs.append(doc)
    else:
        intro_text = full_text[:chapter_matches[0].start()].strip()
        if intro_text:
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', intro_text) if p.strip()]
            chunks_content = []
            current_chunk = []
            current_length = 0

            for paragraph in paragraphs:
                sentences = smart_sentence_split(paragraph)
                for sentence in sentences:
                    sentence_len = len(sentence) + 1
                    if current_length + sentence_len > 2000 and current_chunk:
                        chunks_content.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_length = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_length += sentence_len

            if current_chunk:
                chunks_content.append(" ".join(current_chunk))

            for content in chunks_content:
                doc = Document(page_content=content)
                doc.metadata.update({
                    "author": meta["author"],
                    "book": meta["title"],
                    "chapter": "Вступление"
                })
                final_docs.append(doc)

        for idx, match in enumerate(chapter_matches):
            chapter_title_raw = match.group().strip()
            chapter_title = chapter_title_raw.title() if chapter_title_raw else f"Глава {idx + 1}"

            start_pos = match.end()
            end_pos = chapter_matches[idx + 1].start() if idx + 1 < len(chapter_matches) else len(full_text)
            chapter_content = full_text[start_pos:end_pos].strip()

            if chapter_content:
                paragraphs = [p.strip() for p in re.split(r'\n\s*\n', chapter_content) if p.strip()]
                chunks_content = []
                current_chunk = []
                current_length = 0

                for paragraph in paragraphs:
                    sentences = smart_sentence_split(paragraph)
                    for sentence in sentences:
                        sentence_len = len(sentence) + 1
                        if current_length + sentence_len > 2000 and current_chunk:
                            chunks_content.append(" ".join(current_chunk))
                            current_chunk = [sentence]
                            current_length = len(sentence)
                        else:
                            current_chunk.append(sentence)
                            current_length += sentence_len

                if current_chunk:
                    chunks_content.append(" ".join(current_chunk))

                for content in chunks_content:
                    doc = Document(page_content=content)
                    doc.metadata.update({
                        "author": meta["author"],
                        "book": meta["title"],
                        "chapter": chapter_title
                    })
                    final_docs.append(doc)

    if final_docs:
        db.add_documents(final_docs)
        clear_hardware_cache()

def clear_hardware_cache():
    """
    Очищает оперативную память и видеопамять.
    """
    gc.collect()
    if torch.cuda.is_available():
        with torch.cuda.device('cuda'):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    gc.collect()


def get_user_db(path: str) -> Chroma:
    os.makedirs(path, exist_ok=True)
    return Chroma(persist_directory=path, embedding_function=text_embedder, collection_name="library")
