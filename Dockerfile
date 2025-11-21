FROM python:3.10-slim

# Install FFmpeg (Required for music conversion)
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Set up the app
WORKDIR /app
COPY . /app

# Install Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot
CMD ["python", "main.py"]
