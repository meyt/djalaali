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

.PHONY: release-tools
release-tools: venv
	venv/bin/pip install build twine cibuildwheel

# Source distribution (pure-Python fallback, compiles _calgo.c if possible)
.PHONY: sdist
sdist: release-tools
	rm -rf dist
	venv/bin/python -m build --sdist

# manylinux wheels (x86_64 by default) built inside Docker via cibuildwheel.
# Other platforms (macOS, Windows, aarch64) are built by CI; override the
# target with e.g. `make wheels CIBW_ARCHS=aarch64` (needs qemu binfmt).
CIBW_ARCHS ?= x86_64
.PHONY: wheels
wheels: release-tools
	CIBW_ARCHS=$(CIBW_ARCHS) venv/bin/cibuildwheel --platform linux --output-dir dist

# sdist + wheels, validated and ready for upload
.PHONY: dist
dist: sdist wheels
	venv/bin/twine check dist/*

# Manual upload; twine reads credentials from TWINE_USERNAME/TWINE_PASSWORD
# (use __token__ and a PyPI API token) or ~/.pypirc.
.PHONY: publish-test
publish-test: dist
	venv/bin/twine upload --repository testpypi dist/*

.PHONY: publish
publish: dist
	venv/bin/twine upload dist/*

.PHONY: demo
demo: install
	venv/bin/python demo/manage.py migrate
	venv/bin/python demo/manage.py ensure_admin
	venv/bin/python demo/manage.py runserver

.PHONY: clean
clean:
	rm -rf build dist wheelhouse *.egg-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
