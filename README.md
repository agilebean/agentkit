# agentkit
Shared agents across projects by Chaehan So

## scripts

Standalone personal scripts. `~/.local/bin` holds symlinks to these files, so the repo is the source of truth.

- `switch-opencode-apikey` — rotate the opencode-go API key across every credential store. Writes `~/.local/share/opencode/auth.json` (opencode 1.x), `account.json`, and the `credential` table in `opencode.db` (opencode 2.x and OpenChamber), so the CLI and the app always agree.
  - `switch-opencode-apikey` — toggle to the other key
  - `switch-opencode-apikey --sync` — re-apply the current key to every store
  - `switch-opencode-apikey --list` — list all keys with labels
