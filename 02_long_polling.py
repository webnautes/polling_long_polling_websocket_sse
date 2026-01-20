"""
Long Polling - 서버가 새 데이터가 생길 때까지 응답을 보류

실행: python 02_long_polling.py server / python 02_long_polling.py client
패키지: pip install flask requests
"""

import sys
import time
import random
import threading
from datetime import datetime


def run_server():
    from flask import Flask, jsonify, request
    import logging

    app = Flask(__name__)
    messages = []
    message_id = 0
    lock = threading.Lock()

    # 백그라운드에서 메시지 생성
    def generate_messages():
        nonlocal message_id
        while True:
            time.sleep(random.uniform(3, 8))
            with lock:
                message_id += 1
                messages.append({'id': message_id, 'text': f'메시지 #{message_id}'})
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 새 메시지 생성 → 대기 중인 클라이언트에게 응답")

    threading.Thread(target=generate_messages, daemon=True).start()

    @app.route('/poll')
    def long_poll():
        last_id = int(request.args.get('last_id', 0))
        timeout = 30
        start = time.time()

        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] 요청 수신 → 새 데이터 생길 때까지 응답 보류...")

        # 새 데이터가 생길 때까지 대기
        while time.time() - start < timeout:
            with lock:
                new_msgs = [m for m in messages if m['id'] > last_id]
                if new_msgs:
                    wait = time.time() - start
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {wait:.1f}초 대기 후 응답 전송!")
                    return jsonify({'status': 'data', 'messages': new_msgs})
            time.sleep(0.5)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 타임아웃 (30초) → 빈 응답")
        return jsonify({'status': 'timeout', 'messages': []})

    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    print("=== Long Polling 서버 (localhost:5001) ===")
    print("특징: 새 데이터가 생길 때까지 응답을 보류 (최대 30초)\n")
    app.run(port=5001, debug=False, threaded=True)


def run_client():
    import requests

    print("=== Long Polling 클라이언트 ===")
    print("특징: 서버 응답 올 때까지 대기, 응답 받으면 즉시 재요청\n")

    last_id = 0

    while True:
        try:
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] 서버에 요청 → 응답 대기 중... (최대 30초)")

            start = time.time()
            response = requests.get(f'http://localhost:5001/poll?last_id={last_id}', timeout=35)
            elapsed = time.time() - start
            data = response.json()

            ts = datetime.now().strftime('%H:%M:%S')
            if data['status'] == 'data':
                for msg in data['messages']:
                    print(f"[{ts}] {elapsed:.1f}초 대기 후 응답: \"{msg['text']}\"")
                    last_id = max(last_id, msg['id'])
            else:
                print(f"[{ts}] 타임아웃 ({elapsed:.1f}초)")

            print(f"        → 즉시 다음 요청! (대기 없음)\n")

        except requests.exceptions.ConnectionError:
            print("서버 연결 실패. 3초 후 재시도...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n종료")
            break


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 02_long_polling.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    else:
        run_client()
