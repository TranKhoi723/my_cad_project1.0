# Dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. Cài các gói cần thiết
RUN apt-get update && apt-get install -y \
    freecad freecad-python3 \
    python3-pip \
    xvfb \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Cài Python packages
RUN python3 -m pip install --no-cache-dir "ezdxf>=1.1.0" matplotlib pillow cairosvg


# 3. Làm việc tại thư mục /app
WORKDIR /app

# 4. Copy script chạy chính
COPY docker/entrypoint.sh /app/entrypoint.sh

# 5. Cấp quyền thực thi
RUN chmod +x /app/entrypoint.sh

# 6. Thiết lập entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
