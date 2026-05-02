#!/bin/bash
# ==========================================
# 检查远程 feed-x.json 是否有更新，并通过飞书机器人通知
# 点击按钮可复制运行命令到剪贴板
# ==========================================

BASE="$HOME/.hermes/skills/builder-digest"
ENV_FILE="$BASE/.env"
export $(cat "$ENV_FILE" | xargs)

LOCAL_FILE="$BASE/data/feed-x.json"
REMOTE_URL="https://raw.githubusercontent.com/zarazhangrui/follow-builders/main/feed-x.json"

LOCAL_TIME=$(python3 -c "import json; d=json.load(open('$LOCAL_FILE')); print(d.get('generatedAt',''))")
REMOTE_TIME=$(curl -s "$REMOTE_URL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('generatedAt',''))")

echo "本地: $LOCAL_TIME"
echo "远程: $REMOTE_TIME"

if [ "$REMOTE_TIME" \> "$LOCAL_TIME" ]; then
    echo "✅ 远程有更新！发送飞书通知..."

    if [ -n "$FEISHU_WEBHOOK" ]; then
        export REMOTE_TIME="$REMOTE_TIME"
        export LOCAL_TIME="$LOCAL_TIME"
        python3 << 'PYEOF'
import requests, os

rem = os.environ.get('REMOTE_TIME', '未知')
loc = os.environ.get('LOCAL_TIME', '未知')

data = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "Builder Digest · 数据已更新"},
            "template": "wathet"
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"远程 feed-x.json 已更新\n**🕒 {rem}**\n\n本地数据为 {loc}，可点击下方按钮复制命令，粘贴到终端运行。"}
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📋 复制运行命令"},
                        "url": "https://www.w3schools.com",
                        "type": "primary",
                        "value": "bash ~/.hermes/skills/builder-digest/scripts/run-all.sh"
                    }
                ]
            }
        ]
    }
}
requests.post(os.environ.get('FEISHU_WEBHOOK'), json=data, timeout=10)
PYEOF
        echo "✅ 飞书通知已发送"
    else
        echo "⚠️ 未配置 FEISHU_WEBHOOK"
    fi
else
    echo "远程未更新，无需操作"
fi
