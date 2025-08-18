import json
import logging
import os
import sys
import time
from pathlib import Path

import streamlit as st

# Импортируем функции из основного скрипта
from github_rag import (
    build_index,
    load_github_repo,
    load_index,
    load_local_directory,
    preprocess_documents,
    run_query,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main():  # noqa: C901
    st.set_page_config(
        page_title='GitHub RAG Explorer',
        page_icon='🦙',
        layout='wide',
        initial_sidebar_state='expanded',
    )

    st.title('GitHub RAG Explorer 🦙')
    st.markdown("""
    Этот инструмент позволяет создать RAG (Retrieval Augmented Generation) систему для GitHub репозиториев,
    используя LlamaIndex. Загрузите репозиторий, постройте индекс и задавайте вопросы!
    """)

    # Сайдбар для API ключей и настроек
    with st.sidebar:
        st.header('Настройки')

        # API ключи
        openai_api_key = st.text_input(
            'OpenAI API Key',
            type='password',
            help='Введите ваш API ключ OpenAI',
        )
        anthropic_api_key = st.text_input(
            'Anthropic API Key',
            type='password',
            help='Введите ваш API ключ Anthropic',
        )
        github_token = st.text_input(
            'GitHub Token',
            type='password',
            help='Введите ваш персональный токен GitHub',
        )

        st.divider()

        # Настройки моделей
        st.subheader('Настройки моделей')
        model_provider = st.selectbox(
            'Провайдер модели',
            options=['openai', 'anthropic', 'ollama'],
            help='Выберите провайдера для языковой модели',
        )

        # Разные модели для разных провайдеров
        if model_provider == 'openai':
            model_name = st.selectbox(
                'Модель',
                options=[
                    'gpt-4o',
                    'gpt-4',
                    'gpt-4-turbo',
                    'o1',
                    'o3-mini',
                    'gpt-4.5-preview',
                ],
                help='Выберите модель OpenAI',
            )
        elif model_provider == 'anthropic':
            model_name = st.selectbox(
                'Модель',
                options=[
                    'claude-3-7-sonnet-latest',
                    'claude-3-5-sonnet-latest',
                    'claude-3-opus-latest',
                ],
                help='Выберите модель Anthropic',
            )
        else:  # ollama
            model_name = st.text_input(
                'Модель',
                value='llama3',
                help='Введите название модели Ollama (llama3, codellama, mistral и т.д.)',
            )

        st.divider()

        # Настройки индексации
        st.subheader('Настройки индексации')
        index_path = st.text_input(
            'Путь для сохранения индекса', value='./llama_index'
        )

        # Кнопка для сохранения настроек
        if st.button('Сохранить настройки'):
            if openai_api_key:
                os.environ['OPENAI_API_KEY'] = openai_api_key
                st.success('OpenAI API Key сохранен!')
            if anthropic_api_key:
                os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key
                st.success('Anthropic API Key сохранен!')
            if github_token:
                os.environ['GITHUB_TOKEN'] = github_token
                st.success('GitHub Token сохранен!')

            # Сохранение настроек в session_state
            st.session_state.model_provider = model_provider
            st.session_state.model_name = model_name
            st.success('Настройки модели сохранены!')

    # Проверка наличия необходимых API ключей
    if model_provider == 'openai' and not openai_api_key:
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            st.warning(
                'OpenAI API Key не указан. Пожалуйста, введите его в боковом меню.'
            )
        else:
            os.environ['OPENAI_API_KEY'] = openai_api_key

    if model_provider == 'anthropic' and not anthropic_api_key:
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            st.warning(
                'Anthropic API Key не указан. Пожалуйста, введите его в боковом меню.'
            )
        else:
            os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key

    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN')

    # Сохранение настроек модели в session_state
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = model_provider
        st.session_state.model_name = model_name

    # Основные вкладки
    tabs = [
        'Загрузка репозитория',
        'Загрузка локальной директории',
        'Запросы к индексу',
        'Информация о индексе',
    ]

    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = tabs[0]

    # Создаем кнопки-вкладки
    cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        if cols[i].button(tab, key=f'tab_{i}', use_container_width=True):
            st.session_state.active_tab = tab

    st.divider()

    # Содержимое вкладок
    if st.session_state.active_tab == 'Загрузка репозитория':
        st.header('Загрузка репозитория')

        col1, col2 = st.columns(2)
        with col1:
            owner = st.text_input(
                'Владелец репозитория', help='Например: jerryjliu'
            )
        with col2:
            repo = st.text_input(
                'Имя репозитория', help='Например: llama_index'
            )

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

        col1, col2 = st.columns(2)
        with col1:
            exclude_exts = st.text_input(
                'Исключаемые расширения (опционально)',
                value='.png,.jpg,.jpeg,.gif,.svg,.ico,.json,.ipynb,.pyc,.pyo,.pyd',
                help='Список расширений файлов для исключения, разделенный запятыми.',
            )
        with col2:
            include_exts = st.text_input(
                'Включаемые расширения (опционально)',
                value='',
                help='Список расширений файлов для включения, разделенный запятыми. Если заполнено, будут индексироваться ТОЛЬКО эти расширения.',
            )

        if st.button(
            'Загрузить репозиторий и построить индекс', type='primary'
        ):
            if not github_token:
                st.error(
                    'GitHub Token не указан. Пожалуйста, введите его в боковом меню.'
                )
            elif (
                st.session_state.model_provider == 'openai'
                and not os.environ.get('OPENAI_API_KEY')
            ) or (
                st.session_state.model_provider == 'anthropic'
                and not os.environ.get('ANTHROPIC_API_KEY')
            ):
                st.error(
                    f'API ключ для {st.session_state.model_provider} не указан. Пожалуйста, введите его в боковом меню.'
                )
            elif not owner or not repo:
                st.error('Пожалуйста, укажите владельца и имя репозитория.')
            else:
                # Преобразование строк в списки
                filter_dirs_list = (
                    [d.strip() for d in filter_dirs.split(',')]
                    if filter_dirs
                    else None
                )
                exclude_exts_list = (
                    [e.strip() for e in exclude_exts.split(',')]
                    if exclude_exts
                    else None
                )
                include_exts_list = (
                    [e.strip() for e in include_exts.split(',')]
                    if include_exts
                    else None
                )

                # Загрузка репозитория
                with st.spinner(
                    f'Загрузка репозитория {owner}/{repo} (ветка: {branch})...'
                ):
                    documents = load_github_repo(
                        github_token=github_token,
                        owner=owner,
                        repo=repo,
                        branch=branch,
                        filter_directories=filter_dirs_list,
                        exclude_extensions=exclude_exts_list,
                        include_extensions=include_exts_list,
                    )

                if not documents:
                    st.error(
                        'Не удалось загрузить документы из репозитория или репозиторий пуст.'
                    )
                else:
                    st.success(
                        f'Загружено {len(documents)} документов из репозитория.'
                    )

                    # Предобработка документов
                    st.subheader('Предобработка документов')
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    # Разбиваем документы на части для отслеживания прогресса
                    doc_count = len(documents)
                    processed_docs = []

                    for i, doc in enumerate(documents):
                        # Обновление прогресса
                        progress = (i + 1) / doc_count
                        progress_bar.progress(progress)
                        status_text.text(
                            f'Обработка документа {i + 1} из {doc_count}'
                        )

                        # Обработка одного документа
                        processed_doc = preprocess_documents([doc])
                        processed_docs.extend(processed_doc)

                    progress_bar.progress(1.0)
                    status_text.text(
                        f'Обработка завершена. Всего документов после обработки: {len(processed_docs)}'
                    )

                    # Построение индекса
                    st.subheader('Построение индекса')
                    # Создаем директорию для индекса, если она не существует
                    Path(index_path).mkdir(parents=True, exist_ok=True)

                    with st.spinner('Построение и сохранение индекса...'):
                        index = build_index(
                            processed_docs,
                            index_path,
                            st.session_state.model_provider,
                            st.session_state.model_name,
                        )

                    # Сохранение информации о репозитории
                    source_info = {
                        'type': 'github',
                        'owner': owner,
                        'repo': repo,
                        'branch': branch,
                        'total_documents': len(processed_docs),
                        'index_path': index_path,
                        'model_provider': st.session_state.model_provider,
                        'model_name': st.session_state.model_name,
                        'timestamp': str(time.time()),
                    }

                    # Сохранение информации в JSON файл
                    with open(Path(index_path) / 'source_info.json', 'w') as f:
                        json.dump(source_info, f, indent=4)

                    st.success(
                        f'Индекс успешно создан и сохранен в {index_path}'
                    )
                    st.session_state.index_path = index_path

                    # Предложение перейти на вкладку запросов
                    st.info(
                        "Теперь вы можете перейти на вкладку 'Запросы к индексу', чтобы задать вопросы."
                    )

                    # Автоматический переход на вкладку запросов
                    st.session_state.active_tab = 'Запросы к индексу'
                    st.experimental_rerun()

    elif st.session_state.active_tab == 'Загрузка локальной директории':
        st.header('Загрузка локальной директории')

        directory = st.text_input(
            'Путь к директории',
            help='Введите полный путь к локальной директории, которую нужно индексировать',
        )

        col1, col2 = st.columns(2)
        with col1:
            exclude_exts = st.text_input(
                'Исключаемые расширения (опционально)',
                value='.png,.jpg,.jpeg,.gif,.svg,.ico,.json,.ipynb,.pyc,.pyo,.pyd',
                help='Список расширений файлов для исключения, разделенный запятыми.',
                key='local_exclude_exts',
            )
        with col2:
            include_exts = st.text_input(
                'Включаемые расширения (опционально)',
                value='',
                help='Список расширений файлов для включения, разделенный запятыми. Если заполнено, будут индексироваться ТОЛЬКО эти расширения.',
                key='local_include_exts',
            )

        if st.button('Загрузить директорию и построить индекс', type='primary'):
            if not directory:
                st.error('Пожалуйста, укажите путь к директории.')
            elif not os.path.exists(directory) or not os.path.isdir(directory):
                st.error(f'Указанная директория не существует: {directory}')
            elif (
                st.session_state.model_provider == 'openai'
                and not os.environ.get('OPENAI_API_KEY')
            ) or (
                st.session_state.model_provider == 'anthropic'
                and not os.environ.get('ANTHROPIC_API_KEY')
            ):
                st.error(
                    f'API ключ для {st.session_state.model_provider} не указан. Пожалуйста, введите его в боковом меню.'
                )
            else:
                # Преобразование строк в списки
                exclude_exts_list = (
                    [e.strip() for e in exclude_exts.split(',')]
                    if exclude_exts
                    else None
                )
                include_exts_list = (
                    [e.strip() for e in include_exts.split(',')]
                    if include_exts
                    else None
                )

                # Загрузка файлов из директории
                with st.spinner(
                    f'Загрузка файлов из директории {directory}...'
                ):
                    documents = load_local_directory(
                        directory_path=directory,
                        exclude_extensions=exclude_exts_list,
                        include_extensions=include_exts_list,
                    )

                if not documents:
                    st.error(
                        'Не удалось загрузить документы из директории или директория пуста.'
                    )
                else:
                    st.success(
                        f'Загружено {len(documents)} документов из директории.'
                    )

                    # Предобработка документов
                    st.subheader('Предобработка документов')
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()

                    # Разбиваем документы на части для отслеживания прогресса
                    doc_count = len(documents)
                    processed_docs = []

                    for i, doc in enumerate(documents):
                        # Обновление прогресса
                        progress = (i + 1) / doc_count
                        progress_bar.progress(progress)
                        status_text.text(
                            f'Обработка документа {i + 1} из {doc_count}'
                        )

                        # Обработка одного документа
                        processed_doc = preprocess_documents([doc])
                        processed_docs.extend(processed_doc)

                    progress_bar.progress(1.0)
                    status_text.text(
                        f'Обработка завершена. Всего документов после обработки: {len(processed_docs)}'
                    )

                    # Построение индекса
                    st.subheader('Построение индекса')
                    # Создаем директорию для индекса, если она не существует
                    Path(index_path).mkdir(parents=True, exist_ok=True)

                    with st.spinner('Построение и сохранение индекса...'):
                        index = build_index(
                            processed_docs,
                            index_path,
                            st.session_state.model_provider,
                            st.session_state.model_name,
                        )

                    # Сохранение информации о директории
                    source_info = {
                        'type': 'local',
                        'directory': directory,
                        'total_documents': len(processed_docs),
                        'index_path': index_path,
                        'model_provider': st.session_state.model_provider,
                        'model_name': st.session_state.model_name,
                        'timestamp': str(time.time()),
                    }

                    # Сохранение информации в JSON файл
                    with open(Path(index_path) / 'source_info.json', 'w') as f:
                        json.dump(source_info, f, indent=4)

                    st.success(
                        f'Индекс успешно создан и сохранен в {index_path}'
                    )
                    st.session_state.index_path = index_path

                    # Предложение перейти на вкладку запросов
                    st.info(
                        "Теперь вы можете перейти на вкладку 'Запросы к индексу', чтобы задать вопросы."
                    )

                    # Автоматический переход на вкладку запросов
                    st.session_state.active_tab = 'Запросы к индексу'
                    st.experimental_rerun()

    elif st.session_state.active_tab == 'Запросы к индексу':
        st.header('Запросы к индексу')

        # Выбор пути к индексу
        if 'index_path' not in st.session_state:
            st.session_state.index_path = index_path

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
            source_info_path = Path(custom_index_path) / 'source_info.json'
            if source_info_path.exists():
                with open(source_info_path) as f:
                    source_info = json.load(f)

                # Отображение информации в зависимости от типа источника
                if source_info.get('type') == 'github':
                    st.info(
                        f'Индекс для репозитория: **{source_info.get("owner", "N/A")}/{source_info.get("repo", "N/A")}** '
                        f'(ветка: {source_info.get("branch", "N/A")})\n\n'
                        f'Всего документов: {source_info.get("total_documents", "N/A")}\n\n'
                        f'Модель: {source_info.get("model_provider", "N/A")} / {source_info.get("model_name", "N/A")}'
                    )
                elif source_info.get('type') == 'local':
                    st.info(
                        f'Индекс для локальной директории: **{source_info.get("directory", "N/A")}**\n\n'
                        f'Всего документов: {source_info.get("total_documents", "N/A")}\n\n'
                        f'Модель: {source_info.get("model_provider", "N/A")} / {source_info.get("model_name", "N/A")}'
                    )

            # Опции для запросов
            model_col1, model_col2 = st.columns(2)
            with model_col1:
                query_model_provider = st.selectbox(
                    'Провайдер модели для запроса',
                    options=['openai', 'anthropic', 'ollama'],
                    index=['openai', 'anthropic', 'ollama'].index(
                        st.session_state.model_provider
                    )
                    if st.session_state.model_provider
                    in ['openai', 'anthropic', 'ollama']
                    else 0,
                )
            with model_col2:
                if query_model_provider == 'openai':
                    query_model_name = st.selectbox(
                        'Модель для запроса',
                        options=[
                            'gpt-4o',
                            'gpt-4',
                            'gpt-4-turbo',
                            'o1',
                            'o3-mini',
                            'gpt-4.5-preview',
                        ],
                    )
                elif query_model_provider == 'anthropic':
                    query_model_name = st.selectbox(
                        'Модель для запроса',
                        options=[
                            'claude-3-7-sonnet-latest',
                            'claude-3-5-sonnet-latest',
                            'claude-3-opus-latest',
                        ],
                    )
                else:  # ollama
                    query_model_name = st.text_input(
                        'Модель для запроса', value='llama3'
                    )

            # Загрузка индекса
            if (
                'index' not in st.session_state
                or st.session_state.index_path != custom_index_path
            ):
                with st.spinner('Загрузка индекса...'):
                    index = load_index(
                        custom_index_path,
                        query_model_provider,
                        query_model_name,
                    )
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
                            response = run_query(
                                st.session_state.index,
                                query,
                                top_k,
                                query_model_provider,
                                query_model_name,
                            )

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
                    st.divider()
                    st.subheader('История запросов')

                    for item in reversed(st.session_state.query_history):
                        with st.expander(
                            f'Запрос: {item["query"][:50]}{"..." if len(item["query"]) > 50 else ""}'
                        ):
                            st.markdown(f'**Запрос:** {item["query"]}')
                            st.markdown(f'**Ответ:** {item["response"]}')

    elif st.session_state.active_tab == 'Информация о индексе':
        st.header('Информация о индексе')

        # Выбор пути к индексу
        if 'index_path' not in st.session_state:
            st.session_state.index_path = index_path

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
            source_info_path = Path(custom_index_path) / 'source_info.json'
            if source_info_path.exists():
                with open(source_info_path, 'rb') as f:
                    source_info = json.load(f)

                # Отображение информации о индексированном источнике
                st.subheader('Основная информация')

                if source_info.get('type') == 'github':
                    st.markdown('**Тип источника:** GitHub репозиторий')
                    st.markdown(
                        f'**Репозиторий:** {source_info.get("owner", "N/A")}/{source_info.get("repo", "N/A")}'
                    )
                    st.markdown(
                        f'**Ветка:** {source_info.get("branch", "N/A")}'
                    )
                elif source_info.get('type') == 'local':
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
                st.markdown(
                    f'**Модель:** {source_info.get("model_name", "N/A")}'
                )

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
                    st.markdown(
                        f'- {file.name} ({file.stat().st_size / 1024:.2f} KB)'
                    )

                # Опции
                st.subheader('Опции')
                if st.button('Удалить индекс', type='secondary'):
                    confirm = st.checkbox('Подтвердите удаление индекса')
                    if confirm:
                        import shutil

                        try:
                            shutil.rmtree(custom_index_path)
                            st.success(
                                f'Индекс успешно удален из {custom_index_path}'
                            )
                            # Удаление сохраненного пути
                            if 'index_path' in st.session_state:
                                del st.session_state.index_path
                            if 'index' in st.session_state:
                                del st.session_state.index
                            st.rerun()
                        except Exception as e:
                            st.error(f'Ошибка при удалении индекса: {e}')


if __name__ == '__main__':
    main()
