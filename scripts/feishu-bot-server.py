from flask import Flask, request, jsonify
import subprocess, os

app = Flask(__name__)

@app.route('/feishu/webhook', methods=['POST'])
def feishu_callback():
    data = request.get_json()
    print("=== 收到飞书请求 ===")
    print(data)

    # 1. 飞书 URL 验证
    if data and data.get('type') == 'url_verification':
        challenge = data.get('challenge', '')
        print(f"=== 挑战码: {challenge} ===")
        return jsonify({"challenge": challenge})

    # 2. 消息事件
    if data and data.get('header', {}).get('event_type') == 'im.message.receive_v1':
        event = data.get('event', {})
        msg = event.get('message', {})
        content = msg.get('content', '')
        print(f"=== 收到消息: {content} ===")

        # 解析 @机器人 /run 命令
        if '/run' in content:
            print("=== 开始执行 Builder Digest 全流程... ===")
            subprocess.Popen(
                ['bash', os.path.expanduser('~/.hermes/skills/builder-digest/scripts/run-all.sh')],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return jsonify({'msg': '已启动 Builder Digest 全流程'})

    return jsonify({'msg': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765)
