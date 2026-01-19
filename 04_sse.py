
"""
================================================================================
SERVER-SENT EVENTS (SSE)
================================================================================

[ 개념 ]
서버에서 클라이언트로 "단방향 스트림"을 열어 이벤트를 푸시하는 방식입니다.
HTTP 기반이며, 브라우저의 EventSource API로 쉽게 사용할 수 있습니다.
WebSocket과 달리 서버→클라이언트 방향만 지원합니다.


[ SSE 메시지 형식 ]
    
    기본 형식:
        data: 메시지 내용\n
        \n
    
    이벤트 타입 지정:
        event: notification\n
        data: {"message": "알림"}\n
        \n
    
    메시지 ID (재연결 시 사용):
        id: 123\n
        data: 메시지\n
        \n
    
    재연결 간격 설정:
        retry: 3000\n
        \n



================================================================================
실행 방법:
    터미널 1: python 04_sse.py server
    터미널 2: python 04_sse.py client  (서버가 준비됐다는 메시지 확인 후)
    
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
    """
    SSE 서버
    
    역할:
    - HTTP 연결을 유지하며 이벤트 스트림 전송
    - 클라이언트→서버 통신을 위한 별도 엔드포인트 제공
    
    핵심:
    - Content-Type: text/event-stream
    - 연결을 끊지 않고 데이터를 계속 전송
    """
    
    from flask import Flask, Response, request, jsonify
    
    app = Flask(__name__)
    
    # ---------------------------------------------------------
    # 이벤트 스트림 생성기
    # ---------------------------------------------------------
    def generate_events():
        """
        SSE 이벤트를 생성하는 제너레이터 함수
        
        SSE 형식 규칙:
        1. 각 필드는 "필드명: 값\n" 형식
        2. 이벤트 끝은 빈 줄 (\n\n)로 구분
        3. data 필드는 필수, 나머지는 선택
        
        Yields:
            str: SSE 형식의 이벤트 문자열
        """
        event_id = 0
        event_types = ['news', 'stock', 'notification', 'update']
        
        # === 재연결 간격 설정 ===
        # retry: 연결이 끊어졌을 때 재연결까지 대기 시간 (밀리초)
        # 브라우저의 EventSource가 자동으로 재연결 시도
        yield "retry: 3000\n\n"
        
        # === 이벤트 생성 루프 ===
        while True:
            event_id += 1
            event_type = random.choice(event_types)
            
            # 이벤트 데이터 생성
            data = {
                'id': event_id,
                'type': event_type,
                'message': f'{event_type.upper()} 이벤트 #{event_id}',
                'time': datetime.now().strftime('%H:%M:%S'),
                # 주식 이벤트는 가격 포함
                'value': round(random.uniform(100, 200), 2) if event_type == 'stock' else None
            }
            
            # === SSE 형식으로 이벤트 구성 ===
            # id: 이벤트 ID (재연결 시 Last-Event-ID 헤더로 전송됨)
            # event: 이벤트 타입 (클라이언트에서 addEventListener로 구분)
            # data: 실제 데이터 (JSON 문자열)
            event = f"id: {event_id}\n"
            event += f"event: {event_type}\n"
            event += f"data: {json.dumps(data, ensure_ascii=False)}\n"
            event += "\n"  # 이벤트 종료 (빈 줄)
            
            print(f"📤 이벤트 전송: {event_type} #{event_id}")
            
            # yield: 제너레이터에서 값을 하나씩 반환
            # Flask가 이를 스트리밍 응답으로 변환
            yield event
            
            # 2~5초 간격으로 이벤트 생성
            time.sleep(random.uniform(2, 5))
    
    # ---------------------------------------------------------
    # 라우트 정의: GET /events (SSE 스트림)
    # ---------------------------------------------------------
    @app.route('/events')
    def stream():
        """
        SSE 스트림 엔드포인트
        
        핵심 헤더:
        - Content-Type: text/event-stream (SSE 명시)
        - Cache-Control: no-cache (캐싱 방지)
        - Connection: keep-alive (연결 유지)
        
        Returns:
            Response: 스트리밍 응답
        """
        print(f"✅ 클라이언트 연결됨")
        
        return Response(
            generate_events(),  # 제너레이터를 응답 본문으로
            mimetype='text/event-stream',  # SSE MIME 타입
            headers={
                'Cache-Control': 'no-cache',  # 캐싱 비활성화
                'Connection': 'keep-alive',    # 연결 유지
                'X-Accel-Buffering': 'no'     # Nginx 버퍼링 비활성화 (프록시 환경)
            }
        )
    
    # ---------------------------------------------------------
    # 라우트 정의: POST /action (클라이언트→서버)
    # ---------------------------------------------------------
    @app.route('/action', methods=['POST'])
    def action():
        """
        클라이언트→서버 요청을 위한 엔드포인트
        
        SSE는 단방향이므로:
        - 서버→클라이언트: SSE 스트림 (/events)
        - 클라이언트→서버: 별도 HTTP 요청 (/action)
        
        실제 사용 예:
        - 사용자가 좋아요 클릭 → POST /action
        - 메시지 전송 → POST /action
        """
        data = request.json
        print(f"📩 클라이언트 액션 수신: {data}")
        
        return jsonify({
            'status': 'ok',
            'received': data,
            'time': datetime.now().strftime('%H:%M:%S')
        })
    
    # ---------------------------------------------------------
    # 서버 시작
    # ---------------------------------------------------------
    print("=" * 60)
    print("🖥️  SSE (Server-Sent Events) 서버 시작")
    print("=" * 60)
    print(f"📍 주소: http://localhost:5003")
    print(f"📍 스트림: GET /events")
    print(f"📍 액션: POST /action")
    print("-" * 60)
    
    # ⭐ 클라이언트 실행 타이밍 안내
    print("\n" + "=" * 60)
    print("✅ 서버 준비 완료!")
    print("👉 이제 다른 터미널에서 클라이언트를 실행하세요:")
    print("   python 04_sse.py client")
    print("=" * 60 + "\n")
    
    # threaded=True: SSE 연결은 오래 유지되므로 필수
    
    # Flask/Werkzeug 로그 레벨 조정 (불필요한 로그 숨김)
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # ERROR 이상만 표시
    
    app.run(port=5003, debug=False, threaded=True)


# =============================================================================
# 클라이언트 구현
# =============================================================================

def run_client():
    """
    SSE 클라이언트
    
    역할:
    - 서버의 이벤트 스트림에 연결
    - 스트리밍 응답을 줄 단위로 파싱
    - 이벤트 타입에 따라 다르게 처리
    
    브라우저에서는 EventSource API 사용:
        const es = new EventSource('/events');
        es.addEventListener('news', (e) => console.log(e.data));
    """
    
    import requests
    
    print("=" * 60)
    print("📱 SSE (Server-Sent Events) 클라이언트 시작")
    print("=" * 60)
    print("서버로부터 이벤트 스트림을 수신합니다.")
    print("-" * 60)
    print("(Ctrl+C로 종료)\n")
    
    # 이벤트 타입별 이모지
    type_emoji = {
        'news': '📰',
        'stock': '📈',
        'notification': '🔔',
        'update': '🔄'
    }
    
    try:
        # === SSE 연결 ===
        # stream=True: 응답을 스트리밍으로 받음 (연결 유지)
        # 일반 요청과 달리 응답이 완료되기 전에 데이터 처리 시작
        response = requests.get(
            'http://localhost:5003/events',
            stream=True,  # ⭐ 스트리밍 모드 활성화
            headers={'Accept': 'text/event-stream'}
        )
        
        print("✅ 서버에 연결되었습니다!\n")
        
        # 현재 파싱 중인 이벤트 데이터
        current_event = {}
        
        # === 스트림 처리 루프 ===
        # iter_lines(): 응답을 줄 단위로 읽기
        for line in response.iter_lines():
            if line:
                # 바이트를 문자열로 디코딩
                line = line.decode('utf-8')
                
                # === SSE 필드 파싱 ===
                if line.startswith('id: '):
                    # 이벤트 ID
                    current_event['id'] = line[4:]
                    
                elif line.startswith('event: '):
                    # 이벤트 타입
                    current_event['event'] = line[7:]
                    
                elif line.startswith('data: '):
                    # 이벤트 데이터
                    current_event['data'] = line[6:]
                    
                elif line.startswith('retry: '):
                    # 재연결 간격 (밀리초)
                    print(f"⚙️  재연결 간격 설정: {line[7:]}ms")
                    
            else:
                # === 빈 줄 = 이벤트 완료 ===
                # SSE에서 빈 줄은 이벤트의 끝을 의미
                if 'data' in current_event:
                    try:
                        # JSON 데이터 파싱
                        data = json.loads(current_event['data'])
                        event_type = current_event.get('event', 'message')
                        emoji = type_emoji.get(event_type, '📨')
                        
                        # 이벤트 출력
                        print(f"{emoji} [{event_type.upper()}] {data['message']} ({data['time']})")
                        
                        # 주식 이벤트는 가격도 표시
                        if data.get('value'):
                            print(f"   └─ 현재가: ${data['value']}")
                            
                    except json.JSONDecodeError:
                        # JSON이 아닌 경우 그대로 출력
                        print(f"📨 {current_event['data']}")
                
                # 다음 이벤트를 위해 초기화
                current_event = {}
                
    except requests.exceptions.ConnectionError:
        print("⚠️  서버에 연결할 수 없습니다.")
        print("   서버가 실행 중인지 확인하세요: python 04_sse.py server")
        
    except KeyboardInterrupt:
        print("\n\n👋 클라이언트를 종료합니다.")


# =============================================================================
# 클라이언트 구현 (액션 전송 포함)
# =============================================================================

def run_client_with_action():
    """
    SSE 클라이언트 (양방향 시뮬레이션)
    
    역할:
    - 이벤트 수신 (SSE 스트림)
    - 액션 전송 (별도 HTTP POST)
    
    SSE의 양방향 통신 패턴:
    - 수신: GET /events (SSE 스트림)
    - 송신: POST /action (일반 HTTP)
    """
    
    import requests
    import threading
    
    print("=" * 60)
    print("📱 SSE 클라이언트 (액션 전송 포함)")
    print("=" * 60)
    print("이벤트를 수신하면서 서버에 액션을 보낼 수 있습니다.")
    print("-" * 60)
    print("(Ctrl+C로 종료)\n")
    
    # 스레드 종료 플래그
    stop_event = threading.Event()
    
    # 이벤트 타입별 이모지
    type_emoji = {
        'news': '📰',
        'stock': '📈',
        'notification': '🔔',
        'update': '🔄'
    }
    
    # ---------------------------------------------------------
    # 이벤트 수신 스레드
    # ---------------------------------------------------------
    def receive_events():
        """백그라운드에서 이벤트 수신"""
        try:
            response = requests.get(
                'http://localhost:5003/events',
                stream=True
            )
            
            current_event = {}
            
            for line in response.iter_lines():
                # 종료 신호 확인
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
                            data = json.loads(current_event['data'])
                            event_type = current_event.get('event', 'message')
                            emoji = type_emoji.get(event_type, '📨')
                            print(f"\n{emoji} [{event_type.upper()}] {data['message']}")
                            print("액션 입력 (또는 Enter): ", end='', flush=True)
                        except:
                            pass
                    current_event = {}
                    
        except:
            pass
    
    # 수신 스레드 시작 (데몬 모드)
    thread = threading.Thread(target=receive_events, daemon=True)
    thread.start()
    
    print("✅ 서버에 연결되었습니다!")
    print("   이벤트를 수신하면서 액션을 입력할 수 있습니다.\n")
    
    # ---------------------------------------------------------
    # 메인 루프: 사용자 입력 처리
    # ---------------------------------------------------------
    try:
        while True:
            action = input("액션 입력 (또는 Enter): ").strip()
            
            if action:
                # 별도 HTTP 요청으로 서버에 액션 전송
                # SSE 스트림과 독립적으로 동작
                response = requests.post(
                    'http://localhost:5003/action',
                    json={
                        'action': action,
                        'time': datetime.now().isoformat()
                    }
                )
                result = response.json()
                print(f"✅ 액션 전송됨: {action} (서버 응답: {result['status']})")
                
    except KeyboardInterrupt:
        stop_event.set()
        print("\n\n👋 클라이언트를 종료합니다.")


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
        print("  python 04_sse.py client-action - 클라이언트 (수신 + 액션 전송)")
        print("\n실행 순서:")
        print("  1. 터미널 1: python 04_sse.py server")
        print("  2. (서버 준비 메시지 확인)")
        print("  3. 터미널 2: python 04_sse.py client")
        sys.exit(1)
    
    if sys.argv[1] == 'server':
        run_server()
    elif sys.argv[1] == 'client':
        run_client()
    else:
        run_client_with_action()
