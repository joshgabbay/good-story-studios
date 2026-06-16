// ─────────────────────────────────────────────────────────────────────────────
// ⚠️  REFERENCE PROTOTYPE — NOT what runs in production.
//
// Production is a scheduled claude.ai cloud routine (CCR). The authoritative
// definition lives in `routine.md` + `routine-prompt.txt` in this folder.
// When this file and the routine disagree, the routine wins.
//
// Ways this prototype is behind the live routine:
//   • No "Actor Tie-Ins" block (live routine adds 2–4 grounded actors per film).
//   • No distributor verification (live routine refiles a film under its verified
//     current distributor — e.g. a shelved WB title now released by Ketchup Ent.).
//   • No role-grounding rule (live routine omits an actor's role unless grounded).
//   • Delivery differs: this drafts via Gmail only; the routine emails the full
//     recipients list via Supabase (email_queue + send-film-slate-email) AND drafts.
// To make this runnable-and-current again, port Steps 4–5 of routine-prompt.txt.
// ─────────────────────────────────────────────────────────────────────────────

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
    window_end: { type: 'string', description: 'YYYY-MM-DD, exactly 3 calendar months from today' },
    month_year_label: { type: 'string', description: 'e.g. "July 2026"' },
    display_date: { type: 'string', description: 'e.g. "Generated July 1, 2026"' },
  },
  required: ['today', 'window_end', 'month_year_label', 'display_date'],
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
          initial_synopsis: { type: 'string' },
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
    release_date: { type: 'string', description: 'Human-readable, e.g. "Jul 11, 2026"' },
    date_status: { type: 'string', enum: ['confirmed', 'anticipated'] },
    synopsis: { type: 'string', description: 'Exactly 2 short sentences about the film premise' },
    corroboration_count: { type: 'number' },
    include: { type: 'boolean' },
  },
  required: ['title', 'studio_name', 'studio_key', 'release_date', 'date_status', 'synopsis', 'corroboration_count', 'include'],
}

const CREATOR_TIEIN_SCHEMA = {
  type: 'object',
  properties: {
    film_title: { type: 'string' },
    studio_key: { type: 'string' },
    creator_name: { type: 'string' },
    tie_in: { type: 'string', description: 'Exactly 2 short sentences: one naming the creator and one describing the specific sponsored segment idea' },
  },
  required: ['film_title', 'studio_key', 'creator_name', 'tie_in'],
}

// ── Phase 1: Setup ─────────────────────────────────────────────────────────

phase('Setup')

const dateInfo = await agent(
  'Run the bash command: date "+%Y-%m-%d" and return the result. Then compute: window_end = exactly 3 calendar months later (e.g. 2026-07-01 → 2026-10-01). month_year_label = current month and year (e.g. "July 2026"). display_date = "Generated " + formatted date (e.g. "Generated July 1, 2026"). Return as structured JSON.',
  { phase: 'Setup', label: 'get-date', schema: DATE_SCHEMA }
)

const studiosRaw = await agent(
  'Read the file at path: automations/01-monthly-film-slate-newsletter/studios.json using the Read tool. Return the full file contents as a string.',
  { phase: 'Setup', label: 'read-studios' }
)

const recipientsRaw = await agent(
  'Read the file at path: automations/01-monthly-film-slate-newsletter/recipients.json using the Read tool. Return the full file contents as a string.',
  { phase: 'Setup', label: 'read-recipients' }
)

const creatorProfiles = await agent(
  'Read the file at path: good_story_context.md using the Read tool. Return the full file contents. This is the creator deep-dive profile doc for Good Story Studios.',
  { phase: 'Setup', label: 'read-creator-profiles' }
)

const emailTemplate = await agent(
  'Read the file at path: automations/01-monthly-film-slate-newsletter/email-template.html using the Read tool. Return the full HTML as a string.',
  { phase: 'Setup', label: 'read-template' }
)

const studios = JSON.parse(studiosRaw).studios
const recipients = JSON.parse(recipientsRaw).recipients

// ── Phase 2: Research ──────────────────────────────────────────────────────

phase('Research')

log(`Researching film slates for ${studios.length} studios. Window: ${dateInfo.today} → ${dateInfo.window_end}`)

const studioResearch = await parallel(studios.map(studio => () =>
  agent(
    `Research upcoming film releases from "${studio.name}" releasing between ${dateInfo.today} and ${dateInfo.window_end} (next 3 months).

Check these sources:
1. ${studio.wikipedia_url}
2. Web search: "${studio.search_hint}"
3. Deadline, Variety, Hollywood Reporter, IMDb

For each film found in the window: record title, release date (YYYY-MM-DD if confirmed, or "anticipated YYYY-MM" if not exact), date_status (confirmed/anticipated/unconfirmed), and any description.

If no films release in this window, return an empty releases array. Do NOT include films outside the ${dateInfo.today}–${dateInfo.window_end} window.

studio_key: ${studio.key}`,
    { phase: 'Research', label: `research:${studio.key}`, schema: STUDIO_RELEASES_SCHEMA }
  )
))

const studiosWithFilms = studioResearch
  .filter(Boolean)
  .filter(r => r.releases && r.releases.length > 0)

log(`Studios with releases in window: ${studiosWithFilms.length}. Verifying dates.`)

// ── Phase 3: Verify ────────────────────────────────────────────────────────

phase('Verify')

const allFilms = studiosWithFilms.flatMap(s =>
  s.releases.map(film => ({
    ...film,
    studio_key: s.studio_key,
    studio_name: studios.find(st => st.key === s.studio_key).name,
  }))
)

log(`Triple-checking ${allFilms.length} films across independent sources.`)

const verifiedFilms = await parallel(allFilms.map(film => () =>
  agent(
    `Triple-check the release date for "${film.title}" (${film.studio_name}).

Claimed date: ${film.release_date} (${film.date_status})
Required window: ${dateInfo.today} to ${dateInfo.window_end}

1. Search for this film on Wikipedia, IMDb, Deadline, Variety, studio site, and Fandango
2. Count independent sources that corroborate the date (corroboration_count)
3. If sources conflict, use the most commonly cited date
4. Write exactly 2 short sentences for synopsis — actual plot/premise, not marketing copy
5. Set include=true only if: release date is within the window AND corroboration_count >= 2
6. Format release_date as human-readable: e.g. "Jul 11, 2026" (not YYYY-MM-DD)
7. If anticipated but clearly within window with 1+ source, set date_status="anticipated" and include=true

studio_key: ${film.studio_key}, studio_name: ${film.studio_name}`,
    { phase: 'Verify', label: `verify:${film.studio_key}:${film.title.slice(0, 22)}`, schema: VERIFIED_FILM_SCHEMA }
  )
))

const confirmedFilms = verifiedFilms.filter(Boolean).filter(f => f.include)
log(`${confirmedFilms.length} films passed verification.`)

// ── Phase 4: Generate ──────────────────────────────────────────────────────

phase('Generate')

// Generate creator tie-ins for each film in parallel
const tieIns = await parallel(confirmedFilms.map(film => () =>
  agent(
    `You are a senior talent manager at Good Story Studios. For the film below, pick ONE creator from Good Story's roster whose content is the best organic fit, then write a specific 2-sentence sponsored-segment pitch.

FILM: "${film.title}" (${film.studio_name}, ${film.release_date})
SYNOPSIS: ${film.synopsis}

GOOD STORY CREATOR PROFILES:
${creatorProfiles}

Rules:
- Pick the creator whose existing video format most naturally connects to this film's premise, genre, or themes
- The integration must feel organic — not a generic "sponsored by" read
- Sentence 1: name the creator and the thematic angle
- Sentence 2: describe the specific segment format or hook (reference their actual series/format if relevant)
- Be specific: use the creator's real channel name, format name, past video type

Return: film_title, studio_key (${film.studio_key}), creator_name, tie_in (2 sentences).`,
    { phase: 'Generate', label: `tiein:${film.studio_key}:${film.title.slice(0, 20)}`, schema: CREATOR_TIEIN_SCHEMA }
  )
))

// Build tie-in lookup map
const tieInMap = {}
for (const t of tieIns.filter(Boolean)) {
  tieInMap[t.film_title] = t
}

// Group confirmed films by studio, sorted by release date
const filmsByStudio = {}
for (const film of confirmedFilms) {
  if (!filmsByStudio[film.studio_key]) {
    filmsByStudio[film.studio_key] = { studio_name: film.studio_name, films: [] }
  }
  filmsByStudio[film.studio_key].films.push(film)
}

// ── Assemble HTML using the design template structure ──────────────────────

let studioBlocksHtml = ''

for (const key of Object.keys(filmsByStudio)) {
  const { studio_name, films } = filmsByStudio[key]
  const sortedFilms = films.sort((a, b) => a.release_date.localeCompare(b.release_date))

  let filmEntriesHtml = ''
  for (const film of sortedFilms) {
    const tiein = tieInMap[film.title]
    const tieinText = tiein
      ? `<strong>${tiein.creator_name}:</strong> ${tiein.tie_in}`
      : 'No creator tie-in identified for this film.'

    const dateLabel = film.date_status === 'anticipated'
      ? `${film.release_date} <em style="font-size:11px;opacity:0.8;">(anticipated)</em>`
      : film.release_date

    filmEntriesHtml += `
              <!-- Film: ${film.title} -->
              <table class="film-entry" role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:20px;">
                <tbody><tr>
                  <td style="background-color:#FAFBFF;border-radius:16px;padding:20px 24px;border:1.5px solid #EDF2FB;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:10px;">
                      <tbody><tr>
                        <td style="vertical-align:middle;">
                          <span style="font-family:'Nunito',Arial,sans-serif;font-size:16px;font-weight:800;color:#2D2D2D;line-height:1.3;">${film.title}</span>
                        </td>
                        <td style="text-align:right;vertical-align:middle;white-space:nowrap;padding-left:12px;">
                          <span style="font-family:'Nunito',Arial,sans-serif;font-size:12px;font-weight:700;color:#6B90D9;background-color:#EDF2FB;border-radius:20px;padding:3px 10px;display:inline-block;">${dateLabel}</span>
                        </td>
                      </tr></tbody>
                    </table>
                    <p style="margin:0 0 14px 0;font-family:'Nunito',Arial,sans-serif;font-size:14px;font-weight:400;color:#7A7E8B;line-height:1.65;">
                      ${film.synopsis}
                    </p>
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                      <tbody><tr>
                        <td style="background-color:#EDF2FB;border-radius:12px;padding:14px 18px;">
                          <p style="margin:0 0 5px 0;font-family:'Nunito',Arial,sans-serif;font-size:12px;font-weight:900;color:#6B90D9;text-transform:uppercase;letter-spacing:0.8px;">
                            Creator Opportunity ✦
                          </p>
                          <p style="margin:0;font-family:'Nunito',Arial,sans-serif;font-size:13px;font-weight:600;color:#5A78BB;line-height:1.6;">
                            ${tieinText}
                          </p>
                        </td>
                      </tr></tbody>
                    </table>
                  </td>
                </tr></tbody>
              </table>`
  }

  studioBlocksHtml += `
            <!-- ─── STUDIO: ${studio_name} ─── -->
            <table class="studio-block" role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:36px;">
              <tbody><tr>
                <td>
                  <h2 style="margin:0 0 20px 0;font-family:'Nunito',Arial,sans-serif;font-size:20px;font-weight:900;color:#6B90D9;letter-spacing:-0.2px;border-left:5px solid #F2C53D;padding-left:14px;line-height:1.2;">
                    ${studio_name}
                  </h2>
                  ${filmEntriesHtml}
                </td>
              </tr></tbody>
            </table>`
}

// Inject into template
const finalHtml = emailTemplate
  .replace('{{MONTH_YEAR}}', dateInfo.month_year_label)
  .replace('{{STUDIO_BLOCKS}}', studioBlocksHtml)
  .replace('{{GENERATED_DATE}}', dateInfo.display_date)

// ── Phase 5: Send ──────────────────────────────────────────────────────────

phase('Send')

const subject = `Good Story Studios — Monthly Film Slate: ${dateInfo.month_year_label}`
const toList = recipients.join(', ')

const draftResult = await agent(
  `Create a Gmail draft using the mcp__claude_ai_Gmail__create_draft tool.

Parameters:
- to: "${toList}"
- subject: "${subject}"
- body (HTML): the full HTML email below

HTML EMAIL (send this as the body):
${finalHtml}

Confirm the draft was created and return any draft ID or confirmation.`,
  { phase: 'Send', label: 'create-gmail-draft' }
)

const filmList = confirmedFilms.map(f => `${f.title} (${f.studio_name})`).join(', ')
log(`Draft created. ${confirmedFilms.length} films across ${Object.keys(filmsByStudio).length} studios.`)

return {
  month: dateInfo.month_year_label,
  studios_with_releases: Object.keys(filmsByStudio).length,
  total_films: confirmedFilms.length,
  films: filmList,
  recipients: toList,
  draft_result: draftResult,
}
