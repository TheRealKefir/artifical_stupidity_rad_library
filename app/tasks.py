from celery import shared_task
from app.services.rag_service import RagService


@shared_task(bind=True)
def process_book_task(file_path, user_id, meta):
    vector_store = RagService.get_vector_db()
    RagService.ingest_book(file_path, vector_store, user_id, meta)
    return f"Книга {meta.get('title')} успешно проиндексирована"
