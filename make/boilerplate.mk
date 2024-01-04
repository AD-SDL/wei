######################################
# Boilerplate Makefile Configuration #
# You can probably leave as is       #
######################################

# List all rules in the project
RULES := $(foreach makefile,$(MAKEFILE_LIST),\
	$(shell grep -E '^[a-zA-Z0-9_-]+:.*' $(makefile) | sed -E 's/^([a-zA-Z0-9_-]+):.*$$/\1/' | sort -u))

# Variables that we don't save to the .env file
ENV_FILTER := $(.VARIABLES)
ENV_FILTER += TEMP .SHELLSTATUS PHONY_RULES

#####################
# Boilerplate Rules #
#####################

help: # Show help for each target
	@echo ""
	@echo "Usage: make <rule>, where <rule> is one of:"
	@echo ""
	@for file in $(MAKEFILE_LIST); \
		do grep -E '^[a-zA-Z0-9 -_]+:.*#' $$file | sort | \
			while read -r l; \
				do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; \
			done; \
		done \
	| sort -u
