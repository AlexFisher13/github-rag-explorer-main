# GitHub RAG Explorer 🦙

GitHub RAG Explorer позволяет создавать системы Retrieval Augmented Generation (RAG) для GitHub репозиториев и локальных директорий кода с использованием LlamaIndex.

## Функциональные возможности

- 📦 Индексация GitHub репозиториев с фильтрацией по директориям и расширениям файлов
- 📂 Индексация локальных директорий с аналогичными фильтрами
- 🔍 Выполнение запросов к индексу с использованием различных языковых моделей
- 🧠 Поддержка LLM от OpenAI, Anthropic и Ollama
- 🌐 Веб-интерфейс на Streamlit для удобного использования
- 🖥️ CLI для интеграции в скрипты и автоматизацию

## Установка

### Установка с помощью Poetry (рекомендуется)

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/github-rag-explorer.git
cd github-rag-explorer

# Установка зависимостей с помощью Poetry
poetry install

# Активация виртуального окружения
poetry shell
```

### Альтернативная установка с помощью pip

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/github-rag-explorer.git
cd github-rag-explorer

# Установка с помощью pip
pip install .
```

## Настройка окружения

Для работы с приложением необходимо настроить переменные окружения с API ключами:

```bash
# Создайте файл .env в корне проекта
touch .env

# Добавьте свои API ключи
echo "OPENAI_API_KEY=your_openai_api_key" >> .env
echo "ANTHROPIC_API_KEY=your_anthropic_api_key" >> .env
echo "GITHUB_TOKEN=your_github_token" >> .env
```

Или настройте их в веб-интерфейсе приложения.

## Использование

### Веб-интерфейс

При использовании Poetry:

```bash
# Запуск веб-интерфейса в окружении Poetry
poetry run github-rag-explorer
```

или если вы уже активировали окружение Poetry:

```bash
github-rag-explorer
```

Другие способы:

```bash
poetry run streamlit run -m github_rag_explorer.ui.app
```

### Командная строка

При использовании Poetry:

```bash
# Индексация GitHub репозитория
poetry run github-rag index-github --owner username --repo repository_name

# Индексация локальной директории
poetry run github-rag index-local --directory /path/to/directory

# Выполнение запроса к индексу
poetry run github-rag query --index-path ./llama_index --query "Как работает VectorStoreIndex?"
```

Или если вы уже активировали окружение Poetry:

```bash
github-rag index-github --owner username --repo repository_name
```

## Примеры использования

### Индексация общедоступного репозитория

```bash
poetry run github-rag index-github --owner jerryjliu --repo llama_index --branch main --filter-dirs llama_index/core --exclude-exts .md .json .ipynb
```

### Запрос к индексу с использованием Claude

```bash
poetry run github-rag query --index-path ./llama_index --query "Объясни, как использовать VectorStoreIndex" --model-provider anthropic --model-name claude-3-5-sonnet-latest
```

## Разработка

### Настройка окружения разработчика

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/github-rag-explorer.git
cd github-rag-explorer

# Установка зависимостей разработки
poetry install --with dev

# Активация виртуального окружения
poetry shell
```

### Запуск тестов

```bash
poetry run pytest
```

### Проверка кода

```bash
ruff check --fix
```

## Структура проекта

```
github_rag_explorer/
├── pyproject.toml      # Файл конфигурации Poetry
├── github_rag_explorer/
│   ├── constants.py    # Константы и настройки
│   ├── config.py       # Работа с конфигурацией
│   ├── models/         # Модули для работы с языковыми моделями
│   ├── data/           # Загрузчики данных
│   ├── indexing/       # Построение и запросы к индексам
│   ├── ui/             # Веб-интерфейс на Streamlit
│   └── cli.py          # Интерфейс командной строки
└── tests/              # Тесты
```

## Требования

- Python 3.12+
- Poetry (управление зависимостями)

## Лицензия

MIT

## Вклад в проект

Приветствуются pull-запросы. Для масштабных изменений сначала обсудите предлагаемые изменения, создав issue.
