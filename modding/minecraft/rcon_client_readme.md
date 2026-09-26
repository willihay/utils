# Minecraft RCON Test Client

A minimal, dependency-free Python RCON client for scripting against a local
Fabric/Minecraft dev server (e.g. Gradle's `runServer` task in a Fabric Loom
mod project). Useful for automated/reproducible testing of gameplay logic
(entity persistence, commands, world state) without manually playing through
the GUI client each time.

Implements the [Source RCON protocol](https://developer.valvesoftware.com/wiki/Source_RCON_Protocol)
directly over a raw socket - no external dependencies required, just a
standard Python 3 install.

## Why RCON instead of piping stdin into `runServer`?

You might be tempted to just pipe commands into the server's console stdin
(e.g. `"summon ... `n stop" | .\gradlew.bat runServer`). This is unreliable:
commands sent immediately at startup can race the server's world/dimension
initialization and fail with generic "unexpected error" messages. RCON
commands are sent *after* the server is fully up and listening, so they
don't hit that race condition.

## Setup

1. **Enable RCON in your dev server's `server.properties`** (typically at
   `<your-mod-project>\run\server.properties`):

   ```properties
   enable-rcon=true
   rcon.password=your-local-dev-password
   rcon.port=25575
   ```

   This file only affects your local dev server - it's not something you'd
   ship or use in production. Treat the password as a throwaway local-only
   value (do not reuse a real/shared password here).

2. **Start the dev server** and wait for it to finish loading (`Done (...)!`
   and `RCON running on 0.0.0.0:25575` in the log):

   ```powershell
   cd C:\path\to\your\mod\project
   .\gradlew.bat runServer --console=plain --no-daemon
   ```

   For scripted use, you can start this in the background and poll the log
   for "RCON running" before proceeding.

3. **Set your RCON password as an environment variable** (recommended, so it
   isn't hardcoded in the script or shell history):

   ```powershell
   $env:RCON_PASSWORD = "your-local-dev-password"
   ```

   You can also override the host/port the same way if needed:

   ```powershell
   $env:RCON_HOST = "127.0.0.1"
   $env:RCON_PORT = "25575"
   ```

## Usage

Run one or more commands (each is sent in order over a single connection,
and each response is printed):

```powershell
py C:\Users\willo\git-willihay\modding-scripts\minecraft\rcon_client.py "list" "time set day"
```

> **Note:** On Windows, plain `python`/`python3` may resolve to the Microsoft
> Store app execution alias instead of a real interpreter, depending on how
> Python was installed. If that happens, use the Python Launcher (`py`)
> instead, as shown above.

### Examples

**Check who/what is loaded:**
```powershell
py rcon_client.py "list"
```

**Summon a custom entity and inspect its NBT** (useful for testing
persistence bugs - summon, save, restart the server, then re-query):
```powershell
py rcon_client.py `
  "execute in minecraft:overworld run forceload add -16 -16 16 16" `
  "execute in minecraft:overworld run setblock 0 -61 0 minecraft:stone" `
  "execute in minecraft:overworld run summon touristry:tourist 0.5 -60 0.5" `
  "data get entity @e[type=touristry:tourist,limit=1] UUID" `
  "data get entity @e[type=touristry:tourist,limit=1]" `
  "save-all flush"
```

**Stop the server cleanly from a script:**
```powershell
py rcon_client.py "stop"
```

### Notes on commands

- Commands run via RCON use an "owner"-level command source with no
  associated player, so relative coordinates (`~ ~ ~`) and player-relative
  selectors (`@p`, `@s`) won't work as expected. Use absolute coordinates
  and `@e[type=...]` selectors instead.
- If you're summoning/inspecting entities far from any loaded chunk (no
  players are online), use `forceload add <x1> <z1> <x2> <z2>` first so the
  chunk actually loads and ticks.
- `data get entity <selector> <NbtPath>` requires the selector to resolve to
  exactly one entity - add `limit=1` (and `sort=nearest` only if you have a
  meaningful reference position) to avoid "Only one entity is allowed"
  errors.

## Using from Python directly

You can also import and call `run_commands(...)` directly instead of using
the CLI, e.g. from a larger test script:

```python
from rcon_client import run_commands

results = run_commands([
    "data get entity @e[type=touristry:tourist,limit=1] BaseModelVariant",
], password="your-local-dev-password")

for command, response in results:
    print(command, "->", response)
```

## Security reminder

RCON grants full admin/owner-level command access with no further
authentication once connected. Only enable it on local dev servers you
control, never on a server exposed to the internet or a shared network
without a firewall, and don't commit real passwords to source control.
