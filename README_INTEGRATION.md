# Integration Testing

## Quick Start

```bash
# Set in .env
THORDATA_INTEGRATION=true
THORDATA_PROXY_HOST=vpn9wq0d.pr.thordata.net
THORDATA_RESIDENTIAL_USERNAME=your_username
THORDATA_RESIDENTIAL_PASSWORD=your_password
THORDATA_UPSTREAM_PROXY=socks5://127.0.0.1:7898  # For TUN mode

# Run test
pytest tests/test_integration_proxy_protocols.py -v
```

## Protocol Support

SDK supports: **HTTP**, **HTTPS**, **SOCKS5**, **SOCKS5h**

See `PROXY_PROTOCOLS.md` for details.

## TUN Mode

With TUN mode (Clash Verge), the test:
- Tests **HTTPS** protocol (most reliable)
- Skips HTTP (often times out)
- Skips SOCKS5h (TUN mode limitation)

This is expected behavior.
