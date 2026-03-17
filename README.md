# dnsexists

DNS availability checker. Checks whether domain names are registered across a set of TLDs, and tracks expiry of domains you own.

## Install

```bash
pip install -r requirements.txt
```

## Usage

### Single-name check

Check one name across all supported TLDs:

```bash
python dnsexists.py --name myproject
```

Outputs available domains to `output/myproject.csv`.

### Field mode — discover trending names

Fetch trending names from GitHub, Hacker News, Reddit, and Product Hunt, score them, and check DNS availability:

```bash
python dnsexists.py --field dev
python dnsexists.py --field dev --limit 10
```

- `--limit N` — cap the number of names to check (default: all selected)
- Saves candidates to `dev/input/candidates.csv`
- Per-name results go to `dev/output/<name>.csv`
- Top-10 scored available domains go to `dev/output/insight/insight_<timestamp>.csv`
- All available domains are appended to `output/available.csv` (already-checked names are skipped)

### Expiry tracker

Check which domains in your watchlist expire within 30 days:

```bash
python expiry_checker.py
```

- Reads `expiry/domains.csv` (columns: `domain`, `expiration_date`, `notes`)
- Fetches missing expiry dates via WHOIS and writes them back
- Outputs `expiry/output/YYYY-MM-DD-expiring.csv`

## TLDs checked

`.com` `.net` `.org` `.io` `.co` `.ai` `.dev` `.app` `.it` `.eu` `.info` `.biz` `.me` `.online` `.store` `.shop` `.tech` `.news` `.club` `.xyz`

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | No | GitHub API token — increases rate limit for `--field dev` |
| `PRODUCT_HUNT_TOKEN` | No | Product Hunt API token — enables Product Hunt as a source |

## Output files

| Path | Description |
|---|---|
| `output/<name>.csv` | Available domains for a single-name check |
| `output/available.csv` | Cumulative list of all available domains found in field mode |
| `dev/input/candidates.csv` | Scored candidates fetched in the last `--field dev` run |
| `dev/output/<name>.csv` | Per-name availability results from field mode |
| `dev/output/insight/insight_<ts>.csv` | Top-10 scored available domains from last field run |
| `expiry/output/YYYY-MM-DD-expiring.csv` | Domains expiring within 30 days |
