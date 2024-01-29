############################################
# Docker- and Docker Compose-related rules #
############################################

build: init requirements/requirements.txt requirements/dev.txt # Builds the docker image for APP_NAME
	docker compose -f $(COMPOSE_FILE) --profile test build $(args)

publish-docker: build # Publishes the docker image
	docker login $(REGISTRY)
	docker push ${IMAGE}:${PROJECT_VERSION}

start: # Starts all the docker containers and detaches, allowing you to run other commands
start: $(if $(findstring $(USE_DIASPORA),true), register_diaspora)
	docker compose -f $(COMPOSE_FILE) up -d $(args)

exec: # Opens a shell in the APP_NAME container
	docker compose -f $(COMPOSE_FILE) exec -u app $(APP_NAME) /bin/bash $(args)

up: # Starts all the docker containers and attaches, allowing you to see the logs
	docker compose -f $(COMPOSE_FILE) up $(args)

ps: # Shows the status of all the docker containers
	docker compose -f $(COMPOSE_FILE) ps $(args)

restart: # Restarts all the docker containers
	docker compose -f $(COMPOSE_FILE) restart $(args)

pull: # Pull the latest versions of the required containers
	docker compose -f ${COMPOSE_FILE} pull

update: pull build stop start # Pulls, builds, stops, and then starts all containers

down: stop # Stops all the docker containers
stop: # Stops all the docker containers
	docker compose -f $(COMPOSE_FILE) down $(args)

logs: # Shows the logs for all the docker containers
	docker compose -f $(COMPOSE_FILE) logs -f $(args)

remove: # Removes all the docker containers, but preserves volumes
	docker compose -f $(COMPOSE_FILE) down --rmi all $(args)
