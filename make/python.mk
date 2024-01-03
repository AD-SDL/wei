################
# Python Rules #
################

# (Make sure you've installed PDM)

register_diaspora_local: init-python # Registers diaspora for logging events (local python, no container)
	pdm run python scripts/register_diaspora.py

init-python: init pdm.lock # Installs the python environment (requires PDM)

build-python: init-python # Builds the pypi package for APP_NAME
	pdm build

publish-python: init-python # Publishes the pypi package for wei
	@echo "Username: __token__"
	@echo "Password: Create token with privileges here: https://pypi.org/manage/account/token/"
	pdm publish

###############################
# Python Dependency Managment #
###############################

pdm.lock: pyproject.toml # Generates the pdm.lock file
	pdm install -p $(PROJECT_DIR)

requirements/*.txt: pyproject.toml
	pdm export --prod -o requirements/requirements.txt --without-hashes
	pdm export --group dev -o requirements/dev.txt --without-hashes
	pdm export --group docs -o requirements/docs.txt --without-hashes

deps: requirements/*.txt # Generates the requirements files for APP_NAME
