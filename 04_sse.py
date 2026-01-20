"""
SSE (Server-Sent Events): 서버 → 클라이언트 단방향 스트림
- HTTP 연결 유지하며 서버가 이벤트를 계속 전송
- 클라이언트 → 서버는 별도 HTTP 요청 필요
- 이 예제: 5개 메시지 전송 후 연결 종료 → 클라이언트 재연결 반복
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
            for n in range(1, 6):  # 5개 메시지만 전송
                print(f"[서버] 클라이언트 #{client_num}에게 메시지 #{n}/5 전송")
                data = json.dumps({'msg': f'이벤트 메시지 #{n}/5', 'msg_num': n, 'total': 5})
                yield f"data: {data}\n\n"
                time.sleep(5)  # 5초 간격

            # 완료 메시지 전송
            print(f"[서버] 클라이언트 #{client_num}에게 5개 전송 완료 → 연결 종료")
            data = json.dumps({'msg': '5개 전송 완료, 연결 종료', 'done': True})
            yield f"data: {data}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    print("SSE 서버 시작 (localhost:5003)")
    print("(5개 메시지 전송 후 연결 종료)\n")
    app.run(port=5003, threaded=True)


def run_client():
    import requests

    print("SSE 클라이언트 시작")
    print("(5개 메시지 수신 후 재연결 반복)\n")

    session_count = 0

    while True:
        try:
            session_count += 1
            print(f"[클라이언트] === 세션 #{session_count} 시작 ===")
            print(f"[클라이언트] SSE 연결 시도...")

            res = requests.get('http://localhost:5003/events', stream=True)
            print(f"[클라이언트] SSE 연결됨\n")

            for line in res.iter_lines():
                if line:
                    line = line.decode()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])

                        if data.get('done'):
                            print(f"[클라이언트] 서버 → 클라이언트: {data['msg']}")
                            print(f"[클라이언트] === 세션 #{session_count} 종료 ===\n")
                            break
                        else:
                            msg_num = data.get('msg_num', '?')
                            total = data.get('total', '?')
                            print(f"[클라이언트] 서버 → 클라이언트: {data['msg']}")

            print(f"[클라이언트] 3초 후 재연결...\n")
            time.sleep(3)

        except requests.exceptions.ConnectionError:
            print("서버 연결 실패, 3초 후 재시도...")
            time.sleep(3)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 04_sse.py server|client")
        sys.exit(1)
    run_server() if sys.argv[1] == 'server' else run_client()
