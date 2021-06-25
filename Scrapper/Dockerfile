# operating system for running python
FROM python:3.8-slim-buster
# Environment variable
ENV PYTHONUNBUFFERED 1
# updating the OS
RUN apt-get update
# installing netcat dependency
RUN apt-get install -y netcat


# routing the directory app 
WORKDIR /app
# copying the file from local to virtual machine (docker)
COPY requirements.txt .
# installs the packages mentioned in requirements.txt
RUN pip install -r requirements.txt
# COPY localdirectory remote_directory
COPY . .