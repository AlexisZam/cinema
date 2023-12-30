MAKEFLAGS += -B -j2

clean-images:
	docker system prune -af --volumes

install-python:
	pyenv install -s

install-python-deps:
	poetry install --sync --no-root --only dev --only docs --only test
	poetry run poetry -C ./backend/ install
	poetry run poetry -C ./jobs/ install

show-outdated-python-deps:
	poetry show -aoT --with dev --with docs --with test
	poetry -C ./backend/ show -aoT
	poetry -C ./jobs/ show -aoT

upgrade-python-deps:
	poetry lock
	poetry -C ./backend/ lock
	poetry -C ./jobs/ lock

install-git-hooks:
	poetry run pre-commit install --install

run-git-hooks:
	poetry run pre-commit run -a

serve-docs:
	poetry run mkdocs serve

show-dead-code:
	poetry run vulture . | grep -v attribute | grep -v method

################### Javascript ###################

show-outdated-js-deps:
	pnpm dlx npm-check-updates
