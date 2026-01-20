"""
WebSocket: 연결 한 번 수립 후 양방향 실시간 통신
- 서버 ↔ 클라이언트 양방향 통신
- 서버가 먼저 클라이언트에게 메시지 전송 가능 (Push)
"""

import sys
import json
import asyncio
import random

async def run_server():
    import websockets

    clients = set()

    async def handle(ws):
        clients.add(ws)
        print(f"[서버] 클라이언트 연결됨")

        try:
            async for msg in ws:
                print(f"[서버] 클라이언트 → 서버: {msg}")

                # 서버가 클라이언트 메시지에 응답 (양방향!)
                reply = f"'{msg}'에 대한 서버 응답입니다"
                await ws.send(json.dumps({'type': 'reply', 'msg': reply}))
                print(f"[서버] 서버 → 클라이언트: {reply}")
        except:
            pass
        finally:
            clients.discard(ws)
            print(f"[서버] 클라이언트 연결 종료")

    # 서버가 먼저 클라이언트에게 메시지 전송 (Push)
    async def server_push():
        n = 0
        while True:
            await asyncio.sleep(random.uniform(7, 10))
            if clients:
                n += 1
                msg = f"서버가 먼저 보내는 알림 #{n}"
                print(f"[서버] 서버 → 클라이언트: {msg} (클라이언트 요청 없이!)")
                for c in clients:
                    await c.send(json.dumps({'type': 'push', 'msg': msg}))

    print("WebSocket 서버 시작 (localhost:5002)\n")
    async with websockets.serve(handle, "localhost", 5002):
        asyncio.create_task(server_push())
        await asyncio.Future()


async def run_client():
    import websockets

    print("WebSocket 클라이언트 시작")
    print("메시지를 입력하면 서버와 대화할 수 있습니다\n")

    async with websockets.connect("ws://localhost:5002") as ws:
        print("[클라이언트] 서버 연결됨 (연결 1회만 수립)\n")

        async def receive():
            async for msg in ws:
                data = json.loads(msg)
                if data['type'] == 'push':
                    print(f"\n[클라이언트] 서버 → 클라이언트: {data['msg']} (서버가 먼저 보냄!)")
                else:
                    print(f"[클라이언트] 서버 → 클라이언트: {data['msg']}")
                print("보낼 메시지: ", end='', flush=True)

        async def send():
            loop = asyncio.get_event_loop()
            while True:
                msg = await loop.run_in_executor(None, lambda: input("보낼 메시지: "))
                if msg.strip():
                    await ws.send(msg)
                    print(f"[클라이언트] 클라이언트 → 서버: {msg}")

        await asyncio.gather(receive(), send())


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 03_websocket.py server|client")
        sys.exit(1)
    try:
        asyncio.run(run_server() if sys.argv[1] == 'server' else run_client())
    except KeyboardInterrupt:
        pass
