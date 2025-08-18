"""
Интерфейс командной строки для GitHub RAG Explorer.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from github_rag_explorer.constants import (
    DEFAULT_BRANCH,
    DEFAULT_CONFIG_PATH,
    DEFAULT_INDEX_PATH,
    DEFAULT_MODEL_NAMES,
    DEFAULT_MODEL_PROVIDER,
)
from github_rag_explorer.data.loader import GitHubLoader, LocalDirectoryLoader
from github_rag_explorer.data.processor import DocumentProcessor
from github_rag_explorer.indexing.builder import IndexBuilder, save_source_info
from github_rag_explorer.indexing.query import QueryEngine

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict[str, Any]:
    """
    Загрузить конфигурацию из JSON файла.

    Args:
        config_path: Путь к файлу конфигурации

    Returns:
        Словарь с настройками
    """
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)
            logger.info(f'Конфигурация загружена из {config_path}')
        except Exception as e:
            logger.error(f'Ошибка при загрузке конфигурации: {e}')

    return config


def setup_api_keys(
    args: argparse.Namespace, config: dict[str, Any]
) -> dict[str, Any]:
    """
    Настройка API ключей и параметров модели.

    Args:
        args: Аргументы командной строки
        config: Словарь с конфигурацией

    Returns:
        Словарь с настройками API ключей и моделей
    """
    # Получение API ключей
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

    # Получение настроек модели
    model_provider = args.model_provider or config.get(
        'model_provider', DEFAULT_MODEL_PROVIDER
    )
    model_name = (
        args.model_name
        or config.get('model_name')
        or DEFAULT_MODEL_NAMES.get(model_provider)
    )

    # Установка API ключей в переменные окружения
    if openai_api_key:
        os.environ['OPENAI_API_KEY'] = openai_api_key

    if anthropic_api_key:
        os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key

    return {
        'openai_api_key': openai_api_key,
        'anthropic_api_key': anthropic_api_key,
        'github_token': github_token,
        'model_provider': model_provider,
        'model_name': model_name,
    }


def index_github_command(
    args: argparse.Namespace, settings: dict[str, Any]
) -> None:
    """
    Выполнить команду индексации GitHub репозитория.

    Args:
        args: Аргументы командной строки
        settings: Словарь с настройками
    """
    # Проверка GitHub токена
    if not settings['github_token']:
        logger.error(
            'GitHub токен не указан. Используйте --github-token или установите переменную окружения GITHUB_TOKEN'
        )
        return

    # Проверка API ключей в зависимости от выбранного провайдера модели
    if (
        settings['model_provider'] == 'openai'
        and not settings['openai_api_key']
    ):
        logger.error(
            'OpenAI API ключ не указан. Используйте --openai-api-key или установите переменную окружения OPENAI_API_KEY'
        )
        return
    elif (
        settings['model_provider'] == 'anthropic'
        and not settings['anthropic_api_key']
    ):
        logger.error(
            'Anthropic API ключ не указан. Используйте --anthropic-api-key или установите переменную окружения ANTHROPIC_API_KEY'
        )
        return

    # Загрузка репозитория
    loader = GitHubLoader(
        owner=args.owner,
        repo=args.repo,
        github_token=settings['github_token'],
        branch=args.branch,
        filter_directories=args.filter_dirs,
        exclude_extensions=args.exclude_exts,
        include_extensions=args.include_exts,
    )

    documents = loader.load()

    if not documents:
        logger.error('Не удалось загрузить документы из репозитория')
        return

    # Предобработка документов
    processor = DocumentProcessor()
    processed_docs = processor.process(documents)

    # Построение и сохранение индекса
    index_path = args.index_path
    Path(index_path).mkdir(parents=True, exist_ok=True)

    builder = IndexBuilder(
        model_provider=settings['model_provider'],
        model_name=settings['model_name'],
        index_path=index_path,
    )
    builder.build_index(processed_docs)

    # Сохранение данных о репозитории
    save_source_info(
        index_path=index_path,
        source_type='github',
        total_documents=len(processed_docs),
        model_provider=settings['model_provider'],
        model_name=settings['model_name'],
        owner=args.owner,
        repo=args.repo,
        branch=args.branch,
    )

    logger.info(f'Индекс успешно создан и сохранен в {index_path}')


def index_local_command(
    args: argparse.Namespace, settings: dict[str, Any]
) -> None:
    """
    Выполнить команду индексации локальной директории.

    Args:
        args: Аргументы командной строки
        settings: Словарь с настройками
    """
    # Проверка пути к директории
    if not os.path.exists(args.directory) or not os.path.isdir(args.directory):
        logger.error(f'Указанная директория не существует: {args.directory}')
        return

    # Проверка API ключей в зависимости от выбранного провайдера модели
    if (
        settings['model_provider'] == 'openai'
        and not settings['openai_api_key']
    ):
        logger.error(
            'OpenAI API ключ не указан. Используйте --openai-api-key или установите переменную окружения OPENAI_API_KEY'
        )
        return
    elif (
        settings['model_provider'] == 'anthropic'
        and not settings['anthropic_api_key']
    ):
        logger.error(
            'Anthropic API ключ не указан. Используйте --anthropic-api-key или установите переменную окружения ANTHROPIC_API_KEY'
        )
        return

    # Загрузка файлов из директории
    loader = LocalDirectoryLoader(
        directory_path=args.directory,
        exclude_extensions=args.exclude_exts,
        include_extensions=args.include_exts,
    )

    documents = loader.load()

    if not documents:
        logger.error(
            'Не удалось загрузить документы из директории или директория пуста'
        )
        return

    # Предобработка документов
    processor = DocumentProcessor()
    processed_docs = processor.process(documents)

    # Построение и сохранение индекса
    index_path = args.index_path
    Path(index_path).mkdir(parents=True, exist_ok=True)

    builder = IndexBuilder(
        model_provider=settings['model_provider'],
        model_name=settings['model_name'],
        index_path=index_path,
    )

    builder.build_index(processed_docs)

    # Сохранение данных о директории
    save_source_info(
        index_path=index_path,
        source_type='local',
        total_documents=len(processed_docs),
        model_provider=settings['model_provider'],
        model_name=settings['model_name'],
        directory=args.directory,
    )

    logger.info(f'Индекс успешно создан и сохранен в {index_path}')


def query_command(args: argparse.Namespace, settings: dict[str, Any]) -> None:
    """
    Выполнить команду запроса к индексу.

    Args:
        args: Аргументы командной строки
        settings: Словарь с настройками
    """
    # Проверка существования индекса
    index_path = args.index_path
    if not os.path.exists(index_path):
        logger.error(f'Индекс не найден по пути {index_path}')
        return

    # Определение параметров модели для запроса
    query_model_provider = args.model_provider or settings['model_provider']
    query_model_name = args.model_name or settings['model_name']

    # Загрузка индекса
    from github_rag_explorer.indexing.builder import IndexLoader

    loader = IndexLoader(
        index_path=index_path,
        model_provider=query_model_provider,
        model_name=query_model_name,
    )

    index = loader.load()

    if not index:
        logger.error('Не удалось загрузить индекс')
        return

    # Вывод информации об источнике, если доступна
    source_info_path = Path(index_path) / 'source_info.json'
    if source_info_path.exists():
        try:
            with open(source_info_path) as f:
                source_info = json.load(f)

            source_type = source_info.get('type')
            if source_type == 'github':
                logger.info(
                    f'Запрос к индексу репозитория: {source_info.get("owner")}/{source_info.get("repo")} '
                    f'(ветка: {source_info.get("branch")})'
                )
            elif source_type == 'local':
                logger.info(
                    f'Запрос к индексу локальной директории: {source_info.get("directory")}'
                )
        except Exception as e:
            logger.warning(f'Не удалось загрузить информацию о источнике: {e}')

    # Выполнение запроса
    query_engine = QueryEngine(
        index=index,
        model_provider=query_model_provider,
        model_name=query_model_name,
    )

    response = query_engine.query(args.query, args.top_k)

    # Вывод ответа
    print('\n=== Ответ на запрос ===')
    print(response)
    print('======================\n')


def main():
    """Точка входа для CLI."""
    parser = argparse.ArgumentParser(
        description='RAG система для GitHub репозиториев и локальных директорий с использованием LlamaIndex'
    )

    # Общие аргументы
    parser.add_argument(
        '--config',
        type=str,
        default=DEFAULT_CONFIG_PATH,
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
        choices=['openai', 'anthropic', 'ollama'],
        help=f'Провайдер языковой модели (по умолчанию: {DEFAULT_MODEL_PROVIDER})',
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
        '--branch', type=str, default=DEFAULT_BRANCH, help='Ветка репозитория'
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
        default=DEFAULT_INDEX_PATH,
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
        default=DEFAULT_INDEX_PATH,
        help='Путь для сохранения индекса',
    )

    # Подпарсер для команды "query"
    query_parser = subparsers.add_parser(
        'query', help='Выполнить запрос к индексу'
    )
    query_parser.add_argument(
        '--index-path',
        type=str,
        default=DEFAULT_INDEX_PATH,
        help='Путь к индексу',
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
    config = load_config(args.config)

    # Настройка API ключей и параметров модели
    settings = setup_api_keys(args, config)

    # Обработка команд
    if args.command == 'index-github':
        index_github_command(args, settings)
    elif args.command == 'index-local':
        index_local_command(args, settings)
    elif args.command == 'query':
        query_command(args, settings)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
