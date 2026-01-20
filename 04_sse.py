"""
================================================================================
SERVER-SENT EVENTS (SSE) - 서버 → 클라이언트 단방향 스트림
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                           SSE 동작 원리                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   클라이언트                                        서버                     │
│       │                                              │                      │
│       │═══════ [HTTP 연결 수립 (1회)] ══════════════│                      │
│       │                                              │                      │
│       │         <<<< 단방향 스트림 >>>>              │                      │
│       │                                              │                      │
│       │<─────────────────────────── 이벤트 #1       │  ← 서버→클라이언트   │
│       │                                              │                      │
│       │<─────────────────────────── 이벤트 #2       │  ← 서버→클라이언트   │
│       │                                              │                      │
│       │<─────────────────────────── 이벤트 #3       │  ← 서버→클라이언트   │
│       │                                              │    (계속 전송)        │
│       │         <<<< 연결 유지 >>>>                  │                      │
│       ▼                                              ▼                      │
│                                                                             │
│   ⚠️  클라이언트 → 서버 방향은 별도 HTTP 요청 필요                           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  📌 핵심: HTTP 기반 "단방향" 스트림 (서버 → 클라이언트)                       │
│  ✅ 장점: HTTP 기반이라 방화벽 통과 쉬움, 자동 재연결, 브라우저 내장 지원      │
│  ⚠️  단점: 단방향만 지원 (양방향 필요시 WebSocket 사용)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔄 WebSocket vs SSE                                                        │
│     WebSocket: 양방향 (클라이언트 ↔ 서버), 별도 프로토콜                     │
│     SSE: 단방향 (서버 → 클라이언트), HTTP 기반, 더 간단                      │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
실행 방법:
    터미널 1: python 04_sse.py server
    터미널 2: python 04_sse.py client

필요한 패키지:
    pip install flask requests
================================================================================
"""

import sys
import time
import json
import random
from datetime import datetime


# =============================================================================
# 서버 구현
# =============================================================================

def run_server():
    """SSE 서버 - 서버에서 클라이언트로 단방향 이벤트 스트림"""

    from flask import Flask, Response, request, jsonify

    app = Flask(__name__)

    def generate_events():
        """이벤트를 계속 생성하여 스트리밍"""
        event_id = 0
        event_types = ['news', 'stock', 'notification', 'update']
        type_emoji = {
            'news': '📰',
            'stock': '📈',
            'notification': '🔔',
            'update': '🔄'
        }

        # 재연결 간격 설정 (클라이언트에게 전달)
        yield "retry: 3000\n\n"
        print(f"  ⚙️  재연결 간격: 3000ms 설정됨")

        while True:
            event_id += 1
            event_type = random.choice(event_types)
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            emoji = type_emoji.get(event_type, '📨')

            data = {
                'id': event_id,
                'type': event_type,
                'message': f'{event_type.upper()} 이벤트 #{event_id}',
                'time': timestamp,
                'value': round(random.uniform(100, 200), 2) if event_type == 'stock' else None
            }

            # SSE 형식으로 이벤트 구성
            event = f"id: {event_id}\n"
            event += f"event: {event_type}\n"
            event += f"data: {json.dumps(data, ensure_ascii=False)}\n"
            event += "\n"

            print()
            print(f"  [{timestamp}] ───▶ {emoji} [{event_type.upper()}] 이벤트 #{event_id}")
            print(f"               📤 단방향 스트림으로 클라이언트에게 푸시!")

            yield event

            time.sleep(random.uniform(2, 5))

    @app.route('/events')
    def stream():
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print()
        print(f"  [{timestamp}] ══════ ✅ 클라이언트 SSE 연결!")
        print(f"               🔗 HTTP 연결 수립 → 단방향 스트림 시작")
        print(f"               📡 Content-Type: text/event-stream")

        return Response(
            generate_events(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

    @app.route('/action', methods=['POST'])
    def action():
        """클라이언트 → 서버 통신 (별도 HTTP 요청)"""
        data = request.json
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        print()
        print(f"  [{timestamp}] ◀─── 📩 클라이언트 액션 수신: \"{data.get('action', '')}\"")
        print(f"               ⚠️  SSE는 단방향! 클라이언트→서버는 별도 HTTP 요청")

        return jsonify({
            'status': 'ok',
            'received': data,
            'time': timestamp
        })

    # 로그 설정
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "🖥️  SSE 서버 시작" + " " * 29 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📍 스트림: http://localhost:5003/events" + " " * 26 + "║")
    print("║  📍 액션: POST http://localhost:5003/action" + " " * 23 + "║")
    print("║  📌 특징: 서버 → 클라이언트 '단방향' 이벤트 스트림" + " " * 14 + "║")
    print("║  ⭐ 핵심: HTTP 기반, 브라우저 EventSource API 지원" + " " * 15 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("┌" + "─" * 68 + "┐")
    print("│  ✅ 서버 준비 완료! 다른 터미널에서 클라이언트 실행:" + " " * 15 + "│")
    print("│     python 04_sse.py client" + " " * 39 + "│")
    print("└" + "─" * 68 + "┘")
    print()
    print("─" * 70)
    print("  아래에서 단방향 스트림 흐름을 확인하세요:")
    print("  (서버가 2~5초 간격으로 이벤트를 클라이언트에게 푸시)")
    print("─" * 70)

    app.run(port=5003, debug=False, threaded=True)


# =============================================================================
# 클라이언트 구현
# =============================================================================

def run_client():
    """SSE 클라이언트 - 서버로부터 이벤트 스트림 수신"""

    import requests

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "📱 SSE 클라이언트 시작" + " " * 26 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📌 특징: 서버로부터 '단방향' 이벤트 스트림 수신" + " " * 18 + "║")
    print("║  ⭐ 핵심: HTTP 기반 → 방화벽 친화적, 자동 재연결 지원" + " " * 12 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  서버에서 이벤트가 푸시될 때마다 표시됩니다.")
    print("  (Ctrl+C로 종료)")
    print()

    type_emoji = {
        'news': '📰',
        'stock': '📈',
        'notification': '🔔',
        'update': '🔄'
    }

    try:
        # 스트리밍 응답 수신
        response = requests.get(
            'http://localhost:5003/events',
            stream=True,
            headers={'Accept': 'text/event-stream'}
        )

        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print("─" * 70)
        print(f"  [{timestamp}] ══════ ✅ 서버 SSE 연결 완료!")
        print(f"               🔗 HTTP 연결 유지 → 단방향 스트림 수신 중")
        print("─" * 70)
        print()

        event_count = 0
        current_event = {}

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')

                if line.startswith('id: '):
                    current_event['id'] = line[4:]
                elif line.startswith('event: '):
                    current_event['event'] = line[7:]
                elif line.startswith('data: '):
                    current_event['data'] = line[6:]
                elif line.startswith('retry: '):
                    print(f"  ⚙️  재연결 간격 설정: {line[7:]}ms (서버 지정)")
            else:
                if 'data' in current_event:
                    try:
                        event_count += 1
                        data = json.loads(current_event['data'])
                        event_type = current_event.get('event', 'message')
                        emoji = type_emoji.get(event_type, '📨')
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                        print(f"  [{timestamp}] ◀─── {emoji} [{event_type.upper()}] {data['message']}")

                        if data.get('value'):
                            print(f"               └─ 현재가: ${data['value']}")

                        print(f"               📨 수신 이벤트 총: {event_count}개")
                        print()

                    except json.JSONDecodeError:
                        print(f"  📨 {current_event['data']}")

                current_event = {}

    except requests.exceptions.ConnectionError:
        print("  ⚠️  서버에 연결할 수 없습니다.")
        print("     서버가 실행 중인지 확인하세요: python 04_sse.py server")

    except KeyboardInterrupt:
        print()
        print()
        print("═" * 70)
        print("  📊 최종 통계")
        print("─" * 70)
        print(f"  수신한 이벤트: {event_count}개")
        print()
        print("  ✅ SSE 장점:")
        print("     - HTTP 기반 → 방화벽/프록시 통과 용이")
        print("     - 브라우저 EventSource API 내장 지원")
        print("     - 자동 재연결 (연결 끊어지면 자동 복구)")
        print("  ⚠️  SSE 단점:")
        print("     - 단방향만 지원 (양방향 필요시 WebSocket)")
        print("═" * 70)
        print()
        print("👋 클라이언트를 종료합니다.")


# =============================================================================
# 클라이언트 구현 (액션 전송 포함)
# =============================================================================

def run_client_with_action():
    """SSE 클라이언트 - 수신 + 액션 전송"""

    import requests
    import threading

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 14 + "📱 SSE 클라이언트 (액션 전송 모드)" + " " * 18 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📌 수신: SSE 스트림 (서버 → 클라이언트)" + " " * 26 + "║")
    print("║  📌 송신: HTTP POST (클라이언트 → 서버) - 별도 요청!" + " " * 13 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  이벤트를 수신하면서 서버에 액션을 보낼 수 있습니다.")
    print("  (액션 입력 후 Enter, Ctrl+C로 종료)")
    print()

    stop_event = threading.Event()
    event_count = 0
    action_count = 0

    type_emoji = {
        'news': '📰',
        'stock': '📈',
        'notification': '🔔',
        'update': '🔄'
    }

    def receive_events():
        nonlocal event_count
        try:
            response = requests.get('http://localhost:5003/events', stream=True)
            current_event = {}

            for line in response.iter_lines():
                if stop_event.is_set():
                    break

                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        current_event['data'] = line[6:]
                    elif line.startswith('event: '):
                        current_event['event'] = line[7:]
                else:
                    if 'data' in current_event:
                        try:
                            event_count += 1
                            data = json.loads(current_event['data'])
                            event_type = current_event.get('event', 'message')
                            emoji = type_emoji.get(event_type, '📨')
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                            print(f"\n  [{timestamp}] ◀─── {emoji} [{event_type.upper()}] {data['message']}")
                            print(f"               📨 수신: {event_count}개 | 📤 액션: {action_count}개")
                            print("  액션 입력: ", end='', flush=True)
                        except:
                            pass
                    current_event = {}
        except:
            pass

    thread = threading.Thread(target=receive_events, daemon=True)
    thread.start()

    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print("─" * 70)
    print(f"  [{timestamp}] ══════ ✅ 서버 연결 완료!")
    print(f"               🔗 SSE: 서버→클라이언트 | HTTP: 클라이언트→서버")
    print("─" * 70)
    print()

    try:
        while True:
            action = input("  액션 입력: ").strip()

            if action:
                action_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                response = requests.post(
                    'http://localhost:5003/action',
                    json={'action': action, 'time': datetime.now().isoformat()}
                )
                result = response.json()

                print(f"  [{timestamp}] ───▶ 📤 액션 전송: \"{action}\"")
                print(f"               ⚠️  별도 HTTP POST 요청으로 전송됨 (SSE는 단방향!)")
                print(f"               📨 수신: {event_count}개 | 📤 액션: {action_count}개")

    except KeyboardInterrupt:
        stop_event.set()
        print()
        print()
        print("═" * 70)
        print("  📊 최종 통계")
        print("─" * 70)
        print(f"  수신한 이벤트: {event_count}개 (SSE 스트림)")
        print(f"  전송한 액션: {action_count}개 (별도 HTTP 요청)")
        print()
        print("  ⚠️  SSE의 양방향 통신 패턴:")
        print("     - 서버→클라이언트: SSE 스트림 (단방향)")
        print("     - 클라이언트→서버: 별도 HTTP 요청 필요")
        print("  💡 진정한 양방향이 필요하면: WebSocket 사용")
        print("═" * 70)
        print()
        print("👋 클라이언트를 종료합니다.")


# =============================================================================
# 메인 실행부
# =============================================================================

if __name__ == '__main__':
    valid_args = ['server', 'client', 'client-action']

    if len(sys.argv) != 2 or sys.argv[1] not in valid_args:
        print(__doc__)
        print("\n사용법:")
        print("  python 04_sse.py server        - 서버 실행")
        print("  python 04_sse.py client        - 클라이언트 (수신만)")
        print("  python 04_sse.py client-action - 클라이언트 (수신 + 액션)")
        print("\n실행 순서:")
        print("  1. 터미널 1: python 04_sse.py server")
        print("  2. 터미널 2: python 04_sse.py client")
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    elif sys.argv[1] == 'client':
        run_client()
    else:
        run_client_with_action()
