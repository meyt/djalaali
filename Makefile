.PHONY: venv
venv:
	test -d venv || python3 -m venv venv

.PHONY: install
install: venv
	venv/bin/pip install -e ".[dev]"

.PHONY: test
test:
	venv/bin/python -m pytest

.PHONY: lint
lint:
	venv/bin/ruff check .

.PHONY: build
build:
	venv/bin/python -m build

.PHONY: demo
demo: install
	venv/bin/python demo/manage.py migrate
	venv/bin/python demo/manage.py ensure_admin
	venv/bin/python demo/manage.py runserver

.PHONY: clean
clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
