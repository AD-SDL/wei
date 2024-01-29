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

checks: # Runs all the pre-commit checks
	@pre-commit install
	@pre-commit run --all-files || { echo "Checking fixes\n" ; pre-commit run --all-files; }

register_diaspora: # Registers diaspora for logging events
	docker compose -f $(COMPOSE_FILE) run "$(APP_NAME)" \
		wei/scripts/register_diaspora.py

DOCS := docs/build/*
NOT_PHONY += $(DOCS)
docs: $(DOCS) # Builds the docs for wei
$(DOCS): wei/* docs/source/*
	cd $(PROJECT_DIR)/docs && pdm run make clean html

publish: build publish-docker publish-python # Publishes the docker image and pypi package for wei

test: # Run Pytests
	docker compose -f $(COMPOSE_FILE) up -d
	docker compose -f $(COMPOSE_FILE) run test_app
	docker compose -f $(COMPOSE_FILE) stop

################################################################################

# Determine which rules don't correspond to actual files (add rules to NOT_PHONY to exclude)
.PHONY: $(filter-out $(NOT_PHONY), $(RULES))
