"""Build og-anim.html: a 1200x630 frame whose state is set by #t=<seconds>."""
import math
import random

random.seed(7)
ff = open("fontfaces.css", encoding="utf-8").read()

W, H = 492, 518          # artwork panel
CY = 300                 # where the stream converges
paths = []
for i in range(30):
    y0 = -60 + i * (H + 120) / 29 + random.uniform(-8, 8)
    y1 = CY + (i - 14.5) * 2.2 + random.uniform(-3, 3)
    c1x, c2x = random.uniform(150, 230), random.uniform(260, 360)
    d = f"M-20 {y0:.1f} C{c1x:.1f} {y0:.1f} {c2x:.1f} {y1:.1f} {W + 20} {y1:.1f}"
    r = random.random()
    if i in (9, 21):
        stroke, width, op = "#14151C", 2.6, 0.85
    elif r < 0.25:
        stroke, width, op = "#3E2FD0", 1.6, 0.7
    else:
        stroke, width, op = "#FFFFFF", random.choice([1.2, 1.6, 2.2]), random.uniform(0.45, 0.9)
    paths.append((d, stroke, width, op))

lines = "\n".join(
    f'<path class="ln" d="{d}" stroke="{s}" stroke-width="{w}" stroke-opacity="{o:.2f}" fill="none" stroke-linecap="round"/>'
    for d, s, w, o in paths)
streaks = "\n".join(
    f'<path class="st" d="{d}" stroke="#FFFFFF" stroke-width="{w + 1.4}" fill="none" stroke-linecap="round"/>'
    for k, (d, s, w, o) in enumerate(paths) if k % 3 == 1)

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{ff}
:root{{--c1:#F7F7FB;--c2:#14151C;--c4:#5C5F6B;--c7:#6558F5}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{background:var(--c1);position:relative;font-family:"Stack Sans Text","Stack Sans Text Fallback",Arial,sans-serif}}
body:before{{content:"";position:absolute;inset:0;background:radial-gradient(60% 80% at 0% 0%,rgba(101,88,245,.10),transparent 60%),radial-gradient(50% 70% at 100% 100%,rgba(59,130,246,.10),transparent 60%)}}
.left{{position:absolute;left:72px;top:64px;bottom:60px;width:560px;display:flex;flex-direction:column}}
.mark{{width:30px;height:30px}}
.sig{{display:flex;align-items:center;gap:10px}}
h1{{margin-top:auto;font-family:"Stack Sans Headline","Stack Sans Headline Fallback",Arial,sans-serif;font-weight:500;font-size:72px;line-height:.98;letter-spacing:-.04em;color:var(--c2)}}
h1 span{{color:var(--c7);display:block}}
p{{margin-top:24px;font-size:24px;line-height:1.35;font-weight:500;color:var(--c4);max-width:520px}}
.tag{{margin-top:auto;padding-top:28px;font-family:"Stack Sans Notch","Stack Sans Notch Fallback",Arial,sans-serif;font-weight:500;font-size:17px;letter-spacing:.06em;text-transform:uppercase;color:var(--c4);display:flex;justify-content:space-between;width:100%}}
.tag b{{color:var(--c7);font-weight:500}}
svg.art{{position:absolute;left:652px;top:56px;width:{W}px;height:{H}px;overflow:visible}}
#shadow{{position:absolute;left:652px;top:56px;width:{W}px;height:{H}px;border-radius:28px;box-shadow:0 30px 60px -30px rgba(20,21,28,.35)}}
.word{{font-family:"Stack Sans Headline","Stack Sans Headline Fallback",Arial,sans-serif;font-weight:600;font-size:128px;letter-spacing:-6px}}
</style></head><body>
<div class="left">
  <h1>Less admin.<span>More selling time.</span></h1>
  <p>The sales productivity platform that works with the sales tools you already own.</p>
  <div class="tag"><span>[Founding pilot · free for 30 days]</span><b class="sig"><img class="mark" src="favicon.svg" alt="">pipeleap.com</b></div>
</div>
<div id="shadow"></div>
<svg class="art" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#6558F5"/><stop offset=".55" stop-color="#5B7BF7"/><stop offset="1" stop-color="#8CC4FF"/>
    </linearGradient>
    <linearGradient id="navy" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1E2A5E"/><stop offset=".55" stop-color="#0B3F96"/><stop offset="1" stop-color="#1257C4"/></linearGradient>
    <radialGradient id="glow" cx=".82" cy=".58" r=".5"><stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <rect id="panelMask" width="{W}" height="{H}" rx="28" fill="#fff"/>
      <text id="wordMask" class="word" x="{W/2}" y="{CY + 44}" text-anchor="middle"><tspan fill="none">Pipe</tspan><tspan fill="#fff">leap</tspan></text>
    </mask>
    <mask id="m2" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <text id="wordMask2" class="word" x="{W/2}" y="{CY + 44}" text-anchor="middle"><tspan fill="none">Pipe</tspan><tspan fill="#fff">leap</tspan></text>
    </mask>
  </defs>
  <g mask="url(#m)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect id="glowRect" width="{W}" height="{H}" fill="url(#glow)"/>
    <rect id="navyRect" width="{W}" height="{H}" fill="url(#navy)" opacity="0"/>
    <g id="flow"><g id="lines">{lines}</g>
    <g id="streaks">{streaks}</g></g>
  </g>
  <g mask="url(#m2)"><g id="heroWrap" opacity="0"><image id="heroImg" href="hero.svg" preserveAspectRatio="xMidYMid slice"/></g></g>
  <text id="wordSolid" class="word" x="{W/2}" y="{CY + 44}" text-anchor="middle" opacity="0"><tspan fill="#14151C">Pipe</tspan><tspan fill="none">leap</tspan></text>
</svg>
<script>
const T = parseFloat((location.hash.match(/t=([0-9.]+)/)||[])[1]||'5.2');
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
document.querySelectorAll('.ln').forEach((p,i)=>{{
  const L=p.getTotalLength(); p.style.strokeDasharray=L;
  const k=ease(clamp((T-0.05-i*0.035)/1.25));
  p.style.strokeDashoffset=L*(1-k);
}});
document.querySelectorAll('.st').forEach((p,i)=>{{
  const L=p.getTotalLength(); const seg=70;
  p.style.strokeDasharray=seg+' '+(L+seg);
  const speed=L/1.6, start=0.9+i*0.17;
  const pos=((T-start)*speed)%(L+seg*2);
  p.style.strokeDashoffset = (T<start)? seg : (seg - pos);
  p.style.strokeOpacity = (T<start)?0:0.9;
}});
// reveal: panel dissolves, artwork remains only inside the word
const r=ease(clamp((T-2.4)/1.2));
document.getElementById('panelMask').setAttribute('fill-opacity', (1-r).toFixed(3));
document.getElementById('shadow').style.opacity=(1-r).toFixed(3);
const w=document.getElementById('wordMask');const ws=document.getElementById('wordSolid');ws.setAttribute('opacity',r.toFixed(3));
const s=1.06-0.06*r; const tf=`translate({W/2} {CY}) scale(${{s}}) translate(-{W/2} -{CY})`;w.setAttribute('transform',tf);ws.setAttribute('transform',tf);document.getElementById('wordMask2').setAttribute('transform',tf);
document.getElementById('glowRect').style.opacity = 1;document.getElementById('navyRect').setAttribute('opacity','0');
const sx=w.getStartPositionOfChar(4).x, ex=w.getEndPositionOfChar(7).x, base={CY + 44}, fs=128;
const yTop=base-0.98*fs, yBot=base+0.30*fs, cx=(sx+ex)/2, cy=(yTop+yBot)/2;
const hi=document.getElementById('heroImg');
hi.setAttribute('x',sx);hi.setAttribute('y',yTop);hi.setAttribute('width',ex-sx);hi.setAttribute('height',yBot-yTop);
hi.setAttribute('transform',`translate(${{cx}} ${{cy}}) scale(-2.4 2.4) translate(${{-cx}} ${{-cy}})`);
const hw=document.getElementById('heroWrap');hw.setAttribute('transform',tf);hw.setAttribute('opacity',r.toFixed(3));
document.getElementById('flow').setAttribute('opacity',(1-r).toFixed(3));
document.fonts.ready.then(()=>document.body.setAttribute('data-ready','1'));
</script>
</body></html>"""
open("og-anim.html", "w", encoding="utf-8").write(html)
print("ok")
