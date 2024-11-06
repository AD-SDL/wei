################################################################################
# AD-SDL WEI Makefile
################################################################################
.DEFAULT_GOAL := init

.PHONY: init checks test clean down up restart rebuild

init: # Do the initial configuration of the project
	@test -e .env || cp example.env .env
ifeq ($(shell uname),Darwin)
	@sed -i '' 's/^USER_ID=.*/USER_ID=1000/' .env
	@sed -i '' 's/^GROUP_ID=.*/GROUP_ID=1000/' .env
else
	@sed -i 's/^USER_ID=.*/USER_ID=$(shell id -u)/' .env
	@sed -i 's/^GROUP_ID=.*/GROUP_ID=$(shell id -g)/' .env
endif
ifeq ($(OS),Windows_NT)
	@where pdm || (Invoke-WebRequest -Uri https://pdm-project.org/install-pdm.py -UseBasicParsing).Content | py -
else
    @where pdm || curl -sSL https://pdm-project.org/install-pdm.py | python3 -
endif


.env: init

checks: # Runs all the pre-commit checks
	@pre-commit install
	@pre-commit run --all-files || { echo "Checking fixes\n" ; pre-commit run --all-files; }

test: init .env build up # Runs all the tests
	@docker compose exec test_wei_server pytest -p no:cacheprovider wei || (docker compose logs --tail 25 && false)
	@docker compose down

down:
	@docker compose down

up:
	@docker compose up -d --remove-orphans

restart: build up

rebuild: restart

clean:
	@rm .env

.PHONY += docs
docs: src docs/source # Builds the docs for wei
	cd docs && pdm run make clean html

build: build-python # Builds the project
	@docker compose --profile test build

################
# Python Rules #
################

# (Make sure you've installed PDM)

init-python: init pdm-update pdm.lock deps # Installs the python environment (requires PDM)

build-python: init-python # Builds the pypi package for APP_NAME
	pdm build

publish-python: init-python # Publishes the pypi package for wei
	@echo "Username: __token__"
	@echo "Password: Create token with privileges here: https://pypi.org/manage/account/token/"
	pdm publish

###############################
# Python Dependency Managment #
###############################

pdm-update:
	pdm self update

pdm.lock: pyproject.toml # Generates the pdm.lock file
	pdm install --group :all

requirements/*.txt: pdm.lock
	pdm export --without-hashes --group :all -o requirements/requirements.txt
	pdm export --without-hashes --group dev -o requirements/dev.txt
	pdm export --without-hashes --group docs -o requirements/docs.txt

.PHONY += deps
deps: requirements/*.txt # Generates the requirements files for APP_NAME
	pdm install --group :all
