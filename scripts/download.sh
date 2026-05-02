#!/bin/bash
# ==========================================
# Builder Digest · download.sh
# 从 GitHub 下载最新的 JSON 数据文件
# ==========================================

set -euo pipefail

# --- 配置 ---
DATA_DIR="$HOME/.hermes/skills/builder-digest/data"
LOG_DIR="$HOME/.hermes/skills/builder-digest/logs"
LOG_FILE="$LOG_DIR/download-$(date +%Y-%m-%d).log"

# 下载列表：文件名|URL
declare -a FILES=(
    "feed-x.json|https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-x.json"
    "feed-podcasts.json|https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-podcasts.json"
    "feed-blogs.json|https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-blogs.json"
)

# --- 初始化 ---
mkdir -p "$DATA_DIR" "$LOG_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] download.sh 开始执行" | tee "$LOG_FILE"

SUCCESS=0
FAIL=0
EXIT_CODE=0

# --- 下载函数 ---
download_and_validate() {
    local filename="$1"
    local url="$2"
    local filepath="$DATA_DIR/$filename"

    echo -n "[$(date '+%H:%M:%S')] 下载 $filename ... " | tee -a "$LOG_FILE"

    # 下载（覆盖旧文件，超时30秒，重试2次）
    if curl -fSL --connect-timeout 30 --retry 2 -o "$filepath" "$url" 2>>"$LOG_FILE"; then
        # 校验 JSON 格式
        if python3 -m json.tool "$filepath" > /dev/null 2>&1; then
            echo "✅ 成功" | tee -a "$LOG_FILE"
            ((SUCCESS++))
            return 0
        else
            echo "❌ JSON 格式无效" | tee -a "$LOG_FILE"
            ((FAIL++))
            EXIT_CODE=1
            return 1
        fi
    else
        echo "❌ 下载失败" | tee -a "$LOG_FILE"
        ((FAIL++))
        EXIT_CODE=1
        return 1
    fi
}

# --- 逐个下载 ---
for entry in "${FILES[@]}"; do
    filename="${entry%%|*}"
    url="${entry##*|}"
    download_and_validate "$filename" "$url"
done

# --- 汇总报告 ---
echo "" | tee -a "$LOG_FILE"
echo "[$(date '+%H:%M:%S')] 下载完成：$SUCCESS 成功，$FAIL 失败" | tee -a "$LOG_FILE"

exit $EXIT_CODE
