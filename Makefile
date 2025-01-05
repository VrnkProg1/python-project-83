install:
	poetry install

dev:
	poetry run flask --debug --app page_analyzer.app:app run


build:
	./build.sh

lint:
	poetry run flake8 .

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
