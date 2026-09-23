import time
import uuid

from fastapi import Request


async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    return response