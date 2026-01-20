"""
SSE (Server-Sent Events): 서버 → 클라이언트 단방향 스트림
- HTTP 연결 유지하며 서버가 이벤트를 계속 전송
- 클라이언트 → 서버는 별도 HTTP 요청 필요
"""

import sys
import time
import json
import random

def run_server():
    from flask import Flask, Response
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    app = Flask(__name__)

    @app.route('/events')
    def events():
        def generate():
            n = 0
            while True:
                n += 1
                print(f"[서버] 서버 → 클라이언트: 이벤트 #{n}")
                data = json.dumps({'msg': f'이벤트 #{n}'})
                yield f"data: {data}\n\n"  # SSE 형식
                time.sleep(random.uniform(2, 4))

        print(f"[서버] 클라이언트 SSE 연결됨")
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
