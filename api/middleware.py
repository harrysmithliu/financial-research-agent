from __future__ import annotations

from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from observability.logging import get_logger
from observability.request_context import request_id_context


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp, request_id_header: str) -> None:
        self.app = app
        self.request_id_header = request_id_header.lower()
        self.logger = get_logger(__name__)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._get_request_id(scope)
        token = request_id_context.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((self.request_id_header.encode(), request_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            self.logger.info(
                "request_started",
                extra={
                    "request_id": request_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                },
            )
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_context.reset(token)

    def _get_request_id(self, scope: Scope) -> str:
        headers = scope.get("headers", [])
        header_name = self.request_id_header.encode()
        for name, value in headers:
            if name.lower() == header_name:
                decoded = value.decode().strip()
                if decoded:
                    return decoded
        return str(uuid4())
