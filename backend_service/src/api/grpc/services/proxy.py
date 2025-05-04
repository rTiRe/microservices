import grpc

from src.api.grpc.protobufs import proxy_pb2_grpc


class ProxyService(proxy_pb2_grpc.CentrifugoProxyServicer):
    @staticmethod
    async def serve() -> None:
        server = grpc.aio.server()
        proxy_pb2_grpc.add_CentrifugoProxyServicer_to_server(ProxyService(), server)
        server.add_insecure_port('[::]:1337')
        await server.start()
        await server.wait_for_termination()
