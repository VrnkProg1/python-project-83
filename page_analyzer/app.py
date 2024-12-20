import psycopg2
from flask import render_template, request, flash, redirect, url_for, Flask, session
from dotenv import load_dotenv
import os
from datetime import datetime
import validators

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
            return cur.fetchone() is not None  # Возвращает True, если URL существует


@app.route('/urls/<int:id>', methods=['GET'])
def view_url(id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Выполняем запрос для получения URL по его id
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (id,))
            url = cur.fetchone()

    return render_template('url_detail.html', url=url)


@app.route('/urls', methods=['GET'])
def list_urls():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Выполняем запрос для получения URL по его id
            cur.execute("SELECT *  FROM urls;")
            urls = cur.fetchall()

    return render_template('urls.html', urls=urls)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
