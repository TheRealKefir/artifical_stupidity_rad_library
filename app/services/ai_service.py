import logging
from flask import current_app
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)


class AIService:
    @staticmethod
    def _get_llm():
        repo_id = current_app.config.get('HF_LLM_MODEL')
        api_token = current_app.config.get('HUGGINGFACE_API_KEY')
        return HuggingFaceEndpoint(
            repo_id=repo_id,
            huggingfacehub_api_token=api_token,
            task="text-generation",
            temperature=0.7,
            max_new_tokens=512,
            repetition_penalty=1.1,
        )

    @staticmethod
    def generate_answer(query, context_documents, chat_history):
        try:
            llm = AIService._get_llm()

            context_text = "\n\n".join([doc.page_content for doc in context_documents])

            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "Ты — полезный ИИ-ассистент, который отвечает на вопросы по конкретной книге. "
                    "Используй ТОЛЬКО предоставленный контекст для ответа. "
                    "Если в контексте нет информации, вежливо скажи, что в книге об этом не сказано.\n\n"
                    "КОНТЕКСТ ИЗ КНИГИ:\n{context}"
                )),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ])

            chain = prompt | llm | StrOutputParser()

            response = chain.invoke({
                "context": context_text,
                "history": chat_history,
                "input": query
            })

            logger.info("Ответ от ИИ успешно сгенерирован")
            return response

        except Exception as e:
            logger.error(f"Ошибка при обращении к LLM: {str(e)}", exc_info=True)
            return "Извините, я не смог обработать ваш запрос к нейросети."
