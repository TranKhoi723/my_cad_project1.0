FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# --- LAYER 1: Install system packages (Least frequently changed) ---
# This layer only rebuilds if you change the list of apt-get packages.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    freecad \
    python3 \
    python3-venv \
    git \
    fonts-open-sans \
    xvfb \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# --- LAYER 2: Create virtual environment ---
# This layer almost never rebuilds.
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Update pip in the virtual environment
RUN pip install --no-cache-dir --upgrade pip

# --- LAYER 3: Install Python libraries (Only rebuilds if this list changes) ---
# Separate pip installation into a distinct layer. Docker will cache this layer.
# It only reruns if you change the list of libraries in this command.
RUN pip install --no-cache-dir \
    ezdxf \
    matplotlib \
    Pillow \
    lxml \
    numpy \
    scikit-learn

# --- LAYER 4: Copy your source code (Most frequently changed) ---
WORKDIR /app
# Place this COPY layer near the end. When you modify code in the scripts/ directory,
# only this layer and subsequent layers will rebuild, which is very fast.
COPY scripts/ /app/scripts/

RUN chmod +x /app/scripts/*.sh
RUN chmod +x /app/scripts/*.py

# ENTRYPOINT remains unchanged
ENTRYPOINT ["python", "/app/scripts/pipeline.py"]
