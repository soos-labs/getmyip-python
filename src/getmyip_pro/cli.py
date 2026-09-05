"""CLI: `getmyip [-json] [-field name] [-key KEY] [ip]` — как у getmyip-go."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys

from . import APIError, Client


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="getmyip", description="IP geolocation via getmyip.pro (free, no key needed)")
    p.add_argument("ip", nargs="?", help="address to look up (default: your own IP)")
    p.add_argument("-json", action="store_true", help="print raw JSON")
    p.add_argument("-field", help="print a single field (e.g. org, country_code)")
    p.add_argument("-key", default=os.environ.get("GETMYIP_API_KEY", ""), help="API key (or env GETMYIP_API_KEY)")
    a = p.parse_args(argv)

    # GETMYIP_BASE_URL — свой инстанс (self-hosted) или мок в тестах
    base = os.environ.get("GETMYIP_BASE_URL")
    c = Client(api_key=a.key, **({"base_url": base} if base else {}))
    try:
        r = c.lookup(a.ip) if a.ip else c.me()
    except APIError as e:
        print(f"getmyip: {e.error or e.status}", file=sys.stderr)
        return 1

    d = {**dataclasses.asdict(r), **r.extra}
    d.pop("extra", None)
    if a.field:
        v = d.get(a.field)
        if v is None:
            print(f"getmyip: unknown field {a.field!r}", file=sys.stderr)
            return 1
        print(v)
        return 0
    if a.json:
        print(json.dumps(d, ensure_ascii=False))
        return 0

    print(f"IP:       {r.ip}")
    loc = ", ".join(x for x in (r.city, r.country) if x)
    if loc:
        print(f"Location: {loc} ({r.country_code})")
    if r.org:
        print(f"Network:  {r.org}" + (f" (AS{r.asn})" if r.asn else ""))
    if r.timezone:
        print(f"Timezone: {r.timezone}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
