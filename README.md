# Полная архитектурная спецификация RAG-библиотеки

Данный документ описывает структуру и реализацию многопользовательской системы для работы с книгами на базе ИИ.
Основной стек: **Flask, SQLite, Alembic (Flask-Migrate), Celery, Redis и LangChain (Hugging Face API).**

---

## 1. Структура директорий проекта

```text
/project_root
│
├── app/                        # Основной пакет приложения
│   ├── blueprints/             # Слой контроллеров (API маршруты)
│   │   ├── auth_routes.py      # Вход, регистрация
│   │   ├── root_routes.py      # Корневые роуты
│   │   ├── chat_routes.py      # Чат и вопросы к ИИ
│   │   └── user_routes         # роуты изменения аккаунта юзера
│   │
│   ├── models/                 # Слой данных (SQLAlchemy)
│   │   ├── user.py             # Модель User
│   │   ├── chat.py             # Модели Chat и Message
│   │   └── __init__.py         # Регистрация моделей для Alembic
│   │
│   ├── services/               # Слой бизнес-логики (ИИ и сервисы)
│   │   ├── auth_service.py     # Логика аутентификации
│   │   ├── rag_service.py      # Обработка TXT, чанкинг, эмбеддинги
│   │   ├── ai_service.py       # Генерация ответов через HF API
│   │   ├── chat_service.py     # Оркестрация диалога и истории
│   │   ├── user_service        # Логика юзерских роутов
│   │   └── __init__.py
│   │
│   ├── utils/                  # Вспомогательные инструменты
│   │   ├── decorators.py       # Проверка прав собственности (Ownership)
│   │   └── logging.py          # Конфигурация логгера
│   │
│   ├── static/                 # CSS и JS (динамический чат)
│   ├── templates/              # HTML шаблоны (Jinja2)
│   ├── extensions.py           # Инициализация db, migrate, login_manager
│   ├── tasks.py                # Фоновые задачи Celery
│   └── __init__.py             # Фабрика приложений (create_app)
│
├── migrations/                 # Папка миграций Alembic
├── instance/                   # Локальное хранилище (app.db, vector_db)
├── config.py                   # Классы конфигурации (Dev/Prod)
├── celery_worker.py            # Точка входа для воркера Celery
├── main.py                     # Основная точка входа для запуска Flask
└── pyproject.toml              # Зависимости
```

---

## 2. Ключевые конфигурационные файлы

### `config.py` *(Пульт управления)*

Содержит настройки доступа к:

* SQLite
* Redis
* Hugging Face API
* Celery
* LangChain

Используемые модели:

* **Эмбеддинги:** `intfloat/multilingual-e5-large`
* **LLM:** `zephyr-7b-beta`

---

### `app/extensions.py` *(Предотвращение циклических импортов)*

Здесь создаются пустые экземпляры расширений, которые импортируются во все остальные модули.

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
```

---

### `app/__init__.py` *(Фабрика приложений)*

Собирает приложение и инициализирует все зависимости.

Ключевая особенность для SQLite:

```python
migrate.init_app(app, db, render_as_batch=True)
```

Параметр `render_as_batch=True` обязателен для корректной работы Alembic с SQLite.

---

## 3. Модели данных (`app/models/`)

Для работы RAG и системы чатов используются 4 основные таблицы.

### `User`

Хранит данные пользователей.

| Поле          | Тип     | Описание         |
| ------------- | ------- | ---------------- |
| id            | Integer | Первичный ключ   |
| username      | String  | Имя пользователя |
| email         | String  | Email            |
| password_hash | String  | Хэш пароля       |

---

### `Chat`

Хранит сессии диалогов пользователя.

| Поле       | Тип      | Описание       |
| ---------- | -------- | -------------- |
| id         | Integer  | Первичный ключ |
| user_id    | Integer  | Владелец чата  |
| title      | String   | Название чата  |
| created_at | DateTime | Дата создания  |

---

### `Message`

Хранит сообщения внутри чатов.

| Поле      | Тип      | Описание             |
| --------- | -------- | -------------------- |
| id        | Integer  | Первичный ключ       |
| chat_id   | Integer  | Привязка к чату      |
| role      | String   | `user` / `assistant` |
| content   | Text     | Текст сообщения      |
| timestamp | DateTime | Время отправки       |

---

## 4. Сервисный слой (`app/services/`)

### `rag_service.py` *(Подготовка данных)*

Отвечает за **Ingestion Pipeline**:

* загрузка PDF
* извлечение текста
* нарезка текста на чанки
* генерация эмбеддингов
* запись в векторное хранилище

#### Основные принципы:

* Используется `RecursiveCharacterTextSplitter`
* Размер overlap: `200`
* Каждый чанк получает `user_id` в метаданных
* Это обеспечивает изоляцию пользовательских данных

#### Назначение:

* подготовить текст для retrieval
* обеспечить безопасный multi-user search
* отправить чанки в vector store

---

### `ai_service.py` *(Генерация ответа)*

Отвечает за взаимодействие с LLM.

#### Сборка промпта:

```text
{System Instructions}
+ {Context from Book}
+ {Chat History}
+ {User Question}
```

#### Обязанности:

* сборка prompt template
* вызов `HuggingFaceEndpoint`
* управление параметрами генерации:

  * `temperature`
  * `max_tokens`
  * `top_p`

---

### `chat_service.py` *(Оркестрация диалога)*

Связывает SQLite, vector store и LLM.

#### Основные методы:

##### `save_message()`

Сохраняет сообщение в БД.

##### `get_chat_history()`

Получает последние `N` сообщений и преобразует их в:

* `HumanMessage`
* `AIMessage`

для передачи в LangChain.

##### `send_chat_message()`

Основной orchestration flow:

1. сохранить сообщение пользователя
2. найти релевантный контекст
3. получить историю диалога
4. вызвать LLM
5. сохранить ответ
6. вернуть JSON

---

## 5. Асинхронность и безопасность

### `app/tasks.py` *(Celery)*

Процесс индексации книги вынесен в фоновые задачи через Celery.

#### Зачем это нужно:

* Flask отвечает пользователю мгновенно
* PDF обрабатывается в фоне
* UI не блокируется
* статус книги обновляется асинхронно

#### Механизм:

* книга загружается
* создаётся запись в БД
* запускается `process_book_task.delay(book_id)`
* Celery обрабатывает PDF
* после завершения статус меняется на `ready`

---

### `app/utils/decorators.py`

Содержит кастомный декоратор:

```python
@check_ownership(Model)
```

#### Назначение:

* автоматически извлекает ID из URL
* проверяет принадлежность объекта текущему пользователю
* защищает от доступа к чужим книгам и чатам

#### Поведение:

Если объект не принадлежит `current_user.id`, возвращается `404`.

---

## 6. Жизненный цикл запроса (Flow)

### Загрузка книги

```text
library.upload
→ process_book_task.delay()
→ Celery обрабатывает TXT
→ создаются эмбеддинги
→ статус меняется на 'ready'
```

---

### Вопрос в чате

```text
chat.ask
→ ChatService.send_chat_message()
→ поиск релевантных чанков (filter by user_id)
→ генерация ответа через HF API
→ сохранение истории
→ JSON response
```

---

## 7. Команды для запуска

### Миграции

```bash
flask db init
flask db migrate -m "init"
flask db upgrade
```

---

### Redis

```bash
redis-server
```

Redis должен быть запущен до старта Celery.

---

### Celery Worker

```bash
celery -A celery_worker.celery worker --loglevel=info
```

---

### Flask-приложение

```bash
python run.py
```

---

## 8. Итог

Данная архитектура реализует:

* многопользовательскую RAG-систему
* безопасную изоляцию пользовательских данных
* асинхронную индексацию книг
* хранение истории диалогов
* масштабируемую сервисную архитектуру
* удобную интеграцию с Hugging Face API

Архитектура разделена на независимые слои:

* **Blueprints** — HTTP/API слой
* **Services** — бизнес-логика
* **Models** — слой данных
* **Tasks** — асинхронная обработка
* **Utils** — инфраструктурные инструменты

Это делает систему:

* расширяемой
* поддерживаемой
* безопасной
* удобной для дальнейшего роста
