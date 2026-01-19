
"""
================================================================================
WEBSOCKET (웹소켓)
================================================================================

[ 개념 ]
HTTP와 달리 클라이언트와 서버 간에 "지속적인 양방향 연결"을 유지하는 프로토콜입니다.
한 번 연결되면 양쪽 모두 자유롭게 데이터를 보낼 수 있습니다.
처음에 HTTP로 핸드셰이크를 하고, 이후 WebSocket 프로토콜로 업그레이드됩니다.


================================================================================
실행 방법:
    터미널 1: python 03_websocket.py server
    터미널 2: python 03_websocket.py client  (서버가 준비됐다는 메시지 확인 후)
    
필요한 패키지:
    pip install websockets
================================================================================
"""

import sys
import json
import asyncio
import random
from datetime import datetime


# =============================================================================
# 서버 구현
# =============================================================================

async def run_server():
    """
    WebSocket 서버
    
    역할:
    - 클라이언트 연결 관리 (연결/해제)
    - 양방향 메시지 송수신
    - 모든 클라이언트에게 브로드캐스트
    - 서버에서 클라이언트로 푸시 알림
    
    async/await:
    - WebSocket은 비동기 I/O가 효율적
    - asyncio: 파이썬의 비동기 프로그래밍 라이브러리
    """
    
    # websockets: WebSocket 프로토콜 구현 라이브러리
    import websockets
    
    # 연결된 모든 클라이언트를 저장하는 집합
    # set 사용: 중복 방지, O(1) 추가/삭제
    connected_clients = set()
    
    # 클라이언트 번호 카운터
    client_counter = 0
    
    # ---------------------------------------------------------
    # 클라이언트 연결 핸들러
    # ---------------------------------------------------------
    async def handle_client(websocket):
        """
        개별 클라이언트의 연결을 처리하는 코루틴
        
        Parameters:
            websocket: 클라이언트와의 WebSocket 연결 객체
            
        생명주기:
        1. 연결 수립 → connected_clients에 추가
        2. 메시지 수신 대기 (무한 루프)
        3. 연결 종료 → connected_clients에서 제거
        
        Note:
            websockets 10.x 이상에서는 path 매개변수가 deprecated됨
            필요시 websocket.path로 접근 가능
        """
        nonlocal client_counter
        client_counter += 1
        client_id = client_counter
        
        # === 클라이언트 연결 등록 ===
        connected_clients.add(websocket)
        print(f"✅ 클라이언트 #{client_id} 연결됨 (현재 {len(connected_clients)}명)")
        
        # 입장 알림을 모든 클라이언트에게 브로드캐스트
        await broadcast({
            'type': 'system',
            'message': f'클라이언트 #{client_id}님이 입장했습니다.',
            'time': datetime.now().strftime('%H:%M:%S')
        }, exclude=None)
        
        try:
            # === 메시지 수신 루프 ===
            # async for: 비동기적으로 메시지를 하나씩 수신
            # 연결이 유지되는 동안 계속 대기
            async for message in websocket:
                print(f"📩 클라이언트 #{client_id}: {message}")
                
                # 받은 메시지를 모든 클라이언트에게 브로드캐스트
                await broadcast({
                    'type': 'chat',
                    'from': f'클라이언트 #{client_id}',
                    'message': message,
                    'time': datetime.now().strftime('%H:%M:%S')
                })
                
        except websockets.exceptions.ConnectionClosed:
            # 클라이언트가 연결을 끊음 (정상/비정상)
            pass
            
        finally:
            # === 클라이언트 연결 해제 ===
            # finally: 예외 발생 여부와 관계없이 항상 실행
            connected_clients.discard(websocket)
            print(f"❌ 클라이언트 #{client_id} 연결 종료 (현재 {len(connected_clients)}명)")
            
            # 퇴장 알림 브로드캐스트
            await broadcast({
                'type': 'system',
                'message': f'클라이언트 #{client_id}님이 퇴장했습니다.',
                'time': datetime.now().strftime('%H:%M:%S')
            })
    
    # ---------------------------------------------------------
    # 브로드캐스트 함수
    # ---------------------------------------------------------
    async def broadcast(data, exclude=None):
        """
        모든 연결된 클라이언트에게 메시지 전송
        
        Parameters:
            data: 전송할 데이터 (딕셔너리)
            exclude: 제외할 클라이언트 (선택)
            
        WebSocket의 강점:
        - 서버가 먼저 클라이언트에게 데이터를 보낼 수 있음
        - Polling/Long Polling과 달리 요청 없이 푸시 가능
        """
        if not connected_clients:
            return
        
        # 딕셔너리를 JSON 문자열로 변환
        # ensure_ascii=False: 한글 등 유니코드 그대로 유지
        message = json.dumps(data, ensure_ascii=False)
        
        # 모든 클라이언트에게 동시에 전송
        tasks = []
        for client in connected_clients:
            if client != exclude:
                # asyncio.create_task: 비동기 작업 생성
                tasks.append(asyncio.create_task(client.send(message)))
        
        if tasks:
            # asyncio.gather: 여러 비동기 작업을 동시에 실행
            # return_exceptions=True: 일부 실패해도 나머지 계속 실행
            await asyncio.gather(*tasks, return_exceptions=True)
    
    # ---------------------------------------------------------
    # 서버 푸시 알림 (서버 → 클라이언트)
    # ---------------------------------------------------------
    async def server_push_notifications():
        """
        서버에서 주기적으로 알림을 푸시하는 코루틴
        
        WebSocket의 핵심 기능:
        - 클라이언트 요청 없이 서버가 먼저 데이터 전송
        - Polling 방식에서는 불가능한 기능
        """
        notification_count = 0
        
        while True:
            # 5~10초 랜덤 간격으로 알림 생성
            await asyncio.sleep(random.uniform(5, 10))
            
            if connected_clients:
                notification_count += 1
                print(f"📢 서버 알림 #{notification_count} 브로드캐스트")
                
                await broadcast({
                    'type': 'notification',
                    'message': f'서버 알림 #{notification_count}',
                    'time': datetime.now().strftime('%H:%M:%S')
                })
    
    # ---------------------------------------------------------
    # 서버 시작
    # ---------------------------------------------------------
    print("=" * 60)
    print("🖥️  WEBSOCKET 서버 시작 중...")
    print("=" * 60)
    
    # WebSocket 서버 시작
    # websockets.serve: 지정된 호스트/포트에서 WebSocket 서버 실행
    server = await websockets.serve(handle_client, "localhost", 5002)
    
    # 서버 푸시 알림 태스크 시작 (백그라운드)
    asyncio.create_task(server_push_notifications())
    
    # ⭐ 서버가 실제로 바인딩된 후 클라이언트 실행 안내
    print(f"📍 주소: ws://localhost:5002")
    print("-" * 60)
    print("\n" + "=" * 60)
    print("✅ 서버 준비 완료!")
    print("👉 이제 다른 터미널에서 클라이언트를 실행하세요:")
    print("   python 03_websocket.py client")
    print("=" * 60 + "\n")
    
    # 서버가 종료될 때까지 대기 (무한 실행)
    # Ctrl+C로 종료 가능
    await asyncio.Future()  # 무한 대기 (server.wait_closed() 대신)


# =============================================================================
# 클라이언트 구현
# =============================================================================

async def run_client():
    """
    WebSocket 클라이언트
    
    역할:
    - 서버에 WebSocket 연결
    - 사용자 입력을 서버로 전송
    - 서버로부터 메시지 수신 (동시 처리)
    
    양방향 통신:
    - 메시지 수신과 송신이 독립적으로 동작
    - 서버 메시지를 기다리면서 동시에 입력 가능
    """
    
    import websockets
    
    print("=" * 60)
    print("📱 WEBSOCKET 클라이언트 시작")
    print("=" * 60)
    print("서버와 양방향 통신합니다.")
    print("-" * 60)
    print("메시지를 입력하면 서버로 전송됩니다.")
    print("(빈 줄 입력 시 건너뛰기, Ctrl+C로 종료)\n")
    
    # WebSocket 서버 주소
    # ws://: WebSocket 프로토콜 (HTTP의 ws 버전)
    # wss://: 보안 WebSocket (HTTPS의 wss 버전)
    uri = "ws://localhost:5002"
    
    try:
        # === WebSocket 연결 ===
        # async with: 연결 자동 관리 (연결/해제)
        async with websockets.connect(uri) as websocket:
            print("✅ 서버에 연결되었습니다!\n")
            
            # ---------------------------------------------------------
            # 메시지 수신 코루틴
            # ---------------------------------------------------------
            async def receive_messages():
                """
                서버로부터 메시지를 수신하는 코루틴
                
                비동기 처리:
                - 메시지가 올 때까지 대기 (블로킹 없음)
                - 다른 작업(입력)과 동시에 실행
                """
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        
                        # 메시지 타입에 따라 다르게 표시
                        if data['type'] == 'system':
                            print(f"\n💬 [시스템] {data['message']}")
                        elif data['type'] == 'notification':
                            print(f"\n🔔 [알림] {data['message']}")
                        elif data['type'] == 'chat':
                            print(f"\n💭 [{data['from']}] {data['message']}")
                        
                        # 입력 프롬프트 다시 표시
                        print("메시지 입력: ", end='', flush=True)
                except:
                    pass
            
            # ---------------------------------------------------------
            # 메시지 송신 코루틴
            # ---------------------------------------------------------
            async def send_messages():
                """
                사용자 입력을 서버로 전송하는 코루틴
                
                run_in_executor:
                - input()은 블로킹 함수
                - executor에서 실행하여 비동기 처리
                """
                loop = asyncio.get_event_loop()
                
                while True:
                    try:
                        # 비동기적으로 사용자 입력 받기
                        # run_in_executor: 블로킹 함수를 비동기로 실행
                        message = await loop.run_in_executor(
                            None,  # 기본 executor 사용
                            lambda: input("메시지 입력: ")
                        )
                        
                        if message.strip():
                            # 서버로 메시지 전송
                            await websocket.send(message)
                            
                    except EOFError:
                        break
            
            # === 수신과 송신을 동시에 실행 ===
            # asyncio.gather: 여러 코루틴을 동시에 실행
            # WebSocket의 양방향 통신 구현
            await asyncio.gather(
                receive_messages(),
                send_messages()
            )
            
    except ConnectionRefusedError:
        print("⚠️  서버에 연결할 수 없습니다.")
        print("   서버가 실행 중인지 확인하세요: python 03_websocket.py server")
        
    except KeyboardInterrupt:
        print("\n\n👋 클라이언트를 종료합니다.")


# =============================================================================
# 메인 실행부
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print(__doc__)
        print("\n사용법: python 03_websocket.py [server|client]")
        print("\n실행 순서:")
        print("  1. 터미널 1: python 03_websocket.py server")
        print("  2. (서버 준비 메시지 확인)")
        print("  3. 터미널 2: python 03_websocket.py client")
        sys.exit(1)
    
    try:
        # asyncio.run: 비동기 메인 함수 실행
        if sys.argv[1] == 'server':
            asyncio.run(run_server())
        else:
            asyncio.run(run_client())
            
    except KeyboardInterrupt:
        print("\n종료됨")
