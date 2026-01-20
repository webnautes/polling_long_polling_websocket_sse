"""
Long Polling: 서버가 새 데이터 있을 때까지 응답을 보류
- 클라이언트 요청 → 서버가 데이터 생길 때까지 대기 → 응답
- 장점: 빈 응답 없음 (Polling보다 효율적)
"""

import sys
import time
import threading

def run_server():
    from flask import Flask, jsonify, request
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app = Flask(__name__)
    messages = []
    lock = threading.Lock()
    connection_count = 0  # 연결 횟수 카운터
    clients = {}  # client_id -> connection_number

    # 백그라운드에서 5초마다 메시지 생성
    def generate_messages():
        while True:
            time.sleep(5)  # 5초 간격
            with lock:
                msg_num = len(messages) + 1
                messages.append(f"메시지 #{msg_num}")
                print(f"[서버] 새 메시지 생성됨! (메시지 #{msg_num}) → 대기 중인 클라이언트에게 응답")

    threading.Thread(target=generate_messages, daemon=True).start()

    @app.route('/poll')
    def long_poll():
        nonlocal connection_count

        client_id = request.args.get('client_id', 'unknown')
        last_id = int(request.args.get('last_id', 0))

        # 새 클라이언트 접속 확인
        if client_id not in clients:
            connection_count += 1
            clients[client_id] = connection_count
            print(f"[서버] 클라이언트 #{clients[client_id]} 접속 (ID: {client_id})")

        print(f"[서버] 클라이언트 #{clients[client_id]} 요청 받음 → 새 데이터 생길 때까지 응답 보류...")

        # 새 데이터가 생길 때까지 대기 (최대 30초)
        for _ in range(60):
            with lock:
                if len(messages) > last_id:
                    new_messages = messages[last_id:]
                    print(f"[서버] 클라이언트 #{clients[client_id]}에게 메시지 #{last_id + 1}~#{len(messages)} 전송\n")
                    return jsonify({'messages': new_messages, 'last_id': len(messages)})
            time.sleep(0.5)

        print(f"[서버] 클라이언트 #{clients[client_id]} 타임아웃 → 빈 응답\n")
        return jsonify({'messages': [], 'last_id': last_id})

    print("Long Polling 서버 시작 (localhost:5001)\n")
    app.run(port=5001, threaded=True)


def run_client():
    import requests
    import uuid

    client_id = str(uuid.uuid4())[:8]  # 짧은 고유 ID
    print(f"Long Polling 클라이언트 시작 (ID: {client_id})\n")
    last_id = 0

    while True:
        try:
            print(f"[클라이언트] 서버에 요청 → 응답 대기중...")
            res = requests.get(f'http://localhost:5001/poll?client_id={client_id}&last_id={last_id}', timeout=35)
            data = res.json()

            if data['messages']:
                for i, msg in enumerate(data['messages']):
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
