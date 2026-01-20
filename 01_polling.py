"""
Polling: 클라이언트가 주기적으로 서버에 요청
- 서버는 데이터 유무와 관계없이 즉시 응답
- 단점: 데이터 없어도 요청/응답 발생 (비효율)
"""

import sys
import time
import threading
from datetime import datetime

def run_server():
    from flask import Flask, jsonify, request
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app = Flask(__name__)
    message_count = 0
    connection_count = 0  # 연결 횟수 카운터
    clients = {}  # client_id -> last_seen_time
    client_timeout = 5  # 5초 동안 요청 없으면 접속해제로 간주

    def check_disconnected_clients():
        """주기적으로 접속해제된 클라이언트 확인"""
        while True:
            time.sleep(2)
            now = time.time()
            disconnected = []
            for client_id, last_seen in list(clients.items()):
                if now - last_seen > client_timeout:
                    disconnected.append(client_id)
            for client_id in disconnected:
                del clients[client_id]
                print(f"[서버] 클라이언트 {client_id} 접속해제")

    # 백그라운드에서 접속해제 체크
    checker_thread = threading.Thread(target=check_disconnected_clients, daemon=True)
    checker_thread.start()

    @app.route('/poll')
    def poll():
        nonlocal message_count, connection_count

        client_id = request.args.get('client_id', 'unknown')
        connection_count += 1

        # 매 요청마다 새 연결 표시 (polling 특성)
        print(f"[서버] 연결 #{connection_count} - 클라이언트 {client_id}")

        # 클라이언트 접속 추적 (타임아웃용)
        clients[client_id] = time.time()

        # 5의 배수 요청마다 메시지 생성
        if connection_count % 5 == 0:
            message_count += 1
            print(f"[서버] 요청 #{connection_count} (5의 배수) → 메시지 #{message_count} 전송\n")
            return jsonify({"has_message": True, "message_num": message_count})
        else:
            print(f"[서버] 요청 #{connection_count} → 메시지 없음 → 빈 응답\n")
            return jsonify({"has_message": False})

    print("Polling 서버 시작 (localhost:5000)\n")
    app.run(port=5000)


def run_client():
    import requests
    import uuid

    client_id = str(uuid.uuid4())[:8]  # 짧은 고유 ID
    print(f"Polling 클라이언트 시작 (ID: {client_id})\n")
    request_count = 0

    while True:
        try:
            request_count += 1
            print(f"[클라이언트] 요청 #{request_count} 전송...")
            res = requests.get(f'http://localhost:5000/poll?client_id={client_id}', timeout=5)
            data = res.json()

            if data.get("has_message"):
                msg_num = data.get("message_num")
                print(f"[클라이언트] 응답: 메시지 있음 (#{msg_num})")
            else:
                print(f"[클라이언트] 응답: 메시지 없음")

            print(f"[클라이언트] 5초 대기...\n")
            time.sleep(5)  # 폴링 간격

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
