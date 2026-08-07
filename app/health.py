from __future__ import annotations

import asyncio
import json
import logging

log = logging.getLogger(__name__)


async def _handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        await asyncio.wait_for(reader.read(4096), timeout=2)
        body = json.dumps({"status": "ok", "service": "AniWave"}).encode()
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: close\r\n\r\n"
            + body
        )
        writer.write(response)
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def start_health_server(host: str, port: int) -> asyncio.AbstractServer:
    server = await asyncio.start_server(_handler, host, port)
    log.info("Health server listening on %s:%s", host, port)
    return server
