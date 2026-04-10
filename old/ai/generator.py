import re
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from old.data.exceptions import NoBookLoaded
from .chunker import get_user_db, ingest_book
from normalize import build_prompt
import tempfile
import os



def extract_chapter(query: str) -> Optional[str]:
    query_lower = query.lower()
    numbers = re.findall(r'\b(\d+)\b', query_lower)
    words = ['первая', 'вторая', 'третья', 'четвертая', 'пятая', 'шестая', 'седьмая', 'восьмая', 'девятая', 'десятая']

    if numbers:
        num = int(numbers[0])
        if 1 <= num <= 10:
            return words[num - 1]

    for word in words:
        if word in query_lower:
            return word
    return None


def load_local_model(model_name: str):
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
        )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
        return {"tokenizer": tokenizer, "pipeline": pipe}
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки локальной модели: {e}")


def generate_answer(prompt_for_llm: str, user_id: int, llm) -> str:
    if llm is None:
        llm = load_local_model('Qwen/Qwen3.5-4B')

    if isinstance(llm, dict) and "pipeline" in llm:
        try:
            pipe = llm["pipeline"]
            tokenizer = llm["tokenizer"]
            db = get_user_db(f"/db/chroma/user_{user_id}")
            results = db.similarity_search(prompt_for_llm, k=5)

            # Фильтр по главе, если упомянута
            chapter = extract_chapter(prompt_for_llm)
            if chapter:
                results = [r for r in results if chapter in r.metadata.get('chapter', '').lower()]

            results = results[:3]

            context_parts = []
            sources_info = []
            for doc in results:
                m = doc.metadata
                context_parts.append(
                    f"Книга: {m.get('book', 'Неизвестно')}, Глава: {m.get('chapter', 'Неизвестно')}\nТекст: {doc.page_content}")
                sources_info.append(f"📍 {m.get('book')} — {m.get('chapter')}")

            context = "\n\n".join(context_parts)
            final_prompt = build_prompt(prompt_for_llm, context)
            messages = [
                {"role": "system",
                 "content": "Ты — помощник, отвечающий на вопросы по книгам. Отвечай кратко и по делу."},
                {"role": "user", "content": final_prompt}
            ]
            prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            outputs = pipe(prompt_text)
            full_response = outputs[0]["generated_text"]
            return full_response.split(prompt_text)[-1].strip()
        except Exception as e:
            return f"⚠️ Ошибка генерации: {e}"


def load_book_to_user_db(book, user_id):
    user_db = get_user_db(f"/db/chroma/user_{user_id}")
    ingest_book(book, user_db)
    if not book:
        raise NoBookLoaded("Book not found")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(book.getvalue())
        path = f.name
    ingest_book(path, user_db)
    os.unlink(path)

