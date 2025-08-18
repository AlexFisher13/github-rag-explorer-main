"""
Главное приложение Streamlit.
"""

import logging
import os
import sys

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import bootstrap

from github_rag_explorer.constants import UI_TABS
from github_rag_explorer.ui.components import (
    render_header,
    render_sidebar,
    render_tabs,
    setup_page_config,
)
from github_rag_explorer.ui.pages import (
    github_repo_page,
    index_info_page,
    local_directory_page,
    query_page,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# Настройка страницы
setup_page_config()

# Отрисовка заголовка
render_header()

# Отрисовка боковой панели
settings = render_sidebar()

# Проверка API ключей в переменных окружения
if not settings['openai_api_key']:
    settings['openai_api_key'] = os.environ.get('OPENAI_API_KEY')

if not settings['anthropic_api_key']:
    settings['anthropic_api_key'] = os.environ.get('ANTHROPIC_API_KEY')

if not settings['github_token']:
    settings['github_token'] = os.environ.get('GITHUB_TOKEN')

# Сохранение настроек модели в session_state
if 'model_provider' not in st.session_state:
    st.session_state.model_provider = settings['model_provider']
    st.session_state.model_name = settings['model_name']

# Отрисовка вкладок
active_tab = render_tabs(UI_TABS)

# Отрисовка содержимого активной вкладки
if active_tab == 'Загрузка репозитория':
    github_repo_page(settings)
elif active_tab == 'Загрузка локальной директории':
    local_directory_page(settings)
elif active_tab == 'Запросы к индексу':
    query_page(settings)
elif active_tab == 'Информация о индексе':
    index_info_page(settings)
