
clean:
	rm -Rf .pytest_cache

install:
	poetry install

test:
	poetry run pytest

build:
	poetry build