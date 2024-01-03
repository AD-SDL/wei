################################################################################
# AD-SDL WEI Makefile
################################################################################
MAKEFILE := $(lastword $(MAKEFILE_LIST))
MAKEFILE_DIR := $(dir $(MAKEFILE))
INCLUDE_DIR := $(MAKEFILE_DIR)/make

include $(INCLUDE_DIR)/boilerplate.mk # Boilerplate, can probably leave as-is
include $(INCLUDE_DIR)/config.mk # Project-specific configuration
include $(INCLUDE_DIR)/docker.mk # Docker-related rules
include $(INCLUDE_DIR)/python.mk # Python-related rules

################################################################################
# Rules: Add anything you want to be able to run with `make <target>` below

default: checks build $(DOCS) # Runs checks, builds wei and registers diaspora if necessary
default: $(if $(findstring $(USE_DIASPORA),true), register_diaspora)

checks: # Runs all the pre-commit checks
	@pre-commit install
	@pre-commit run --all-files || { echo "Checking fixes\n" ; pre-commit run --all-files; }

register_diaspora: build # Registers diaspora for logging events
	docker compose -f $(COMPOSE_FILE) run "$(APP_NAME)" \
		wei/scripts/register_diaspora.py

DOCS := docs/build/*
NOT_PHONY += $(DOCS)
docs: $(DOCS) # Builds the docs for wei
$(DOCS): wei/* docs/source/*
	cd $(PROJECT_DIR)/docs && pdm run make clean html

publish: build publish-docker publish-python # Publishes the docker image and pypi package for wei

exec: # Opens a shell in the APP_NAME container
	docker compose -f $(COMPOSE_FILE) exec $(APP_NAME) /bin/bash $(args)

test: # Run Pytests
	docker compose -f $(COMPOSE_FILE) exec $(APP_NAME) /bin/bash -c "pytest wei"

init: .env $(WEI_DATA_DIR) $(REDIS_DIR) # Do the initial configuration of the project

$(WEI_DATA_DIR):
	mkdir -p $(WEI_DATA_DIR)

$(REDIS_DIR):
	mkdir -p $(REDIS_DIR)

################################################################################

# Determine which rules don't correspond to actual files (add rules to NOT_PHONY to exclude)
PHONY_RULES := $(filter-out $(NOT_PHONY), $(RULES))

# Declare all targets as PHONY, except $(NOT_PHONY)
.PHONY: $(PHONY_RULES)
