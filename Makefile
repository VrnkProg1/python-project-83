install:
	pip install uv
	uv sync
	./build.sh

dev:
	uv run flask --debug --app page_analyzer:app run


build:
	

lint:
	uv run ruff check .

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
