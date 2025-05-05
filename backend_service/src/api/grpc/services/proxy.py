import json
import httpx

import grpc
import jwt

from src.api.grpc.protobufs import proxy_pb2_grpc, proxy_pb2
from src.api.sqlc import ws_requests
from src.storage.postgres import engine


PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApWUuKoo/aKrDUZxiWLQT7jl64cCLg2ibTrWRHcJdUakA/YEcSkqGs4vX3iWNcCwfjRkBgMes2/aCEC1LULX63OaZrsn7SmzT1jLrmynR6DN0GU4iYsGTYIG6EqxnRcia8G5xkY6adFmGEtL7tiwRKc2VFZOAT02o9ehu49yzHfM6aHkv1ioWOzm6EgrRKUssOTGGUaDVTsETlbF2/ZcvaMnJ9BLszBkdTcOPvQRKEldzWGR1ztmrqspHSZlyLWWEzZbOwDK8nYZjWyte6oLzQK092T6LtBTdpLR6u0AJclPGmycRg6nr645+LYKyuZweYZR94U3IJ8ZPsQx9aBed/QIDAQAB\n-----END PUBLIC KEY-----'


class ProxyService(proxy_pb2_grpc.CentrifugoProxyServicer):
    @staticmethod
    async def serve() -> None:
        server = grpc.aio.server()
        proxy_pb2_grpc.add_CentrifugoProxyServicer_to_server(ProxyService(), server)
        server.add_insecure_port('[::]:1337')
        await server.start()
        await server.wait_for_termination()

    async def Connect(
        self,
        request: proxy_pb2.ConnectRequest,
        context: grpc.aio.ServicerContext,
    ) -> proxy_pb2.ConnectResponse:
        data = json.loads(request.data.decode())
        token_data =jwt.decode(data['token'], PUBLIC_KEY, algorithms=['RS256'], audience='account', verify=True)
        user_data = {
            'id': token_data['sub'],
            'username': token_data['preferred_username'],
            'given_name': token_data['given_name'],
            'family_name': token_data['family_name'],
            'email': token_data['email'],
        }
        async with engine.connect() as connection:
            querier = ws_requests.AsyncQuerier(connection)
            user = await querier.get_user_by_id(id=user_data['id'])
            if not user:
                await querier.create_user(
                    id=user_data['id'],
                    username=user_data['username'],
                    given_name=user_data['given_name'],
                    family_name=user_data['family_name'],
                    enabled=True,
                )
            await connection.commit()
        return proxy_pb2.ConnectResponse(
            result=proxy_pb2.ConnectResult(
                user=user_data['id'],
            ),
        )