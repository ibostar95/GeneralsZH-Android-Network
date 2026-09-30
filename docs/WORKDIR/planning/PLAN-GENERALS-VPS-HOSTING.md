# Generals retail-data hosting

Keep all game files, tooling, logs, and candidate configuration beneath
`/srv/generalszh-android-network`. Existing application directories, containers,
object storage, and firewall rules are out of scope.

## Serving and resource limits

The dedicated static route is `/generals-files/` with an alias to the project's
`public/` directory. Version `v1/` contains 34 archives and a portable manifest
with relative download URLs, byte lengths, and SHA-256 values. No additional
application process is needed to serve the data.

The user reports a 200 Mbit/s VPS link and allocates up to 100 Mbit/s to game
downloads. A connection limit of four active Generals responses, each limited
to 3,000,000 bytes/s, caps sustained payload at 96 Mbit/s. This leaves headroom
for protocol overhead, but it is not a wire-level traffic shaper and short
bursts are possible. Requests above the active-response limit return HTTP 429;
the Android installer must retry these with backoff. The rate and connection
limits apply only to the Generals route.

Both a new dedicated hostname and a route on an existing hostname require
nginx configuration activation. The new subdomain requires DNS and its own
TLS certificate. Adding a route to an existing domain requires one scoped
include in its HTTPS server block. Validate the combined nginx configuration,
record the exact route diff, and verify existing endpoints before and after
activation. Use a graceful nginx reload; do not restart applications or modify
their certificates. The syntax-test configuration is never used to start a
second nginx server.

## Download statistics

The dedicated JSON access log records timestamp, method, path, status, bytes,
and request completion. It records no IP addresses, query strings, account
tokens, or user agents. `scripts/build/linux/generals-data/generals-data-stats.py` produces totals,
daily counters, and per-file counters from plain or gzip-rotated logs.

Only archive GET responses contribute to data transfer totals. Completed HTTP
200 responses, range responses, interrupted responses, and errors are counted
separately; HEAD and manifest requests do not inflate download counters. These
are HTTP transfer statistics, not unique players or verified installations of
the complete game. A future completion metric must come from an installer
that has validated every required file, rather than dividing requests by 34.

Keep logs and statistics outside `public/`. Run the report through SSH or
copy its aggregate JSON locally for viewing. Establish log rotation before
unattended public operation; report coverage follows the retained log files.

## Deployment record — 2026-09-30

The live manifest is
`https://kinotrack.uz/generals-files/v1/game-data-manifest.json`.
All 34 server archives were SHA-256 verified against the local manifest
before moving the staged directory atomically into `public/v1/`. The public
manifest also matched locally when fetched through public DNS and TLS. Range
requests returned HTTP 206 and the expected `BIGF` header.

The existing KinoTrack HTTPS server received exactly one include pointing to
the project-owned location snippet. Added `/etc/nginx/conf.d/generals-download-log.conf`
for the dedicated format and connection zone, and `/etc/logrotate.d/generals-downloads`
for this route's logs only. Tested the complete candidate and then the active
configuration before a graceful reload. The original host configuration and
deployment metadata are private under the project's `backups/` and `config/`
directories. Existing HTTPS root probes passed before and after activation;
the nginx master PID stayed unchanged. These probes do not constitute full
functional tests of the other products.

The statistics command is read-only and keeps its output off the public route:

```sh
python3 /srv/generalszh-android-network/tools/generals-data-stats.py \
  /srv/generalszh-android-network/logs/downloads.jsonl*
```

At validation time the log contained two four-byte range checks, zero complete
archive transfers, and zero errors. These are deployment probes, not players.
Logs rotate daily or above 5 MiB with 14 retained rotations; reports cover
only the supplied retained logs. The Android retail installer is still pending.
