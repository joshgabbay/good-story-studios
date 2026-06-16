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

## As-built (production routine)

The original ask above is implemented and extended by the live cloud routine. See
`routine.md` (deployment + behavior) and `routine-prompt.txt` (verbatim prompt) for the
source of truth. Differences from the original ask:

- **Window is 3 months**, not 6 (the original first line said 6; the body and the build use 3).
- **24 studios** (see `studios.json`) — low-yield studios were trimmed from the original list.
- **Actor Tie-Ins** were added on top of the per-film creator tie-in: 2–4 grounded actors,
  each with a short idea for appearing in that creator's video.
- **Accuracy/verification layer**: every date, distributor, premise, character, and actor is
  grounded in that-run web results only. Films are dropped if unverifiable or out of window;
  a film is filed under its **verified distributor** (not the page it was found on); an actor's
  role label appears **only when grounded**.
- **Delivery**: emails the full `recipients.json` list (via Supabase) and creates a Gmail draft.
