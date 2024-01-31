############################################
# Docker- and Docker Compose-related rules #
############################################
PROFILES += $(if $(findstring $(DEBUG),true),debug)

DC := docker compose \
	-f $(COMPOSE_FILE) \
	--env-file $(ENV_FILE) \
	$(foreach profile,$(PROFILES),--profile $(profile))

test: start # Run Pytests
	$(DC) run $(APP_NAME)

run: # Runs a command in a container, starting it if necessary
# The line below ensures that if we're using diaspora, we register it before running
run: $(if $(findstring $(USE_DIASPORA),true), register_diaspora)
	@$(DC) ps --services --all
	@read -p "Type the name of a container listed above to run the command in: " CONTAINER_NAME && \
	read -p "Type the command you wish to run: " APP_COMMAND && \
	$(DC) run "$$CONTAINER_NAME" $$APP_COMMAND $(args)

exec: init # Opens a shell in a running container
	@$(DC) ps --services
	@read -p "Type the name of a container listed above to open a shell in that container: " CONTAINER_NAME && \
	$(DC) exec -u app "$$CONTAINER_NAME" /bin/bash $(args)

build: init requirements/requirements.txt requirements/dev.txt # Builds the docker image for APP_NAME
	$(DC) --profile test build $(args)

publish-docker: build # Publishes the docker image
	docker login $(REGISTRY)
	docker push ${IMAGE}:${PROJECT_VERSION}

start: init # Starts all the docker containers and detaches, allowing you to run other commands
start: $(if $(findstring $(USE_DIASPORA),true), register_diaspora)
	$(DC) up -d --remove-orphans $(args)

up: init # Starts all the docker containers and attaches, allowing you to see the logs
	$(DC) up --remove-orphans $(args)

ps: init # Shows the status of all the docker containers
	$(DC) ps $(args)

restart: init # Restarts all the docker containers
	$(DC) restart $(args)

pull: init # Pull the latest versions of the required containers
	$(DC) pull

update: init pull build stop start # Pulls, builds, stops, and then starts all containers

down: stop # Stops all the docker containers
stop: init # Stops all the docker containers
	$(DC) down $(args)

logs: init # Shows the logs for all the docker containers
	$(DC) logs -f $(args)

remove: init # Removes all the docker containers, but preserves volumes
	$(DC) down --rmi all $(args)
