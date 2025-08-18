import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Pygments для определения языка
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

# LlamaIndex импорты
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import CodeSplitter
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.schema import TextNode
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.ollama import Ollama

# Импорты для разных моделей
from llama_index.llms.openai import OpenAI
from llama_index.readers.github import GithubClient, GithubRepositoryReader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def detect_language(file_path: str) -> str | None:
    """
    Определение языка программирования по имени файла с помощью Pygments
    """
    try:
        lexer = get_lexer_for_filename(file_path)
        return lexer.name.lower()
    except ClassNotFound:
        return None


def load_github_repo(
    github_token: str,
    owner: str,
    repo: str,
    branch: str = 'main',
    filter_directories: list[str] = None,
    exclude_extensions: list[str] = None,
    include_extensions: list[str] = None,
) -> list[Document]:
    """
    Загрузка данных из GitHub репозитория
    """
    logger.info(f'Загрузка репозитория {owner}/{repo} (ветка: {branch})')

    # Настройка GitHub клиента
    github_client = GithubClient(github_token=github_token, verbose=True)

    # Настройка фильтров
    include_filter_type = GithubRepositoryReader.FilterType.INCLUDE
    exclude_filter_type = GithubRepositoryReader.FilterType.EXCLUDE

    # Установка значений по умолчанию, если они не предоставлены
    if filter_directories is None:
        filter_directories_tuple = None
    else:
        filter_directories_tuple = (filter_directories, include_filter_type)

    # Настройка фильтров по расширениям файлов
    extension_filters = []

    # Обработка включаемых расширений
    if include_extensions:
        extension_filters.append((include_extensions, include_filter_type))

    # Обработка исключаемых расширений
    if exclude_extensions is None and not include_extensions:
        exclude_extensions = [
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

    if exclude_extensions:
        extension_filters.append((exclude_extensions, exclude_filter_type))

    # Загрузка документов
    try:
        reader = GithubRepositoryReader(
            github_client=github_client,
            owner=owner,
            repo=repo,
            use_parser=False,
            verbose=True,
            filter_directories=filter_directories_tuple,
            filter_file_extensions=extension_filters[0]
            if len(extension_filters) == 1
            else None,
        )

        # Если есть два фильтра (include и exclude), применим их последовательно
        documents = reader.load_data(branch=branch)

        # Применение второго фильтра, если он есть
        if len(extension_filters) > 1:
            filtered_docs = []
            ext_list, filter_type = extension_filters[1]

            for doc in documents:
                file_path = doc.metadata.get('file_path', '')
                file_ext = Path(file_path).suffix.lower()

                if filter_type == exclude_filter_type and file_ext in ext_list:
                    continue
                elif (
                    filter_type == include_filter_type
                    and file_ext not in ext_list
                ):
                    continue

                filtered_docs.append(doc)

            documents = filtered_docs

        logger.info(f'Загружено {len(documents)} документов')
        return documents
    except Exception as e:
        logger.error(f'Ошибка при загрузке репозитория: {e}')
        return []


def load_local_directory(
    directory_path: str,
    exclude_extensions: list[str] = None,
    include_extensions: list[str] = None,
) -> list[Document]:
    """
    Загрузка данных из локальной директории
    """
    logger.info(f'Загрузка файлов из директории {directory_path}')

    try:
        # Настройка параметров для SimpleDirectoryReader
        reader_params = {
            'input_dir': directory_path,
            'recursive': True,
            'exclude_hidden': True,
        }

        # Если указаны расширения для включения, используем их как required_exts
        if include_extensions:
            reader_params['required_exts'] = include_extensions

        # Если указаны расширения для исключения, создаем паттерны исключения
        if exclude_extensions:
            # Создаем паттерны glob для исключения
            exclude_patterns = []
            for ext in exclude_extensions:
                # Убираем точку из расширения, если она есть в начале
                if ext.startswith('.'):
                    ext = ext[1:]
                # Формируем паттерн glob для исключения
                exclude_patterns.append(f'**/*.{ext}')

            reader_params['exclude'] = exclude_patterns

        # Используем SimpleDirectoryReader для загрузки файлов
        reader = SimpleDirectoryReader(**reader_params)

        documents = reader.load_data()
        logger.info(f'Загружено {len(documents)} документов из директории')
        return documents
    except Exception as e:
        logger.error(f'Ошибка при загрузке файлов из директории: {e}')
        return []


def preprocess_documents(documents: list[Document]) -> list[Document]:
    """
    Предобработка документов и разделение кода на ноды с учетом языка программирования
    """
    processed_docs = []

    for doc in documents:
        # Извлечение пути к файлу из метаданных
        file_path = doc.metadata.get('file_path', '')
        if not file_path:
            # Если нет пути, просто добавляем документ как есть
            processed_docs.append(doc)
            continue

        # Определение языка программирования
        language = detect_language(file_path)

        if language:
            # Создаем разделитель кода с учетом языка
            try:
                splitter = CodeSplitter(
                    language=language,
                    chunk_lines=40,  # Настраиваемый параметр
                    chunk_lines_overlap=15,  # Настраиваемый параметр
                    max_chars=1500,  # Настраиваемый параметр
                )

                # Получение нод из документа (правильное использование API)
                nodes = splitter.get_nodes_from_documents([doc])

                # Преобразование нод обратно в документы
                for i, node in enumerate(nodes):
                    # Копирование метаданных и добавление информации о чанке
                    chunk_metadata = dict(doc.metadata)
                    chunk_metadata['chunk_index'] = i
                    chunk_metadata['language'] = language
                    chunk_metadata['total_chunks'] = len(nodes)

                    # Объединяем метаданные ноды и документа
                    if isinstance(node, TextNode):
                        # Если имеет метаданные, объединяем их
                        node_metadata = node.metadata or {}
                        for key, value in chunk_metadata.items():
                            if key not in node_metadata:
                                node_metadata[key] = value

                        processed_docs.append(
                            Document(text=node.text, metadata=node_metadata)
                        )
                    else:
                        # Обычное добавление документа
                        processed_docs.append(
                            Document(
                                text=node.get_content(), metadata=chunk_metadata
                            )
                        )
            except Exception as e:
                logger.warning(
                    f'Ошибка при разделении файла {file_path}: {e}. Используем документ целиком.'
                )
                # Если произошла ошибка при разделении, используем документ как есть
                processed_docs.append(doc)
        else:
            # Если язык не определен, просто добавляем документ как есть
            processed_docs.append(doc)

    logger.info(f'После предобработки: {len(processed_docs)} документов')
    return processed_docs


def setup_llm(model_provider: str, model_name: str = None) -> Any:
    """
    Настройка языковой модели на основе провайдера и имени модели
    """
    logger.info(
        f'Настройка языковой модели: {model_provider}, модель: {model_name or "по умолчанию"}'
    )

    if model_provider.lower() == 'openai':
        # Настройка OpenAI модели
        model = model_name or 'gpt-4o'
        return OpenAI(model=model)

    elif model_provider.lower() == 'anthropic':
        # Настройка Claude модели
        model = model_name or 'claude-3-5-sonnet-latest'
        return Anthropic(model=model)

    elif model_provider.lower() == 'ollama':
        # Настройка Ollama модели
        model = model_name or 'llama3'
        return Ollama(model=model)

    else:
        logger.warning(
            f'Неизвестный провайдер моделей: {model_provider}. Используется OpenAI по умолчанию.'
        )
        return OpenAI(model='gpt-4o')


def build_index(
    documents: list[Document],
    index_path: str = None,
    model_provider: str = 'openai',
    model_name: str = None,
) -> VectorStoreIndex:
    """
    Построение индекса из документов и сохранение его в указанный путь
    """
    logger.info('Построение индекса...')

    # Настройка языковой модели
    llm = setup_llm(model_provider, model_name)

    # Настройка глобальных параметров для индекса
    Settings.llm = llm

    # Создание индекса
    index = VectorStoreIndex.from_documents(documents)

    # Сохранение индекса, если указан путь
    if index_path:
        logger.info(f'Сохранение индекса в {index_path}')
        index.storage_context.persist(persist_dir=index_path)

        # Сохранение информации о модели
        model_info = {'provider': model_provider, 'model_name': model_name}

        with open(Path(index_path) / 'model_info.json', 'w') as f:
            json.dump(model_info, f, indent=4)

    return index


def load_index(
    index_path: str, model_provider: str = None, model_name: str = None
) -> VectorStoreIndex:
    """
    Загрузка существующего индекса из указанного пути
    """
    try:
        logger.info(f'Загрузка индекса из {index_path}')

        # Попытка загрузки сохраненной информации о модели
        model_info_path = Path(index_path) / 'model_info.json'
        if model_info_path.exists() and not (model_provider and model_name):
            with open(model_info_path) as f:
                model_info = json.load(f)
                model_provider = model_provider or model_info.get(
                    'provider', 'openai'
                )
                model_name = model_name or model_info.get('model_name')

        # Настройка языковой модели
        llm = setup_llm(model_provider or 'openai', model_name)
        Settings.llm = llm

        # Загрузка индекса
        storage_context = StorageContext.from_defaults(persist_dir=index_path)
        return load_index_from_storage(storage_context)
    except Exception as e:
        logger.error(f'Ошибка при загрузке индекса: {e}')
        return None


def run_query(
    index: VectorStoreIndex,
    query: str,
    top_k: int = 5,
    model_provider: str = None,
    model_name: str = None,
) -> str:
    """
    Выполнение запроса к индексу
    """
    logger.info(f'Выполнение запроса: {query}')

    # Настройка модели для запроса, если указана
    if model_provider and model_name:
        llm = setup_llm(model_provider, model_name)
        Settings.llm = llm

    # Создание и выполнение запроса
    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
    )
    response = query_engine.query(query)
    return str(response)


def main():  # noqa: C901
    """
    Основная функция скрипта
    """
    parser = argparse.ArgumentParser(
        description='RAG система для GitHub репозиториев и локальных директорий с использованием LlamaIndex'
    )

    # Общие аргументы
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Путь к файлу конфигурации',
    )
    parser.add_argument(
        '--openai-api-key',
        type=str,
        help='API ключ OpenAI (или установите переменную окружения OPENAI_API_KEY)',
    )
    parser.add_argument(
        '--anthropic-api-key',
        type=str,
        help='API ключ Anthropic (или установите переменную окружения ANTHROPIC_API_KEY)',
    )
    parser.add_argument(
        '--github-token',
        type=str,
        help='GitHub токен (или установите переменную окружения GITHUB_TOKEN)',
    )
    parser.add_argument(
        '--model-provider',
        type=str,
        default='openai',
        choices=['openai', 'anthropic', 'ollama'],
        help='Провайдер языковой модели (openai, anthropic, ollama)',
    )
    parser.add_argument(
        '--model-name', type=str, help='Имя модели для выбранного провайдера'
    )

    # Команды для подпарсеров
    subparsers = parser.add_subparsers(
        dest='command', help='Команда для выполнения'
    )

    # Подпарсер для команды "index-github"
    github_parser = subparsers.add_parser(
        'index-github', help='Построить индекс для GitHub репозитория'
    )
    github_parser.add_argument(
        '--owner', type=str, required=True, help='Владелец репозитория'
    )
    github_parser.add_argument(
        '--repo', type=str, required=True, help='Имя репозитория'
    )
    github_parser.add_argument(
        '--branch', type=str, default='main', help='Ветка репозитория'
    )
    github_parser.add_argument(
        '--filter-dirs',
        type=str,
        nargs='+',
        help='Список директорий для включения',
    )
    github_parser.add_argument(
        '--exclude-exts',
        type=str,
        nargs='+',
        help='Список расширений файлов для исключения',
    )
    github_parser.add_argument(
        '--include-exts',
        type=str,
        nargs='+',
        help='Список расширений файлов для включения',
    )
    github_parser.add_argument(
        '--index-path',
        type=str,
        default='./index',
        help='Путь для сохранения индекса',
    )

    # Подпарсер для команды "index-local"
    local_parser = subparsers.add_parser(
        'index-local', help='Построить индекс для локальной директории'
    )
    local_parser.add_argument(
        '--directory',
        type=str,
        required=True,
        help='Путь к локальной директории',
    )
    local_parser.add_argument(
        '--exclude-exts',
        type=str,
        nargs='+',
        help='Список расширений файлов для исключения',
    )
    local_parser.add_argument(
        '--include-exts',
        type=str,
        nargs='+',
        help='Список расширений файлов для включения',
    )
    local_parser.add_argument(
        '--index-path',
        type=str,
        default='./index',
        help='Путь для сохранения индекса',
    )

    # Подпарсер для команды "query"
    query_parser = subparsers.add_parser(
        'query', help='Выполнить запрос к индексу'
    )
    query_parser.add_argument(
        '--index-path', type=str, default='./index', help='Путь к индексу'
    )
    query_parser.add_argument(
        '--query', type=str, required=True, help='Текст запроса'
    )
    query_parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Количество результатов для возврата',
    )
    query_parser.add_argument(
        '--model-provider',
        type=str,
        choices=['openai', 'anthropic', 'ollama'],
        help='Провайдер языковой модели для запроса (переопределяет глобальную настройку)',
    )
    query_parser.add_argument(
        '--model-name',
        type=str,
        help='Имя модели для запроса (переопределяет глобальную настройку)',
    )

    # Парсинг аргументов
    args = parser.parse_args()

    # Загрузка конфигурации
    config = {}
    if os.path.exists(args.config):
        with open(args.config) as f:
            config = json.load(f)

    # Установка API ключей и параметров модели
    openai_api_key = (
        args.openai_api_key
        or config.get('openai_api_key')
        or os.environ.get('OPENAI_API_KEY')
    )
    anthropic_api_key = (
        args.anthropic_api_key
        or config.get('anthropic_api_key')
        or os.environ.get('ANTHROPIC_API_KEY')
    )
    github_token = (
        args.github_token
        or config.get('github_token')
        or os.environ.get('GITHUB_TOKEN')
    )
    model_provider = args.model_provider or config.get(
        'model_provider', 'openai'
    )
    model_name = args.model_name or config.get('model_name')

    # Проверка ключей в зависимости от выбранного провайдера модели
    if model_provider == 'openai' and not openai_api_key:
        logger.error(
            'OpenAI API ключ не указан. Используйте --openai-api-key или установите переменную окружения OPENAI_API_KEY'
        )
        return
    elif model_provider == 'anthropic' and not anthropic_api_key:
        logger.error(
            'Anthropic API ключ не указан. Используйте --anthropic-api-key или установите переменную окружения ANTHROPIC_API_KEY'
        )
        return

    # Установка API ключей в переменные окружения
    if openai_api_key:
        os.environ['OPENAI_API_KEY'] = openai_api_key
    if anthropic_api_key:
        os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key

    # Обработка команд
    if args.command == 'index-github':
        # Проверка GitHub токена
        if not github_token:
            logger.error(
                'GitHub токен не указан. Используйте --github-token или установите переменную окружения GITHUB_TOKEN'
            )
            return

        # Загрузка репозитория
        documents = load_github_repo(
            github_token=github_token,
            owner=args.owner,
            repo=args.repo,
            branch=args.branch,
            filter_directories=args.filter_dirs,
            exclude_extensions=args.exclude_exts,
            include_extensions=args.include_exts,
        )

        if not documents:
            logger.error('Не удалось загрузить документы из репозитория')
            return

        # Предобработка документов
        processed_docs = preprocess_documents(documents)

        # Построение и сохранение индекса
        index_path = args.index_path
        Path(index_path).mkdir(parents=True, exist_ok=True)
        index = build_index(
            processed_docs, index_path, model_provider, model_name
        )

        # Сохранение данных о репозитории в конфигурацию
        source_info = {
            'type': 'github',
            'owner': args.owner,
            'repo': args.repo,
            'branch': args.branch,
            'index_path': index_path,
            'total_documents': len(processed_docs),
            'model_provider': model_provider,
            'model_name': model_name,
        }

        with open(Path(index_path) / 'source_info.json', 'w') as f:
            json.dump(source_info, f, indent=4)

        logger.info(f'Индекс успешно создан и сохранен в {index_path}')

    elif args.command == 'index-local':
        # Проверка пути к директории
        if not os.path.exists(args.directory) or not os.path.isdir(
            args.directory
        ):
            logger.error(
                f'Указанная директория не существует: {args.directory}'
            )
            return

        # Загрузка файлов из директории
        documents = load_local_directory(
            directory_path=args.directory,
            exclude_extensions=args.exclude_exts,
            include_extensions=args.include_exts,
        )

        if not documents:
            logger.error(
                'Не удалось загрузить документы из директории или директория пуста'
            )
            return

        # Предобработка документов
        processed_docs = preprocess_documents(documents)

        # Построение и сохранение индекса
        index_path = args.index_path
        Path(index_path).mkdir(parents=True, exist_ok=True)
        index = build_index(
            processed_docs, index_path, model_provider, model_name
        )

        # Сохранение данных о директории в конфигурацию
        source_info = {
            'type': 'local',
            'directory': args.directory,
            'index_path': index_path,
            'total_documents': len(processed_docs),
            'model_provider': model_provider,
            'model_name': model_name,
        }

        with open(Path(index_path) / 'source_info.json', 'w') as f:
            json.dump(source_info, f, indent=4)

        logger.info(f'Индекс успешно создан и сохранен в {index_path}')

    elif args.command == 'query':
        # Проверка существования индекса
        index_path = args.index_path
        if not os.path.exists(index_path):
            logger.error(f'Индекс не найден по пути {index_path}')
            return

        # Определение параметров модели для запроса
        query_model_provider = args.model_provider or model_provider
        query_model_name = args.model_name or model_name

        # Загрузка индекса
        index = load_index(index_path, query_model_provider, query_model_name)
        if not index:
            logger.error('Не удалось загрузить индекс')
            return

        # Вывод информации об источнике, если доступна
        source_info_path = Path(index_path) / 'source_info.json'
        if source_info_path.exists():
            with open(source_info_path) as f:
                source_info = json.load(f)

            if source_info.get('type') == 'github':
                logger.info(
                    f'Запрос к индексу репозитория: {source_info.get("owner")}/{source_info.get("repo")} (ветка: {source_info.get("branch")})'
                )
            elif source_info.get('type') == 'local':
                logger.info(
                    f'Запрос к индексу локальной директории: {source_info.get("directory")}'  # noqa: E501
                )

        # Выполнение запроса
        response = run_query(
            index,
            args.query,
            args.top_k,
            query_model_provider,
            query_model_name,
        )

        # Вывод ответа
        print('\n=== Ответ на запрос ===')
        print(response)
        print('======================\n')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
