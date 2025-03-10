FROM python:3.12

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc postgresql-client libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project to the working dir in the container /app/
COPY . .

# expose port the app will run on, the default port for FastAPI
EXPOSE 8000

# add script for running migrations before starting the app
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# command to run the app, starting with migrations check up
CMD ["/start.sh"]
