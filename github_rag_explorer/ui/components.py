"""
Компоненты пользовательского интерфейса на Streamlit.
"""

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import streamlit as st

from github_rag_explorer.constants import (
    DEFAULT_EXCLUDE_EXTENSIONS,
    DEFAULT_MODEL_NAMES,
    DEFAULT_MODEL_PROVIDER,
    LLM_MODELS,
    LLM_PROVIDERS,
)


def setup_page_config():
    """Настройка конфигурации страницы."""
    st.set_page_config(
        page_title='GitHub RAG Explorer',
        page_icon='🦙',
        layout='wide',
        initial_sidebar_state='expanded',
    )


def render_header():
    """Отрисовка заголовка приложения."""
    st.title('GitHub RAG Explorer 🦙')
    st.markdown("""
    Этот инструмент позволяет создать RAG (Retrieval Augmented Generation) систему для GitHub репозиториев,
    используя LlamaIndex. Загрузите репозиторий, постройте индекс и задавайте вопросы!
    """)


def render_sidebar() -> dict[str, str]:
    """
    Отрисовка боковой панели с настройками.

    Returns:
        Словарь с настройками
    """
    settings = {}

    with st.sidebar:
        st.header('Настройки')

        # API ключи
        settings['openai_api_key'] = st.text_input(
            'OpenAI API Key',
            type='password',
            help='Введите ваш API ключ OpenAI',
        )
        settings['anthropic_api_key'] = st.text_input(
            'Anthropic API Key',
            type='password',
            help='Введите ваш API ключ Anthropic',
        )
        settings['github_token'] = st.text_input(
            'GitHub Token',
            type='password',
            help='Введите ваш персональный токен GitHub',
        )

        st.divider()

        # Настройки моделей
        st.subheader('Настройки моделей')
        settings['model_provider'] = st.selectbox(
            'Провайдер модели',
            options=LLM_PROVIDERS,
            help='Выберите провайдера для языковой модели',
        )

        # Разные модели для разных провайдеров
        model_provider = settings['model_provider']
        if model_provider == 'openai':
            settings['model_name'] = st.selectbox(
                'Модель',
                options=LLM_MODELS['openai'],
                help='Выберите модель OpenAI',
            )
        elif model_provider == 'anthropic':
            settings['model_name'] = st.selectbox(
                'Модель',
                options=LLM_MODELS['anthropic'],
                help='Выберите модель Anthropic',
            )
        else:  # ollama
            settings['model_name'] = st.text_input(
                'Модель',
                value=DEFAULT_MODEL_NAMES['ollama'],
                help='Введите название модели Ollama (llama3, codellama, mistral и т.д.)',
            )

        st.divider()

        # Настройки индексации
        st.subheader('Настройки индексации')
        settings['index_path'] = st.text_input(
            'Путь для сохранения индекса', value='./llama_index'
        )

        # Кнопка для сохранения настроек
        if st.button('Сохранить настройки'):
            if settings['openai_api_key']:
                os.environ['OPENAI_API_KEY'] = settings['openai_api_key']
                st.success('OpenAI API Key сохранен!')
            if settings['anthropic_api_key']:
                os.environ['ANTHROPIC_API_KEY'] = settings['anthropic_api_key']
                st.success('Anthropic API Key сохранен!')
            if settings['github_token']:
                os.environ['GITHUB_TOKEN'] = settings['github_token']
                st.success('GitHub Token сохранен!')

            # Сохранение настроек в session_state
            st.session_state.model_provider = settings['model_provider']
            st.session_state.model_name = settings['model_name']
            st.success('Настройки модели сохранены!')

    return settings


def render_tabs(tabs: list[str]) -> str:
    """
    Отрисовка вкладок приложения.

    Args:
        tabs: Список названий вкладок

    Returns:
        Название активной вкладки
    """
    # Инициализация активной вкладки
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = tabs[0]

    # Создаем кнопки-вкладки
    cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        if cols[i].button(tab, key=f'tab_{i}', use_container_width=True):
            st.session_state.active_tab = tab

    st.divider()

    return st.session_state.active_tab


def render_file_filters() -> tuple[str, str]:
    """
    Отрисовка полей для фильтрации файлов.

    Returns:
        Кортеж (exclude_extensions, include_extensions)
    """
    col1, col2 = st.columns(2)

    with col1:
        exclude_exts = st.text_input(
            'Исключаемые расширения (опционально)',
            value=','.join(DEFAULT_EXCLUDE_EXTENSIONS),
            help='Список расширений файлов для исключения, разделенный запятыми.',
        )
    with col2:
        include_exts = st.text_input(
            'Включаемые расширения (опционально)',
            value='',
            help='Список расширений файлов для включения, разделенный запятыми. Если заполнено, будут индексироваться ТОЛЬКО эти расширения.',
        )

    return exclude_exts, include_exts


def process_file_filters(
    exclude_exts: str, include_exts: str
) -> tuple[list[str], list[str]]:
    """
    Обработка строковых фильтров файлов в списки.

    Args:
        exclude_exts: Строка с исключаемыми расширениями
        include_exts: Строка с включаемыми расширениями

    Returns:
        Кортеж (exclude_exts_list, include_exts_list)
    """
    exclude_exts_list = (
        [e.strip() for e in exclude_exts.split(',')] if exclude_exts else None
    )
    include_exts_list = (
        [e.strip() for e in include_exts.split(',')] if include_exts else None
    )

    return exclude_exts_list, include_exts_list


def render_processing_progress(
    total_docs: int, process_func: Callable[[int], Any]
):
    """
    Отрисовка индикатора прогресса обработки документов.

    Args:
        total_docs: Общее количество документов
        process_func: Функция обработки одного документа, принимает индекс
    """
    st.subheader('Предобработка документов')
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    for i in range(total_docs):
        # Обновление прогресса
        progress = (i + 1) / total_docs
        progress_bar.progress(progress)
        status_text.text(f'Обработка документа {i + 1} из {total_docs}')

        # Вызов функции обработки
        process_func(i)

    progress_bar.progress(1.0)
    status_text.text(f'Обработка завершена. Всего документов: {total_docs}')


def render_model_selection() -> tuple[str, str]:
    """
    Отрисовка полей выбора модели.

    Returns:
        Кортеж (model_provider, model_name)
    """
    model_col1, model_col2 = st.columns(2)

    with model_col1:
        # Получаем провайдер из session_state или используем значение по умолчанию
        default_provider = st.session_state.get(
            'model_provider', DEFAULT_MODEL_PROVIDER
        )
        provider_index = (
            LLM_PROVIDERS.index(default_provider)
            if default_provider in LLM_PROVIDERS
            else 0
        )

        query_model_provider = st.selectbox(
            'Провайдер модели для запроса',
            options=LLM_PROVIDERS,
            index=provider_index,
        )

    with model_col2:
        if query_model_provider == 'openai':
            query_model_name = st.selectbox(
                'Модель для запроса', options=LLM_MODELS['openai']
            )
        elif query_model_provider == 'anthropic':
            query_model_name = st.selectbox(
                'Модель для запроса', options=LLM_MODELS['anthropic']
            )
        else:  # ollama
            query_model_name = st.text_input(
                'Модель для запроса', value=DEFAULT_MODEL_NAMES['ollama']
            )

    return query_model_provider, query_model_name


def render_source_info(index_path: str) -> dict[str, Any] | None:
    """
    Отображение информации об индексированном источнике.

    Args:
        index_path: Путь к индексу

    Returns:
        Словарь с информацией о источнике или None
    """
    source_info_path = Path(index_path) / 'source_info.json'

    if source_info_path.exists():
        with open(source_info_path) as f:
            source_info = json.load(f)
        return source_info

    return None


def render_query_history(query_history: list[dict[str, Any]]):
    """
    Отрисовка истории запросов.

    Args:
        query_history: Список запросов и ответов
    """
    if query_history:
        st.divider()
        st.subheader('История запросов')

        for item in reversed(query_history):
            with st.expander(
                f'Запрос: {item["query"][:50]}{"..." if len(item["query"]) > 50 else ""}'
            ):
                st.markdown(f'**Запрос:** {item["query"]}')
                st.markdown(f'**Ответ:** {item["response"]}')
