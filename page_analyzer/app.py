import psycopg2
from flask import render_template, request, flash, redirect, url_for, Flask, session
from dotenv import load_dotenv
import os
from datetime import datetime
import validators
import requests

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
                cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)", (url, created_at))
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
                
@app.route('/add-url', methods=['POST']) # Добавление url в БД
def add_url():
    url = request.form['url']
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Валидация URL
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
            id = cur.fetchone() is not None  # Возвращает True, если URL существует
            return id


@app.route('/urls/<int:id>', methods=['GET'])
def view_url(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Выполняем запрос для получения URL по его id
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()
        
            cur.execute("SELECT id, created_at, status_code FROM url_checks WHERE url_id = %s", (id,))
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
                LEFT JOIN url_checks ON latest_checks.url_id = url_checks.url_id 
                                      AND latest_checks.created_at = url_checks.created_at
                GROUP BY urls.id, urls.name, latest_checks.created_at, url_checks.status_code
                ORDER BY urls.id DESC;
            ''')
            url = cur.fetchall()

    return render_template('urls.html', urls = url)


def get_url(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM  urls WHERE id = %s", (id,))
            result = cur.fetchone()
            return result[0]


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    url = get_url(id)
    try:
        response = requests.get(url)  # Делаем запрос по URL
        status_code = response.status_code  # Получаем код ответа
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Добавляем запись в таблицу url_checks
                if validators.url(url):
                    cur.execute("INSERT INTO url_checks (url_id, created_at, status_code) VALUES (%s, %s, %s)", (id, datetime.now(), status_code))
                    conn.commit()
                    flash("Проверка успешно добавлена.", 'success')
    except Exception as e:
        flash(f"Произошла ошибка при проверке", 'error')
    
    return redirect(url_for('view_url', id=id))


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
