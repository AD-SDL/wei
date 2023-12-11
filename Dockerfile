FROM python:3.11

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/wei
LABEL org.opencontainers.image.description="The Workcell Execution Interface (WEI)"
LABEL org.opencontainers.image.licenses=MIT

RUN mkdir /wei

# Copy wei files
COPY wei /wei/wei
COPY tests /wei/tests
COPY pyproject.toml /wei/pyproject.toml
COPY README.md /wei/README.md
COPY scripts /wei/scripts


# Install dependencies and wei
RUN pip install -e /wei
