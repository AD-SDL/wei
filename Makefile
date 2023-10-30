.DEFAULT_GOAL := all
package_name = wei
extra_folders = examples/ tests/
black = black --target-version py37 $(package_name) $(extra_folders)
flake8 = flake8 $(package_name)/ $(extra_folders)
pylint = pylint $(package_name)/ $(extra_folders)
pydocstyle = pydocstyle $(package_name)/
run_mypy = mypy --config-file setup.cfg

.PHONY: format lint mypy all black isort

black:
	black --target-version py37 $(package_name) $(extra_folders)

isort:
	isort --atomic $(package_name) $(extra_folders)

format: isort black 

lint: format
	$(black) --check --diff
	$(flake8)
	$(pydocstyle)

mypy:
	$(run_mypy) --package $(package_name)
	$(run_mypy) $(package_name)/
	$(run_mypy) $(extra_folders)

all: format lint
