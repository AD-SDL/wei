FROM python:3.11

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/wei
LABEL org.opencontainers.image.description="The Workcell Execution Interface (WEI)"
LABEL org.opencontainers.image.licenses=MIT

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} wei
RUN useradd --create-home -u ${USER_ID} --shell /bin/bash -g wei wei

USER wei
WORKDIR /home/wei

RUN mkdir -p wei/requirements
RUN mkdir .wei
RUN mkdir .diaspora

# Install Python Dependencies first, for caching purposes
COPY --chown=wei:wei requirements/requirements.txt wei/requirements/requirements.txt
COPY --chown=wei:wei requirements/dev.txt wei/requirements/dev.txt
RUN --mount=type=cache,target=/home/${CONTAINER_USER}/.cache,uid=${USER_ID},gid=${GROUP_ID} \
    pip install -r wei/requirements/requirements.txt

# Copy wei files
COPY --chown=wei:wei wei wei/wei
COPY --chown=wei:wei tests wei/tests
COPY --chown=wei:wei pyproject.toml wei/pyproject.toml
COPY --chown=wei:wei README.md wei/README.md
COPY --chown=wei:wei scripts wei/scripts
COPY --chown=wei:wei workcell_defs wei/workcell_defs

# Install dependencies and wei
RUN --mount=type=cache,target=/home/${CONTAINER_USER}/.cache,uid=${USER_ID},gid=${GROUP_ID} \
    pip install -e wei
