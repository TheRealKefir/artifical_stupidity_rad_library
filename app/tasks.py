from celery import shared_task

@shared_task(bind=True)
def process_book_task(self, file_path, user_id):
    from app import create_app
    from app.services.rag_service import RagService

    flask_app = create_app()

    with flask_app.app_context():
        vector_store = RagService.get_vector_db()
        RagService.ingest_book(file_path, vector_store, user_id)
        return f"Книга {file_path} успешно проиндексирована"