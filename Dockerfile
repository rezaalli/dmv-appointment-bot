# Base image
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm -f google-chrome-stable_current_amd64.deb

# Set display port to avoid crash
ENV DISPLAY=:99

# Install pip dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . /app

# Expose the Flask port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
