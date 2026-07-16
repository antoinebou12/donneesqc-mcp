# Design: User context + events soon

**Date:** 2026-07-16
**Status:** Implemented
**Sources:**
- Agent-supplied phone GPS / system time (primary)
- Client IP headers (`X-Forwarded-For`) — never MCP host egress
- https://ipapi.co/{ip}/json/ (configurable)
- Festivals + https://www.donneesquebec.ca/ (vmtl-evenements-publics)

## Goal

Help agents answer “near me” / “what’s on soon” without inventing location or using the Vercel/Docker server IP.

| MCP tool | Purpose |
| --- | --- |
| `common_get_context` | Date/time + location (agent GPS → address → client IP) |
| Soft defaults on `*_nearby` / avis / briefing | Auto-fill omitted date/location via same resolver |
| `mtl_events_soon` | Festivals + civic events in `[now, now+hours]` |

## Resolution order

**Time:** agent `date`/`timezone` → `America/Toronto` now.
**Location:** agent lat/lon → address geocode → public client IP geo → clear error.
**Never:** geolocate empty IP / host self / private IPs.

## Architecture

```
helpers/common/context.py
helpers/mtl/nearby.py          # resolve_user_point
helpers/mtl/events_soon.py
tools/common/get_context.py
tools/mtl/events/events_soon.py
```

## Non-goals

- True device GPS APIs inside the MCP process
- Composite `mtl_near_me` (briefing already covers nearby bundle)
- Inventing festival coordinates
