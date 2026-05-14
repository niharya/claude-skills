# atses.md

Per-ATS ingestion recipes for the JD-fetch step. Build this up across runs — the first time an ATS shape works, capture it here so subsequent runs don't relitigate the path. The shared pattern under most modern ATSes is "JS shell on the public page, JSON behind an API endpoint." This file records the specific endpoint per ATS plus the parse step.

The general flow is in `SKILL.md` step 4. This file holds the specifics.

---

## Ashby

**Shape.** LinkedIn URL → mirrored Ashby posting URL → Ashby public page is a JS shell → public API endpoint returns the full JSON for the org's job board.

**Recipe.**

1. Start from the canonical Ashby posting URL (e.g. `https://jobs.ashbyhq.com/{org}/{job-id}`). If the user supplied a LinkedIn URL, get the canonical Ashby URL by asking.
2. `tabs_context_mcp` (`createIfEmpty: true`) → `navigate` to the API endpoint:
   ```
   https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true
   ```
   `{org}` is the slug in the public URL after `ashbyhq.com/`.
3. `javascript_tool`:
   ```js
   const text = document.body.innerText;
   const data = JSON.parse(text);
   const job = data.jobs.find(j => j.id === "{job-id}");
   return { title: job.title, location: job.locationName, body: job.descriptionPlain };
   ```
   `descriptionPlain` carries the JD body as text. `descriptionHtml` is the same content with HTML tags.
4. Save `body` as `examples/<slug>/jd.txt`.

**Notes.**

- The API is public for posted jobs. No auth header needed.
- `includeCompensation=true` surfaces salary band when the org publishes it.
- If the job has been pulled, the find returns undefined — confirm the URL with the user before guessing.

---

## Greenhouse

**Shape.** Public boards expose a JSON API at `boards-api.greenhouse.io`. Most JDs render server-side, so `web_fetch` may work without falling to Chrome. If it doesn't, the API is reliable.

**Recipe.**

1. From a public URL like `https://boards.greenhouse.io/{org}/jobs/{id}` or `https://job-boards.greenhouse.io/{org}/jobs/{id}`, derive the API URL:
   ```
   https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{id}
   ```
2. Try `web_fetch` on the API URL first — it returns JSON.
3. If `web_fetch` is blocked, navigate in Chrome and `javascript_tool` to parse `document.body.innerText` as JSON. Read `content` (HTML body, decode entities) and `title` / `location.name`.

---

## Lever

**Shape.** Public board at `jobs.lever.co/{org}` and per-job at `jobs.lever.co/{org}/{id}`. Pages mostly render server-side, so `web_fetch` is often enough.

**Recipe.**

1. Try `web_fetch` on the JD URL first. The body is usually in `<div class="section page-centered">` blocks.
2. If `web_fetch` fails, fall to Chrome → `get_page_text`. Lever pages are short enough that `get_page_text` typically works.
3. Public API: `https://api.lever.co/v0/postings/{org}/{id}` returns JSON if needed.

---

## Workday

**Shape.** Workday is the hardest of the major ATSes. The public page is a heavy JS app. Each tenant has its own subdomain (e.g., `companyname.wd1.myworkdayjobs.com`). There's an internal JSON endpoint but the URL pattern varies per tenant.

**Recipe.**

1. `web_fetch` will not work. Go straight to Chrome.
2. Navigate to the URL. Wait for hydration.
3. `get_page_text` — works often enough. If not, inspect the network with `read_network_requests` to find the underlying `wday/cxs/...` JSON endpoint and navigate to that.
4. As a last resort, ask the user to paste the JD body.

---

## Phenom

**Shape.** Tenant-specific subdomains (e.g., `careers.{company}.com` powered by Phenom). Pages are SPA. JSON typically exposed at a `/api/...` endpoint visible in the network panel.

**Recipe.**

1. `web_fetch` will likely fail. Go to Chrome.
2. Navigate to the JD URL. Use `read_network_requests` to find the Phenom JSON endpoint while the page hydrates.
3. Navigate to the JSON endpoint and `javascript_tool` to parse `document.body.innerText`.
4. Ask the user to paste if the network inspection doesn't surface a usable endpoint.

---

## LinkedIn

LinkedIn JD bodies are not retrievable from `linkedin.com/jobs/view/...` URLs. The page is a sign-in wall.

**Recipe.**

1. Use the LinkedIn URL only to read the page title / company name.
2. Look for a mirrored canonical posting URL (Ashby / Greenhouse / Lever / Workday) — many companies cross-post.
3. If no canonical URL is findable, ask the user to paste the JD body directly.

Do not attempt `curl` / `wget` / Python `requests` workarounds — compliance rules block them.

---

## Notes for new ATSes

When a new ATS shape surfaces:

1. Capture the public URL pattern, the API endpoint pattern, and the parse snippet.
2. Note any quirks (auth, rate-limits, region gating).
3. Add a new section to this file.
4. The pattern under everything is "JS shell on the public page, JSON behind an API endpoint." Find the JSON endpoint and the rest follows.
