"""
================================================================================
LONG POLLING (롱 폴링) - 지연 응답 방식
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                        LONG POLLING 동작 원리                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   클라이언트                                        서버                     │
│       │                                              │                      │
│       │──────── [요청 #1] ────────>│                │                      │
│       │         ......대기......    │  (응답 보류)   │  ← 데이터 생길       │
│       │         ......대기......    │               │    때까지 대기!       │
│       │<──────────────────────────│ ✨ 새 데이터!   │                      │
│       │                                              │                      │
│       │──────── [요청 #2] ────────>│  ← 즉시 재요청! │                      │
│       │         ......대기......    │               │                      │
│       │         ......대기......    │               │                      │
│       │<──────────────────────────│ ⏰ 타임아웃     │  ← 30초 후 빈 응답   │
│       │                                              │                      │
│       │──────── [요청 #3] ────────>│  ← 즉시 재요청! │                      │
│       ▼          ... 반복 ...                        ▼                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  📌 핵심: 서버가 "새 데이터가 생길 때까지" 응답을 보류                        │
│  ✅ 장점: 빈 응답 없음 → Polling보다 효율적                                  │
│  ⚠️  단점: 서버가 연결을 오래 유지 → 리소스 사용                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔄 Polling vs Long Polling                                                 │
│     Polling: 클라이언트가 2초마다 요청 → 빈 응답 다수                        │
│     Long Polling: 데이터 있을 때만 응답 → 효율적                             │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
실행 방법:
    터미널 1: python 02_long_polling.py server
    터미널 2: python 02_long_polling.py client

필요한 패키지:
    pip install flask requests
================================================================================
"""

import sys
import time
import random
import threading
from datetime import datetime


# =============================================================================
# 서버 구현
# =============================================================================

def run_server():
    """Long Polling 서버 - 새 데이터가 생길 때까지 응답 보류"""

    from flask import Flask, jsonify, request

    app = Flask(__name__)
    messages = []
    message_id = 0
    lock = threading.Lock()

    # 백그라운드 메시지 생성기
    def background_message_generator():
        nonlocal message_id
        while True:
            time.sleep(random.uniform(3, 8))
            with lock:
                message_id += 1
                new_msg = {
                    'id': message_id,
                    'text': f'메시지 #{message_id}',
                    'time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                }
                messages.append(new_msg)
                print(f"\n  📨 새 메시지 생성: \"{new_msg['text']}\" - 대기 중인 클라이언트에게 즉시 전송!")

    thread = threading.Thread(target=background_message_generator, daemon=True)
    thread.start()

    @app.route('/poll')
    def long_poll():
        last_id = int(request.args.get('last_id', 0))
        timeout = 30
        start_time = time.time()

        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print()
        print(f"  [{timestamp}] ◀─── 요청 수신 (last_id={last_id})")
        print(f"               ⏳ 새 데이터 생길 때까지 응답 보류 중...")

        # ===== 핵심: 데이터가 생길 때까지 대기 =====
        while time.time() - start_time < timeout:
            with lock:
                new_messages = [m for m in messages if m['id'] > last_id]
                if new_messages:
                    wait_time = time.time() - start_time
                    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    print(f"  [{timestamp}] ───▶ ✅ {wait_time:.1f}초 대기 후 응답! ({len(new_messages)}개 메시지)")
                    return jsonify({
                        'status': 'new_data',
                        'messages': new_messages,
                        'wait_time': round(wait_time, 1)
                    })
            time.sleep(0.5)

        # 타임아웃
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        print(f"  [{timestamp}] ───▶ ⏰ {timeout}초 타임아웃 - 빈 응답")
        return jsonify({
            'status': 'timeout',
            'messages': [],
            'wait_time': timeout
        })

    # 로그 설정
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 16 + "🖥️  LONG POLLING 서버 시작" + " " * 25 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📍 주소: http://localhost:5001/poll?last_id=N" + " " * 21 + "║")
    print("║  📌 특징: 새 데이터가 생길 때까지 '응답을 보류'함" + " " * 17 + "║")
    print("║  ⏰ 타임아웃: 30초 (최대 대기 시간)" + " " * 31 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("┌" + "─" * 68 + "┐")
    print("│  ✅ 서버 준비 완료! 다른 터미널에서 클라이언트 실행:" + " " * 15 + "│")
    print("│     python 02_long_polling.py client" + " " * 30 + "│")
    print("└" + "─" * 68 + "┘")
    print()
    print("─" * 70)
    print("  아래에서 요청/대기/응답 흐름을 확인하세요:")
    print("  (백그라운드에서 3~8초 간격으로 메시지 자동 생성)")
    print("─" * 70)

    app.run(port=5001, debug=False, threaded=True)


# =============================================================================
# 클라이언트 구현
# =============================================================================

def run_client():
    """Long Polling 클라이언트 - 응답 받으면 즉시 재요청"""

    import requests

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 14 + "📱 LONG POLLING 클라이언트 시작" + " " * 22 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📌 특징: 서버 응답을 기다림 (최대 30초)" + " " * 26 + "║")
    print("║  ✅ 장점: 데이터 있을 때만 응답 → Polling보다 효율적!" + " " * 13 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  (Ctrl+C로 종료)")
    print()
    print("─" * 70)
    print("  📊 통계              │  📡 실시간 요청/응답")
    print("─" * 70)

    last_id = 0
    request_num = 0
    data_responses = 0
    timeout_responses = 0
    total_wait_time = 0

    while True:
        try:
            request_num += 1
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            print()
            print(f"  총 요청: {request_num:3d}        │  [{timestamp}] ───▶ 서버에 요청 #{request_num}")
            print(f"  데이터 수신: {data_responses:3d}     │               ⏳ 서버 응답 대기 중... (최대 30초)")

            # HTTP GET 요청 (Long Polling)
            start_time = time.time()
            response = requests.get(
                f'http://localhost:5001/poll?last_id={last_id}',
                timeout=35
            )
            elapsed = time.time() - start_time
            total_wait_time += elapsed

            data = response.json()
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            if data['status'] == 'new_data':
                data_responses += 1
                print(f"  타임아웃: {timeout_responses:3d}       │  [{timestamp}] ◀─── ✅ {elapsed:.1f}초 대기 후 응답!")
                for msg in data['messages']:
                    print(f"  평균 대기: {total_wait_time/request_num:.1f}s    │           └─ \"{msg['text']}\"")
                    last_id = max(last_id, msg['id'])
                print(f"                       │           🚀 즉시 다음 요청! (대기 시간 없음)")
            else:
                timeout_responses += 1
                print(f"  타임아웃: {timeout_responses:3d}       │  [{timestamp}] ◀─── ⏰ 타임아웃 ({elapsed:.1f}초)")
                print(f"  평균 대기: {total_wait_time/request_num:.1f}s    │           🚀 즉시 재연결!")

            # ===== Long Polling 핵심: 응답 받으면 바로 재요청 (대기 없음!) =====

        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  서버 연결 실패! 3초 후 재시도...")
            time.sleep(3)
        except requests.exceptions.Timeout:
            print(f"  ⚠️  클라이언트 타임아웃. 재연결...")
        except KeyboardInterrupt:
            print()
            print()
            print("═" * 70)
            print(f"  📊 최종 통계")
            print("─" * 70)
            print(f"  총 요청 횟수: {request_num}")
            print(f"  데이터 수신: {data_responses}회")
            print(f"  타임아웃: {timeout_responses}회")
            if request_num > 0:
                print(f"  평균 대기 시간: {total_wait_time/request_num:.1f}초")
                efficiency = (data_responses / request_num) * 100 if request_num > 0 else 0
                print(f"  효율성: {efficiency:.1f}%")
            print()
            print("  ✅ Long Polling 장점: 빈 응답이 거의 없음!")
            print("  ⚠️  단점: 연결 유지에 서버 리소스 필요")
            print("  💡 더 나은 대안: WebSocket (양방향), SSE (서버→클라이언트)")
            print("═" * 70)
            print()
            print("👋 클라이언트를 종료합니다.")
            break


# =============================================================================
# 메인 실행부
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print(__doc__)
        print("\n사용법: python 02_long_polling.py [server|client]")
        print("\n실행 순서:")
        print("  1. 터미널 1: python 02_long_polling.py server")
        print("  2. 터미널 2: python 02_long_polling.py client")
        sys.exit(1)

    if sys.argv[1] == 'server':
        run_server()
    else:
        run_client()
