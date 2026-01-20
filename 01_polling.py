"""
Polling: 클라이언트가 주기적으로 서버에 요청
- 서버는 데이터 유무와 관계없이 즉시 응답
- 단점: 데이터 없어도 요청/응답 발생 (비효율)
"""

import sys
import time
import random
from datetime import datetime

def run_server():
    from flask import Flask, jsonify
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app = Flask(__name__)
    messages = []

    @app.route('/poll')
    def poll():
        # 30% 확률로 새 메시지 생성 (시뮬레이션)
        if random.random() > 0.7:
            messages.append(f"메시지 #{len(messages)+1}")
            print(f"[서버] 요청 받음 → 새 메시지 있음! → 즉시 응답")
        else:
            print(f"[서버] 요청 받음 → 새 메시지 없음 → 즉시 응답 (빈 응답)")

        return jsonify(messages[-3:])

    print("Polling 서버 시작 (localhost:5000)\n")
    app.run(port=5000)


def run_client():
    import requests

    print("Polling 클라이언트 시작\n")

    while True:
        try:
            print(f"[클라이언트] 서버에 요청...")
            res = requests.get('http://localhost:5000/poll', timeout=5)
            data = res.json()

            if data:
                print(f"[클라이언트] 응답: {data[-1]}")
            else:
                print(f"[클라이언트] 응답: (빈 응답)")

            print(f"[클라이언트] 2초 대기...\n")
            time.sleep(2)  # 폴링 간격

        except requests.exceptions.ConnectionError:
            print("서버 연결 실패")
            time.sleep(2)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 01_polling.py server|client")
        sys.exit(1)
    run_server() if sys.argv[1] == 'server' else run_client()
