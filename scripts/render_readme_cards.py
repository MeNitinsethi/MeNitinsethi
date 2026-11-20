import json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
CARDS, DATA = ROOT / "cards", ROOT / "data"
USER = os.getenv("GITHUB_REPOSITORY_OWNER", "MeNitinsethi")
TOKEN = os.getenv("GITHUB_TOKEN", "")

def api(url, method="GET", payload=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN: req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

def svg(title, eyebrow, body, accent="#60A5FA", width=1000, height=210, extra=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs><linearGradient id="bg"><stop stop-color="#0B1220"/><stop offset="1" stop-color="#172554"/></linearGradient></defs>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="22" fill="url(#bg)" stroke="#334155"/>
<circle cx="{width-70}" cy="25" r="80" fill="{accent}" opacity=".08"><animate attributeName="r" values="65;90;65" dur="7s" repeatCount="indefinite"/></circle>
<text x="36" y="40" fill="{accent}" font-family="Arial" font-size="13" letter-spacing="3">{escape(eyebrow.upper())}</text>
<text x="36" y="88" fill="#F8FAFC" font-family="Arial" font-size="29" font-weight="700">{escape(title)}</text>
<text x="36" y="125" fill="#CBD5E1" font-family="Arial" font-size="16">{escape(body)}</text>{extra}
<circle cx="{width-45}" cy="{height-28}" r="5" fill="{accent}"><animate attributeName="opacity" values=".3;1;.3" dur="2s" repeatCount="indefinite"/></circle></svg>'''

def main():
    CARDS.mkdir(exist_ok=True); DATA.mkdir(exist_ok=True)
    profile = api(f"https://api.github.com/users/{USER}")
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=updated")
    events = api(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    stats = {"generated_at":datetime.now(timezone.utc).isoformat(),"username":USER,
             "public_repositories":profile.get("public_repos",len(repos)),
             "followers":profile.get("followers",0),
             "stars":sum(x.get("stargazers_count",0) for x in repos),
             "recent_push_events":sum(x.get("type")=="PushEvent" for x in events)}
    (DATA/"profile_stats.json").write_text(json.dumps(stats,indent=2)+"\n")
    extra = "".join(f'<text x="{x}" y="175" fill="#F8FAFC" font-family="Arial" font-size="26" font-weight="700">{v}</text><text x="{x}" y="193" fill="#94A3B8" font-family="Arial" font-size="10">{label}</text>' for x,v,label in [(40,stats["public_repositories"],"PUBLIC REPOS"),(280,stats["followers"],"FOLLOWERS"),(520,stats["stars"],"STARS"),(760,stats["recent_push_events"],"RECENT PUSHES")])
    (CARDS/"activity.svg").write_text(svg("GitHub at a glance","Live profile snapshot","Public profile metrics • refreshed daily",extra=extra))
    query = "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}"
    try:
        result=api("https://api.github.com/graphql","POST",{"query":query,"variables":{"login":USER}})
        cal=result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        days=[d for w in cal["weeks"] for d in w["contributionDays"]][-364:]
        cells=""
        for i,d in enumerate(days):
            level=min(4,d["contributionCount"])
            color=["#172554","#1E3A8A","#1D4ED8","#3B82F6","#93C5FD"][level]
            cells+=f'<rect x="{36+(i//7)*13}" y="{72+(i%7)*13}" width="9" height="9" rx="2" fill="{color}"><title>{escape(d["date"])}: {d["contributionCount"]}</title></rect>'
        total=cal["totalContributions"]
        (CARDS/"contributions.svg").write_text(svg("Contribution calendar","Consistency over time",f"{total} contributions in the last year • hover over a square for details",accent="#34D399",height=210,extra=cells))
    except Exception as e:
        print("Contribution calendar unavailable with this token:",e)
        (CARDS/"contributions.svg").write_text(svg("Contribution calendar","Consistency over time","GitHub GraphQL contribution data is not available to this workflow token.",accent="#34D399"))
    print("Profile cards generated.")

if __name__=="__main__": main()
