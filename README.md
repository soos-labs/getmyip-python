# getmyip-pro (Python)

Tiny, dependency-free Python client **and CLI** for the [getmyip.pro](https://getmyip.pro) IP geolocation API — privacy-first (no logs, no trackers), with ip-api-compatible JSON.

> One plan: free. 60 requests/min, 10,000/day, batch up to 100 IPs — no signup,
> no key. Hit the ceiling? Email tech@getmyip.pro and we'll raise it for you.

[![Test](https://github.com/soos-labs/getmyip-python/actions/workflows/test.yml/badge.svg)](https://github.com/soos-labs/getmyip-python/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/getmyip-pro)](https://pypi.org/project/getmyip-pro/)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)

## CLI

```sh
pip install getmyip-pro
```

```console
$ getmyip
IP:       45.82.64.40
Location: Naaldwijk, Netherlands (NL)
Network:  WorldStream B.V. (AS49981)
Timezone: Europe/Amsterdam

$ getmyip 8.8.8.8
IP:       8.8.8.8
Location: United States (US)
Network:  Google LLC (AS15169)

$ getmyip -field org 8.8.8.8
Google LLC

$ getmyip -json 8.8.8.8
{"ip": "8.8.8.8", "country": "United States", ...}
```

An API key is optional (the anonymous tier needs none); pass `-key` or set `GETMYIP_API_KEY` for higher limits.

## Library

```python
from getmyip_pro import Client

c = Client()                      # Client(api_key="...") to raise limits
me = c.me()                       # your own IP
r = c.lookup("8.8.8.8")           # any IPv4/IPv6
rs = c.batch(["8.8.8.8", "1.1.1.1"])

print(r.country, r.org, r.asn)    # United States Google LLC 15169
```

Errors raise `getmyip_pro.APIError` with `.status` and `.error` (e.g. `rate_limited` — see [limits](https://getmyip.pro/limits)).

No dependencies: stdlib `urllib` only. Python 3.9+.

## Related

- Go client/CLI: [soos-labs/getmyip-go](https://github.com/soos-labs/getmyip-go)
- Node.js client/CLI: [soos-labs/getmyip-js](https://github.com/soos-labs/getmyip-js)
- API docs: [docs.getmyip.pro](https://docs.getmyip.pro)
