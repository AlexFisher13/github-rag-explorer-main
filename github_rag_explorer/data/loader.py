"""
Модули для загрузки данных из GitHub репозиториев и локальных директорий.
"""

import logging
import os
from pathlib import Path

from github_rag_explorer.constants import (
    DEFAULT_BRANCH,
    DEFAULT_EXCLUDE_EXTENSIONS,
)
from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.readers.github import GithubClient, GithubRepositoryReader

logger = logging.getLogger(__name__)


class BaseLoader:
    """Базовый класс для загрузчиков данных."""

    def load(self) -> list[Document]:
        """
        Загрузить данные из источника.

        Returns:
            Список объектов Document
        """
        raise NotImplementedError('Метод должен быть реализован в подклассе')


class GitHubLoader(BaseLoader):
    """Класс для загрузки данных из GitHub репозитория."""

    def __init__(
        self,
        owner: str,
        repo: str,
        github_token: str,
        branch: str = DEFAULT_BRANCH,
        filter_directories: list[str] | None = None,
        exclude_extensions: list[str] | None = None,
        include_extensions: list[str] | None = None,
        verbose: bool = True,
    ):
        """
        Инициализация загрузчика GitHub.

        Args:
            owner: Владелец репозитория
            repo: Имя репозитория
            github_token: Токен GitHub для доступа к API
            branch: Ветка репозитория
            filter_directories: Список директорий для включения
            exclude_extensions: Список расширений файлов для исключения
            include_extensions: Список расширений файлов для включения
            verbose: Включить подробный вывод
        """
        self.owner = owner
        self.repo = repo
        self.github_token = github_token
        self.branch = branch
        self.filter_directories = filter_directories
        self.exclude_extensions = (
            exclude_extensions or DEFAULT_EXCLUDE_EXTENSIONS
        )
        self.include_extensions = include_extensions
        self.verbose = verbose

    def load(self) -> list[Document]:
        """
        Загрузить файлы из GitHub репозитория.

        Returns:
            Список объектов Document
        """
        logger.info(
            f'Загрузка репозитория {self.owner}/{self.repo} (ветка: {self.branch})'
        )

        try:
            # Настройка GitHub клиента
            github_client = GithubClient(
                github_token=self.github_token, verbose=self.verbose
            )

            # Настройка фильтров
            include_filter_type = GithubRepositoryReader.FilterType.INCLUDE
            exclude_filter_type = GithubRepositoryReader.FilterType.EXCLUDE

            # Настройка фильтра директорий
            if self.filter_directories is None:
                filter_directories_tuple = None
            else:
                filter_directories_tuple = (
                    self.filter_directories,
                    include_filter_type,
                )

            # Настройка фильтров расширений файлов
            extension_filters = []

            # Обработка включаемых расширений
            if self.include_extensions:
                extension_filters.append(
                    (self.include_extensions, include_filter_type)
                )

            # Обработка исключаемых расширений
            if self.exclude_extensions and not self.include_extensions:
                extension_filters.append(
                    (self.exclude_extensions, exclude_filter_type)
                )

            # Инициализация загрузчика GitHub
            reader = GithubRepositoryReader(
                github_client=github_client,
                owner=self.owner,
                repo=self.repo,
                use_parser=False,
                verbose=self.verbose,
                filter_directories=filter_directories_tuple,
                filter_file_extensions=extension_filters[0]
                if extension_filters
                else None,
            )

            # Загрузка данных
            documents = reader.load_data(branch=self.branch)

            # Применение второго фильтра, если есть
            if len(extension_filters) > 1:
                filtered_docs = []
                ext_list, filter_type = extension_filters[1]

                for doc in documents:
                    file_path = doc.metadata.get('file_path', '')
                    file_ext = Path(file_path).suffix.lower()

                    if (
                        filter_type == exclude_filter_type
                        and file_ext in ext_list
                    ):
                        continue
                    elif (
                        filter_type == include_filter_type
                        and file_ext not in ext_list
                    ):
                        continue

                    filtered_docs.append(doc)

                documents = filtered_docs

            logger.info(f'Загружено {len(documents)} документов из репозитория')
            return documents

        except Exception as e:
            logger.error(f'Ошибка при загрузке репозитория: {e}')
            return []


class LocalDirectoryLoader(BaseLoader):
    """Класс для загрузки данных из локальной директории."""

    def __init__(
        self,
        directory_path: str,
        exclude_extensions: list[str] | None = None,
        include_extensions: list[str] | None = None,
        recursive: bool = True,
        exclude_hidden: bool = True,
    ):
        """
        Инициализация загрузчика локальной директории.

        Args:
            directory_path: Путь к директории
            exclude_extensions: Список расширений файлов для исключения
            include_extensions: Список расширений файлов для включения
            recursive: Рекурсивный обход директорий
            exclude_hidden: Исключать скрытые файлы
        """
        self.directory_path = directory_path
        self.exclude_extensions = (
            exclude_extensions or DEFAULT_EXCLUDE_EXTENSIONS
        )
        self.include_extensions = include_extensions
        self.recursive = recursive
        self.exclude_hidden = exclude_hidden

    def load(self) -> list[Document]:
        """
        Загрузить файлы из локальной директории.

        Returns:
            Список объектов Document
        """
        logger.info(f'Загрузка файлов из директории {self.directory_path}')

        try:
            # Проверка существования директории
            if not os.path.exists(self.directory_path) or not os.path.isdir(
                self.directory_path
            ):
                logger.error(f'Директория не существует: {self.directory_path}')
                return []

            # Настройка параметров для SimpleDirectoryReader
            reader_params = {
                'input_dir': self.directory_path,
                'recursive': self.recursive,
                'exclude_hidden': self.exclude_hidden,
            }

            # Если указаны расширения для включения, используем их как required_exts
            if self.include_extensions:
                reader_params['required_exts'] = self.include_extensions

            # Если указаны расширения для исключения, создаем паттерны исключения
            if self.exclude_extensions and not self.include_extensions:
                # Создаем паттерны glob для исключения
                exclude_patterns = []
                for ext in self.exclude_extensions:
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
