# Dockerfile (Phiên bản tối ưu hóa - Cách 2)
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# --- LỚP 1: Cài đặt các gói hệ thống (Ít thay đổi nhất) ---
# Lớp này chỉ build lại khi bạn thay đổi danh sách các gói apt-get.
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

# --- LỚP 2: Tạo môi trường ảo ---
# Lớp này gần như không bao giờ build lại.
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Cập nhật pip trong môi trường ảo
RUN pip install --no-cache-dir --upgrade pip

# --- LỚP 3: Cài đặt các thư viện Python (Chỉ build lại khi danh sách này thay đổi) ---
# Tách việc cài đặt pip ra một lớp riêng. Docker sẽ cache lớp này.
# Nó chỉ chạy lại nếu bạn thay đổi danh sách các thư viện trong dòng lệnh này.
RUN pip install --no-cache-dir \
    ezdxf \
    matplotlib \
    Pillow \
    lxml \
    numpy \
    scikit-learn

# --- LỚP 4: Sao chép mã nguồn của bạn (Thay đổi thường xuyên nhất) ---
WORKDIR /app
# Đặt lớp COPY này ở gần cuối. Khi bạn sửa code trong thư mục scripts/,
# chỉ có lớp này và các lớp sau nó được build lại, diễn ra rất nhanh.
COPY scripts/ /app/scripts/

RUN chmod +x /app/scripts/*.sh
RUN chmod +x /app/scripts/*.py

# ENTRYPOINT vẫn giữ nguyên
ENTRYPOINT ["python", "/app/scripts/pipeline.py"]