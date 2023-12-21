FROM python:3.11

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/wei
LABEL org.opencontainers.image.description="The Workcell Execution Interface (WEI)"
LABEL org.opencontainers.image.licenses=MIT

RUN groupadd wei
RUN useradd --create-home --shell /bin/bash -g wei wei

USER wei
WORKDIR /home/wei

RUN mkdir wei
RUN mkdir .wei
RUN mkdir .diaspora

# Copy wei files
COPY --chown=wei:wei wei wei/wei
COPY --chown=wei:wei tests wei/tests
COPY --chown=wei:wei pyproject.toml wei/pyproject.toml
COPY --chown=wei:wei README.md wei/README.md
COPY --chown=wei:wei scripts wei/scripts


# Install dependencies and wei
RUN pip install -e wei
