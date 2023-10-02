FROM python:3.10

RUN mkdir /app

# Copy app files
COPY examples /app/examples
COPY requirements /app/requirements
COPY requirements /app/requirements
COPY wei /app/wei
COPY tests /app/tests
COPY setup.cfg /app/setup.cfg
COPY setup.py /app/setup.py


# Install dependencies
RUN python -m pip install --upgrade pip
RUN pip install -r app/requirements/requirements.txt
RUN pip install -r app/requirements/dev.txt
RUN pip install git+https://github.com/luckierdodge/pottery@master

# Install wei
RUN pip install -e /app
