"""
Константы и настройки по умолчанию для GitHub RAG Explorer.
"""

# Настройки приложения
APP_TITLE = 'GitHub RAG Explorer 🦙'
APP_DESCRIPTION = """
Этот инструмент позволяет создать RAG (Retrieval Augmented Generation) систему для GitHub репозиториев,
используя LlamaIndex. Загрузите репозиторий, постройте индекс и задавайте вопросы!
"""

# Пути по умолчанию
DEFAULT_INDEX_PATH = './llama_index'
DEFAULT_CONFIG_PATH = 'config.json'

# Настройки логгирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Вкладки UI
UI_TABS = [
    'Загрузка репозитория',
    'Загрузка локальной директории',
    'Запросы к индексу',
    'Информация о индексе',
]

# Настройки разделения документов
DEFAULT_CHUNK_LINES = 40
DEFAULT_CHUNK_LINES_OVERLAP = 15
DEFAULT_MAX_CHARS = 1500

# Расширения файлов
DEFAULT_EXCLUDE_EXTENSIONS = [
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.svg',
    '.ico',
    '.json',
    '.ipynb',
    '.pyc',
    '.pyo',
    '.pyd',
]

# Настройки LLM моделей
LLM_PROVIDERS = ['openai', 'anthropic', 'ollama']

# Модели для разных провайдеров
LLM_MODELS: dict[str, list[str]] = {
    'openai': [
        'gpt-4o',
        'gpt-4',
        'gpt-4-turbo',
        'o1',
        'o3-mini',
        'gpt-4.5-preview',
    ],
    'anthropic': [
        'claude-3-7-sonnet-latest',
        'claude-3-5-sonnet-latest',
        'claude-3-opus-latest',
    ],
    'ollama': ['llama3'],
}

# Значения моделей по умолчанию
DEFAULT_MODEL_PROVIDER = 'openai'
DEFAULT_MODEL_NAMES: dict[str, str] = {
    'openai': 'gpt-4o',
    'anthropic': 'claude-3-5-sonnet-latest',
    'ollama': 'llama3',
}

# Настройки GitHub
DEFAULT_BRANCH = 'main'
