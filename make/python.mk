################
# Python Rules #
################

# (Make sure you've installed PDM)

register_diaspora_local: init-python # Registers diaspora for logging events (local python, no container)
	pdm run python scripts/register_diaspora.py

init-python: init pdm.lock deps # Installs the python environment (requires PDM)

build-python: init-python # Builds the pypi package for APP_NAME
	pdm build

publish-python: init-python # Publishes the pypi package for wei
	@echo "Username: __token__"
	@echo "Password: Create token with privileges here: https://pypi.org/manage/account/token/"
	pdm publish

###############################
# Python Dependency Managment #
###############################

NOT_PHONY += pdm.lock
pdm.lock: pyproject.toml # Generates the pdm.lock file
	pdm install -p $(PROJECT_DIR) --group :all

NOT_PHONY += requirements/*.txt
requirements/*.txt: pdm.lock
	pdm export --without-hashes --prod -o requirements/requirements.txt
	pdm export --without-hashes --group dev -o requirements/dev.txt
	pdm export --without-hashes --group docs -o requirements/docs.txt

deps: requirements/*.txt # Generates the requirements files for APP_NAME
	pdm install -p $(PROJECT_DIR) --group :all
