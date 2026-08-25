"""MCP tools backed by the official Futu OpenAPI."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

from mcp.server.fastmcp import FastMCP

from .config import OpenDConfig

mcp = FastMCP("moomoo-market-data")


def _futu() -> Any:
    try:
        import futu
    except ImportError as exc:
        raise RuntimeError("futu-api is not installed; run: pip install -e .") from exc
    return futu


@contextmanager
def _quote_context() -> Iterator[Any]:
    futu = _futu()
    config = OpenDConfig.from_env()
    context = futu.OpenQuoteContext(host=config.host, port=config.port)
    try:
        yield context
    finally:
        context.close()


def _records(frame: Any) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _require_ok(result: tuple[Any, Any], operation: str) -> Any:
    futu = _futu()
    code, payload = result
    if code != futu.RET_OK:
        raise RuntimeError(f"{operation} failed: {payload}")
    return payload


def _normalize_codes(codes: list[str]) -> list[str]:
    normalized = [code.strip().upper() for code in codes if code.strip()]
    if not normalized:
        raise ValueError("At least one symbol is required")
    if len(normalized) > 50:
        raise ValueError("At most 50 symbols may be requested at once")
    for code in normalized:
        if "." not in code:
            raise ValueError(f"Invalid symbol {code!r}; use Futu format such as US.AAPL")
    return list(dict.fromkeys(normalized))


def _enum(enum_type: Any, value: str, label: str) -> Any:
    key = value.strip().upper()
    try:
        return getattr(enum_type, key)
    except AttributeError as exc:
        raise ValueError(f"Unsupported {label}: {value}") from exc


@mcp.tool()
def moomoo_connection_status() -> dict[str, Any]:
    """Check whether the configured Futu OpenD endpoint is reachable."""
    config = OpenDConfig.from_env()
    with _quote_context():
        return {"connected": True, "host": config.host, "port": config.port,
                "mode": "read-only market data"}


@mcp.tool()
def moomoo_snapshot(codes: list[str]) -> list[dict[str, Any]]:
    """Get market snapshots. Symbols must look like US.AAPL or HK.00700."""
    symbols = _normalize_codes(codes)
    with _quote_context() as context:
        frame = _require_ok(context.get_market_snapshot(symbols), "get_market_snapshot")
    return _records(frame)


@mcp.tool()
def moomoo_quote(codes: list[str]) -> list[dict[str, Any]]:
    """Subscribe and return the latest real-time quote for each symbol."""
    futu = _futu()
    symbols = _normalize_codes(codes)
    with _quote_context() as context:
        _require_ok(context.subscribe(symbols, [futu.SubType.QUOTE], subscribe_push=False),
                    "subscribe QUOTE")
        frame = _require_ok(context.get_stock_quote(symbols), "get_stock_quote")
    return _records(frame)


@mcp.tool()
def moomoo_candles(code: str, count: int = 100, ktype: str = "K_DAY",
                    autype: str = "QFQ") -> list[dict[str, Any]]:
    """Return current candles. ktype examples: K_1M, K_5M, K_DAY."""
    if not 1 <= count <= 1000:
        raise ValueError("count must be between 1 and 1000")
    symbol = _normalize_codes([code])[0]
    futu = _futu()
    kl_type = _enum(futu.KLType, ktype, "ktype")
    subtype = _enum(futu.SubType, ktype, "ktype")
    au_type = _enum(futu.AuType, autype, "autype")
    with _quote_context() as context:
        _require_ok(context.subscribe([symbol], [subtype], subscribe_push=False),
                    f"subscribe {ktype}")
        frame = _require_ok(context.get_cur_kline(symbol, count, kl_type, au_type),
                            "get_cur_kline")
    return _records(frame)


@mcp.tool()
def moomoo_order_book(code: str, depth: int = 10) -> dict[str, Any]:
    """Return the real-time bid/ask order book for one symbol."""
    if not 1 <= depth <= 50:
        raise ValueError("depth must be between 1 and 50")
    symbol = _normalize_codes([code])[0]
    futu = _futu()
    with _quote_context() as context:
        _require_ok(context.subscribe([symbol], [futu.SubType.ORDER_BOOK],
                                      subscribe_push=False), "subscribe ORDER_BOOK")
        book = _require_ok(context.get_order_book(symbol, num=depth), "get_order_book")
    return book


@mcp.tool()
def moomoo_ticker(code: str, count: int = 100) -> list[dict[str, Any]]:
    """Return recent real-time time-and-sales records for one symbol."""
    if not 1 <= count <= 1000:
        raise ValueError("count must be between 1 and 1000")
    symbol = _normalize_codes([code])[0]
    futu = _futu()
    with _quote_context() as context:
        _require_ok(context.subscribe([symbol], [futu.SubType.TICKER],
                                      subscribe_push=False), "subscribe TICKER")
        frame = _require_ok(context.get_rt_ticker(symbol, count), "get_rt_ticker")
    return _records(frame)


@mcp.tool()
def moomoo_search_securities(market: str, query: str, security_type: str = "STOCK",
                             limit: int = 20) -> list[dict[str, Any]]:
    """Search securities in a market such as US, HK, SH, or SZ."""
    if not query.strip():
        raise ValueError("query cannot be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    futu = _futu()
    market_value = _enum(futu.Market, market, "market")
    type_value = _enum(futu.SecurityType, security_type, "security_type")
    with _quote_context() as context:
        frame = _require_ok(context.get_stock_basicinfo(market=market_value,
                                                        stock_type=type_value),
                            "get_stock_basicinfo")
    needle = query.strip().casefold()
    mask = (frame["code"].astype(str).str.casefold().str.contains(needle, regex=False)
            | frame["name"].astype(str).str.casefold().str.contains(needle, regex=False))
    return _records(frame.loc[mask].head(limit))


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
