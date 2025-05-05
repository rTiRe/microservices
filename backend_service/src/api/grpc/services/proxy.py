import json
import httpx

import grpc
import jwt

from src.api.grpc.protobufs import proxy_pb2_grpc, proxy_pb2
from src.api.sqlc import ws_requests
from src.storage.postgres import engine
from config import settings


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
        token_data =jwt.decode(data['token'], settings.kc_public_key, algorithms=['RS256'], audience='account', verify=True)
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

    async def Subscribe(
        self,
        request: proxy_pb2.SubscribeRequest,
        context: grpc.aio.ServicerContext,
    ) -> proxy_pb2.SubscribeResponse:
        async with engine.connect() as connection:
            querier = ws_requests.AsyncQuerier(connection)
            await querier.subscribe_user_to_channel(
                user_id=request.user,
                channel=request.channel,
                can_publish=True,
            )
            await connection.commit()
        return proxy_pb2.SubscribeResponse()

    async def RPC(
        self,
        request: proxy_pb2.RPCRequest,
        context: grpc.aio.ServicerContext,
    ) -> proxy_pb2.RPCResponse:
        if request.method == 'get_user_channels':
            async with engine.connect() as connection:
                querier = ws_requests.AsyncQuerier(connection)
                channels = [channel.channel async for channel in querier.chan_list_by_user_id(user_id=request.user)]
            return proxy_pb2.RPCResponse(
                result=proxy_pb2.RPCResult(
                    data=f'{{ "channels": {json.dumps(channels)} }}'.encode(),
                ),
            )
        return super().RPC(request, context)
