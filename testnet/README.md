# El Tor regtest test network (`testnet/labctl`)

A hermetic, single-host El Tor network for testing paid circuits end to end. It uses **real Lightning
settlement on regtest**, so it needs no real funds and no internet. Everything listens on loopback.

| Component | What runs |
| --- | --- |
| Chain | `bitcoind -regtest`, mined on demand |
| Lightning | Core Lightning: `payer` (the client's wallet), one receiving node per **paid** relay (`r<nick>`), and `zero`, shared by the zero-priced relays. Each paid relay gets a direct payer channel and its own amountless BOLT12 offer. `clnrest` serves plain HTTP on 127.0.0.1 |
| Tor | el-tor's Chutney fork in `basic-min` numbering: authorities `000a`–`003a`, exit `004r`, foundation client `005c`, middles `006m`–`008m`, plus an ordinary client `009c`. Every node has its own `127.0.x.y` address, so Tor's exit-enclave hint never captures the origin |
| El Tor | `ElTorFoundation 1` on every relay and on `005c`. Paid relays also publish `ElTorFoundationTerms` and their `PaymentBolt12Offer`. One `eltor-foundation-relay` controller per relay and one `eltor-foundation-client` (paid streams only: `__ElTorRequirePaidStreams 1`) |
| Origin | `127.0.0.1:18880`, `GET /bytes/<n>?seed=<s>[&rate=<B/s>]` (at most 64 MiB; rate ≥ 100 B/s), deterministic bytes, so every transfer is checked byte for byte |

## Safety

Run it in a **single-user VM or container**, not on a shared or LAN-facing host:

- **Loopback only.** Every listener (bitcoind, CLN, clnrest, each Tor node's ORPort/DirPort/ControlPort/SocksPort,
  the origin) binds a 127.0.x.y address, so only processes on this host can use the network. Exits keep Chutney's
  permissive policy (narrowing it to the origin leaves clients with no usable exit), so anything that can reach a
  client's SocksPort can exit wherever this host can connect: one more reason to run it in an offline VM.
- **Ports are not authenticated.** Another local user who binds a lab port first would receive the plaintext
  control password or the clnrest runes.
- **State directory.** `$ELTOR_LAB_STATE` must be an absolute directory you own that no one else can write. `up`
  creates it 0700 and marks it with `.eltor-lab`. `wipe` refuses an unmarked directory, and refuses while any lab
  service still listens.
- **Pid files** record each process's start time, so a reused pid is never signalled.

## Requirements

All on one Linux host or VM:

- el-tor's `tor` and `tor-gencert`, plus eltord's `eltor-foundation-*` binaries, in `$ELTOR_LAB_BIN`.
- Bitcoin Core in `$ELTOR_LAB_BITCOIN`.
- Core Lightning v24.11 or later (tested with v26.06.10) in `$ELTOR_LAB_CLN`.
- el-tor's Chutney checkout in `$ELTOR_LAB_CHUTNEY`.
- `python3`, `curl` and SQLite.

State goes to `$ELTOR_LAB_STATE` (default `/lab`). On Python 3.12 and later, `testnet/pyshim` supplies import-only
`asyncore`/`asynchat` stand-ins, because Chutney's `Traffic.py` still imports them. Chutney's own traffic
verifier is not used.

## Use

```sh
labctl up                                   # default: 006m paid 1000 msat/round, path 006m -> 007m -> 004r
labctl up --paid 006m:1000 --paid 007m:2000 --path 006m,007m,004r --periods 3
labctl status                               # processes, bootstrap, settlement (payer listpays vs relay listinvoices)
labctl fetch 1048576                        # checksummed 1 MiB through 005c (paid streams only)
labctl fetch 65536 --client plain-client    # through 009c on the relays' free allowance
labctl fetch 600000 --rate 20000            # a slow stream that crosses payment rounds
labctl scenario renewal                     # 15 min checksummed stream across the round 10->11 renewal
labctl scenario payer-stop                  # also: relay-ln-down, zero-ctl-down (fault scenarios)
labctl ln payer listpays                    # any lightning-cli call on any lab node
labctl mine 6
labctl ctl 006m GETINFO status/bootstrap-phase
labctl down && labctl wipe
```

Each scenario prints one JSON line with `"result": "PASS"|"FAIL"` and its evidence. Fault scenarios stop one
dependency on a fresh paid path. The path must close within `--limit` seconds (default 150), with no free fallback
through the paid-only client and nothing settled after the close; then a fresh path must come back. One round
funded ahead (`lead_ms`) may settle between the fault and the close, by design, and is reported separately.

`up` is idempotent. On a fresh state it mines and funds the chain, opens channels, creates offers and runes,
configures Chutney, appends the El Tor lines to each torrc, provisions every ledger, starts Tor and the
controllers, and then waits until a checksummed fetch succeeds through the paid-only client. That fetch proves
the paid path is active. It then prints the settlement evidence.

Logs are in `$ELTOR_LAB_STATE/logs` (controllers, origin), `net/nodes/<nick>/{notice,info}.log` (Tor) and
`ln/<node>/lightningd.log` (CLN). Private files (control password, runes, account JSON, ledgers, plan) are in
`foundation/`, and `lab.json` also holds the control password; all are mode 0600.
