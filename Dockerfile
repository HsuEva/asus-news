# 使用 Python 3.9 Slim
FROM python:3.9-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 設定工作目錄
WORKDIR /app

# 1. 安裝系統依賴
# 我們需要 gnupg 來處理金鑰
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    # Chrome 執行所需依賴 (Debian 12/13 適用)
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libnspr4 \
    xdg-utils \
    libgbm1 \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# 2. 安裝 Google Chrome (使用新版 signed-by 機制，不使用 apt-key)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | \
    gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# 3. 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製程式碼
COPY . .

# 5. 預設指令
CMD ["tail", "-f", "/dev/null"]