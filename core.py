import pydantic


class Response(pydantic.BaseModel):
    latency: float
    servers: list[int]
    memory_used: float
