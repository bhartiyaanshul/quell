"""``http_probe`` — issue a single HTTP request and return status + body head."""

from __future__ import annotations

import httpx

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_BODY_MAX = 8192


@register_tool(
    name="http_probe",
    description=(
        "Issue an HTTP request and return the status code, selected headers, "
        "and the first few KB of the body."
    ),
    parameters=[
        ToolParameterSpec(
            name="url", type="string", description="Fully-qualified URL to probe."
        ),
        ToolParameterSpec(
            name="method",
            type="string",
            description="HTTP method (default GET).",
            required=False,
        ),
        ToolParameterSpec(
            name="timeout_seconds",
            type="float",
            description="Request timeout (default 10s).",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def http_probe(
    url: str,
    method: str = "GET",
    timeout_seconds: float = 10.0,
) -> ToolResult:
    """Hit *url* once and return status + body head + select headers."""
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.request(method.upper(), url)
    except httpx.HTTPError as exc:
        return ToolResult.failure("http_probe", f"Request failed: {exc}")

    body = resp.text[:_BODY_MAX]
    headers = {
        k: v
        for k, v in resp.headers.items()
        if k.lower()
        in {
            "content-type",
            "content-length",
            "server",
            "x-request-id",
            "retry-after",
        }
    }
    lines = [
        f"HTTP {resp.status_code}",
        *(f"{k}: {v}" for k, v in headers.items()),
        "",
        body,
    ]
    return ToolResult.success(
        "http_probe",
        "\n".join(lines),
        metadata={
            "status_code": resp.status_code,
            "url": url,
            "method": method.upper(),
        },
    )
