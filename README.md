# Good Story Studios

**Founder:** Zack Honarvar  
**Website:** https://www.itsgoodstory.com  
**Holding company:** The Good Internet  
**Location:** Los Angeles, CA (Venice area)  
**Founded:** 2017 as One Day Entertainment → rebranded July 2025

## What They Do
Specialized brand-partnership studio — proactively sources and packages YouTube brand deals. Treats creator channels as TV networks and recurring formats as series. Does NOT take % of AdSense, merch, or speaking (handled by sister companies).

## The Good Internet Ecosystem
| Company | Focus |
|---------|-------|
| Good Story Studios | Brand partnerships & content development |
| Fan of a Fan | Merch (fulfillment sold to Selery May 2025; brand/design retained) |
| Boring Stuff | Finance, accounting, HR, tax for creators |
| Building Thingz | Startup incubator for creator-founded businesses |
| Good Creator Speakers | Booking creators for paid speaking/keynotes |

## Creator Roster (~10 clients)
- Airrack (16.3M subs) — stunts, challenges, Guinness records
- Yes Theory (9.5M subs) — adventure, travel, Seek Discomfort apparel
- Drew Binsky (5.5M subs) — visited all 197 countries
- Theorist Media / MatPat (~44M combined) — Game/Film/Food/Style Theory
- Marko Terzo (8M subs) — sneaker customization, fashion
- The Cheeky Boyos (10M+ TikTok) — comedy, pranks
- Jesse Michels — UAP/frontier science (American Alchemy)
- Alberta Tech — AI/tech comedy commentary
- Joon Lee — sports journalism (Morning Announcements)
- Grant Rudow (~129K) — business/finance explainers

## Automation Projects
See `good_story_context.md` section 9 for full ranked priority list.

- [ ] Priority 1: Brand Deal Pipeline System (HubSpot + email parsing)
- [ ] Priority 2: Pitch Deck / Media Kit Generator
- [ ] Priority 3: Inbound Email Triage
- [ ] Priority 4: Creator Performance Intelligence Digest
- [ ] Priority 5: Contract & Deliverable Tracking

## Repo Structure
- `good_story_context.md` — Full business intelligence brief, including deep-dive creator profiles (June 2026)
- `AUTOMATIONS.md` / `automations_spec.md` — Automation priorities and raw notes
- `automations/` — One folder per built automation (spec, code, config, scheduled routine)
  - `01-monthly-film-slate-newsletter/` — Monthly studio film-slate email: each upcoming film with its release date, studio, a 2-sentence synopsis, and the studio's PR/marketing point of contact (from `studio-contacts.json`). **Live** as a scheduled cloud routine (1st of each month); see that folder's `routine.md` for the production definition.

## Files
- `good_story_context.md` — Full business intelligence brief (June 2026)
