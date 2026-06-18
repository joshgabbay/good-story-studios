"""Generate a realistic large synthetic sponsored-video CSV for scale/demo testing.

Usage: python tools/gen_sample.py <month YYYY-MM> <n_rows> <out.csv> [seed]
Deterministic given a seed. NOT committed output — for local validation only.
"""
import csv
import random
import sys

# (display, list of raw-spelling variants that should all collapse to one brand)
BRANDS = [
    ("BetterHelp", ["BetterHelp", "Better Help", "betterhelp.com"]),
    ("NordVPN", ["NordVPN", "Nord VPN", "nordvpn.com"]),
    ("ExpressVPN", ["ExpressVPN", "Express VPN"]),
    ("Squarespace", ["Squarespace", "Square space"]),
    ("HelloFresh", ["HelloFresh", "Hello Fresh"]),
    ("Manscaped", ["Manscaped", "manscaped.com"]),
    ("Skillshare", ["Skillshare", "Skill Share"]),
    ("Audible", ["Audible", "audible.com"]),
    ("AG1", ["AG1", "Athletic Greens"]),
    ("Raid: Shadow Legends", ["Raid Shadow Legends"]),
    ("Ground News", ["Ground News"]),
    ("Shopify", ["Shopify", "shopify.com"]),
    ("Honey", ["Honey", "Join Honey"]),
    ("Factor", ["Factor", "Factor Meals"]),
    ("Surfshark", ["Surfshark", "surfshark.com"]),
    ("Established Titles", ["Established Titles"]),
    ("Rocket Money", ["Rocket Money"]),
    ("MagicSpoon", ["Magic Spoon"]),
    ("Aura", ["Aura"]),
    ("Incogni", ["Incogni"]),
]

def main():
    month = sys.argv[1]
    n = int(sys.argv[2])
    out = sys.argv[3]
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    rng = random.Random(seed + hash(month) % 1000)
    y, m = month.split("-")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Video Title", "Video URL", "Channel", "Sponsor", "Publish Date", "Length (s)"])
        for i in range(n):
            disp, variants = rng.choice(BRANDS)
            sponsor = rng.choice(variants)
            # ~15% of videos are multi-sponsor
            if rng.random() < 0.15:
                disp2, var2 = rng.choice(BRANDS)
                sponsor = sponsor + "; " + rng.choice(var2)
            # ~25% short-form (< 600s)
            length = rng.choice([45, 120, 300, 480]) if rng.random() < 0.25 else rng.choice([620, 800, 1200, 1800, 2400])
            day = rng.randint(1, 28)
            w.writerow([f"Video {i}", f"https://yt/{month}/{i}", f"Channel{rng.randint(1,400)}",
                        sponsor, f"{y}-{m}-{day:02d}", length])

if __name__ == "__main__":
    main()
