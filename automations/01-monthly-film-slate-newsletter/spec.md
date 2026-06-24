# Automation #1   
  
  
- I want to be able to enter someone’s email, and on the first day of every month they get an email in their inbox about each major Hollywood studio’s upcoming film slate for the next 6 months. Pull data for the following studios ONLY:   
* Disney  
* Marvel Studios  
* Lucasfilm  
* 20th Century Studios  
* Pixar Animation Studios  
* Walt Disney Animation Studios  
* Warner Bros. Pictures  
* New Line Cinema  
* DC Studios  
* HBO  
* Universal Pictures  
* DreamWorks Animation  
* Focus Features  
* Illumination  
* Paramount Pictures  
* CBS Studios  
* Showtime  
* Sony Pictures Entertainment  
* Columbia Pictures  
* TriStar Pictures  
* Sony Pictures Television  
* Netflix Studios  
* Amazon MGM Studios  
* MGM  
* Apple TV+  
* Lionsgate  
* A24  
* Miramax  
* Skydance Media  
* Legendary Entertainment  
* Blumhouse Productions  
    - Basically on the first of every month, scour the internet for any information possible on each studios film slate for the next 3 months, simplify the information, to the point where all you need to know is what movies are coming from what studios, and the date they are coming out. If a studio doesn’t have a movie in the next 3 months, omit the studio completely from the list. Do not miss any films, it is very important that you find every single one. However, you must also triple check as there can be 0 release date inaccuracies. Even if there is not an exact confirmed release date yet, if you anticipate it is within the 3 month window, then include it. Next to the name of each film, give a two sentence synopsis of what the film will be about. Only two sentences, and they should be relatively short. Here’s the key part: this email list is for people who work at Good Story Studios, who manages YouTube creators. Here is a list of creators they manage, and it is only these creators:   
* Airrack  
*   
* Yes theory  
*   
* Drew Binsky  
*   
* Alberta tech  
*   
* Theorist Media (game theorist, film theorist, food theorist)  
*   
* Marko Terzo  
*   
* Joon Lee  
*   
* Jesse michels   
*   
* Grant Rudow   
        - After the two sentence synopsis of the film, write two more sentences, about how the film could connect to one or two of the YouTubers and come up with a creative way that the film could be integrated into a YouTube video for that specific YouTuber as a sponsored segment, but also in a way that fits well with the YouTuber’s brand and the type of content they make. Refer to the md file for the complete profile on each YouTuber to create as specific a video content creation connecter as possible. This is the key and valuable part of this process.   

---

## Refocus — 2026-06-24 (current direction)

Per leadership feedback, the automation was **refocused away from creative recommendations**.
The AI no longer suggests how a film could be integrated, which roster creator fits, or any brand
concept — that work belongs to the Good Story team and the automation must not step on it.

The newsletter is now strictly: **film → release date → studio → studio point of contact.**

- The per-film **Creator Opportunity** and **Actor Tie-In** blocks were **removed**.
- The 2-sentence synopsis stays (factual context only).
- Each studio block now shows the studio's **PR/marketing point of contact** (name, title, email),
  looked up from a new **`studio-contacts.json`** database — researched once, up front, and reused
  every run (not researched live). The essential, money-making piece is knowing *who to contact*
  at each studio about a marketing deal to feature a film in a YouTube video.
- Contacts are **partnerships-first** (brand/promotional/strategic partnerships leads), with a
  publicity/PR contact as a fallback. Research-derived contacts are `speculative` + `unverified`;
  Zack's CRM contacts get added as `confirmed` and automatically take priority. See
  `routine.md` → "Studio contacts database" for the schema and how to add confirmed contacts.

## As-built (production routine)

The original ask above is implemented and extended by the live cloud routine. See
`routine.md` (deployment + behavior) and `routine-prompt.txt` (verbatim prompt) for the
source of truth. Differences from the original ask:

- **Window is 3 months**, not 6 (the original first line said 6; the body and the build use 3).
- **24 studios** (see `studios.json`) — low-yield studios were trimmed from the original list.
- **Creator tie-ins + Actor Tie-Ins** were originally added on top of each film, but were
  **removed on 2026-06-24** (see "Refocus" above) and replaced by the per-studio contact block.
- **Accuracy/verification layer**: every date, distributor, premise, character, and actor is
  grounded in that-run web results only. Films are dropped if unverifiable or out of window;
  a film is filed under its **verified distributor** (not the page it was found on); an actor's
  role label appears **only when grounded**.
- **Delivery**: emails the full `recipients.json` list (via Supabase) and creates a Gmail draft.
