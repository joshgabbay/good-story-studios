# Good Story Studios — Automation Priorities

Three automations to build, in order of priority.

---

## Automation 1: Email → HubSpot → Slack + Google Sheets Pipeline

**What it does:**
Every inbound brand email is scraped for deal-relevant data and auto-synced across systems.

**Flow:**
```
Inbound email → parse brand name + deal info
             → create/update HubSpot deal or contact
             → push relevant changes to Google Sheets
             → send Slack notification to team on major actions (deal closed, new deal, etc.)
```

**Key rules:**
- Extract brand name from email content — not just sender. If email is from an agency but about OpenAI, it's tagged as OpenAI. Original sender still stored for reference.
- Every inbound email is scraped. Applicable data auto-imports into HubSpot.
- Major events (deal closed, stage change, new brand) trigger a Slack message to the team.
- HubSpot is the source of truth — all other systems pull from it.
- Connects with Boring Stuff for invoice generation.

---

## Automation 2: YouTube Sponsorship Intelligence (Monthly Email from Joshua Cohen)

**What it does:**
Joshua Cohen sends a monthly email with a Google Sheet of 25,000+ sponsored YouTube videos. This automation processes the full sheet and surfaces actionable brand intelligence.

**Flow:**
```
Joshua Cohen email arrives with Google Sheet attachment
→ Parse all long-form video entries
→ Count sponsor appearances (multi-sponsor videos count each brand individually)
→ Rank brands by sponsorship volume for the month
→ Compare to prior month: which brands are spending more / same / less
→ Cross-reference against Good Story's HubSpot: flag brands they've had contact with
→ Prioritize brands with existing relationships for follow-up
→ Generate report → Good Story manually reviews → approved report sent to recipient
```

**Key rules:**
- Focus on long-form content only.
- Count multi-sponsor videos per brand individually.
- Always compare month-over-month trends.
- Cross-reference with HubSpot contact history and flag prior relationships.
- Report requires manual approval before it goes out (Good Story reviews first).
- Delivered via Slack on a timed interval.

---

## Automation 3: Inbound Email Triage & Lead Scoring

**What it does:**
Filters the flood of inbound emails so the team is only notified about high-quality, legitimate brand leads. Scammy/spammy/irrelevant emails are silently deprioritized.

**Scoring signals to check:**
- Does the company have an Influencer Marketing Manager on LinkedIn?
- Company size and employee count (LinkedIn)
- Funding status and financial health
- Current/previous creator sponsorship activity
- Are they actively hiring for influencer/creator marketing roles? (signals growing budget)
- Relevance to Good Story's creator roster

**Flow:**
```
Inbound email arrives
→ Research sender company across LinkedIn, funding DBs, ad tracking
→ Score lead quality
→ High-quality leads: notify team with a brief on the company
→ Low-quality / spam: archive or auto-decline, no notification
```

**Key rules:**
- Only surface the "super important" ones.
- Include context: funding, team size, influencer marketing headcount, past creator sponsorships.
- Track if they've been hiring for influencer roles — signals active/growing budget.

---

## Bonus: Competitor Sponsorship Monitoring

When a competitor creator channel publishes a video with a **brand new sponsor** (one not previously seen), trigger a Slack notification.

---

## Files
- `automations_spec.md` — raw notes from Good Story
- `good_story_context.md` — full business intelligence brief
