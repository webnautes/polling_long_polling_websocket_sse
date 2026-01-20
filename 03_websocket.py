"""
WebSocket - 한 번 연결 후 양방향 실시간 통신

실행: python 03_websocket.py server / python 03_websocket.py client
패키지: pip install websockets
"""

import sys
import json
import asyncio
import random
from datetime import datetime


async def run_server():
    import websockets

    clients = set()

    async def handle_client(websocket):
        clients.add(websocket)
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] 클라이언트 연결 (현재 {len(clients)}명)")

        try:
            async for message in websocket:
                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] 클라이언트 → 서버: \"{message}\"")

                # 모든 클라이언트에게 브로드캐스트
                data = json.dumps({'type': 'chat', 'message': message, 'time': ts})
                for client in clients:
                    await client.send(data)
                print(f"[{ts}] 서버 → 클라이언트들: 브로드캐스트")

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            clients.discard(websocket)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 클라이언트 연결 종료 (현재 {len(clients)}명)")

    # 서버가 먼저 클라이언트에게 메시지 전송 (Push)
    async def server_push():
        count = 0
        while True:
            await asyncio.sleep(random.uniform(5, 10))
            if clients:
                count += 1
                ts = datetime.now().strftime('%H:%M:%S')
                data = json.dumps({'type': 'push', 'message': f'서버 알림 #{count}', 'time': ts})
                for client in clients:
                    await client.send(data)
                print(f"[{ts}] 서버 → 클라이언트들: PUSH 알림 (서버가 먼저 전송!)")

    print("=== WebSocket 서버 (localhost:5002) ===")
    print("특징: 연결 1회 수립 후 양방향 통신, 서버가 먼저 전송 가능\n")

    server = await websockets.serve(handle_client, "localhost", 5002)
    asyncio.create_task(server_push())
    await asyncio.Future()


async def run_client():
    import websockets

    print("=== WebSocket 클라이언트 ===")
    print("특징: 연결 유지하며 양방향 통신 (메시지 입력 or 서버 푸시 수신)\n")

    try:
        async with websockets.connect("ws://localhost:5002") as ws:
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] 서버 연결 완료 (연결 1회 수립됨)\n")

            async def receive():
                async for message in ws:
                    data = json.loads(message)
                    ts = datetime.now().strftime('%H:%M:%S')
                    if data['type'] == 'push':
                        print(f"\n[{ts}] 서버 → 클라이언트: \"{data['message']}\" (서버가 먼저 보냄!)")
                    else:
                        print(f"\n[{ts}] 수신: \"{data['message']}\"")
                    print("메시지 입력: ", end='', flush=True)

            async def send():
                loop = asyncio.get_event_loop()
                while True:
                    message = await loop.run_in_executor(None, lambda: input("메시지 입력: "))
                    if message.strip():
                        await ws.send(message)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 클라이언트 → 서버: \"{message}\"")

            await asyncio.gather(receive(), send())

    except ConnectionRefusedError:
        print("서버 연결 실패. 서버가 실행 중인지 확인하세요.")
    except KeyboardInterrupt:
        print("\n종료")


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 03_websocket.py [server|client]")
        sys.exit(1)

    try:
        if sys.argv[1] == 'server':
            asyncio.run(run_server())
        else:
            asyncio.run(run_client())
    except KeyboardInterrupt:
        print("\n종료")
