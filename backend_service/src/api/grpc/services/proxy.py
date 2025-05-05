import json
import httpx

import grpc

from src.api.grpc.protobufs import proxy_pb2_grpc, proxy_pb2


class ProxyService(proxy_pb2_grpc.CentrifugoProxyServicer):
    @staticmethod
    async def serve() -> None:
        server = grpc.aio.server()
        proxy_pb2_grpc.add_CentrifugoProxyServicer_to_server(ProxyService(), server)
        server.add_insecure_port('[::]:1337')
        await server.start()
        await server.wait_for_termination()

    @staticmethod
    async def get_user_from_token(token: str) -> dict | None:
        url = f'http://keycloak:8080/realms/myrealm/protocol/openid-connect/userinfo'
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=5.0)
            except Exception as e:
                print("Keycloak error:", e, flush=True)
                return None
            await response.raise_for_status()
            print(response.json(), flush=True)
            return response.json()


    async def Connect(
        self,
        request: proxy_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> proxy_pb2.ConnectResponse:
        data = json.loads(request.data.decode())
        await self.get_user_from_token(data['token'])
        # print(data['token'], flush=True)
        return proxy_pb2.ConnectResponse(
            result=proxy_pb2.ConnectResult(
                user="52",
            ),
        )