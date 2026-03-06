# Use Python 3.12 (more stable for 'av' than 3.14)
FROM python:3.12-slim

# Install system dependencies for 'av' (FFmpeg development files)
RUN apt-get update && apt-get install -y \
    libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev libavfilter-dev \
    pkg-config gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your scripts
COPY . .

# Keep the container running so you can "enter" it via VS Code
CMD ["tail", "-f", "/dev/null"]