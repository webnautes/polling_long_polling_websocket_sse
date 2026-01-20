"""
Long Polling: 서버가 새 데이터 있을 때까지 응답을 보류
- 클라이언트 요청 → 서버가 데이터 생길 때까지 대기 → 응답
- 장점: 빈 응답 없음 (Polling보다 효율적)
"""

import sys
import time
import random
import threading

def run_server():
    from flask import Flask, jsonify, request
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app = Flask(__name__)
    messages = []
    lock = threading.Lock()

    # 백그라운드에서 랜덤하게 메시지 생성
    def generate_messages():
        while True:
            time.sleep(random.uniform(3, 7))
            with lock:
                messages.append(f"메시지 #{len(messages)+1}")
                print(f"[서버] 새 메시지 생성됨! → 대기 중인 클라이언트에게 응답")

    threading.Thread(target=generate_messages, daemon=True).start()

    @app.route('/poll')
    def long_poll():
        last_id = int(request.args.get('last_id', 0))
        print(f"[서버] 요청 받음 → 새 데이터 생길 때까지 응답 보류...")

        # 새 데이터가 생길 때까지 대기 (최대 30초)
        for _ in range(60):
            with lock:
                if len(messages) > last_id:
                    return jsonify({'messages': messages[last_id:], 'last_id': len(messages)})
            time.sleep(0.5)

        print(f"[서버] 타임아웃 → 빈 응답")
        return jsonify({'messages': [], 'last_id': last_id})

    print("Long Polling 서버 시작 (localhost:5001)\n")
    app.run(port=5001, threaded=True)


def run_client():
    import requests

    print("Long Polling 클라이언트 시작\n")
    last_id = 0

    while True:
        try:
            print(f"[클라이언트] 서버에 요청 → 응답 대기중...")
            res = requests.get(f'http://localhost:5001/poll?last_id={last_id}', timeout=35)
            data = res.json()

            if data['messages']:
                for msg in data['messages']:
                    print(f"[클라이언트] 응답 받음: {msg}")
                last_id = data['last_id']
            else:
                print(f"[클라이언트] 타임아웃 (30초)")

            print(f"[클라이언트] 즉시 다음 요청!\n")  # 대기 없이 바로 재요청

        except requests.exceptions.ConnectionError:
            print("서버 연결 실패")
            time.sleep(3)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 02_long_polling.py server|client")
        sys.exit(1)
    run_server() if sys.argv[1] == 'server' else run_client()
