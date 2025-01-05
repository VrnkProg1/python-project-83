install:
	pip install uv
	uv sync

dev:
	uv run flask --debug --app page_analyzer:app run


build:
	./build.sh

lint:
	poetry run flake8 .

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
