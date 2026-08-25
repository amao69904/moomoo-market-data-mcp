# moomoo Market Data MCP

A read-only Model Context Protocol server that exposes real-time market data from the official Futu OpenAPI (`futu-api`) to Codex and other MCP clients.

> This project only provides market-data tools. It contains no order placement, account, position, or fund-transfer functions.

## Tools

- `moomoo_connection_status` — verify the Futu OpenD connection
- `moomoo_snapshot` — market snapshots for one or more symbols
- `moomoo_quote` — subscribed real-time quotes
- `moomoo_candles` — current K-line/candlestick data
- `moomoo_order_book` — real-time order book
- `moomoo_ticker` — recent time-and-sales records
- `moomoo_search_securities` — search securities by code or name

Symbols use Futu's format, for example `US.AAPL`, `HK.00700`, and `SH.600519`.

## Requirements

- Python 3.10+
- Futu OpenD installed, logged in, and running
- The required real-time quote entitlement in your moomoo/Futu account

The default OpenD endpoint is `127.0.0.1:11111`. This server does not need your moomoo password.

## Install and run

```bash
git clone https://github.com/amao69904/moomoo-market-data-mcp.git
cd moomoo-market-data-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
moomoo-market-data-mcp
```

Optional environment variables:

```bash
export FUTU_OPEND_HOST=127.0.0.1
export FUTU_OPEND_PORT=11111
```

## Codex MCP configuration

Add the server using the Python environment where it was installed:

```toml
[mcp_servers.moomoo-market-data]
command = "/absolute/path/to/moomoo-market-data-mcp/.venv/bin/moomoo-market-data-mcp"

[mcp_servers.moomoo-market-data.env]
FUTU_OPEND_HOST = "127.0.0.1"
FUTU_OPEND_PORT = "11111"
```

Restart Codex after changing MCP configuration, then call `moomoo_connection_status`.

## Data and safety notes

- Availability, latency, depth, and coverage depend on OpenD, account region, exchange hours, and quote entitlements.
- Subscription quotas are enforced by Futu.
- Returned data is informational and is not investment advice.
- Do not expose OpenD to the public internet. Keep it on localhost or a trusted private network.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
