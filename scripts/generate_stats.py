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
COMMITS = 0
FEATURED = ["StockWise-AI", "EcoSwap-MAD-Project", "RoyalLudo", "PDFForge", "Enterprise-Flow-ERP",
            "OS-Simulator", "AutoFlow", "Movie-Recommendation-System", "UzairMart", "MediCare-"]
LANG_COLORS = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5", "Java": "#b07219",
               "C++": "#f34b7d", "C": "#888888", "HTML": "#e34c26", "CSS": "#563d7c", "PHP": "#4F5D95",
               "Kotlin": "#A97BFF", "Dart": "#00B4AB", "C#": "#178600", "Shell": "#89e051",
               "Assembly": "#6E4C13", "Jupyter Notebook": "#DA5B0B", "SCSS": "#c6538c"}


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
    global COMMITS
    COMMITS = 0
    for year in range(start_year, today.year + 1):
        frm = f"{year}-01-01T00:00:00Z"
        to = f"{year}-12-31T23:59:59Z"
        q = ('query{user(login:"%s"){contributionsCollection(from:"%s",to:"%s")'
             '{totalCommitContributions contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}') % (USER, frm, to)
        cc = gql(q, token)["user"]["contributionsCollection"]
        COMMITS += cc["totalCommitContributions"]
        cal = cc["contributionCalendar"]
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


def frame(w, h, body, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{defs().replace("</defs>", extra + "</defs>")}'
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


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def wrap(text, width, lines):
    words, out, cur = (text or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    out = out[:lines]
    if len(words) and len(" ".join(out)) < len(" ".join(words)):
        out[-1] = out[-1][: width - 1].rstrip() + "…"
    return out


def fetch_profile(token):
    q = ('query{user(login:"%s"){followers{totalCount} following{totalCount} '
         'pullRequests{totalCount} issues{totalCount} repositories(privacy:PUBLIC,ownerAffiliations:OWNER){totalCount}}}') % USER
    return gql(q, token)["user"]


def fetch_repos(token):
    repos, page = [], 1
    while True:
        chunk = rest(f"/users/{USER}/repos?per_page=100&page={page}&sort=pushed", token)
        repos += chunk
        if len(chunk) < 100:
            return repos
        page += 1


def fetch_languages(repos, token):
    tot = {}
    for r in repos:
        if r["fork"]:
            continue
        try:
            for k, v in rest(f"/repos/{USER}/{r['name']}/languages", token).items():
                tot[k] = tot.get(k, 0) + v
        except Exception:
            pass
    return tot


def stats_card_svg(info):
    W, H = 490, 220
    pending = info is None
    v = (lambda k: "–") if pending else (lambda k: f"{info[k]:,}")
    items = [("Total Stars", "stars", "gB"), ("Total Commits", "commits", "gA"), ("Pull Requests", "prs", "gC"),
             ("Issues", "issues", "gA"), ("Public Repos", "repos", "gB"), ("Followers", "followers", "gC")]
    b = (f'<text x="28" y="40" font-family="{FONT}" font-size="21" font-weight="700" fill="#e6edf3">GitHub Stats</text>'
         f'<text x="{W-28}" y="40" text-anchor="end" font-family="{MONO}" font-size="12" fill="#8b949e">@{USER}</text>')
    for i, (label, key, g) in enumerate(items):
        col, row = i % 3, i // 3
        x, y = 28 + col * 150, 70 + row * 66
        b += (f'<rect x="{x-8}" y="{y-6}" width="138" height="56" rx="12" fill="#ffffff" fill-opacity=".04" stroke="#36BCF7" stroke-opacity=".18"/>'
              f'<text x="{x+4}" y="{y+26}" font-family="{FONT}" font-size="26" font-weight="800" fill="url(#{g})">{v(key)}'
              f'<animate attributeName="opacity" from="0" to="1" dur="{0.6+i*0.15:.2f}s" fill="freeze"/></text>'
              f'<text x="{x+4}" y="{y+43}" font-family="{FONT}" font-size="12" fill="#8b949e">{label}</text>')
    return frame(W, H, b)


def langs_card_svg(langs):
    W, H = 490, 220
    b = f'<text x="28" y="40" font-family="{FONT}" font-size="21" font-weight="700" fill="#e6edf3">Top Languages</text>'
    if not langs:
        b += f'<text x="28" y="110" font-family="{FONT}" font-size="14" fill="#8b949e">Syncing language data…</text>'
        return frame(W, H, b)
    total = sum(langs.values())
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    other = total - sum(v for _, v in top)
    if other > 0:
        top.append(("Other", other))
    x, bw = 28, W - 56
    b += f'<clipPath id="lc"><rect x="28" y="56" width="{bw}" height="12" rx="6"/></clipPath><g clip-path="url(#lc)">'
    for name, val in top:
        w = bw * val / total
        col = LANG_COLORS.get(name, "#8b949e")
        b += (f'<rect x="{x:.1f}" y="56" width="{w:.1f}" height="12" fill="{col}"><animate attributeName="width" from="0" to="{w:.1f}" dur="1.1s" fill="freeze"/></rect>')
        x += w
    b += '</g>'
    for i, (name, val) in enumerate(top):
        col = LANG_COLORS.get(name, "#8b949e")
        cx, cy = 28 + (i % 2) * 220, 98 + (i // 2) * 28
        b += (f'<circle cx="{cx+5}" cy="{cy-4}" r="5" fill="{col}"/>'
              f'<text x="{cx+18}" y="{cy}" font-family="{FONT}" font-size="14" fill="#e6edf3">{esc(name)}</text>'
              f'<text x="{cx+196}" y="{cy}" text-anchor="end" font-family="{MONO}" font-size="13" fill="#8b949e">{100*val/total:.1f}%</text>')
    return frame(W, H, b)


def pin_svg(r):
    W, H = 490, 150
    pending = r is None
    name = FEATURED[0] if pending else r["name"]
    lang = None if pending else r.get("language")
    desc = "Syncing…" if pending else (r.get("description") or
        (f"A {lang} project. Open the repository to explore the code and README." if lang else "Open the repository to explore the code and README."))
    stars = 0 if pending else r["stargazers_count"]
    forks = 0 if pending else r["forks_count"]
    when = "" if pending else dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")).strftime("Updated %b %-d, %Y")
    b = (f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="18" fill="none" stroke="url(#gA)" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="120 {2*(W+H)-120}">'
         f'<animate attributeName="stroke-dashoffset" from="0" to="-{2*(W+H)}" dur="6s" repeatCount="indefinite"/></rect>'
         f'<text x="26" y="42" font-family="{FONT}" font-size="20" font-weight="700" fill="url(#gA)">{esc(name)}</text>')
    for i, line in enumerate(wrap(desc, 62, 2)):
        b += f'<text x="26" y="{70+i*20}" font-family="{FONT}" font-size="14" fill="#c9d1d9">{esc(line)}</text>'
    y = 126
    x = 26
    if lang:
        b += (f'<circle cx="{x+5}" cy="{y-4}" r="5" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>'
              f'<text x="{x+16}" y="{y}" font-family="{FONT}" font-size="13" fill="#e6edf3">{esc(lang)}</text>')
        x += 24 + len(lang) * 8
    b += (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="13" fill="#f7b731">★ {stars}</text>'
          f'<text x="{x+52}" y="{y}" font-family="{FONT}" font-size="13" fill="#8b949e">⑂ {forks}</text>'
          f'<text x="{W-26}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="12" fill="#8b949e">{esc(when)}</text>')
    return frame(W, H, b)


def write_extra(token, days=None):
    """Stats card, languages card and featured-project cards (all self-hosted)."""
    repos = fetch_repos(token)
    prof = fetch_profile(token)
    own = [r for r in repos if not r["fork"]]
    info = {"stars": sum(r["stargazers_count"] for r in own), "commits": COMMITS,
            "prs": prof["pullRequests"]["totalCount"], "issues": prof["issues"]["totalCount"],
            "repos": prof["repositories"]["totalCount"], "followers": prof["followers"]["totalCount"]}
    write_svg("projects-by-category", category_chart_svg(own_repos(repos)))
    write_svg("project-activity", activity_chart_svg(own_repos(repos)))
    write_svg("stats", stat_row_svg(len(own_repos(repos))))
    write_svg("gh-stats", stats_card_svg(info))
    langs = fetch_languages(repos, token)
    write_svg("top-langs", langs_card_svg(langs))
    try:
        cur = streaks(days)[0] if days else 0
        commits = fetch_commits(own_repos(repos), token)
        info2 = dict(info, streak=cur)
        write_svg("snake", snake_svg(days or []))
        write_svg("terminal", terminal_svg(info2, commits))
        write_svg("orbit", orbit_svg(langs))
        write_svg("coding-clock", clock_svg(commits))
        write_svg("commit-ticker", ticker_svg(commits))
    except Exception as e:  # never let the lab break the rest of the update
        print("lab graphics skipped:", repr(e))
    try:
        log = track_changes(own_repos(repos), token)
        write_svg("repo-radar", radar_svg(own_repos(repos), log))
    except Exception as e:
        print("radar skipped:", repr(e))
    by = {r["name"]: r for r in repos}
    for n in FEATURED:
        if n in by:
            write_svg("pin-" + n, pin_svg(by[n]))


# ---------------------------------------------------------------- change detection + radar
def track_changes(repos, token):
    """Diff the current repo list against the last snapshot; keep a rolling changelog."""
    import json
    snap_p, log_p = "data/snapshot.json", "data/changelog.json"
    os.makedirs("data", exist_ok=True)
    try:
        old = json.load(open(snap_p))
    except Exception:
        old = None
    try:
        log = json.load(open(log_p))
    except Exception:
        log = []
    cur = {r["name"]: {"pushed": r["pushed_at"], "stars": r["stargazers_count"], "forks": r["forks_count"],
                       "lang": r.get("language"), "url": r["html_url"]} for r in repos}
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if old is not None:
        for n, c in cur.items():
            o = old.get(n)
            if o is None:
                log.append({"t": now, "kind": "new", "repo": n, "url": c["url"], "msg": "New repository created"})
            else:
                if c["pushed"] != o.get("pushed"):
                    msg, _ = latest_commit(n, token)
                    log.append({"t": now, "kind": "push", "repo": n, "url": c["url"], "msg": msg or "New commits pushed"})
                if c["stars"] > o.get("stars", 0):
                    log.append({"t": now, "kind": "star", "repo": n, "url": c["url"], "msg": f"Starred ({c['stars']} total)"})
                if c["forks"] > o.get("forks", 0):
                    log.append({"t": now, "kind": "fork", "repo": n, "url": c["url"], "msg": f"Forked ({c['forks']} total)"})
        for n in old:
            if n not in cur:
                log.append({"t": now, "kind": "gone", "repo": n, "url": "", "msg": "Repository removed or made private"})
    log = log[-40:]
    json.dump(cur, open(snap_p, "w"), indent=1)
    json.dump(log, open(log_p, "w"), indent=1)
    return log


KIND_ICON = {"new": "🆕", "push": "🚀", "star": "⭐", "fork": "🍴", "gone": "🗑️"}


def changelog_block(log):
    if not log:
        return ("_Watching every repository. The first detected change (new repo, push, star or fork) will appear here "
                "within minutes of it happening._")
    rows = ["| | Repository | What changed | Detected (UTC) |", "|---|---|---|---|"]
    for e in reversed(log[-8:]):
        t = dt.datetime.fromisoformat(e["t"].replace("Z", "+00:00")).strftime("%b %-d, %H:%M")
        name = f"[**{md(e['repo'])}**]({e['url']})" if e["url"] else f"**{md(e['repo'])}**"
        rows.append(f"| {KIND_ICON.get(e['kind'], '•')} | {name} | {md(e['msg'][:80])} | {t} |")
    return "\n".join(rows)


def radar_svg(repos, log):
    """Animated repo radar: rings = how recently a repo changed, dot colour = category."""
    import math
    W, H, cx, cy = 1000, 460, 270, 235
    now = dt.datetime.now(dt.timezone.utc)
    rings = [(7, "this week"), (30, "this month"), (90, "3 months"), (9999, "older")]
    radii = [70, 120, 170, 210]
    b = (f'<text x="40" y="48" font-family="{FONT}" font-size="24" font-weight="700" fill="#e6edf3">Repository Radar</text>'
         f'<text x="40" y="72" font-family="{FONT}" font-size="14" fill="#8b949e">Closer to the centre = changed more recently. Pulsing dots changed this week.</text>')
    for r_, lab in zip(radii, [x[1] for x in rings]):
        b += (f'<circle cx="{cx}" cy="{cy+20}" r="{r_}" fill="none" stroke="#36BCF7" stroke-opacity=".18" stroke-dasharray="3 5"/>'
              f'<text x="{cx+4}" y="{cy+20-r_+14}" font-family="{MONO}" font-size="10" fill="#6e7681">{lab}</text>')
    b += (f'<g><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy+20}" to="360 {cx} {cy+20}" dur="8s" repeatCount="indefinite"/>'
          f'<path d="M{cx} {cy+20} L{cx+210} {cy+20} A210 210 0 0 0 {cx+210*math.cos(-.6):.1f} {cy+20+210*math.sin(-.6):.1f} Z" fill="url(#sweep)" opacity=".5"/>'
          f'<line x1="{cx}" y1="{cy+20}" x2="{cx+210}" y2="{cy+20}" stroke="#36BCF7" stroke-opacity=".8" stroke-width="2"/></g>')
    b += f'<circle cx="{cx}" cy="{cy+20}" r="6" fill="#36BCF7"/>'
    byring = [[], [], [], []]
    for r in repos:
        age = (now - dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))).days
        i = 0 if age <= 7 else 1 if age <= 30 else 2 if age <= 90 else 3
        byring[i].append((age, r))
    for i, grp in enumerate(byring):
        lo = radii[i - 1] if i else 0
        for j, (age, r) in enumerate(sorted(grp, key=lambda x: x[1]["name"])):
            ang = (j / max(len(grp), 1)) * 2 * math.pi + i * 0.7
            rad = lo + (radii[i] - lo) * (0.35 + 0.55 * ((j * 37) % 10) / 10)
            x, y = cx + rad * math.cos(ang), cy + 20 + rad * math.sin(ang)
            col = CATS[categorize(r)][1]
            pulse = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{col}"><animate attributeName="r" values="5;16;5" dur="2.4s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".9;0;.9" dur="2.4s" repeatCount="indefinite"/></circle>') if i == 0 else ""
            b += pulse + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}"/>'
    # legend + live feed
    b += f'<text x="560" y="110" font-family="{FONT}" font-size="16" font-weight="700" fill="#e6edf3">Live change feed</text>'
    y = 138
    if not log:
        b += f'<text x="560" y="{y}" font-family="{MONO}" font-size="13" fill="#8b949e">listening for changes…</text>'
    for e in reversed(log[-6:]):
        t = dt.datetime.fromisoformat(e["t"].replace("Z", "+00:00")).strftime("%b %-d %H:%M")
        b += (f'<text x="560" y="{y}" font-family="{MONO}" font-size="12" fill="#6e7681">{t}</text>'
              f'<text x="650" y="{y}" font-family="{FONT}" font-size="14" fill="#e6edf3">{esc(e["repo"][:26])}</text>'
              f'<text x="650" y="{y+16}" font-family="{MONO}" font-size="11" fill="{ {"push":"#36BCF7","new":"#28c840","star":"#f7b731","fork":"#8b5cf6","gone":"#ff7b72"}.get(e["kind"], "#8b949e") }">{esc(e["kind"].upper())} · {esc(e["msg"][:44])}</text>')
        y += 42
    SHORT = {"web": "Web", "academic": "Academic", "mobile": "Mobile", "synt": "Syntecxhub", "tools": "AI & Tools", "sites": "Sites"}
    for i, (k, (n, col, _)) in enumerate(CATS.items()):
        lx, ly = 560 + (i % 3) * 140, 372 + (i // 3) * 22
        b += f'<circle cx="{lx}" cy="{ly}" r="5" fill="{col}"/><text x="{lx+12}" y="{ly+4}" font-family="{FONT}" font-size="12" fill="#8b949e">{esc(SHORT[k])}</text>'
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%b %-d, %H:%M UTC")
    b += (f'<circle cx="560" cy="435" r="4" fill="#28c840"><animate attributeName="opacity" values="1;.2;1" dur="1.4s" repeatCount="indefinite"/></circle>'
          f'<text x="572" y="439" font-family="{MONO}" font-size="12" fill="#28c840">LIVE · last sync {stamp}</text>')
    extra = ('<radialGradient id="sweep" cx="0" cy="0" r="1"><stop offset="0" stop-color="#36BCF7" stop-opacity=".0"/><stop offset="1" stop-color="#36BCF7" stop-opacity=".35"/></radialGradient>')
    return frame(W, H, b, extra)


def write_svg(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- live project data
CATS = {
    "web": ("Web Applications", "#36BCF7", "🌐"),
    "academic": ("Academic & Systems", "#f7b731", "🎓"),
    "mobile": ("Mobile & Games", "#28c840", "📱"),
    "synt": ("Syntecxhub Projects", "#8b5cf6", "🧩"),
    "tools": ("AI, ERP & Tools", "#ff7b72", "🛠️"),
    "sites": ("Portfolio Sites", "#db61a2", "🖥️"),
}
OVERRIDES = {}
for _k, _names in {
    "mobile": "RoyalLudo EcoSwap-MAD-Project LudoVerse Mobile-App-Development Quiz-Android-App Simple-To-Do-App To-Do-App",
    "tools": "PDFForge StockWise-AI AutoFlow Enterprise-Flow-ERP Movie-Recommendation-System",
    "sites": "Portfolio Portfolio-Updated UzairBaig.github.io",
    "academic": ("Artificial-Intelligence-Lab Lexical-Analyzer OS-Simulator WebProgramming10th-Week WebProgramming8th-Week "
                 "WebProgramming6th-Week PHP-Practice Web-Programming AnalysisofAlgorithmSE ALLSOFTWAREPROJECTS1 "
                 "HCI-And-ComputerGraphics ASM-Project DSA-Final-Project-Collaboration COALLABTASKS DSALATASKS PROJECTS"),
}.items():
    for _n in _names.split():
        OVERRIDES[_n] = _k


def categorize(r):
    n = r["name"]
    if n in OVERRIDES:
        return OVERRIDES[n]
    if n.lower().startswith("syntecxhub"):
        return "synt"
    low = n.lower()
    if "portfolio" in low or low.endswith(".github.io"):
        return "sites"
    lang = r.get("language")
    if lang in ("Kotlin", "Dart") or "android" in low or "mobile" in low:
        return "mobile"
    if lang in ("JavaScript", "TypeScript", "HTML", "CSS", "PHP", "Vue", "SCSS"):
        return "web"
    if lang in ("Python", "Jupyter Notebook") and any(w in low for w in ("ai", "ml", "predict", "recommend")):
        return "tools"
    return "academic"


def own_repos(repos):
    return [r for r in repos if not r["fork"] and r["name"].lower() != USER.lower()]


def pretty(name):
    n = name
    if n.lower().startswith("syntecxhub-"):
        n = n[len("syntecxhub-"):]
    return n.strip("-_ ").replace("-", " ").replace("_", " ")


def short_date(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %-d, %Y")


def lighten(h, f=.28):
    r, g, b = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(c + (255 - c) * f) for c in (r, g, b))


def category_chart_svg(repos):
    groups = {}
    for r in repos:
        groups.setdefault(categorize(r), []).append(r)
    total = len(repos) or 1
    order = sorted(groups, key=lambda k: -len(groups[k]))
    extra = "".join(f'<linearGradient id="gc{k}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CATS[k][1]}"/><stop offset="1" stop-color="{lighten(CATS[k][1])}"/></linearGradient>' for k in order)
    b = (f'<text x="40" y="52" font-family="{FONT}" font-size="24" font-weight="700" fill="#e6edf3">Projects by Category</text>'
         f'<text x="40" y="76" font-family="{FONT}" font-size="14" fill="#8b949e">Every public repository, grouped by what it is (updates automatically)</text>')
    cx, cy, rr, sw = 230, 200, 88, 44
    C = 2 * 3.14159265 * rr
    off = 0
    b += f'<g transform="rotate(-90 {cx} {cy})"><animateTransform attributeName="transform" type="rotate" from="-90 {cx} {cy}" to="270 {cx} {cy}" dur="90s" repeatCount="indefinite"/>'
    for k in order:
        L = len(groups[k]) / total * C
        b += (f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="url(#gc{k})" stroke-width="{sw}" stroke-dasharray="{max(L-3,0.1):.2f} {C-L+3:.2f}" stroke-dashoffset="{-off:.2f}">'
              f'<animate attributeName="stroke-dasharray" from="0 {C:.2f}" to="{max(L-3,0.1):.2f} {C-L+3:.2f}" dur="1.2s" fill="freeze"/></circle>')
        off += L
    b += '</g>'
    b += (f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-family="{FONT}" font-size="44" font-weight="800" fill="url(#gA)">{len(repos)}</text>'
          f'<text x="{cx}" y="{cy+30}" text-anchor="middle" font-family="{FONT}" font-size="14" fill="#8b949e">repositories</text>')
    mx = max(len(v) for v in groups.values()) if groups else 1
    y = 118
    for k in order:
        n, col = CATS[k][0], CATS[k][1]
        cnt = len(groups[k])
        bw = int(430 * cnt / mx)
        b += (f'<circle cx="480" cy="{y}" r="7" fill="{col}"/>'
              f'<text x="500" y="{y+5}" font-family="{FONT}" font-size="17" fill="#e6edf3">{esc(n)}</text>'
              f'<text x="940" y="{y+5}" text-anchor="end" font-family="{MONO}" font-size="16" fill="{col}">{cnt} · {round(100*cnt/total)}%</text>'
              f'<rect x="500" y="{y+13}" width="440" height="6" rx="3" fill="#ffffff" fill-opacity=".07"/>'
              f'<rect x="500" y="{y+13}" width="{bw+10}" height="6" rx="3" fill="{col}"><animate attributeName="width" from="0" to="{bw+10}" dur="1.2s" fill="freeze"/></rect>')
        y += 36
    return frame(1000, 340, b, extra)


def activity_chart_svg(repos):
    import collections
    months = collections.Counter(r["pushed_at"][:7] for r in repos)
    if not months:
        return frame(1000, 330, "")
    first = min(months)
    now = dt.date.today()
    y_, m_ = int(first[:4]), int(first[5:])
    ms = []
    while (y_, m_) <= (now.year, now.month):
        ms.append(f"{y_}-{m_:02d}")
        m_ += 1
        if m_ > 12:
            y_ += 1
            m_ = 1
    x0, x1, base, top = 50, 960, 262, 110
    n = len(ms)
    step = (x1 - x0) / n
    bw = step * 0.62
    mx = max(months.values())
    pk = max(months, key=months.get)
    b = (f'<text x="40" y="52" font-family="{FONT}" font-size="24" font-weight="700" fill="#e6edf3">Project Activity</text>'
         f'<text x="40" y="76" font-family="{FONT}" font-size="14" fill="#8b949e">Repositories by month of last update, {dt.date.fromisoformat(first + "-01").strftime("%b %Y")} → {now.strftime("%b %Y")}</text>'
         f'<text x="960" y="52" text-anchor="end" font-family="{FONT}" font-size="14" fill="#f7b731">Peak: {months[pk]} repos in {pk}</text>')
    for g in range(0, mx + 1, max(1, mx // 4)):
        gy = base - (base - top) * g / mx
        b += f'<line x1="{x0}" y1="{gy:.1f}" x2="{x1}" y2="{gy:.1f}" stroke="#fff" stroke-opacity=".07"/><text x="{x0-8}" y="{gy+4:.1f}" text-anchor="end" font-family="{MONO}" font-size="11" fill="#6e7681">{g}</text>'
    MN = "JFMAMJJASOND"
    for i, mo in enumerate(ms):
        v = months.get(mo, 0)
        bx = x0 + i * step + (step - bw) / 2
        h = (base - top) * v / mx
        if v:
            peak = mo == pk
            b += (f'<rect x="{bx:.1f}" y="{base-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="4" fill="url(#{"peak" if peak else "bar"})">'
                  f'<animate attributeName="height" from="0" to="{h:.1f}" dur="1s" fill="freeze"/><animate attributeName="y" from="{base}" to="{base-h:.1f}" dur="1s" fill="freeze"/>'
                  + ('<animate attributeName="opacity" values="1;.6;1" dur="2s" repeatCount="indefinite"/>' if peak else '') + '</rect>')
            b += f'<text x="{bx+bw/2:.1f}" y="{base-h-6:.1f}" text-anchor="middle" font-family="{MONO}" font-size="12" font-weight="700" fill="#e6edf3">{v}</text>'
        else:
            b += f'<rect x="{bx:.1f}" y="{base-2}" width="{bw:.1f}" height="2" rx="1" fill="#ffffff" fill-opacity=".15"/>'
        mi = int(mo[5:])
        b += f'<text x="{bx+bw/2:.1f}" y="{base+18}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#8b949e">{MN[mi-1]}</text>'
        if mi == 1 or i == 0:
            b += f'<text x="{bx+bw/2:.1f}" y="{base+36}" text-anchor="middle" font-family="{MONO}" font-size="12" font-weight="700" fill="#36BCF7">{mo[:4]}</text>'
    return frame(1000, 330, b)


def stat_row_svg(n_repos):
    cards = [(str(n_repos), "Public Repositories", "#36BCF7", "#8b5cf6"), ("2", "Internships", "#8b5cf6", "#db61a2"),
             ("6", "Core Technologies", "#28c840", "#36BCF7"), ("1", "Cisco C++ Certificate", "#f7b731", "#ff7b72")]
    W, Hh, cw = 1000, 150, 215
    gap = (W - 80 - 4 * cw) / 3
    extra = "".join(f'<linearGradient id="s{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"><animate attributeName="stop-color" values="{a};{c};{a}" dur="4s" repeatCount="indefinite"/></stop>'
                    f'<stop offset="1" stop-color="{c}"><animate attributeName="stop-color" values="{c};{a};{c}" dur="4s" repeatCount="indefinite"/></stop></linearGradient>' for i, (_, _, a, c) in enumerate(cards))
    b = ""
    for i, (num, lab, a, c) in enumerate(cards):
        x = 40 + i * (cw + gap)
        per = 2 * (cw + 92)
        b += (f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="{3+i*.4}s" repeatCount="indefinite"/>'
              f'<rect x="{x:.1f}" y="28" width="{cw}" height="96" rx="16" fill="url(#s{i})" fill-opacity=".1"/>'
              f'<rect x="{x:.1f}" y="28" width="{cw}" height="96" rx="16" fill="none" stroke="{a}" stroke-opacity=".3" stroke-width="2"/>'
              f'<rect x="{x:.1f}" y="28" width="{cw}" height="96" rx="16" fill="none" stroke="url(#s{i})" stroke-width="3" stroke-linecap="round" stroke-dasharray="90 {per-90}"><animate attributeName="stroke-dashoffset" from="0" to="-{per}" dur="3.5s" repeatCount="indefinite"/></rect>'
              f'<text x="{x+cw/2:.1f}" y="84" text-anchor="middle" font-family="{FONT}" font-size="46" font-weight="800" fill="url(#s{i})">{num}</text>'
              f'<text x="{x+cw/2:.1f}" y="110" text-anchor="middle" font-family="{FONT}" font-size="14" fill="#c9d1d9">{lab}</text></g>')
    return frame(W, Hh, b, extra)


def latest_commit(name, token):
    try:
        c = rest(f"/repos/{USER}/{name}/commits?per_page=1", token)[0]["commit"]
        return c["message"].split("\n")[0].strip(), c["author"]["date"]
    except Exception:
        return None, None


def md(t):
    return (t or "").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]").replace("<", "&lt;")


def replace_block(text, name, content, inline=False):
    a, b = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    if a not in text or b not in text:
        return text
    head, rest_ = text.split(a, 1)
    _, tail = rest_.split(b, 1)
    sep = "" if inline else "\n"
    return head + a + sep + content + sep + b + tail


def projects_block(repos):
    groups = {}
    for r in sorted(repos, key=lambda x: x["pushed_at"], reverse=True):
        groups.setdefault(categorize(r), []).append(r)
    out = []
    for i, k in enumerate(sorted(groups, key=lambda k: list(CATS).index(k))):
        name, _, emo = CATS[k]
        rows = ["| Project | Language | Updated | Link |", "|---|---|---|---|"]
        for r in groups[k]:
            desc = f"<br/><sub>{md(r['description'])}</sub>" if r.get("description") else ""
            rows.append(f"| **{md(pretty(r['name']))}**{desc} | {r.get('language') or '–'} | {short_date(r['pushed_at'])} | [Code]({r['html_url']}) |")
        out.append(f"<details{' open' if i == 0 else ''}>\n<summary><b>{emo} {name} ({len(groups[k])})</b></summary>\n<br/>\n\n" + "\n".join(rows) + "\n\n</details>\n")
    return "\n".join(out)


# ---------------------------------------------------------------- developer lab (unique animated graphics)
def placeholder_svg(w, h, title):
    return frame(w, h, f'<text x="{w/2}" y="{h/2}" text-anchor="middle" font-family="{FONT}" font-size="18" fill="#8b949e">{esc(title)}: syncing live data…</text>')


def fetch_commits(repos, token, per_repo=30, limit=20):
    out = []
    for r in sorted(repos, key=lambda x: x["pushed_at"], reverse=True)[:limit]:
        try:
            for c in rest(f"/repos/{USER}/{r['name']}/commits?per_page={per_repo}", token):
                cm = c["commit"]
                if cm["author"]["name"].endswith("[bot]"):
                    continue
                out.append({"date": cm["author"]["date"], "msg": cm["message"].split("\n")[0].strip(), "repo": r["name"]})
        except Exception:
            continue
    out.sort(key=lambda x: x["date"], reverse=True)
    return out


def snake_svg(days):
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0) - dt.timedelta(weeks=52)
    data = {d: c for d, c in days}
    nz = sorted(c for c in data.values() if c > 0)
    q = (lambda p: nz[min(len(nz) - 1, int(len(nz) * p))]) if nz else (lambda p: 1)
    t1, t2, t3 = q(.4), q(.7), q(.9)
    lvl = lambda c: 0 if c == 0 else 1 if c <= t1 else 2 if c <= t2 else 3 if c <= t3 else 4
    cell, gap, x0, y0, step_t = 14, 3, 52, 70, 0.05
    W, H = 1000, 220
    pts, cells = [], []
    for w in range(53):
        for d in (range(7) if w % 2 == 0 else range(6, -1, -1)):
            pts.append((x0 + w * (cell + gap) + cell / 2, y0 + d * (cell + gap) + cell / 2))
            day = start + dt.timedelta(weeks=w, days=d)
            if day <= today:
                cells.append((len(pts) - 1, w, d, data.get(day, 0)))
    T = len(pts) * step_t
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    year = sum(c for d, c in data.items() if d >= today - dt.timedelta(days=365))
    b = (f'<text x="40" y="44" font-family="{FONT}" font-size="22" font-weight="700" fill="#e6edf3">Contribution Snake</text>'
         f'<text x="40" y="64" font-family="{FONT}" font-size="13" fill="#8b949e">Eating {year:,} contributions from the last year. It never gets full.</text>'
         f'<path id="sp" d="{path}" fill="none"/>')
    for i, w, d, c in cells:
        x, y, fill = x0 + w * (cell + gap), y0 + d * (cell + gap), LEVELS[lvl(c)]
        if c == 0:
            b += f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fill}"/>'
        else:
            p = min(0.965, i * step_t / T)
            b += (f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fill}">'
                  f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;{p:.4f};{p+0.004:.4f};0.985;1" dur="{T:.1f}s" repeatCount="indefinite"/></rect>')
    n_seg = 9
    for k in range(n_seg - 1, -1, -1):
        size = 13 if k else 16
        col = "url(#gA)" if k else "#f7b731"
        begin = 0 if k == 0 else -(T - k * step_t * 1.6)
        op = max(0.35, 1 - k * 0.07)
        b += (f'<rect x="{-size/2}" y="{-size/2}" width="{size}" height="{size}" rx="{4 if k else 6}" fill="{col}" opacity="{op:.2f}">'
              f'<animateMotion dur="{T:.1f}s" begin="{begin:.2f}s" repeatCount="indefinite"><mpath href="#sp"/></animateMotion></rect>')
    return frame(W, H, b)


def terminal_svg(info, commits):
    if info is None:
        return placeholder_svg(1000, 400, "Developer terminal")
    fs, cw, lh = 16, 9.6, 27
    lines = [("cmd", "whoami"), ("out", "uzair-baig · software engineer · aspiring UI/UX designer"),
             ("cmd", "cat stats.json"),
             ("out", f'{{ "repos": {info["repos"]}, "commits": {info["commits"]}, "followers": {info["followers"]}, "streak": "{info["streak"]} days" }}'),
             ("cmd", "ls ~/skills"), ("out", "c++  python  react  node  flutter  kotlin  figma"),
             ("cmd", "git log --oneline -3")]
    for c in commits[:3]:
        lines.append(("log", f'{c["repo"]}: {c["msg"]}'[:84]))
    lines += [("cmd", "echo $STATUS"), ("out", "open to internships, collaborations & freelance work")]
    H = 78 + len(lines) * lh + 20
    b = ('<rect x="0" y="0" width="1000" height="44" rx="18" fill="#161b22"/><rect x="0" y="26" width="1000" height="18" fill="#161b22"/>'
         '<circle cx="28" cy="22" r="6" fill="#ff5f57"/><circle cx="48" cy="22" r="6" fill="#febc2e"/><circle cx="68" cy="22" r="6" fill="#28c840"/>'
         f'<text x="500" y="27" text-anchor="middle" font-family="{MONO}" font-size="13" fill="#8b949e">uzair@github: ~/profile</text>')
    t, clips = 0.4, ""
    last_x = last_y = 0
    for i, (kind, text) in enumerate(lines):
        y = 78 + i * lh
        prefix = "$ " if kind == "cmd" else ("• " if kind == "log" else "")
        full = prefix + text
        wpx = len(full) * cw
        dur = max(0.4, len(full) * 0.028)
        clips += f'<clipPath id="tc{i}"><rect x="40" y="{y-fs-2}" height="{lh}" width="0"><animate attributeName="width" from="0" to="{wpx+4:.1f}" dur="{dur:.2f}s" begin="{t:.2f}s" fill="freeze"/></rect></clipPath>'
        col = "#e6edf3" if kind == "cmd" else ("#7ee787" if kind == "log" else "#79c0ff")
        pre = f'<tspan fill="#28c840">$ </tspan>' if kind == "cmd" else (f'<tspan fill="#f7b731">• </tspan>' if kind == "log" else "")
        b += (f'<text x="40" y="{y}" clip-path="url(#tc{i})" xml:space="preserve" font-family="{MONO}" font-size="{fs}" fill="{col}" textLength="{wpx:.1f}" lengthAdjust="spacing">{pre}{esc(text)}</text>')
        t += dur + (0.35 if kind == "cmd" else 0.2)
        last_x, last_y = 40 + wpx + 6, y
    b += (f'<rect x="{last_x:.1f}" y="{last_y-fs+1}" width="9" height="{fs+2}" fill="#36BCF7" opacity="0">'
          f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.01;0.5;0.51;1" dur="1s" begin="{t:.2f}s" repeatCount="indefinite"/></rect>')
    return frame(1000, int(H), clips and f'<defs>{clips}</defs>' + b)


def orbit_svg(langs):
    if not langs:
        return placeholder_svg(1000, 470, "Language orbit")
    import random
    total = sum(langs.values())
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:7]
    W, H, cx, cy = 1000, 470, 500, 247
    random.seed(11)
    b = ""
    for _ in range(70):
        x, y, r = random.randint(12, W - 12), random.randint(12, H - 12), random.choice([0.8, 1.1, 1.6])
        b += f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity=".5"><animate attributeName="opacity" values=".15;.8;.15" dur="{random.uniform(2,5):.1f}s" begin="{random.uniform(0,3):.1f}s" repeatCount="indefinite"/></circle>'
    b += (f'<text x="40" y="44" font-family="{FONT}" font-size="22" font-weight="700" fill="#e6edf3">Language Orbit</text>'
          f'<text x="40" y="64" font-family="{FONT}" font-size="13" fill="#8b949e">Bigger planet = more code. Computed from every public repo.</text>')
    b += f'<circle cx="{cx}" cy="{cy}" r="46" fill="url(#gA)" filter="url(#glow)" opacity=".55"><animate attributeName="r" values="44;50;44" dur="3s" repeatCount="indefinite"/></circle>'
    b += (f'<circle cx="{cx}" cy="{cy}" r="38" fill="#08090f" stroke="url(#gA)" stroke-width="3"/>'
          f'<text x="{cx}" y="{cy+9}" text-anchor="middle" font-family="{FONT}" font-size="26" font-weight="800" fill="url(#gA)">UB</text>')
    for i, (name, val) in enumerate(top):
        r = 70 + i * 20
        share = val / total
        pr = max(7, min(20, 7 + share * 60))
        col = LANG_COLORS.get(name, "#8b949e")
        dur = 14 + i * 7
        b += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".08" stroke-dasharray="2 6"/>'
        a0 = (i * 53) % 360
        b += (f'<g><animateTransform attributeName="transform" type="rotate" from="{a0} {cx} {cy}" to="{a0+360} {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/>'
              f'<g transform="translate({cx+r} {cy})"><circle r="{pr+5:.1f}" fill="{col}" opacity=".25"/><circle r="{pr:.1f}" fill="{col}"/>'
              f'<g><animateTransform attributeName="transform" type="rotate" from="{-a0} 0 0" to="{-a0-360} 0 0" dur="{dur}s" repeatCount="indefinite"/>'
              f'<text y="{pr+16:.1f}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="#e6edf3">{esc(name)} {share*100:.0f}%</text></g></g></g>')
    return frame(W, H, b)


def clock_svg(commits):
    from zoneinfo import ZoneInfo
    import collections
    if not commits:
        return placeholder_svg(1000, 360, "When I code")
    tz = ZoneInfo("Asia/Karachi")
    hrs = collections.Counter(dt.datetime.fromisoformat(c["date"].replace("Z", "+00:00")).astimezone(tz).hour for c in commits)
    total = sum(hrs.values())
    mx = max(hrs.values())
    peak = max(hrs, key=hrs.get)
    fmt_h = lambda h: f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}"
    persona = ("Night Owl 🦉" if peak >= 22 or peak < 5 else "Early Bird 🐦" if peak < 9 else "Daytime Coder ☀️" if peak < 18 else "Evening Hacker 🌆")
    W, H, cx, cy, r0, rmax = 1000, 360, 250, 212, 38, 78
    b = (f'<text x="40" y="44" font-family="{FONT}" font-size="22" font-weight="700" fill="#e6edf3">When I Code</text>'
         f'<text x="40" y="64" font-family="{FONT}" font-size="13" fill="#8b949e">Commit times from my last {total} commits (Pakistan time)</text>')
    b += f'<circle cx="{cx}" cy="{cy}" r="{r0-6}" fill="none" stroke="#fff" stroke-opacity=".08"/><circle cx="{cx}" cy="{cy}" r="{r0+rmax+6}" fill="none" stroke="#fff" stroke-opacity=".06" stroke-dasharray="3 5"/>'
    for h in range(24):
        ln = 4 + (rmax - 4) * hrs.get(h, 0) / mx
        ang = h * 15
        fill = "url(#peak)" if h == peak else "url(#bar)"
        b += (f'<rect x="{cx-5}" y="{cy-r0-ln:.1f}" width="10" height="{ln:.1f}" rx="5" fill="{fill}" transform="rotate({ang} {cx} {cy})" opacity="{1 if hrs.get(h) else .25}">'
              f'<animate attributeName="height" from="0" to="{ln:.1f}" dur="1.1s" fill="freeze"/><animate attributeName="y" from="{cy-r0}" to="{cy-r0-ln:.1f}" dur="1.1s" fill="freeze"/></rect>')
    for h, lab in ((0, "12AM"), (6, "6AM"), (12, "12PM"), (18, "6PM")):
        import math
        a = math.radians(h * 15)
        b += f'<text x="{cx+(r0+rmax+18)*math.sin(a):.1f}" y="{cy-(r0+rmax+18)*math.cos(a)+4:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#8b949e">{lab}</text>'
    b += (f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="800" fill="url(#gB)">{fmt_h(peak)}</text>'
          f'<text x="{cx}" y="{cy+14}" text-anchor="middle" font-family="{FONT}" font-size="11" fill="#8b949e">peak hour</text>')
    b += (f'<text x="520" y="120" font-family="{FONT}" font-size="30" font-weight="800" fill="url(#gB)">{persona}</text>'
          f'<text x="520" y="146" font-family="{FONT}" font-size="14" fill="#c9d1d9">Most commits land around {fmt_h(peak)}.</text>')
    blocks = [("Night  12AM-6AM", range(0, 6), "#8b5cf6"), ("Morning  6AM-12PM", range(6, 12), "#f7b731"),
              ("Afternoon  12PM-6PM", range(12, 18), "#36BCF7"), ("Evening  6PM-12AM", range(18, 24), "#db61a2")]
    for i, (lab, rg, col) in enumerate(blocks):
        v = sum(hrs.get(h, 0) for h in rg)
        pct = 100 * v / total
        y = 190 + i * 40
        b += (f'<text x="520" y="{y}" font-family="{MONO}" font-size="13" fill="#e6edf3">{lab}</text>'
              f'<text x="960" y="{y}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{col}">{pct:.0f}%</text>'
              f'<rect x="520" y="{y+8}" width="440" height="7" rx="3.5" fill="#fff" fill-opacity=".07"/>'
              f'<rect x="520" y="{y+8}" width="{max(3,4.4*pct):.1f}" height="7" rx="3.5" fill="{col}"><animate attributeName="width" from="0" to="{max(3,4.4*pct):.1f}" dur="1.2s" fill="freeze"/></rect>')
    return frame(W, H, b)


def ticker_svg(commits):
    if not commits:
        return placeholder_svg(1000, 64, "Commit ticker")
    fs = 17
    S = "      ◆      ".join(f'{c["repo"]}: {c["msg"][:70]}' for c in commits[:10]) + "      ◆      "
    Wd = round(len(S) * fs * 0.6)
    t = (f'<text x="{{x}}" y="40" font-family="{MONO}" font-size="{fs}" font-weight="700" fill="url(#tk)" xml:space="preserve" textLength="{Wd}" lengthAdjust="spacing">{esc(S)}</text>')
    extra = (f'<linearGradient id="tk" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="500" y2="0" spreadMethod="reflect"><stop offset="0" stop-color="#36BCF7"/><stop offset=".5" stop-color="#8b5cf6"/><stop offset="1" stop-color="#db61a2"/>'
             f'<animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="500 0" dur="6s" repeatCount="indefinite"/></linearGradient>'
             '<clipPath id="tv"><rect x="2" y="2" width="996" height="60" rx="14"/></clipPath>')
    body = (f'<g clip-path="url(#tv)"><g><animateTransform attributeName="transform" type="translate" from="0 0" to="-{Wd} 0" dur="{max(25, Wd//55)}s" repeatCount="indefinite"/>'
            + t.format(x=0) + t.format(x=Wd) + t.format(x=2 * Wd) + '</g></g>')
    return frame(1000, 64, body, extra)


def write_data(days):
    """Export daily counts so the live dashboard can read them."""
    os.makedirs("data", exist_ok=True)
    payload = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": USER,
        "start": days[0][0].isoformat() if days else None,
        "counts": {d.isoformat(): c for d, c in days if c > 0},
    }
    with open("data/contributions.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))


def rest(path, token):
    req = urllib.request.Request("https://api.github.com" + path,
                                 headers={"Authorization": f"bearer {token}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def update_readme(token):
    """Rewrite every auto-generated block in the README from live repo data."""
    path = "README.md"
    text = open(path, encoding="utf-8").read()
    repos = own_repos(fetch_repos(token))
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)
    rows = ["| Repository | Latest change | Language | When |", "|---|---|---|---|"]
    for r in repos[:6]:
        msg, when = latest_commit(r["name"], token)
        rows.append(f"| [**{md(r['name'])}**]({r['html_url']}) | {md((msg or '–')[:70])} | {r.get('language') or '–'} | {short_date(when or r['pushed_at'])} |")
    now = dt.datetime.now(dt.timezone.utc).strftime("%b %-d, %Y %H:%M UTC")
    text = replace_block(text, "RECENT", "\n".join(rows) + f"\n\n<sub>⏱ Auto-updated {now}, follows my latest pushes</sub>")
    text = replace_block(text, "LATEST", " · ".join(f"[{md(r['name'])}]({r['html_url']})" for r in repos[:4]), inline=True)
    text = replace_block(text, "PROJECTS", projects_block(repos))
    try:
        import json
        text = replace_block(text, "CHANGES", changelog_block(json.load(open("data/changelog.json"))))
    except Exception as e:
        print("changes block skipped:", repr(e))
    open(path, "w", encoding="utf-8").write(text)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--demo":
        days, pending = demo_days(), False
    elif mode == "--pending":
        days, pending = [], True
    else:
        token = os.environ["GH_TOKEN"]
        days, pending = fetch_days(token), False
        write_data(days)
        write_extra(token, days)
        update_readme(token)
    os.makedirs(OUT, exist_ok=True)
    if mode == "--pending":
        write_svg("gh-stats", stats_card_svg(None))
        write_svg("top-langs", langs_card_svg(None))
        for n in FEATURED:
            write_svg("pin-" + n, pin_svg(None).replace(esc(FEATURED[0]), esc(n)))
    for name, fn in (("streak", streak_svg), ("contributions", heatmap_svg), ("weekday", weekday_svg)):
        with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
            f.write(fn(days, pending))
    print("wrote", OUT, "mode=", mode or "live", "days=", len(days))


if __name__ == "__main__":
    main()
