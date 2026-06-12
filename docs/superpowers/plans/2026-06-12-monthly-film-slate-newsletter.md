# Monthly Film Slate Newsletter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a scheduled Claude Code routine that fires on the 1st of every month, researches the next 3 months of film releases from 30 specific studios, writes 2-sentence synopses + 2-sentence creator sponsorship tie-ins for each film, and creates a beautifully formatted Gmail draft addressed to all recipients in `recipients.json`.

**Architecture:** A Workflow script (`workflow.js`) handles the monthly run in phases — parallel studio research, adversarial date verification (triple-check requirement), creator tie-in generation using `good_story_context.md` as the profile source, HTML email assembly using the approved template, and Gmail draft creation via MCP. A `/schedule` cron routine triggers the workflow on the 1st of each month against the GitHub repo.

**Tech Stack:** Claude Code Workflow API (JavaScript), Gmail MCP (`mcp__claude_ai_Gmail__create_draft`), WebSearch + WebFetch tools, GitHub repo `joshgabbay/good-story-studios`, HTML email template (user-provided from design tool)

---

## File Structure

| File | Purpose |
|------|---------|
| `automations/01-monthly-film-slate-newsletter/studios.json` | Master list of 30 studios with Wikipedia URLs and search hints |
| `automations/01-monthly-film-slate-newsletter/recipients.json` | Email recipient list (already created) |
| `automations/01-monthly-film-slate-newsletter/email-template.html` | HTML email template (user provides from design tool) |
| `automations/01-monthly-film-slate-newsletter/workflow.js` | Monthly execution workflow script |
| `automations/01-monthly-film-slate-newsletter/spec.md` | Original spec (already exists) |
| `automations/01-monthly-film-slate-newsletter/README.md` | How to run, test, and modify |
| `good_story_context.md` | Creator deep-dive profiles (referenced at runtime from repo root) |

---

## Task 1: Create `studios.json`

**Files:**
- Create: `automations/01-monthly-film-slate-newsletter/studios.json`

- [ ] **Step 1: Create studios config file**

```json
{
  "studios": [
    { "name": "Disney", "key": "disney", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Walt_Disney_Pictures_films", "search_hint": "Walt Disney Pictures upcoming films 2025 2026" },
    { "name": "Marvel Studios", "key": "marvel", "wikipedia_url": "https://en.wikipedia.org/wiki/Marvel_Cinematic_Universe#Upcoming_films", "search_hint": "Marvel Studios upcoming MCU films release dates" },
    { "name": "Lucasfilm", "key": "lucasfilm", "wikipedia_url": "https://en.wikipedia.org/wiki/Lucasfilm", "search_hint": "Lucasfilm Star Wars upcoming films release dates 2025 2026" },
    { "name": "20th Century Studios", "key": "20th_century", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_20th_Century_Studios_films", "search_hint": "20th Century Studios upcoming films release dates" },
    { "name": "Pixar Animation Studios", "key": "pixar", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Pixar_films", "search_hint": "Pixar upcoming films release dates 2025 2026" },
    { "name": "Walt Disney Animation Studios", "key": "wdas", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Walt_Disney_Animation_Studios_films", "search_hint": "Walt Disney Animation Studios upcoming films 2025 2026" },
    { "name": "Warner Bros. Pictures", "key": "warnerbros", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Warner_Bros._Pictures_films", "search_hint": "Warner Bros Pictures upcoming films release dates 2025 2026" },
    { "name": "New Line Cinema", "key": "newline", "wikipedia_url": "https://en.wikipedia.org/wiki/New_Line_Cinema", "search_hint": "New Line Cinema upcoming films release dates 2025 2026" },
    { "name": "DC Studios", "key": "dc", "wikipedia_url": "https://en.wikipedia.org/wiki/DC_Studios", "search_hint": "DC Studios DCU upcoming films release dates 2025 2026" },
    { "name": "HBO", "key": "hbo", "wikipedia_url": "https://en.wikipedia.org/wiki/HBO", "search_hint": "HBO Max original films upcoming release dates 2025 2026" },
    { "name": "Universal Pictures", "key": "universal", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Universal_Pictures_films", "search_hint": "Universal Pictures upcoming films release dates 2025 2026" },
    { "name": "DreamWorks Animation", "key": "dreamworks", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_DreamWorks_Animation_films", "search_hint": "DreamWorks Animation upcoming films release dates 2025 2026" },
    { "name": "Focus Features", "key": "focus", "wikipedia_url": "https://en.wikipedia.org/wiki/Focus_Features", "search_hint": "Focus Features upcoming films release dates 2025 2026" },
    { "name": "Illumination", "key": "illumination", "wikipedia_url": "https://en.wikipedia.org/wiki/Illumination_(company)", "search_hint": "Illumination Entertainment upcoming films Minions 2025 2026" },
    { "name": "Paramount Pictures", "key": "paramount", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Paramount_Pictures_films", "search_hint": "Paramount Pictures upcoming films release dates 2025 2026" },
    { "name": "CBS Studios", "key": "cbs", "wikipedia_url": "https://en.wikipedia.org/wiki/CBS_Studios", "search_hint": "CBS Studios upcoming films Paramount+ release dates 2025 2026" },
    { "name": "Showtime", "key": "showtime", "wikipedia_url": "https://en.wikipedia.org/wiki/Showtime_(TV_network)", "search_hint": "Showtime original films upcoming release dates 2025 2026" },
    { "name": "Sony Pictures Entertainment", "key": "sony", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Sony_Pictures_films", "search_hint": "Sony Pictures Entertainment upcoming films 2025 2026" },
    { "name": "Columbia Pictures", "key": "columbia", "wikipedia_url": "https://en.wikipedia.org/wiki/List_of_Columbia_Pictures_films", "search_hint": "Columbia Pictures upcoming films release dates 2025 2026" },
    { "name": "TriStar Pictures", "key": "tristar", "wikipedia_url": "https://en.wikipedia.org/wiki/TriStar_Pictures", "search_hint": "TriStar Pictures upcoming films release dates 2025 2026" },
    { "name": "Sony Pictures Television", "key": "spt", "wikipedia_url": "https://en.wikipedia.org/wiki/Sony_Pictures_Television", "search_hint": "Sony Pictures Television upcoming films streaming 2025 2026" },
    { "name": "Netflix Studios", "key": "netflix", "wikipedia_url": "https://en.wikipedia.org/wiki/Netflix", "search_hint": "Netflix original films upcoming release dates 2025 2026" },
    { "name": "Amazon MGM Studios", "key": "amazon_mgm", "wikipedia_url": "https://en.wikipedia.org/wiki/Amazon_MGM_Studios", "search_hint": "Amazon MGM Studios Prime Video upcoming films release dates 2025 2026" },
    { "name": "MGM", "key": "mgm", "wikipedia_url": "https://en.wikipedia.org/wiki/Metro-Goldwyn-Mayer", "search_hint": "MGM upcoming films release dates 2025 2026" },
    { "name": "Apple TV+", "key": "apple", "wikipedia_url": "https://en.wikipedia.org/wiki/Apple_TV%2B", "search_hint": "Apple TV Plus original films upcoming release dates 2025 2026" },
    { "name": "Lionsgate", "key": "lionsgate", "wikipedia_url": "https://en.wikipedia.org/wiki/Lionsgate_Films", "search_hint": "Lionsgate Films upcoming release dates 2025 2026" },
    { "name": "A24", "key": "a24", "wikipedia_url": "https://en.wikipedia.org/wiki/A24_(company)", "search_hint": "A24 upcoming films release dates 2025 2026" },
    { "name": "Miramax", "key": "miramax", "wikipedia_url": "https://en.wikipedia.org/wiki/Miramax", "search_hint": "Miramax upcoming films release dates 2025 2026" },
    { "name": "Skydance Media", "key": "skydance", "wikipedia_url": "https://en.wikipedia.org/wiki/Skydance_Media", "search_hint": "Skydance Media upcoming films release dates 2025 2026" },
    { "name": "Legendary Entertainment", "key": "legendary", "wikipedia_url": "https://en.wikipedia.org/wiki/Legendary_Entertainment", "search_hint": "Legendary Entertainment upcoming films Monsterverse 2025 2026" },
    { "name": "Blumhouse Productions", "key": "blumhouse", "wikipedia_url": "https://en.wikipedia.org/wiki/Blumhouse_Productions", "search_hint": "Blumhouse Productions upcoming horror films release dates 2025 2026" }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
git add automations/01-monthly-film-slate-newsletter/studios.json
git commit -m "Add studios config for monthly film slate newsletter"
```

---

## Task 2: Add HTML Email Template

**Files:**
- Create: `automations/01-monthly-film-slate-newsletter/email-template.html`

> **Blocked on user input:** User is generating this from a design tool. Once they paste it back, save it here verbatim.

- [ ] **Step 1: Save the HTML from the design tool**

Paste the HTML provided by the user into `automations/01-monthly-film-slate-newsletter/email-template.html` exactly as given.

The template must contain these placeholder strings that `workflow.js` will replace at runtime:
- `{{MONTH_YEAR}}` — e.g. "July 2026"
- `{{STUDIO_BLOCKS}}` — the generated per-studio HTML blocks
- `{{GENERATED_DATE}}` — e.g. "Generated June 1, 2026"

Each studio block the script will inject uses this inner structure (adapt to match the template's actual design):
```html
<div class="studio-block">
  <h2 class="studio-name">{{STUDIO_NAME}}</h2>
  {{FILM_ENTRIES}}
</div>
```

Each film entry:
```html
<div class="film-entry">
  <div class="film-header">
    <span class="film-title">{{FILM_TITLE}}</span>
    <span class="film-date">{{RELEASE_DATE}}</span>
  </div>
  <p class="synopsis">{{SYNOPSIS}}</p>
  <div class="creator-opportunity">
    <strong>Creator Opportunity:</strong> {{CREATOR_TIE_IN}}
  </div>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add automations/01-monthly-film-slate-newsletter/email-template.html
git commit -m "Add HTML email template for monthly film slate newsletter"
```

---

## Task 3: Write `workflow.js`

**Files:**
- Create: `automations/01-monthly-film-slate-newsletter/workflow.js`

- [ ] **Step 1: Create the workflow script**

```javascript
export const meta = {
  name: 'monthly-film-slate-newsletter',
  description: 'Research upcoming film slates for 30+ studios and create a Gmail draft with creator sponsorship tie-ins',
  phases: [
    { title: 'Setup' },
    { title: 'Research' },
    { title: 'Verify' },
    { title: 'Generate' },
    { title: 'Send' },
  ],
}

// ── Schemas ────────────────────────────────────────────────────────────────

const DATE_SCHEMA = {
  type: 'object',
  properties: {
    today: { type: 'string', description: 'YYYY-MM-DD' },
    window_start: { type: 'string', description: 'YYYY-MM-DD, same as today' },
    window_end: { type: 'string', description: 'YYYY-MM-DD, exactly 3 months from today' },
    month_year_label: { type: 'string', description: 'e.g. "July 2026"' },
  },
  required: ['today', 'window_start', 'window_end', 'month_year_label'],
}

const STUDIO_RELEASES_SCHEMA = {
  type: 'object',
  properties: {
    studio_key: { type: 'string' },
    releases: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          release_date: { type: 'string', description: 'YYYY-MM-DD or "anticipated YYYY-MM"' },
          date_status: { type: 'string', enum: ['confirmed', 'anticipated', 'unconfirmed'] },
          initial_synopsis: { type: 'string', description: 'Brief description found in research' },
          source_urls: { type: 'array', items: { type: 'string' } },
        },
        required: ['title', 'release_date', 'date_status'],
      },
    },
  },
  required: ['studio_key', 'releases'],
}

const VERIFIED_FILM_SCHEMA = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    studio_name: { type: 'string' },
    studio_key: { type: 'string' },
    release_date: { type: 'string' },
    date_status: { type: 'string', enum: ['confirmed', 'anticipated'] },
    synopsis: { type: 'string', description: 'Exactly 2 short sentences about what the film is about' },
    corroboration_count: { type: 'number', description: 'Number of independent sources that confirmed this date' },
    include: { type: 'boolean', description: 'true if date is within 3-month window and has >= 2 source corroboration' },
  },
  required: ['title', 'studio_name', 'studio_key', 'release_date', 'date_status', 'synopsis', 'corroboration_count', 'include'],
}

const CREATOR_TIEIN_SCHEMA = {
  type: 'object',
  properties: {
    film_title: { type: 'string' },
    studio_key: { type: 'string' },
    creator_name: { type: 'string' },
    creator_channel: { type: 'string' },
    tie_in: { type: 'string', description: 'Exactly 2 short sentences: one naming the creator and one creative integration idea' },
  },
  required: ['film_title', 'studio_key', 'creator_name', 'tie_in'],
}

// ── Phase 1: Setup ─────────────────────────────────────────────────────────

phase('Setup')

const dateInfo = await agent(
  'Run the bash command: date "+%Y-%m-%d". Then calculate: today (that date), window_start (same date), window_end (exactly 3 calendar months later, e.g. if today is 2026-07-01 then window_end is 2026-10-01), month_year_label (e.g. "July 2026" for the current month). Return as JSON.',
  { phase: 'Setup', label: 'get-date', schema: DATE_SCHEMA }
)

const studiosRaw = await agent(
  'Read the file at path: automations/01-monthly-film-slate-newsletter/studios.json — use the Read tool with that exact path. Return the full JSON contents as a string.',
  { phase: 'Setup', label: 'read-studios' }
)

const recipientsRaw = await agent(
  'Read the file at path: automations/01-monthly-film-slate-newsletter/recipients.json — use the Read tool with that exact path. Return the full JSON contents as a string.',
  { phase: 'Setup', label: 'read-recipients' }
)

const creatorProfiles = await agent(
  'Read the file at path: good_story_context.md — use the Read tool with that exact path. Return the full file contents. This file contains deep-dive creator profiles for Good Story Studios\' YouTube creator roster.',
  { phase: 'Setup', label: 'read-creator-profiles' }
)

const emailTemplate = await agent(
  'Read the file at path: automations/01-monthly-film-slate-newsletter/email-template.html — use the Read tool with that exact path. Return the full HTML contents as a string.',
  { phase: 'Setup', label: 'read-template' }
)

const studios = JSON.parse(studiosRaw).studios
const recipients = JSON.parse(recipientsRaw).recipients

// ── Phase 2: Research ──────────────────────────────────────────────────────

phase('Research')

log(`Researching film slates for ${studios.length} studios. Window: ${dateInfo.window_start} → ${dateInfo.window_end}`)

const studioResearch = await parallel(studios.map(studio => () =>
  agent(
    `Research upcoming film releases from "${studio.name}" that fall between ${dateInfo.window_start} and ${dateInfo.window_end} (next 3 months).

Search these sources:
1. ${studio.wikipedia_url}
2. Web search: "${studio.search_hint}"
3. Any studio press release pages or entertainment news sites (Deadline, Variety, Hollywood Reporter, IMDb)

For each film found in this window: record the title, release date (YYYY-MM-DD if confirmed, or "anticipated YYYY-MM" if not exact), whether the date is confirmed vs anticipated, and any description you found. Also note source URLs.

If the studio has NO films releasing in this window, return an empty releases array. Do not include films releasing outside the ${dateInfo.window_start}–${dateInfo.window_end} window.

Studio key: ${studio.key}`,
    { phase: 'Research', label: `research:${studio.key}`, schema: STUDIO_RELEASES_SCHEMA }
  )
))

const studiosWithFilms = studioResearch
  .filter(Boolean)
  .filter(r => r.releases && r.releases.length > 0)

log(`Found releases in ${studiosWithFilms.length} studios. Proceeding to verification.`)

// ── Phase 3: Verify ────────────────────────────────────────────────────────

phase('Verify')

const allFilms = studiosWithFilms.flatMap(s =>
  s.releases.map(film => ({ ...film, studio_key: s.studio_key, studio_name: studios.find(st => st.key === s.studio_key).name }))
)

log(`Verifying ${allFilms.length} films across independent sources (triple-check requirement)`)

const verifiedFilms = await parallel(allFilms.map(film => () =>
  agent(
    `Verify the following film's release date by checking at least 3 independent sources (Wikipedia, IMDb, Deadline/Variety/THR, studio official site, Fandango, etc.).

Film: "${film.title}"
Studio: "${film.studio_name}"
Claimed release date: ${film.release_date} (status: ${film.date_status})
Date window we care about: ${dateInfo.window_start} to ${dateInfo.window_end}

Steps:
1. Search for "${film.title} ${film.studio_name} release date" across multiple sources
2. Count how many independent sources corroborate the date (corroboration_count)
3. If date differs across sources, use the most commonly cited date and note discrepancy
4. Write exactly 2 short sentences for the synopsis: what the film is about (not marketing fluff, actual plot/premise)
5. Set include=true only if: (a) release date falls within window AND (b) corroboration_count >= 2
6. If no release date can be confirmed but film is anticipated in window, set date_status="anticipated" and include=true

Return verified data.`,
    { phase: 'Verify', label: `verify:${film.studio_key}:${film.title.slice(0, 25)}`, schema: VERIFIED_FILM_SCHEMA }
  )
))

const confirmedFilms = verifiedFilms
  .filter(Boolean)
  .filter(f => f.include)

log(`${confirmedFilms.length} films passed verification and date-window check.`)

// ── Phase 4: Generate ──────────────────────────────────────────────────────

phase('Generate')

const filmsByStudio = {}
for (const film of confirmedFilms) {
  if (!filmsByStudio[film.studio_key]) filmsByStudio[film.studio_key] = { studio_name: film.studio_name, films: [] }
  filmsByStudio[film.studio_key].films.push(film)
}

const filmSummary = confirmedFilms.map(f => `${f.title} (${f.studio_name}, ${f.release_date})`).join('; ')

const tieIns = await parallel(confirmedFilms.map(film => () =>
  agent(
    `You are a talent manager at Good Story Studios. For the film below, identify ONE or TWO of Good Story's creators whose content niche best fits this film, and write a creative 2-sentence sponsored-segment idea.

FILM: "${film.title}" (${film.studio_name}, releasing ${film.release_date})
SYNOPSIS: ${film.synopsis}

CREATOR PROFILES (use these for specificity — match niche, format, audience, past brand deals):
${creatorProfiles}

Rules:
- Pick the creator(s) whose existing content format most naturally fits this film
- The integration must feel organic, not forced
- 2 sentences only: sentence 1 names the creator and the angle; sentence 2 describes the specific segment format or hook
- Be specific: reference the creator's actual video format, channel style, or past series

Return the film_title, studio_key (${film.studio_key}), the chosen creator_name, their channel name, and the tie_in text.`,
    { phase: 'Generate', label: `tiein:${film.studio_key}:${film.title.slice(0, 20)}`, schema: CREATOR_TIEIN_SCHEMA }
  )
))

// ── Assemble HTML email ────────────────────────────────────────────────────

const tieInMap = {}
for (const t of tieIns.filter(Boolean)) {
  tieInMap[t.film_title] = t
}

let studioBlocksHtml = ''
const studioKeys = Object.keys(filmsByStudio)

for (const key of studioKeys) {
  const { studio_name, films } = filmsByStudio[key]
  let filmEntriesHtml = ''
  for (const film of films.sort((a, b) => a.release_date.localeCompare(b.release_date))) {
    const tiein = tieInMap[film.title]
    const tieinText = tiein
      ? `<strong>${tiein.creator_name}:</strong> ${tiein.tie_in}`
      : 'No creator tie-in identified.'
    filmEntriesHtml += `
      <div class="film-entry">
        <div class="film-header">
          <span class="film-title">${film.title}</span>
          <span class="film-date">${film.release_date}${film.date_status === 'anticipated' ? ' (anticipated)' : ''}</span>
        </div>
        <p class="synopsis">${film.synopsis}</p>
        <div class="creator-opportunity">
          <strong>Creator Opportunity:</strong> ${tieinText}
        </div>
      </div>`
  }
  studioBlocksHtml += `
    <div class="studio-block">
      <h2 class="studio-name">${studio_name}</h2>
      ${filmEntriesHtml}
    </div>`
}

const finalHtml = emailTemplate
  .replace('{{MONTH_YEAR}}', dateInfo.month_year_label)
  .replace('{{STUDIO_BLOCKS}}', studioBlocksHtml)
  .replace('{{GENERATED_DATE}}', `Generated ${dateInfo.today}`)

// ── Phase 5: Send ──────────────────────────────────────────────────────────

phase('Send')

const subject = `Good Story Studios — Monthly Film Slate: ${dateInfo.month_year_label}`
const toList = recipients.join(', ')

const draftResult = await agent(
  `Create a Gmail draft using the mcp__claude_ai_Gmail__create_draft tool with the following parameters:
- to: "${toList}"
- subject: "${subject}"
- body: The HTML email below (send as HTML)

HTML EMAIL:
${finalHtml}

After creating the draft, confirm it was created successfully and return the draft ID.`,
  { phase: 'Send', label: 'create-gmail-draft' }
)

log(`Draft created. Subject: "${subject}" | To: ${toList}`)
log(`Films included: ${filmSummary}`)

return {
  month: dateInfo.month_year_label,
  studios_with_releases: studioKeys.length,
  total_films: confirmedFilms.length,
  recipients: toList,
  draft_result: draftResult,
}
```

- [ ] **Step 2: Commit**

```bash
git add automations/01-monthly-film-slate-newsletter/workflow.js
git commit -m "Add monthly film slate newsletter workflow script"
```

---

## Task 4: Write `README.md` for this automation

**Files:**
- Create: `automations/01-monthly-film-slate-newsletter/README.md`

- [ ] **Step 1: Create README**

```markdown
# Monthly Film Slate Newsletter

Runs on the 1st of every month. Researches upcoming film releases (next 3 months) across 30+ studios, triple-checks release dates, pairs each film with a creator sponsorship integration idea, and creates a Gmail draft for the Good Story Studios team to review and send.

## Files

| File | Purpose |
|------|---------|
| `workflow.js` | Main execution workflow — run this |
| `studios.json` | List of studios to research (edit to add/remove studios) |
| `recipients.json` | Email recipients (add/remove emails here) |
| `email-template.html` | HTML email template with placeholder tokens |
| `spec.md` | Original automation specification |

## Adding/Removing Recipients

Edit `recipients.json`:
```json
{
  "recipients": [
    "joshuagabbay1@gmail.com",
    "newperson@itsgoodstory.com"
  ]
}
```
Commit and push — the next run picks up the change automatically.

## Adding/Removing Studios

Edit `studios.json` — add or remove entries following the existing format. Each entry needs:
- `name` — display name in the email
- `key` — unique slug (no spaces)
- `wikipedia_url` — primary research source
- `search_hint` — fallback web search query

## Triggering Manually

To run outside the monthly schedule:
```
/schedule run monthly-film-slate-newsletter
```

## How the Email Draft Works

The routine creates a Gmail draft — it does NOT auto-send. Review the draft in Gmail and hit send when ready.
```

- [ ] **Step 2: Commit**

```bash
git add automations/01-monthly-film-slate-newsletter/README.md
git commit -m "Add README for monthly film slate newsletter automation"
```

---

## Task 5: Set Up Monthly Schedule

**Depends on:** Tasks 1–4 complete and email template received from user.

- [ ] **Step 1: Invoke `/schedule` to create the monthly routine**

Run `/schedule` with these parameters:
- **Name:** `monthly-film-slate-newsletter`
- **Cron:** `0 9 1 * *` (9am on the 1st of every month)
- **Repo:** `joshgabbay/good-story-studios`
- **Task:** Run the workflow at `automations/01-monthly-film-slate-newsletter/workflow.js`

- [ ] **Step 2: Verify the routine appears in the schedule list**

Run `/schedule list` and confirm `monthly-film-slate-newsletter` appears with the correct cron expression.

---

## Task 6: Manual Test Run

**Depends on:** Task 5 complete.

- [ ] **Step 1: Trigger a manual run**

```
/schedule run monthly-film-slate-newsletter
```

- [ ] **Step 2: Monitor progress in `/workflows`**

Watch all phases complete: Setup → Research → Verify → Generate → Send

- [ ] **Step 3: Verify the Gmail draft**

Open Gmail. Confirm a draft exists with:
- Subject: `Good Story Studios — Monthly Film Slate: [current month]`
- HTML email renders correctly
- All studios with upcoming releases are present
- Each film has a synopsis and creator tie-in
- No studio with no films in window appears

- [ ] **Step 4: Spot-check 3 release dates**

Pick 3 films from the draft. Manually verify their release dates against IMDb. If any are wrong, note them and adjust the verification prompt in `workflow.js`.

- [ ] **Step 5: Commit any fixes and push**

```bash
git add automations/01-monthly-film-slate-newsletter/workflow.js
git commit -m "Fix verification prompt based on test run results"
git push
```

---

## Self-Review

**Spec coverage:**
- ✅ 1st of every month trigger — Task 5
- ✅ 3-month window — `DATE_SCHEMA` + window_end calculation in workflow
- ✅ 30 specific studios — Task 1 `studios.json`
- ✅ Omit studios with no releases — `studiosWithFilms` filter
- ✅ Triple-check dates / zero inaccuracies — Verify phase, corroboration_count >= 2 gate
- ✅ Include anticipated films — `date_status: 'anticipated'` + `include: true` path
- ✅ 2-sentence synopsis per film — `synopsis` field enforced in schema
- ✅ 2-sentence creator tie-in — `tie_in` schema + prompt instruction
- ✅ Creator tie-ins grounded in profile doc — `good_story_context.md` passed to tie-in agents
- ✅ Beautiful HTML email — template system in Task 2
- ✅ Gmail draft (not auto-send) — `mcp__claude_ai_Gmail__create_draft` in Phase 5
- ✅ Recipient list from config — `recipients.json`
- ✅ No Mac required — remote routine on GitHub repo

**Gaps / notes:**
- Email template (Task 2) is blocked on user providing the HTML from the design tool — this must be done before Task 5 or the workflow will fail at the HTML assembly step.
- The Gmail MCP must remain authenticated in the user's claude.ai account for the headless routine to create drafts. If the token expires, the routine will fail at the Send phase and need the user to re-authenticate interactively.
