"""LinkedIn company cover image, 1128x191 (rendered at 2x). Logo overlaps bottom-left on desktop,
so the left ~280px stays empty; key text sits in the centre safe area."""
import random

random.seed(11)
ff = open("fontfaces.css", encoding="utf-8").read()
W, H = 1128, 191
AX, AW = 838, 290                     # streams art on the right, bleeding off the edge
CY = 118

paths = []
for i in range(30):
    y0 = -40 + i * (H + 80) / 29 + random.uniform(-4, 4)
    y1 = CY + (i - 14.5) * 1.3 + random.uniform(-2, 2)
    c1x, c2x = AX + random.uniform(90, 160), AX + random.uniform(220, 320)
    d = f"M{AX - 10} {y0:.1f} C{c1x:.1f} {y0:.1f} {c2x:.1f} {y1:.1f} {W + 10} {y1:.1f}"
    r = random.random()
    if i in (8, 20):
        st, w, op = "#14151C", 1.8, 0.85
    elif r < 0.25:
        st, w, op = "#3E2FD0", 1.2, 0.7
    else:
        st, w, op = "#FFFFFF", random.choice([0.9, 1.2, 1.6]), random.uniform(0.45, 0.9)
    paths.append(f'<path d="{d}" stroke="{st}" stroke-width="{w}" stroke-opacity="{op:.2f}" fill="none" stroke-linecap="round"/>')
streaks = []
for i in range(0, 30, 3):
    y = CY + (i - 14.5) * 1.3
    x = AX + 260 + random.uniform(0, 160)
    streaks.append(f'<line x1="{x:.0f}" y1="{y:.1f}" x2="{x + 44:.0f}" y2="{y:.1f}" stroke="#fff" stroke-width="2.2" stroke-linecap="round" opacity=".9"/>')

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{ff}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#F7F7FB}}
body:before{{content:"";position:absolute;inset:0;background:radial-gradient(40% 120% at 15% 0%,rgba(101,88,245,.10),transparent 60%)}}
svg{{position:absolute;inset:0}}
.copy{{position:absolute;left:280px;top:0;bottom:0;width:520px;white-space:nowrap;display:flex;flex-direction:column;justify-content:center}}
.h{{font-family:"Stack Sans Headline","Stack Sans Headline Fallback",Arial,sans-serif;font-weight:500;font-size:36px;line-height:1;letter-spacing:-1.4px;color:#14151C}}
.h span{{color:#6558F5}}
.s{{margin-top:14px;font-family:"Stack Sans Notch","Stack Sans Notch Fallback",Arial,sans-serif;font-weight:500;font-size:12px;letter-spacing:1.1px;text-transform:uppercase;color:#5C5F6B}}
.s b{{color:#6558F5;font-weight:500}}
</style></head><body>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6558F5"/><stop offset=".55" stop-color="#5B7BF7"/><stop offset="1" stop-color="#8CC4FF"/></linearGradient>
    <radialGradient id="glow" cx=".8" cy=".6" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".22" stop-color="#fff" stop-opacity="1"/></linearGradient>
    <mask id="m"><rect x="{AX}" y="0" width="{AW}" height="{H}" fill="url(#fade)"/></mask>
  </defs>
  <g mask="url(#m)">
    <rect x="{AX}" y="0" width="{AW}" height="{H}" fill="url(#bg)"/>
    <rect x="{AX}" y="0" width="{AW}" height="{H}" fill="url(#glow)"/>
    {''.join(paths)}
    {''.join(streaks)}
  </g>
</svg>
<div class="copy">
  <div class="h">Less admin. <span>More selling time.</span></div>
  <div class="s">Sales productivity platform · <b>works with the tools you already own</b></div>
</div>
</body></html>"""
open("linkedin-banner.html", "w", encoding="utf-8").write(html)
print("ok")
