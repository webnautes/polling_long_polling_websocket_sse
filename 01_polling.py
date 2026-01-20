"""
Polling - 클라이언트가 일정 간격으로 서버에 요청

실행: python 01_polling.py server / python 01_polling.py client
패키지: pip install flask requests
"""

import sys
import time
import random
from datetime import datetime


def run_server():
    from flask import Flask, jsonify
    import logging

    app = Flask(__name__)
    messages = []

    @app.route('/messages')
    def get_messages():
        ts = datetime.now().strftime('%H:%M:%S')

        # 30% 확률로 새 메시지 생성
        if random.random() > 0.7:
            msg = {'id': len(messages) + 1, 'text': f'메시지 #{len(messages) + 1}'}
            messages.append(msg)
            print(f"[{ts}] 요청 수신 → 응답: 새 메시지 \"{msg['text']}\"")
        else:
            print(f"[{ts}] 요청 수신 → 응답: 새 메시지 없음 (데이터 없어도 즉시 응답)")

        return jsonify({'messages': messages[-5:], 'total': len(messages)})

    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    print("=== Polling 서버 (localhost:5000) ===")
    print("특징: 요청 오면 데이터 유무와 관계없이 즉시 응답\n")
    app.run(port=5000, debug=False)


def run_client():
    import requests

    print("=== Polling 클라이언트 ===")
    print("특징: 2초마다 서버에 요청 (데이터 없어도 계속 요청)\n")

    last_count = 0

    while True:
        try:
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] 서버에 요청 전송...")

            response = requests.get('http://localhost:5000/messages', timeout=5)
            data = response.json()

            if data['total'] > last_count:
                print(f"[{ts}] 응답 수신: 새 메시지 {data['total'] - last_count}개!")
                last_count = data['total']
            else:
                print(f"[{ts}] 응답 수신: 새 메시지 없음")

            print(f"        → 2초 대기 후 다시 요청...\n")
            time.sleep(2)

        except requests.exceptions.ConnectionError:
            print("서버 연결 실패. 2초 후 재시도...")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n종료")
            break


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 01_polling.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    else:
        run_client()
