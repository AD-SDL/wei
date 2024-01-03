################
# Python Rules #
################

# (Make sure you've installed PDM)

register_diaspora_local: init-python # Registers diaspora for logging events (local python, no container)
	pdm run python scripts/register_diaspora.py

init-python: init # Installs the python environment (requires PDM)
	pdm install -p $(PROJECT_DIR)

build-python: init init-python # Builds the pypi package for APP_NAME
	pdm build

publish-python: build-python # Publishes the pypi package for wei
	# Username: __token__
	# Password: Create token with privileges here: https://pypi.org/manage/account/token/
	pdm publish

# Generates the requirements files for APP_NAME
NOT_PHONY += requirements/*.txt
requirements/*.txt: pyproject.toml
	pdm export --prod -o requirements/requirements.txt --without-hashes
	pdm export --group dev -o requirements/dev.txt --without-hashes
	pdm export --group docs -o requirements/docs.txt --without-hashes

deps: requirements/*.txt # Generates the requirements files for APP_NAME
