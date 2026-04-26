# SharpSignals — landing page (`sharpsignals.org`)

Single-page static site. Pure HTML/CSS/JS — no build step, no framework.

## Deploy

The fastest free path:

### Cloudflare Pages (recommended)
1. Push this folder (or the whole repo with `web/` as the root) to GitHub
2. Cloudflare Dashboard → **Pages** → **Create project** → Connect repo
3. Build settings:
   - Build command: *(leave blank)*
   - Build output directory: `web`
4. Custom domain: add `sharpsignals.org` → Cloudflare creates the CNAME automatically
5. SSL is automatic

### Alternative: Vercel / Netlify
Both work the same way. Drag-drop the `web/` folder or point at the repo with `web/` as the publish directory.

## Configuring the live data

Headline metrics + sheet link are hydrated by `app.js` from `window.SHARPSIGNALS_CONFIG` and an optional `/stats.json` endpoint.

To wire them up, add a small script tag before `app.js` (or replace the default object in `app.js`):

```html
<script>
  window.SHARPSIGNALS_CONFIG = {
    sheetUrl: "https://docs.google.com/spreadsheets/d/<id>/edit?usp=sharing",
    statsUrl: "/stats.json",
    telegramUrl: "https://t.me/sharpsignals_picks"
  };
</script>
```

The `/stats.json` shape:
```json
{
  "totalPicks": 47,
  "avgClv": 0.0182,
  "hitRate": 0.553,
  "updatedAt": "2026-04-26T12:00:00Z"
}
```

`agents/track_record_agent/` already writes the picks log; a separate small script can read SQLite and write `stats.json` on a daily cron and commit it back to the repo (or push to the same Cloudflare Pages bucket).

## Files

| File          | Purpose                                                          |
| ------------- | ---------------------------------------------------------------- |
| `index.html`  | Single page, all sections (hero, track record, methodology, follow, footer) |
| `styles.css`  | All styling. Tokens mirror `brand/IDENTITY.md`.                  |
| `app.js`      | Hydrate metrics + sheet link. Inert when stats unavailable.      |
| `favicon.svg` | Inline-style line chart, accent-blue on bg-deep                  |

## Compliance check

Page already includes 18+, ConnexOntario number, AGCO mention, and the
analytical-content-not-advice disclaimer in the footer. **Do not strip
those if you redesign** — they're load-bearing for AGCO-licensed-affiliate
eligibility, not just nice-to-haves.

## What's intentionally NOT here yet

- Newsletter signup form (waiting on Substack URL)
- Live track-record table embed (waiting on the public Google Sheet ID)
- Affiliate redirect routes (waiting on first AGCO-licensed sportsbook approval)
- A blog / posts page

These are all additive — the page works as-is for the IG bio link.
