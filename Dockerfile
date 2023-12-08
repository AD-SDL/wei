FROM python:3.11

RUN mkdir /wei

# Copy wei files
COPY wei /wei/wei
COPY tests /wei/tests
COPY pyproject.toml /wei/pyproject.toml
COPY README.md /wei/README.md


# Install dependencies and wei
RUN pip install -e /wei
