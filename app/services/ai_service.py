import logging
from flask import current_app
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

logger = logging.getLogger(__name__)


class AIService:
    _model_pipeline = None

    @staticmethod
    def _get_llm():
        if AIService._model_pipeline is None:
            model_id = current_app.config.get('HF_LLM_MODEL')
            logger.info(f"Загрузка локальной модели из HF: {model_id}")

            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                HF_TOKEN=current_app.config.get("HF_API_TOKEN"),
            )

            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map="cpu",
                token=current_app.config.get("HF_API_TOKEN"),
                low_cpu_mem_usage=True
            )

            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.3,
                repetition_penalty=1.1,
            )

            AIService._model_pipeline = HuggingFacePipeline(pipeline=pipe)

        return AIService._model_pipeline

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
