"""
WebSocket: 연결 한 번 수립 후 양방향 실시간 통신
- 서버 ↔ 클라이언트 양방향 통신
- 서버가 먼저 클라이언트에게 메시지 전송 가능 (Push)
"""

import sys
import json
import asyncio

async def run_server():
    import websockets

    clients = {}  # ws -> client_number
    connection_count = 0
    message_count = 0

    async def handle(ws):
        nonlocal connection_count
        connection_count += 1
        client_num = connection_count
        clients[ws] = client_num
        print(f"[서버] 클라이언트 #{client_num} 연결됨")

        try:
            async for msg in ws:
                print(f"[서버] 클라이언트 #{client_num} → 서버: {msg}")

                # 서버가 클라이언트 메시지에 응답 (양방향!)
                reply = f"'{msg}'에 대한 서버 응답입니다"
                await ws.send(json.dumps({'type': 'reply', 'msg': reply}))
                print(f"[서버] 서버 → 클라이언트 #{client_num}: {reply}")
        except:
            pass
        finally:
            del clients[ws]
            print(f"[서버] 클라이언트 #{client_num} 연결 종료")

    # 서버가 먼저 클라이언트에게 메시지 전송 (Push) - 5초 간격
    async def server_push():
        nonlocal message_count
        while True:
            await asyncio.sleep(5)  # 5초 간격
            if clients:
                message_count += 1
                msg = f"서버가 먼저 보내는 알림 (메시지 #{message_count})"
                client_nums = list(clients.values())
                print(f"[서버] 서버 → 클라이언트 {client_nums}: {msg} (클라이언트 요청 없이!)")
                for ws in list(clients.keys()):
                    try:
                        await ws.send(json.dumps({'type': 'push', 'msg': msg, 'msg_num': message_count}))
                    except:
                        pass

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
                    msg_num = data.get('msg_num', '?')
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
