FROM python:3.11

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/wei
LABEL org.opencontainers.image.description="The Workflow Execution Interface (WEI)"
LABEL org.opencontainers.image.licenses=MIT

RUN set -eux; \
	apt-get update; \
	apt-get install -y gosu; \
	apt-get install -y npm; \
	rm -rf /var/lib/apt/lists/*

# User configuration
ARG USER_ID=9999
ARG GROUP_ID=9999
ARG CONTAINER_USER=app

RUN groupadd -g ${GROUP_ID} ${CONTAINER_USER}
RUN useradd --create-home -u ${USER_ID} --shell /bin/bash -g ${CONTAINER_USER} ${CONTAINER_USER}

WORKDIR /home/${CONTAINER_USER}

RUN mkdir -p wei/requirements
RUN mkdir -p .wei/experiments
RUN mkdir -p .diaspora

# Install Python Dependencies first, for caching purposes
COPY requirements/requirements.txt wei/requirements/requirements.txt
COPY requirements/dev.txt wei/requirements/dev.txt
RUN --mount=type=cache,target=/root/.cache \
    pip install -r wei/requirements/requirements.txt

# Copy wei files
COPY wei wei/wei
COPY tests wei/tests
COPY pyproject.toml wei/pyproject.toml
COPY README.md wei/README.md
COPY scripts wei/scripts
COPY ui wei/ui

# Install dependencies and wei
RUN --mount=type=cache,target=/root/.cache \
    pip install -e wei

COPY wei-entrypoint.sh /wei-entrypoint.sh
RUN chmod +x /wei-entrypoint.sh
ENTRYPOINT [ "/wei-entrypoint.sh" ]

COPY ./ui/package*.json ./

# install project dependencies
RUN npm install 
#--mount=type=cache,target=./node_modules \
#	npm install

# copy project files and folders to the current working directory (i.e. 'app' folder)

# build app for production with minification

RUN npm run build --prefix wei/ui
