FROM python:3.11

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/wei
LABEL org.opencontainers.image.description="The Workflow Execution Interface (WEI)"
LABEL org.opencontainers.image.licenses=MIT

# User configuration
ARG USER_ID=9999
ARG GROUP_ID=9999
ARG CONTAINER_USER=app

ADD https://github.com/FooBarWidget/matchhostfsowner/releases/download/v1.0.1/matchhostfsowner-1.0.1-x86_64-linux.gz /sbin/matchhostfsowner.gz
RUN gunzip /sbin/matchhostfsowner.gz && \
  chown root: /sbin/matchhostfsowner && \
  chmod +x /sbin/matchhostfsowner

RUN groupadd -g ${GROUP_ID} ${CONTAINER_USER}
RUN useradd --create-home -u ${USER_ID} --shell /bin/bash -g ${CONTAINER_USER} ${CONTAINER_USER}

RUN mkdir -p /etc/matchhostfsowner/
RUN echo "\nchown_home: false" >> /etc/matchhostfsowner/config.yml
RUN chown -R root: /etc/matchhostfsowner && \
    chmod 700 /etc/matchhostfsowner && \
    chmod 600 /etc/matchhostfsowner/*

USER ${CONTAINER_USER}
WORKDIR /home/${CONTAINER_USER}

RUN mkdir -p wei/requirements
RUN mkdir -p .wei/temp
RUN mkdir .diaspora

# Install Python Dependencies first, for caching purposes
COPY --chown=${USER_ID}:${GROUP_ID} requirements/requirements.txt wei/requirements/requirements.txt
COPY --chown=${USER_ID}:${GROUP_ID} requirements/dev.txt wei/requirements/dev.txt
RUN --mount=type=cache,target=/home/${CONTAINER_USER}/.cache,uid=${USER_ID},gid=${GROUP_ID} \
    pip install -r wei/requirements/requirements.txt

# Copy wei files
COPY --chown=${USER_ID}:${GROUP_ID} wei wei/wei
COPY --chown=${USER_ID}:${GROUP_ID} tests wei/tests
COPY --chown=${USER_ID}:${GROUP_ID} pyproject.toml wei/pyproject.toml
COPY --chown=${USER_ID}:${GROUP_ID} README.md wei/README.md
COPY --chown=${USER_ID}:${GROUP_ID} scripts wei/scripts
COPY --chown=${USER_ID}:${GROUP_ID} workcell_defs wei/workcell_defs

# Install dependencies and wei
RUN --mount=type=cache,target=/home/${CONTAINER_USER}/.cache,uid=${USER_ID},gid=${GROUP_ID} \
    pip install -e wei

USER root

ENTRYPOINT ["/sbin/matchhostfsowner"]
