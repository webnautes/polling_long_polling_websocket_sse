"""
WebSocket: 연결 한 번 수립 후 양방향 실시간 통신
- 서버 ↔ 클라이언트 양방향 통신
- 서버가 먼저 클라이언트에게 메시지 전송 가능 (Push)
- 이 예제: 숫자를 1씩 증가하며 주고받기, 3의 배수면 서버가 먼저 알림
"""

import sys
import json
import asyncio

async def run_server():
    import websockets

    clients = {}  # ws -> client_number
    connection_count = 0

    async def handle(ws):
        nonlocal connection_count
        connection_count += 1
        client_num = connection_count
        clients[ws] = client_num
        print(f"[서버] 클라이언트 #{client_num} 연결됨")

        try:
            async for msg in ws:
                data = json.loads(msg)
                client_number = data['number']
                print(f"[서버] 클라이언트 #{client_num} → 서버: 숫자 {client_number}")

                await asyncio.sleep(5)  # 5초 대기

                # 서버는 1 증가시킨 숫자를 응답
                server_number = client_number + 1

                # 3의 배수면 서버가 먼저 알림을 보냄 (Push!)
                if server_number % 3 == 0:
                    alert = f"🎉 {server_number}은(는) 3의 배수입니다!"
                    print(f"[서버] 서버 → 클라이언트 #{client_num}: {alert} (서버가 먼저 Push!)")
                    await ws.send(json.dumps({'type': 'alert', 'msg': alert, 'number': server_number}))
                    await asyncio.sleep(1)  # 알림 후 잠시 대기

                print(f"[서버] 서버 → 클라이언트 #{client_num}: 숫자 {server_number}")
                await ws.send(json.dumps({'type': 'number', 'number': server_number}))

        except:
            pass
        finally:
            del clients[ws]
            print(f"[서버] 클라이언트 #{client_num} 연결 종료")

    print("WebSocket 서버 시작 (localhost:5002)")
    print("(숫자 주고받기 + 3의 배수 알림)\n")
    async with websockets.serve(handle, "localhost", 5002):
        await asyncio.Future()


async def run_client():
    import websockets

    print("WebSocket 클라이언트 시작")
    print("(숫자 주고받기 + 3의 배수 알림 수신)\n")

    async with websockets.connect("ws://localhost:5002") as ws:
        print("[클라이언트] 서버 연결됨\n")

        current_number = 1  # 클라이언트는 1부터 시작

        while True:
            # 클라이언트가 현재 숫자 전송
            print(f"[클라이언트] 클라이언트 → 서버: 숫자 {current_number}")
            await ws.send(json.dumps({'number': current_number}))

            # 서버 응답 대기 (알림이 먼저 올 수도 있음)
            while True:
                msg = await ws.recv()
                data = json.loads(msg)

                if data['type'] == 'alert':
                    print(f"[클라이언트] 서버 → 클라이언트: {data['msg']} (서버가 먼저 보냄!)")
                elif data['type'] == 'number':
                    server_number = data['number']
                    print(f"[클라이언트] 서버 → 클라이언트: 숫자 {server_number}")

                    # 클라이언트는 받은 숫자 + 1로 다음 전송 준비
                    current_number = server_number + 1
                    print(f"[클라이언트] 5초 대기 후 {current_number} 전송 예정...\n")
                    await asyncio.sleep(5)
                    break


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("사용법: python 03_websocket.py server|client")
        sys.exit(1)
    try:
        asyncio.run(run_server() if sys.argv[1] == 'server' else run_client())
    except KeyboardInterrupt:
        pass
