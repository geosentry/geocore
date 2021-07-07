# Build from Python 3.9 Docker Base Image
FROM python:3.9-slim

# Set environment variable for app root directory
ENV APPDIR /app
# Set environment variable for app name
ENV APPNAME geocore-spectral
# Set environment variable for port binding
ENV PORT 8080
# Enable unbuffered outputs for realtime Cloud Logging
ENV PYTHONUNBUFFERED True

# Pass Service Account Credentials for GCP Authentication when deploying locally.
# ENV GOOGLE_APPLICATION_CREDENTIALS /googleauth
# COPY ./gcp-service-key.json $GOOGLE_APPLICATION_CREDENTIALS

# Copy contents into the app directory
COPY . $APPDIR
# Change working directory
WORKDIR $APPDIR

# Update apt
RUN apt update
# Install Git
RUN apt install -y git

# Update pip
RUN pip install --upgrade pip
# Install dependencies from requirements.txt
RUN pip install -r requirements.txt
# Install the Terrarium Package from a VCS source
RUN pip install git+https://github.com/geosentry/terrarium#egg=terrarium

# Run a gUnicorn WSGI Server. Timeout is set to 60s
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 60 main:app
