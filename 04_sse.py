"""
SSE (Server-Sent Events): 서버 → 클라이언트 단방향 스트림
- HTTP 연결 유지하며 서버가 이벤트를 계속 전송
- 클라이언트 → 서버는 별도 HTTP 요청 필요
"""

import sys
import time
import json
import threading

def run_server():
    from flask import Flask, Response, request
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app = Flask(__name__)
    connection_count = 0
    lock = threading.Lock()

    @app.route('/events')
    def events():
        nonlocal connection_count

        with lock:
            connection_count += 1
            client_num = connection_count

        print(f"[서버] 클라이언트 #{client_num} SSE 연결됨")

        def generate():
            n = 0
            try:
                while True:
                    n += 1
                    print(f"[서버] 클라이언트 #{client_num}에게 메시지 #{n} 전송")
                    data = json.dumps({'msg': f'이벤트 (메시지 #{n})', 'msg_num': n})
                    yield f"data: {data}\n\n"  # SSE 형식
                    time.sleep(5)  # 5초 간격
            except GeneratorExit:
                print(f"[서버] 클라이언트 #{client_num} SSE 연결 종료")

        return Response(generate(), mimetype='text/event-stream')

    print("SSE 서버 시작 (localhost:5003)\n")
    app.run(port=5003, threaded=True)


def run_client():
    import requests

    print("SSE 클라이언트 시작\n")

    try:
        # stream=True: 응답 완료 전에 데이터 수신 시작
        res = requests.get('http://localhost:5003/events', stream=True)
        print("[클라이언트] SSE 연결됨 (서버 이벤트 수신 대기)\n")

        for line in res.iter_lines():
            if line:
                line = line.decode()
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    msg_num = data.get('msg_num', '?')
                    print(f"[클라이언트] 서버 → 클라이언트: {data['msg']}")

    except requests.exceptions.ConnectionError:
        print("서버 연결 실패")
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 04_sse.py server|client")
        sys.exit(1)
    run_server() if sys.argv[1] == 'server' else run_client()
