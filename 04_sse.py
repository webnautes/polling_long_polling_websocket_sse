"""
SSE (Server-Sent Events) - 서버에서 클라이언트로 단방향 스트림

실행: python 04_sse.py server / python 04_sse.py client
패키지: pip install flask requests
"""

import sys
import time
import json
import random
from datetime import datetime


def run_server():
    from flask import Flask, Response
    import logging

    app = Flask(__name__)

    def generate_events():
        event_id = 0
        yield "retry: 3000\n\n"  # 재연결 간격 설정

        while True:
            event_id += 1
            ts = datetime.now().strftime('%H:%M:%S')
            data = {'id': event_id, 'message': f'이벤트 #{event_id}', 'time': ts}

            event = f"id: {event_id}\n"
            event += f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            print(f"[{ts}] 서버 → 클라이언트: 이벤트 #{event_id} (단방향 스트림)")
            yield event

            time.sleep(random.uniform(2, 5))

    @app.route('/events')
    def stream():
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] 클라이언트 SSE 연결")
        return Response(
            generate_events(),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
        )

    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    print("=== SSE 서버 (localhost:5003) ===")
    print("특징: 서버 → 클라이언트 단방향 이벤트 스트림 (HTTP 기반)\n")
    app.run(port=5003, debug=False, threaded=True)


def run_client():
    import requests

    print("=== SSE 클라이언트 ===")
    print("특징: 서버로부터 단방향 이벤트 수신 (클라이언트→서버는 별도 HTTP 필요)\n")

    try:
        response = requests.get('http://localhost:5003/events', stream=True)
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] 서버 연결 완료 (SSE 스트림 수신 중)\n")

        current_data = None
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    current_data = line[6:]
            else:
                if current_data:
                    data = json.loads(current_data)
                    ts = datetime.now().strftime('%H:%M:%S')
                    print(f"[{ts}] 서버 → 클라이언트: \"{data['message']}\"")
                    current_data = None

    except requests.exceptions.ConnectionError:
        print("서버 연결 실패. 서버가 실행 중인지 확인하세요.")
    except KeyboardInterrupt:
        print("\n종료")


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 04_sse.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    else:
        run_client()
