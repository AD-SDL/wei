FROM python:3.12

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/wei
LABEL org.opencontainers.image.description="The Workflow Execution Interface (WEI)"
LABEL org.opencontainers.image.licenses=MIT

RUN set -eux; \
	apt-get update; \
	apt-get install -y gosu; \
	apt-get install -y npm; \
	apt-get install -y postgresql-client; \
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

# Install Node and Python Dependencies first, for caching purposes
COPY ./src/ui/package*.json ./
RUN npm install

COPY requirements/requirements.txt wei/requirements/requirements.txt
COPY requirements/dev.txt wei/requirements/dev.txt
RUN --mount=type=cache,target=/root/.cache \
	pip install --upgrade setuptools wheel pip && \
    pip install -r wei/requirements/requirements.txt

# Copy rest of wei files
COPY src wei/src
COPY tests wei/tests
COPY pyproject.toml wei/pyproject.toml
COPY README.md wei/README.md
COPY scripts wei/scripts

# Install dependencies and wei
RUN --mount=type=cache,target=/root/.cache \
    pip install ./wei

COPY wei-entrypoint.sh /wei-entrypoint.sh
RUN chmod +x /wei-entrypoint.sh
ENTRYPOINT [ "/wei-entrypoint.sh" ]

# build ui for production with minification
RUN npm run build --prefix wei/src/ui
