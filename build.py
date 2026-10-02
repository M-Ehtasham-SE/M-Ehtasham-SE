#!/usr/bin/env python3
"""Rebuilds every generated graphic from data/*.json and assets/src/*.

Run locally:  pip install pillow && python tools/build.py
In CI:        .github/workflows/build-site.yml runs it on every push to data/, tools/ or assets/src/.
Add --static to bake orbit chips at fixed positions (only for previewing in non-browser renderers).
"""
import base64, html, io, json, math, re, sys, textwrap
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
A, D, T = ROOT / "assets", ROOT / "data", ROOT / "tools" / "templates"
STATIC = "--static" in sys.argv
esc = lambda s: html.escape(str(s), quote=True)
FONT = "font-family:'Fira Code',SFMono-Regular,Consolas,Menlo,monospace"
GRAD = ('<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/>'
        '<stop offset="1" stop-color="#a78bfa"/></linearGradient>')
GLOW = ('<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def write(name, text):
    (A / name).write_text(text, encoding="utf-8")
    print("wrote", name, f"{len(text)/1024:.1f} KB")


def b64_photo():
    im = ImageOps.fit(Image.open(A / "src" / "profile.jpg").convert("RGB"), (360, 360), centering=(0.5, 0.4))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def b64_logo():
    im = Image.open(A / "src" / "logo.png").convert("RGB")
    s = max(im.size); sq = Image.new("RGB", (s, s), "white")
    sq.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
    buf = io.BytesIO(); sq.resize((260, 260), Image.LANCZOS).save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def templates():
    write("hero.svg", (T / "hero.svg").read_text().replace("{{PHOTO}}", b64_photo()))
    write("education.svg", (T / "education.svg").read_text().replace("{{LOGO}}", b64_logo()))


def nav(items):
    for i, (label, anchor) in enumerate(items, 1):
        w = 44 + len(label) * 8
        write(f"nav-{anchor}.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 42" width="{w}" height="42">
<defs>{GRAD}</defs><style>text{{{FONT}}}</style>
<rect x=".5" y=".5" width="{w-1}" height="41" rx="10" fill="#0d1117" stroke="url(#g)" stroke-opacity=".7"/>
<text x="12" y="26" font-size="11" fill="#22d3ee">{i:02d}</text>
<text x="34" y="26" font-size="13" fill="#e5e7eb">{esc(label)}</text>
<rect x="12" y="34" height="2" rx="1" fill="url(#g)" width="0"><animate attributeName="width" values="0;{w-24};0" dur="3.6s" begin="{i*0.4:.1f}s" repeatCount="indefinite"/></rect>
</svg>''')


def terminal(lines):
    step, n = 1.2, len(lines)
    cycle = n * step + 5
    css, body = "", ""
    for i, ln in enumerate(lines):
        a = i * step / cycle * 100; b = a + 1.2
        css += f".l{i}{{animation:k{i} {cycle:.1f}s infinite}}@keyframes k{i}{{0%,{a:.2f}%{{opacity:0}}{b:.2f}%,92%{{opacity:1}}100%{{opacity:0}}}}"
        cmd = ln.startswith("$ ")
        y = 78 + i * 26
        if cmd:
            body += f'<text class="l{i}" x="28" y="{y}" font-size="14"><tspan fill="#22d3ee">$</tspan><tspan fill="#e5e7eb"> {esc(ln[2:])}</tspan></text>'
        else:
            body += f'<text class="l{i}" x="28" y="{y}" font-size="14" fill="#9ca3af">{esc(ln)}</text>'
    h = 78 + n * 26 + 28
    write("terminal.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {h}" width="900" height="{h}">
<defs>{GRAD}</defs>
<style>text{{{FONT}}}{css}.cur{{animation:c 1s steps(1) infinite}}@keyframes c{{50%{{opacity:0}}}}</style>
<rect width="900" height="{h}" rx="12" fill="#0b0f19"/>
<rect x=".5" y=".5" width="899" height="{h-1}" rx="12" fill="none" stroke="url(#g)" stroke-opacity=".6"/>
<rect x="1" y="1" width="898" height="36" rx="11" fill="#111827"/>
<circle cx="24" cy="19" r="6" fill="#ef4444"/><circle cx="44" cy="19" r="6" fill="#eab308"/><circle cx="64" cy="19" r="6" fill="#22c55e"/>
<text x="450" y="23" text-anchor="middle" font-size="12" fill="#6b7280">ehtasham@fast-nuces: ~</text>
{body}
<rect class="cur" x="28" y="{78+n*26-12}" width="9" height="16" fill="#22d3ee"/>
</svg>''')


def orbit(chips):
    cx, cy, W, H = 450, 230, 900, 460
    rings = [(400, 70, -10, 26, 1), (300, 112, 8, 20, 0), (200, 150, -4, 15, 1)]
    groups = [[] for _ in rings]
    for i, c in enumerate(chips):
        groups[i % 3].append(c)
    palette = ["#22d3ee", "#a78bfa", "#818cf8"]
    out = ""
    for r, ((rx, ry, tilt, dur, fwd), names) in enumerate(zip(rings, groups)):
        sweep = 1 if fwd else 0
        path = f"M{cx-rx},{cy} a{rx},{ry} 0 1,{sweep} {2*rx},0 a{rx},{ry} 0 1,{sweep} {-2*rx},0"
        out += f'<g transform="rotate({tilt} {cx} {cy})"><path d="{path}" fill="none" stroke="#22d3ee" stroke-opacity=".22" stroke-dasharray="3 7"/>'
        for j, name in enumerate(names):
            w = len(name) * 7.4 + 24; col = palette[(r + j) % 3]
            chip = (f'<rect x="{-w/2:.0f}" y="-12" width="{w:.0f}" height="24" rx="12" fill="#0d1117" stroke="{col}" stroke-opacity=".8"/>'
                    f'<text x="0" y="4" text-anchor="middle" font-size="12" fill="#e5e7eb">{esc(name)}</text>')
            if STATIC:
                ang = 2 * math.pi * j / max(len(names), 1)
                px = cx + rx * math.cos(ang); py = cy + (ry if fwd else -ry) * math.sin(ang)
                out += f'<g transform="translate({px:.0f} {py:.0f})">{chip}</g>'
            else:
                out += (f'<g>{chip}<animateMotion dur="{dur}s" begin="-{dur*j/len(names):.2f}s" repeatCount="indefinite" '
                        f'rotate="0" path="{path}"/></g>')
        out += "</g>"
    write("orbit.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>{GRAD}{GLOW}<radialGradient id="a"><stop offset="0" stop-color="#6366f1" stop-opacity=".5"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/></radialGradient></defs>
<style>text{{{FONT}}}.p{{transform-origin:{cx}px {cy}px;animation:p 3s ease-in-out infinite}}@keyframes p{{0%,100%{{opacity:.5;transform:scale(1)}}50%{{opacity:1;transform:scale(1.12)}}}}</style>
<rect width="{W}" height="{H}" rx="14" fill="#0b0f19"/>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="url(#g)" stroke-opacity=".5"/>
<text x="24" y="34" font-size="12" fill="#22d3ee">// stack in orbit</text>
<circle class="p" cx="{cx}" cy="{cy}" r="90" fill="url(#a)"/>
<circle cx="{cx}" cy="{cy}" r="46" fill="#0b0f19" stroke="url(#g)" stroke-width="2" filter="url(#glow)"/>
<text x="{cx}" y="{cy+8}" text-anchor="middle" font-size="24" font-weight="700" fill="url(#g)">&lt;/&gt;</text>
{out}
</svg>''')


def chips_row(stack, max_w):
    x, parts = 0, ""
    for s in stack:
        w = len(s) * 6.9 + 18
        if x + w > max_w: break
        parts += (f'<rect x="{x:.0f}" y="0" width="{w:.0f}" height="22" rx="11" fill="#22d3ee" fill-opacity=".1" stroke="#22d3ee" stroke-opacity=".5"/>'
                  f'<text x="{x+w/2:.0f}" y="15" text-anchor="middle" font-size="11" fill="#a5f3fc">{esc(s)}</text>')
        x += w + 8
    return parts


def slug(p):
    return p["repo"].rstrip("/").split("/")[-1].lower().strip("-")


def cards(projects):
    for i, p in enumerate(projects, 1):
        lines = textwrap.wrap(p["tagline"], 54)[:3]
        tl = "".join(f'<text x="24" y="{86+k*18}" font-size="12" fill="#9ca3af">{esc(l)}</text>' for k, l in enumerate(lines))
        title = p["name"] if len(p["name"]) <= 32 else p["name"][:31] + "..."
        write(f"project-{slug(p)}.svg", f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 190" width="440" height="190">
<defs>{GRAD}{GLOW}</defs>
<style>text{{{FONT}}}.d{{stroke-dasharray:140 860;animation:d 7s linear infinite}}@keyframes d{{to{{stroke-dashoffset:-1000}}}}</style>
<rect width="440" height="190" rx="12" fill="#0d1117"/>
<rect x=".5" y=".5" width="439" height="189" rx="12" fill="none" stroke="#30363d"/>
<rect class="d" x="1" y="1" width="438" height="188" rx="12" fill="none" stroke="url(#g)" stroke-width="2" pathLength="1000" filter="url(#glow)"/>
<text x="24" y="38" font-size="11" fill="#22d3ee">PROJECT {i:02d}</text>
<text x="24" y="62" font-size="17" font-weight="700" fill="#e5e7eb">{esc(title)}</text>
{tl}
<g transform="translate(24 148)">{chips_row(p["stack"], 392)}</g>
<text x="416" y="38" text-anchor="end" font-size="12" fill="#a78bfa">open repo &#8599;</text>
</svg>''')


def projects_block(projects):
    out = ""
    for i in range(0, len(projects), 2):
        out += '<p align="center">\n'
        for p in projects[i:i + 2]:
            out += f'  <a href="{p["repo"]}"><img src="./assets/project-{slug(p)}.svg" width="49%" alt="{esc(p["name"])}"/></a>\n'
        out += "</p>\n"
    out += "\n<sub>Open a project below for the details.</sub>\n\n"
    for p in projects:
        out += f'<details>\n<summary><b>{esc(p["name"])}</b></summary>\n<br/>\n\n{p["tagline"]}\n\n'
        out += f'- **Stack:** {" · ".join(p["stack"])}\n'
        if p.get("highlights"): out += f'- **Highlights:** {" · ".join(p["highlights"])}\n'
        if p.get("problem"): out += f'- **Problem it solves:** {p["problem"]}\n'
        links = [f'[Repository]({p["repo"]})'] + ([f'[Live demo]({p["live"]})'] if p.get("live") else [])
        out += f'- **Links:** {" · ".join(links)}\n\n</details>\n\n'
    return out


def readme(projects):
    f = ROOT / "README.md"
    s = f.read_text(encoding="utf-8")
    new = re.sub(r"(<!-- PROJECTS:START -->\n).*?(<!-- PROJECTS:END -->)",
                 lambda m: m.group(1) + projects_block(projects) + m.group(2), s, flags=re.S)
    f.write_text(new, encoding="utf-8"); print("updated README project block")


if __name__ == "__main__":
    site = json.loads((D / "site.json").read_text())
    projects = json.loads((D / "projects.json").read_text())
    templates(); nav(site["nav"]); terminal(site["terminal"]); orbit(site["orbit"]); cards(projects)
    if (ROOT / "README.md").exists(): readme(projects)
