"""
================================================================================
WEBSOCKET (웹소켓) - 양방향 실시간 통신
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEBSOCKET 동작 원리                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   클라이언트                                        서버                     │
│       │                                              │                      │
│       │══════════ [연결 수립 (1회)] ════════════════│                      │
│       │                                              │                      │
│       │         <<<< 양방향 연결 유지 >>>>           │                      │
│       │                                              │                      │
│       │───────────────────────────>│ "안녕하세요"   │  ← 클라이언트→서버   │
│       │                                              │                      │
│       │<───────────────────────────│ "반갑습니다"   │  ← 서버→클라이언트   │
│       │                                              │                      │
│       │<───────────────────────────│ "서버 알림!"   │  ← 서버가 먼저 전송! │
│       │                                              │                      │
│       │───────────────────────────>│ "확인했어요"   │  ← 클라이언트→서버   │
│       │                                              │                      │
│       │         <<<< 연결 계속 유지 >>>>             │                      │
│       ▼                                              ▼                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  📌 핵심: 한 번 연결 후 "양방향" 통신 (HTTP 요청/응답 패턴 X)                 │
│  ✅ 장점: 실시간 양방향, 서버가 먼저 전송 가능, 오버헤드 낮음                 │
│  ⚠️  단점: 연결 유지 필요, 일부 방화벽/프록시에서 차단될 수 있음              │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔄 Polling/Long Polling vs WebSocket                                       │
│     Polling: 매번 새 HTTP 연결 (요청-응답-종료-요청-응답-종료...)            │
│     WebSocket: 연결 1회 수립 후 계속 유지 (효율적!)                          │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
실행 방법:
    터미널 1: python 03_websocket.py server
    터미널 2: python 03_websocket.py client

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
    """WebSocket 서버 - 양방향 실시간 통신"""

    import websockets

    connected_clients = set()
    client_counter = 0
    message_count = {'sent': 0, 'received': 0}

    async def handle_client(websocket):
        nonlocal client_counter
        client_counter += 1
        client_id = client_counter

        connected_clients.add(websocket)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        print()
        print(f"  [{timestamp}] ══════ ✅ 클라이언트 #{client_id} 연결! (현재 {len(connected_clients)}명)")
        print(f"               🔗 연결 1회 수립 → 이후 양방향 통신 (HTTP 요청 X)")

        await broadcast({
            'type': 'system',
            'message': f'클라이언트 #{client_id}님이 입장했습니다.',
            'time': timestamp
        })

        try:
            async for message in websocket:
                message_count['received'] += 1
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                print()
                print(f"  [{timestamp}] ◀─── 클라이언트 #{client_id}: \"{message}\"")
                print(f"               📨 수신: {message_count['received']}개 | 📤 전송: {message_count['sent']}개")

                await broadcast({
                    'type': 'chat',
                    'from': f'클라이언트 #{client_id}',
                    'message': message,
                    'time': timestamp
                })

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            connected_clients.discard(websocket)
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print()
            print(f"  [{timestamp}] ══════ ❌ 클라이언트 #{client_id} 연결 종료 (현재 {len(connected_clients)}명)")

            await broadcast({
                'type': 'system',
                'message': f'클라이언트 #{client_id}님이 퇴장했습니다.',
                'time': timestamp
            })

    async def broadcast(data):
        if not connected_clients:
            return

        message_count['sent'] += len(connected_clients)
        message = json.dumps(data, ensure_ascii=False)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        tasks = [asyncio.create_task(client.send(message)) for client in connected_clients]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if data['type'] != 'system':
            print(f"  [{timestamp}] ───▶ 브로드캐스트: {len(connected_clients)}명에게 전송")

    async def server_push_notifications():
        """서버에서 클라이언트로 먼저 메시지 전송 (Push)"""
        notification_count = 0

        while True:
            await asyncio.sleep(random.uniform(5, 10))

            if connected_clients:
                notification_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                print()
                print(f"  [{timestamp}] ───▶ 🔔 서버 PUSH #{notification_count}")
                print(f"               ⭐ 서버가 '먼저' 클라이언트에게 전송! (Polling에서는 불가능)")

                await broadcast({
                    'type': 'notification',
                    'message': f'서버 알림 #{notification_count}',
                    'time': timestamp
                })

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "🖥️  WEBSOCKET 서버 시작" + " " * 27 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📍 주소: ws://localhost:5002" + " " * 37 + "║")
    print("║  📌 특징: 한 번 연결 후 '양방향' 실시간 통신" + " " * 22 + "║")
    print("║  ⭐ 핵심: 서버가 먼저 클라이언트에게 메시지 전송 가능!" + " " * 10 + "║")
    print("╚" + "═" * 68 + "╝")

    server = await websockets.serve(handle_client, "localhost", 5002)
    asyncio.create_task(server_push_notifications())

    print()
    print("┌" + "─" * 68 + "┐")
    print("│  ✅ 서버 준비 완료! 다른 터미널에서 클라이언트 실행:" + " " * 15 + "│")
    print("│     python 03_websocket.py client" + " " * 33 + "│")
    print("└" + "─" * 68 + "┘")
    print()
    print("─" * 70)
    print("  아래에서 양방향 통신 흐름을 확인하세요:")
    print("  (서버가 5~10초 간격으로 클라이언트에게 PUSH 알림 전송)")
    print("─" * 70)

    await asyncio.Future()


# =============================================================================
# 클라이언트 구현
# =============================================================================

async def run_client():
    """WebSocket 클라이언트 - 양방향 실시간 통신"""

    import websockets

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 16 + "📱 WEBSOCKET 클라이언트 시작" + " " * 24 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║  📌 특징: 서버와 '양방향' 실시간 통신" + " " * 29 + "║")
    print("║  ⭐ 핵심: 연결 1회 수립 → 이후 자유롭게 송수신" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print("  메시지를 입력하면 서버로 전송됩니다.")
    print("  서버에서 오는 메시지도 실시간으로 수신됩니다.")
    print("  (빈 줄 입력 시 건너뛰기, Ctrl+C로 종료)")
    print()

    uri = "ws://localhost:5002"

    try:
        async with websockets.connect(uri) as websocket:
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print("─" * 70)
            print(f"  [{timestamp}] ══════ ✅ 서버 연결 완료!")
            print(f"               🔗 연결 1회 수립됨 - 이후 HTTP 요청 없이 통신")
            print("─" * 70)
            print()

            receive_count = 0
            send_count = 0

            async def receive_messages():
                nonlocal receive_count
                try:
                    async for message in websocket:
                        receive_count += 1
                        data = json.loads(message)
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                        if data['type'] == 'system':
                            print(f"\n  [{timestamp}] ◀─── 💬 [시스템] {data['message']}")
                        elif data['type'] == 'notification':
                            print(f"\n  [{timestamp}] ◀─── 🔔 [서버 PUSH] {data['message']}")
                            print(f"               ⭐ 서버가 '먼저' 보낸 메시지!")
                        elif data['type'] == 'chat':
                            print(f"\n  [{timestamp}] ◀─── 💭 [{data['from']}] {data['message']}")

                        print(f"               📨 수신: {receive_count}개 | 📤 전송: {send_count}개")
                        print("\n  메시지 입력: ", end='', flush=True)
                except:
                    pass

            async def send_messages():
                nonlocal send_count
                loop = asyncio.get_event_loop()

                while True:
                    try:
                        message = await loop.run_in_executor(
                            None,
                            lambda: input("  메시지 입력: ")
                        )

                        if message.strip():
                            send_count += 1
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            await websocket.send(message)
                            print(f"  [{timestamp}] ───▶ 전송 완료: \"{message}\"")
                            print(f"               📨 수신: {receive_count}개 | 📤 전송: {send_count}개")

                    except EOFError:
                        break

            await asyncio.gather(
                receive_messages(),
                send_messages()
            )

    except ConnectionRefusedError:
        print("  ⚠️  서버에 연결할 수 없습니다.")
        print("     서버가 실행 중인지 확인하세요: python 03_websocket.py server")

    except KeyboardInterrupt:
        print()
        print()
        print("═" * 70)
        print("  📊 최종 통계")
        print("─" * 70)
        print(f"  전송한 메시지: {send_count}개")
        print(f"  수신한 메시지: {receive_count}개")
        print()
        print("  ✅ WebSocket 장점:")
        print("     - 연결 1회 수립 후 계속 유지 (매번 HTTP 연결 X)")
        print("     - 양방향 통신 (서버 ↔ 클라이언트)")
        print("     - 서버가 먼저 데이터 전송 가능 (Push)")
        print("═" * 70)
        print()
        print("👋 클라이언트를 종료합니다.")


# =============================================================================
# 메인 실행부
# =============================================================================

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print(__doc__)
        print("\n사용법: python 03_websocket.py [server|client]")
        print("\n실행 순서:")
        print("  1. 터미널 1: python 03_websocket.py server")
        print("  2. 터미널 2: python 03_websocket.py client")
        sys.exit(1)

    try:
        if sys.argv[1] == 'server':
            asyncio.run(run_server())
        else:
            asyncio.run(run_client())
    except KeyboardInterrupt:
        print("\n종료됨")
