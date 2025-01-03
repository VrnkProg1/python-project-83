import psycopg2
from flask import render_template, request, flash, redirect, url_for, Flask
from dotenv import load_dotenv
import os
from datetime import datetime
import validators
import requests
from bs4 import BeautifulSoup

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
app.secret_key = os.getenv('SECRET_KEY')


def add_url_to_db(url):
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                created_at = datetime.now()
                cur.execute('''
                    INSERT INTO urls (name, created_at)
                    VALUES (%s, %s)
                ''', (url, created_at))
                conn.commit()
    except Exception as e:
        flash(f"Ошибка при добавлении URL: {str(e)}")
        raise


def get_id(url):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM  urls WHERE name = %s", (url,))
            result = cur.fetchone()
            return result[0]


@app.route('/add-url', methods=['POST'])  # Добавление url в БД
def add_url():
    url = request.form['url']

    if not validators.url(url) or len(url) > 255:
        flash("Некорректный URL", 'error')
        return redirect(url_for('index'))
    elif check_url_exists(url):
        new_url_id = get_id(url)
        flash("Страница уже существует", 'info')
        return redirect(url_for('view_url', id=new_url_id))
    else:
        add_url_to_db(url)
        new_url_id = get_id(url)
        flash("Страница успешно добавлена", 'success')
        return redirect(url_for('view_url', id=new_url_id))


def check_url_exists(url):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM urls WHERE name = %s", (url,))
            id = cur.fetchone() is not None
            return id


@app.route('/urls/<int:id>', methods=['GET'])
def view_url(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Выполняем запрос для получения URL по его id
            cur.execute('''
                SELECT id, name, created_at
                FROM urls
                WHERE id = %s
            ''', (id,))
            url = cur.fetchone()

            cur.execute('''
                    SELECT id, created_at, status_code, h1, title, description
                    FROM url_checks WHERE url_id = %s
                ''', (id,))
            checks = cur.fetchall()

    return render_template('url_checks.html', url=url, checks=checks)


@app.route('/urls', methods=['GET'])
def list_urls():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT urls.id AS url_id,
                       urls.name AS url_name,
                       latest_checks.created_at AS last_check_date,
                       url_checks.status_code
                FROM urls
                LEFT JOIN (
                    SELECT url_checks.url_id,
                        MAX(url_checks.created_at) AS created_at
                    FROM url_checks
                    GROUP BY url_checks.url_id
                ) AS latest_checks ON urls.id = latest_checks.url_id
                LEFT JOIN url_checks
                    ON latest_checks.url_id = url_checks.url_id
                AND latest_checks.created_at = url_checks.created_at
                GROUP BY
                    urls.id,
                    urls.name,
                    latest_checks.created_at,
                    url_checks.status_code
                ORDER BY urls.id DESC;
            ''')
            url = cur.fetchall()

    return render_template('urls.html', urls=url)


def get_url(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM  urls WHERE id = %s", (id,))
            result = cur.fetchone()
            return result[0]


def analyze_page(url, id):
    try:
        # Загружаем страницу
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки
        html_content = response.text

        # Парсим HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Извлекаем данные
        h1_element = soup.find('h1')
        h1_content = h1_element.text if h1_element else ''

        title_element = soup.title
        title_content = title_element.string if title_element else ''

        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_description_content = meta_description['content'] if meta_description and 'content' in meta_description.attrs else ''  # noqa: E501

        # Выводим данные для проверки
        print(f"H1: {h1_content}, Title: {title_content}, Description: {meta_description_content}")

        return h1_content, title_content, meta_description_content
    except Exception as e:
        print(f"Ошибка при анализе страницы {url}: {e}")


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    url = get_url(id)

    try:
        response = requests.get(url)  # Делаем запрос по URL
        status_code = response.status_code  # Получаем код ответа
        h1, title, description = analyze_page(url, id)
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Добавляем запись в таблицу url_checks
                if validators.url(url):
                    cur.execute('''
                            INSERT INTO url_checks
                                (url_id, h1, title, description, created_at, status_code)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (id, h1, title, description, datetime.now(), status_code))
                    conn.commit()
                    flash("Проверка успешно добавлена.", 'success')
    except Exception:
        flash("Произошла ошибка при проверке", 'error')
    return redirect(url_for('view_url', id=id))


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
