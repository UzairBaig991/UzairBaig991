#!/usr/bin/env python3
"""Generate self-hosted, animated contribution graphics for the profile README.

Writes assets/streak.svg, assets/contributions.svg and assets/weekday.svg.
Real data comes from the GitHub GraphQL API (needs GH_TOKEN). Use --demo to
render with synthetic data (for previews) or --pending for the empty state.
"""
import datetime as dt, json, os, random, sys, urllib.request

USER = os.environ.get("USERNAME", "UzairBaig991")
OUT = os.environ.get("OUT_DIR", "assets")
FONT = "'Segoe UI', Roboto, Arial, sans-serif"
MONO = "Consolas, 'Courier New', monospace"
BG = "#08090f"


def gql(query, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.load(r)
    if "errors" in res:
        raise RuntimeError(res["errors"])
    return res["data"]


def fetch_days(token):
    created = gql('query{user(login:"%s"){createdAt}}' % USER, token)["user"]["createdAt"]
    start_year = int(created[:4])
    today = dt.date.today()
    days = {}
    for year in range(start_year, today.year + 1):
        frm = f"{year}-01-01T00:00:00Z"
        to = f"{year}-12-31T23:59:59Z"
        q = ('query{user(login:"%s"){contributionsCollection(from:"%s",to:"%s")'
             '{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}') % (USER, frm, to)
        cal = gql(q, token)["user"]["contributionsCollection"]["contributionCalendar"]
        for w in cal["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return sorted((dt.date.fromisoformat(k), v) for k, v in days.items() if dt.date.fromisoformat(k) <= today)


def demo_days():
    random.seed(7)
    today = dt.date.today()
    out = []
    for i in range(800, -1, -1):
        d = today - dt.timedelta(days=i)
        busy = 0.75 if i < 260 else 0.3
        out.append((d, random.choice([0, 1, 2, 3, 5, 8]) if random.random() < busy else 0))
    return out


def streaks(days):
    today = dt.date.today()
    cur, i = 0, len(days) - 1
    if i >= 0 and days[i][0] == today and days[i][1] == 0:
        i -= 1
    cur_end = days[i][0] if i >= 0 else today
    while i >= 0 and days[i][1] > 0:
        cur += 1
        i -= 1
    cur_start = cur_end - dt.timedelta(days=cur - 1) if cur else None
    best, run, run_start, best_range = 0, 0, None, None
    for d, c in days:
        if c > 0:
            if run == 0:
                run_start = d
            run += 1
            if run > best:
                best, best_range = run, (run_start, d)
        else:
            run = 0
    return cur, (cur_start, cur_end if cur else None), best, best_range


def fmt(d):
    return d.strftime("%b %-d, %Y") if d else ""


def defs():
    return f'''<defs>
<linearGradient id="gA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#36BCF7"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient>
<linearGradient id="gB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f7b731"/><stop offset="1" stop-color="#ff7b72"/></linearGradient>
<linearGradient id="gC" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#28c840"/><stop offset="1" stop-color="#36BCF7"/></linearGradient>
<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#36BCF7"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient>
<linearGradient id="peak" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7b731"/><stop offset="1" stop-color="#ff7b72"/></linearGradient>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#fff" stroke-opacity=".04"/></pattern>
<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>'''


def frame(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{defs()}'
            f'<rect width="{w}" height="{h}" rx="18" fill="{BG}"/><rect width="{w}" height="{h}" rx="18" fill="url(#grid)"/>'
            f'{body}<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="18" fill="none" stroke="#36BCF7" stroke-opacity=".3" stroke-width="2"/></svg>')


def flame(cx, cy, s=1.0):
    return (f'<g transform="translate({cx} {cy}) scale({s})">'
            '<path d="M0 -26 C4 -16 16 -10 16 5 C16 16 9 24 0 24 C-9 24 -16 16 -16 5 C-16 -3 -11 -9 -6 -13 C-5 -6 -2 -3 1 -2 C3 -10 2 -18 0 -26Z" fill="url(#gB)">'
            '<animate attributeName="opacity" values="1;.78;1" dur="1.3s" repeatCount="indefinite"/></path>'
            '<path d="M0 2 C5 7 8 11 8 15 C8 20 4 22 0 22 C-4 22 -8 20 -8 15 C-8 11 -4 7 0 2Z" fill="#fff" fill-opacity=".9"/></g>')


def streak_svg(days, pending):
    W, H = 1000, 200
    total = sum(c for _, c in days)
    cur, cur_r, best, best_r = streaks(days) if days else (0, (None, None), 0, None)
    n = lambda v: "–" if pending else f"{v:,}"
    first = days[0][0] if days else None
    left_sub = f"{fmt(first)} – Present" if first and not pending else "Syncing with GitHub…"
    cur_sub = (f"{fmt(cur_r[0])} – {fmt(cur_r[1])}" if cur else "Commit today to start one!") if not pending else "Updates daily"
    best_sub = (f"{fmt(best_r[0])} – {fmt(best_r[1])}" if best_r else "") if not pending else ""
    b = ""
    cx = [180, 500, 820]
    for x in (340, 660):
        b += f'<line x1="{x}" y1="36" x2="{x}" y2="164" stroke="#fff" stroke-opacity=".12" stroke-dasharray="3 5"/>'
    b += (f'<text x="{cx[0]}" y="96" text-anchor="middle" font-family="{FONT}" font-size="54" font-weight="800" fill="url(#gA)">{n(total)}</text>'
          f'<text x="{cx[0]}" y="128" text-anchor="middle" font-family="{FONT}" font-size="17" font-weight="600" fill="#e6edf3">Total Contributions</text>'
          f'<text x="{cx[0]}" y="152" text-anchor="middle" font-family="{MONO}" font-size="12" fill="#8b949e">{left_sub}</text>')
    r = 56; C = 2 * 3.14159265 * r
    frac = min(1.0, cur / 30) if cur else 0.0
    b += (f'<circle cx="{cx[1]}" cy="86" r="{r}" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="9"/>'
          f'<g transform="rotate(-90 {cx[1]} 86)"><circle cx="{cx[1]}" cy="86" r="{r}" fill="none" stroke="url(#gB)" stroke-width="9" stroke-linecap="round" '
          f'stroke-dasharray="{C*frac:.1f} {C:.1f}"><animate attributeName="stroke-dasharray" from="0 {C:.1f}" to="{C*frac:.1f} {C:.1f}" dur="1.6s" fill="freeze"/></circle></g>')
    b += flame(cx[1], 54, 0.5)
    b += (f'<text x="{cx[1]}" y="100" text-anchor="middle" font-family="{FONT}" font-size="40" font-weight="800" fill="url(#gB)">{n(cur)}</text>'
          f'<text x="{cx[1]}" y="128" text-anchor="middle" font-family="{FONT}" font-size="14" font-weight="700" fill="#f7b731">Current Streak</text>'
          f'<text x="{cx[1]}" y="176" text-anchor="middle" font-family="{MONO}" font-size="12" fill="#8b949e">{cur_sub}</text>')
    b += (f'<text x="{cx[2]}" y="96" text-anchor="middle" font-family="{FONT}" font-size="54" font-weight="800" fill="url(#gC)">{n(best)}</text>'
          f'<text x="{cx[2]}" y="128" text-anchor="middle" font-family="{FONT}" font-size="17" font-weight="600" fill="#e6edf3">Longest Streak</text>'
          f'<text x="{cx[2]}" y="152" text-anchor="middle" font-family="{MONO}" font-size="12" fill="#8b949e">{best_sub}</text>')
    return frame(W, H, b)


LEVELS = ["#161b22", "#164863", "#1f7aa8", "#36BCF7", "#a78bfa"]


def heatmap_svg(days, pending):
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0) - dt.timedelta(weeks=52)  # a Sunday
    data = {d: c for d, c in days}
    nz = sorted(c for c in data.values() if c > 0)
    q = (lambda p: nz[min(len(nz) - 1, int(len(nz) * p))]) if nz else (lambda p: 1)
    t1, t2, t3 = q(.4), q(.7), q(.9)
    lvl = lambda c: 0 if c == 0 else 1 if c <= t1 else 2 if c <= t2 else 3 if c <= t3 else 4
    cell, gap, x0, y0 = 14, 3, 52, 98
    W, H = 1000, 270
    year_total = sum(c for d, c in data.items() if d >= today - dt.timedelta(days=365))
    sub = "Syncing contribution data…" if pending else f"{year_total:,} contributions in the last year"
    b = (f'<text x="40" y="44" font-family="{FONT}" font-size="22" font-weight="700" fill="#e6edf3">Contribution Heatmap</text>'
         f'<text x="40" y="64" font-family="{FONT}" font-size="13" fill="#8b949e">{sub}</text>')
    for i, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        b += f'<text x="{x0-8}" y="{y0+i*(cell+gap)+11}" text-anchor="end" font-family="{MONO}" font-size="10" fill="#6e7681">{name}</text>'
    last_m = None
    for w in range(53):
        col = ""
        for d in range(7):
            day = start + dt.timedelta(weeks=w, days=d)
            if day > today:
                continue
            c = data.get(day, 0)
            tip = f'<title>{c} contributions on {fmt(day)}</title>'
            col += (f'<rect x="{x0+w*(cell+gap)}" y="{y0+d*(cell+gap)}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[lvl(c)]}">{tip}</rect>')
        wd = start + dt.timedelta(weeks=w)
        if wd.month != last_m and w < 51:
            b += f'<text x="{x0+w*(cell+gap)}" y="{y0-8}" font-family="{MONO}" font-size="10" fill="#8b949e">{wd.strftime("%b")}</text>'
            last_m = wd.month
        b += f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{w*0.03:.2f}s" dur=".5s" fill="freeze"/>{col}</g>'
    lx = W - 40 - 5 * 18 - 70
    b += f'<text x="{lx-8}" y="{H-18}" text-anchor="end" font-family="{MONO}" font-size="11" fill="#8b949e">Less</text>'
    for i, col in enumerate(LEVELS):
        b += f'<rect x="{lx+i*18}" y="{H-29}" width="14" height="14" rx="3" fill="{col}"/>'
    b += f'<text x="{lx+5*18+4}" y="{H-18}" font-family="{MONO}" font-size="11" fill="#8b949e">More</text>'
    return frame(W, H, b)


def weekday_svg(days, pending):
    today = dt.date.today()
    tot = [0] * 7
    for d, c in days:
        if d >= today - dt.timedelta(days=365):
            tot[(d.weekday() + 1) % 7] += c  # Sunday first
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    W, H = 1000, 260
    mx = max(tot) or 1
    best = tot.index(max(tot)) if any(tot) else None
    sub = "Syncing…" if pending else (f"Most active day: {['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][best]}" if best is not None else "")
    b = (f'<text x="40" y="44" font-family="{FONT}" font-size="22" font-weight="700" fill="#e6edf3">Activity by Weekday</text>'
         f'<text x="40" y="64" font-family="{FONT}" font-size="13" fill="#8b949e">Contributions over the last 12 months</text>'
         f'<text x="960" y="44" text-anchor="end" font-family="{FONT}" font-size="14" fill="#f7b731">{sub}</text>')
    base, top, x0, step = 214, 100, 70, 120
    for i, v in enumerate(tot):
        h = (base - top) * v / mx
        x = x0 + i * step
        fill = "url(#peak)" if i == best else "url(#bar)"
        b += (f'<rect x="{x}" y="{base-h:.1f}" width="80" height="{max(h,2):.1f}" rx="8" fill="{fill}"><animate attributeName="height" from="0" to="{max(h,2):.1f}" dur="1s" fill="freeze"/>'
              f'<animate attributeName="y" from="{base}" to="{base-h:.1f}" dur="1s" fill="freeze"/></rect>'
              f'<text x="{x+40}" y="{base-h-8:.1f}" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="700" fill="#e6edf3">{"–" if pending else v}</text>'
              f'<text x="{x+40}" y="{base+22}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="#8b949e">{names[i]}</text>')
    return frame(W, H, b)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--demo":
        days, pending = demo_days(), False
    elif mode == "--pending":
        days, pending = [], True
    else:
        token = os.environ["GH_TOKEN"]
        days, pending = fetch_days(token), False
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("streak", streak_svg), ("contributions", heatmap_svg), ("weekday", weekday_svg)):
        with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
            f.write(fn(days, pending))
    print("wrote", OUT, "mode=", mode or "live", "days=", len(days))


if __name__ == "__main__":
    main()
