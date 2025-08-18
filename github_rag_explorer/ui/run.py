import os

from streamlit.web import bootstrap

def main():
    # получаем текущую папку файла и добавляем app.py
    # к пути, чтобы запустить приложение
    current_directory = os.path.dirname(__file__)
    app = os.path.join(current_directory, 'app.py')
    bootstrap.run(
        app,
        is_hello=False,
        args=[],
        flag_options={},
    )

if __name__ == "__main__":
    main()