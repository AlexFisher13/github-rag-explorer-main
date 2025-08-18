"""
Модули страниц пользовательского интерфейса.
"""

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any

import streamlit as st

from github_rag_explorer.data.loader import GitHubLoader, LocalDirectoryLoader
from github_rag_explorer.data.processor import DocumentProcessor
from github_rag_explorer.indexing.builder import IndexBuilder, save_source_info
from github_rag_explorer.indexing.query import QueryEngine, SourceDetail
from github_rag_explorer.ui.components import (
    process_file_filters,
    render_file_filters,
    render_model_selection,
    render_query_history,
    render_source_info,
)

logger = logging.getLogger(__name__)


def github_repo_page(settings: dict[str, Any]):
    """
    Страница загрузки репозитория GitHub.

    Args:
        settings: Словарь с настройками приложения
    """
    st.header('Загрузка репозитория')

    col1, col2 = st.columns(2)
    with col1:
        owner = st.text_input(
            'Владелец репозитория', help='Например: jerryjliu'
        )
    with col2:
        repo = st.text_input('Имя репозитория', help='Например: llama_index')

    col1, col2 = st.columns(2)
    with col1:
        branch = st.text_input(
            'Ветка', value='main', help='Имя ветки для загрузки'
        )
    with col2:
        filter_dirs = st.text_input(
            'Фильтр директорий (опционально)',
            help='Список директорий для включения, разделенный запятыми. Оставьте пустым для загрузки всего репозитория.',
        )

    # Фильтры файлов
    exclude_exts, include_exts = render_file_filters()

    # Кнопка для запуска индексации
    if st.button('Загрузить репозиторий и построить индекс', type='primary'):
        # Проверка необходимых значений
        github_token = settings['github_token'] or os.environ.get(
            'GITHUB_TOKEN'
        )
        if not github_token:
            st.error(
                'GitHub Token не указан. Пожалуйста, введите его в боковом меню.'
            )
        elif (
            settings['model_provider'] == 'openai'
            and not os.environ.get('OPENAI_API_KEY')
        ) or (
            settings['model_provider'] == 'anthropic'
            and not os.environ.get('ANTHROPIC_API_KEY')
        ):
            st.error(
                f'API ключ для {settings["model_provider"]} не указан. Пожалуйста, введите его в боковом меню.'
            )
        elif not owner or not repo:
            st.error('Пожалуйста, укажите владельца и имя репозитория.')
        else:
            # Обработка фильтров
            filter_dirs_list = (
                [d.strip() for d in filter_dirs.split(',')]
                if filter_dirs
                else None
            )
            exclude_exts_list, include_exts_list = process_file_filters(
                exclude_exts, include_exts
            )

            # Загрузка репозитория
            with st.spinner(
                f'Загрузка репозитория {owner}/{repo} (ветка: {branch})...'
            ):
                loader = GitHubLoader(
                    owner=owner,
                    repo=repo,
                    github_token=github_token,
                    branch=branch,
                    filter_directories=filter_dirs_list,
                    exclude_extensions=exclude_exts_list,
                    include_extensions=include_exts_list,
                )
                documents = loader.load()

            if not documents:
                st.error(
                    'Не удалось загрузить документы из репозитория или репозиторий пуст.'
                )
            else:
                st.success(
                    f'Загружено {len(documents)} документов из репозитория.'
                )

                # Предобработка документов
                processor = DocumentProcessor()
                with st.spinner('Предобработка документов...'):
                    processed_docs = processor.process(documents)

                st.success(
                    f'Предобработка завершена. Всего документов после обработки: {len(processed_docs)}'
                )

                # Построение индекса
                st.subheader('Построение индекса')
                index_path = settings['index_path']
                Path(index_path).mkdir(parents=True, exist_ok=True)

                with st.spinner('Построение и сохранение индекса...'):
                    builder = IndexBuilder(
                        model_provider=settings['model_provider'],
                        model_name=settings['model_name'],
                        index_path=index_path,
                    )
                    builder.build_index(processed_docs)

                # Сохранение информации о репозитории
                save_source_info(
                    index_path=index_path,
                    source_type='github',
                    total_documents=len(processed_docs),
                    model_provider=settings['model_provider'],
                    model_name=settings['model_name'],
                    owner=owner,
                    repo=repo,
                    branch=branch,
                )

                st.success(f'Индекс успешно создан и сохранен в {index_path}')
                st.session_state.index_path = index_path

                # Предложение перейти на вкладку запросов
                st.info(
                    "Теперь вы можете перейти на вкладку 'Запросы к индексу', чтобы задать вопросы."
                )

                # Автоматический переход на вкладку запросов
                st.session_state.active_tab = 'Запросы к индексу'
                st.rerun()


def local_directory_page(settings: dict[str, Any]):
    """
    Страница загрузки локальной директории.

    Args:
        settings: Словарь с настройками приложения
    """
    st.header('Загрузка локальной директории')

    directory = st.text_input(
        'Путь к директории',
        help='Введите полный путь к локальной директории, которую нужно индексировать',
    )

    # Фильтры файлов
    exclude_exts, include_exts = render_file_filters()

    # Кнопка для запуска индексации
    if st.button('Загрузить директорию и построить индекс', type='primary'):
        # Проверка необходимых значений
        if not directory:
            st.error('Пожалуйста, укажите путь к директории.')
        elif not os.path.exists(directory) or not os.path.isdir(directory):
            st.error(f'Указанная директория не существует: {directory}')
        elif (
            settings['model_provider'] == 'openai'
            and not os.environ.get('OPENAI_API_KEY')
        ) or (
            settings['model_provider'] == 'anthropic'
            and not os.environ.get('ANTHROPIC_API_KEY')
        ):
            st.error(
                f'API ключ для {settings["model_provider"]} не указан. Пожалуйста, введите его в боковом меню.'
            )
        else:
            # Обработка фильтров
            exclude_exts_list, include_exts_list = process_file_filters(
                exclude_exts, include_exts
            )

            # Загрузка файлов из директории
            with st.spinner(f'Загрузка файлов из директории {directory}...'):
                loader = LocalDirectoryLoader(
                    directory_path=directory,
                    exclude_extensions=exclude_exts_list,
                    include_extensions=include_exts_list,
                )
                documents = loader.load()

            if not documents:
                st.error(
                    'Не удалось загрузить документы из директории или директория пуста.'
                )
            else:
                st.success(
                    f'Загружено {len(documents)} документов из директории.'
                )

                # Предобработка документов
                processor = DocumentProcessor()
                with st.spinner('Предобработка документов...'):
                    processed_docs = processor.process(documents)

                st.success(
                    f'Предобработка завершена. Всего документов после обработки: {len(processed_docs)}'
                )

                # Построение индекса
                st.subheader('Построение индекса')
                index_path = settings['index_path']
                Path(index_path).mkdir(parents=True, exist_ok=True)

                with st.spinner('Построение и сохранение индекса...'):
                    builder = IndexBuilder(
                        model_provider=settings['model_provider'],
                        model_name=settings['model_name'],
                        index_path=index_path,
                    )
                    builder.build_index(processed_docs)

                # Сохранение информации о директории
                save_source_info(
                    index_path=index_path,
                    source_type='local',
                    total_documents=len(processed_docs),
                    model_provider=settings['model_provider'],
                    model_name=settings['model_name'],
                    directory=directory,
                )

                st.success(f'Индекс успешно создан и сохранен в {index_path}')
                st.session_state.index_path = index_path

                # Предложение перейти на вкладку запросов
                st.info(
                    "Теперь вы можете перейти на вкладку 'Запросы к индексу', чтобы задать вопросы."
                )

                # Автоматический переход на вкладку запросов
                st.session_state.active_tab = 'Запросы к индексу'
                st.rerun()


def query_page(settings: dict[str, Any]):
    """
    Страница запросов к индексу.

    Args:
        settings: Словарь с настройками приложения
    """
    st.header('Запросы к индексу')

    # Выбор пути к индексу
    if 'index_path' not in st.session_state:
        st.session_state.index_path = settings['index_path']

    custom_index_path = st.text_input(
        'Путь к индексу',
        value=st.session_state.index_path,
        help='Путь к директории с сохраненным индексом.',
    )

    if not Path(custom_index_path).exists():
        st.warning(
            f'Директория индекса не найдена по пути {custom_index_path}. Пожалуйста, сначала создайте индекс.'
        )
    else:
        # Загрузка информации об источнике
        source_info = render_source_info(custom_index_path)

        if source_info:
            # Отображение информации о источнике
            source_details = SourceDetail.format_source_info(source_info)
            st.info(source_details)

        # Выбор модели для запроса
        query_model_provider, query_model_name = render_model_selection()

        # Загрузка индекса
        if (
            'index' not in st.session_state
            or st.session_state.index_path != custom_index_path
        ):
            from github_rag_explorer.indexing.builder import IndexLoader

            with st.spinner('Загрузка индекса...'):
                loader = IndexLoader(
                    index_path=custom_index_path,
                    model_provider=query_model_provider,
                    model_name=query_model_name,
                )
                index = loader.load()

            if index:
                st.session_state.index = index
                st.session_state.index_path = custom_index_path
                st.success('Индекс успешно загружен!')
            else:
                st.error(
                    'Не удалось загрузить индекс. Пожалуйста, проверьте путь.'
                )

        # Запрос к индексу
        if 'index' in st.session_state:
            query = st.text_area(
                'Введите ваш запрос',
                height=100,
                placeholder='Например: Как использовать VectorStoreIndex?',
            )
            top_k = st.slider(
                'Количество результатов', min_value=1, max_value=20, value=5
            )

            if st.button('Выполнить запрос', type='primary'):
                if not query:
                    st.error('Пожалуйста, введите запрос.')
                else:
                    with st.spinner('Выполнение запроса...'):
                        query_engine = QueryEngine(
                            index=st.session_state.index,
                            model_provider=query_model_provider,
                            model_name=query_model_name,
                        )
                        response = query_engine.query(query, top_k)

                    st.subheader('Ответ')
                    st.markdown(response)

                    # Сохранение истории запросов
                    if 'query_history' not in st.session_state:
                        st.session_state.query_history = []

                    st.session_state.query_history.append(
                        {
                            'query': query,
                            'response': response,
                            'timestamp': time.time(),
                        }
                    )

            # История запросов
            if (
                'query_history' in st.session_state
                and st.session_state.query_history
            ):
                render_query_history(st.session_state.query_history)


def index_info_page(settings: dict[str, Any]):
    """
    Страница с информацией об индексе.

    Args:
        settings: Словарь с настройками приложения
    """
    st.header('Информация о индексе')

    # Выбор пути к индексу
    if 'index_path' not in st.session_state:
        st.session_state.index_path = settings['index_path']

    custom_index_path = st.text_input(
        'Путь к индексу',
        value=st.session_state.index_path,
        help='Путь к директории с сохраненным индексом.',
    )

    if not Path(custom_index_path).exists():
        st.warning(
            f'Директория индекса не найдена по пути {custom_index_path}. Пожалуйста, сначала создайте индекс.'
        )
    else:
        # Загрузка информации об источнике
        source_info = render_source_info(custom_index_path)

        if source_info:
            # Отображение информации о индексированном источнике
            st.subheader('Основная информация')

            source_type = source_info.get('type', 'unknown')
            if source_type == 'github':
                st.markdown('**Тип источника:** GitHub репозиторий')
                st.markdown(
                    f'**Репозиторий:** {source_info.get("owner", "N/A")}/{source_info.get("repo", "N/A")}'
                )
                st.markdown(f'**Ветка:** {source_info.get("branch", "N/A")}')
            elif source_type == 'local':
                st.markdown('**Тип источника:** Локальная директория')
                st.markdown(
                    f'**Директория:** {source_info.get("directory", "N/A")}'
                )

            st.markdown(
                f'**Всего документов:** {source_info.get("total_documents", "N/A")}'
            )
            st.markdown(
                f'**Провайдер модели:** {source_info.get("model_provider", "N/A")}'
            )
            st.markdown(f'**Модель:** {source_info.get("model_name", "N/A")}')

            # Информация о времени создания
            if 'timestamp' in source_info:
                import datetime

                timestamp = float(source_info.get('timestamp', 0))
                dt = datetime.datetime.fromtimestamp(timestamp)
                st.markdown(
                    f'**Дата создания:** {dt.strftime("%Y-%m-%d %H:%M:%S")}'
                )

        # Дополнительная информация о индексе
        st.subheader('Файлы индекса')
        index_files = list(Path(custom_index_path).glob('*'))
        for file in index_files:
            st.markdown(f'- {file.name} ({file.stat().st_size / 1024:.2f} KB)')

        # Опции
        st.subheader('Опции')
        if st.button('Удалить индекс', type='secondary'):
            confirm = st.checkbox('Подтвердите удаление индекса')
            if confirm:
                try:
                    shutil.rmtree(custom_index_path)
                    st.success(f'Индекс успешно удален из {custom_index_path}')
                    # Удаление сохраненного пути
                    if 'index_path' in st.session_state:
                        del st.session_state.index_path
                    if 'index' in st.session_state:
                        del st.session_state.index
                    st.rerun()
                except Exception as e:
                    st.error(f'Ошибка при удалении индекса: {e}')
