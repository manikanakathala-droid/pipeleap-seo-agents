"""Simple share image/animation: only the Pipeleap wordmark and a tagline that runs out of the
descender of the final "p". State is set by #t=<seconds> (0 to 5.2)."""
import random

random.seed(7)
ff = open("fontfaces.css", encoding="utf-8").read()

CW, CH = 1200, 630
FS = 180                      # wordmark font size
X0, BASE = 92, 352            # wordmark start x and baseline
PX, PY, PW, PH = 60, 120, 1080, 330   # panel used during the stream phase
CY = PY + PH * 0.62           # where streams converge

paths = []
for i in range(34):
    y0 = PY - 60 + i * (PH + 120) / 33 + random.uniform(-6, 6)
    y1 = CY + (i - 16.5) * 2.0 + random.uniform(-3, 3)
    c1x, c2x = PX + random.uniform(300, 440), PX + random.uniform(520, 700)
    d = f"M{PX - 20} {y0:.1f} C{c1x:.1f} {y0:.1f} {c2x:.1f} {y1:.1f} {PX + PW + 20} {y1:.1f}"
    r = random.random()
    if i in (10, 24):
        st, w, op = "#14151C", 2.8, 0.85
    elif r < 0.25:
        st, w, op = "#3E2FD0", 1.8, 0.7
    else:
        st, w, op = "#FFFFFF", random.choice([1.3, 1.8, 2.4]), random.uniform(0.45, 0.9)
    paths.append((d, st, w, op))
lines = "\n".join(f'<path class="ln" d="{d}" stroke="{s}" stroke-width="{w}" stroke-opacity="{o:.2f}" fill="none" stroke-linecap="round"/>' for d, s, w, o in paths)
streaks = "\n".join(f'<path class="st" d="{d}" stroke="#FFFFFF" stroke-width="{w + 1.4}" fill="none" stroke-linecap="round"/>' for k, (d, s, w, o) in enumerate(paths) if k % 3 == 1)

word = lambda id_, pipe, leap: (f'<text id="{id_}" class="word" x="{X0}" y="{BASE}">'
                                f'<tspan fill="{pipe}">Pipe</tspan><tspan fill="{leap}">leap</tspan></text>')

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{ff}
*{{margin:0;padding:0}}
html,body{{width:{CW}px;height:{CH}px;overflow:hidden;background:#F7F7FB}}
body:before{{content:"";position:absolute;inset:0;background:radial-gradient(60% 80% at 0% 0%,rgba(101,88,245,.10),transparent 60%),radial-gradient(50% 70% at 100% 100%,rgba(59,130,246,.10),transparent 60%)}}
svg{{position:absolute;inset:0}}
.word{{font-family:"Stack Sans Headline","Stack Sans Headline Fallback",Arial,sans-serif;font-weight:600;font-size:{FS}px;letter-spacing:-8.5px}}
.tag{{font-family:"Stack Sans Notch","Stack Sans Notch Fallback",Arial,sans-serif;font-weight:500;font-size:22px;letter-spacing:1.5px;text-transform:uppercase}}
</style></head><body>
<svg width="{CW}" height="{CH}" viewBox="0 0 {CW} {CH}">
<g id="all">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6558F5"/><stop offset=".55" stop-color="#5B7BF7"/><stop offset="1" stop-color="#8CC4FF"/></linearGradient>
    <radialGradient id="glow" cx=".82" cy=".6" r=".5"><stop offset="0" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <filter id="sh" x="-10%" y="-10%" width="120%" height="140%"><feDropShadow dx="0" dy="22" stdDeviation="22" flood-color="#14151C" flood-opacity=".22"/></filter>
    <mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{CW}" height="{CH}">
      <rect id="panelMask" class="fixed" x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="30" fill="#fff"/>
      {word("wm1", "none", "#fff")}
    </mask>
    <mask id="m2" maskUnits="userSpaceOnUse" x="0" y="0" width="{CW}" height="{CH}">{word("wm2", "none", "#fff")}</mask>
    <clipPath id="tagClip"><rect id="tagClipRect" x="0" y="0" width="0" height="{CH}"/></clipPath>
  </defs>
  <rect id="shadowRect" class="fixed" x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="30" fill="#F7F7FB" filter="url(#sh)"/>
  <g mask="url(#m)">
    <g class="fixed"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="url(#bg)"/>
    <rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="url(#glow)"/>
    <g id="flow"><g>{lines}</g><g>{streaks}</g></g></g>
  </g>
  <g mask="url(#m2)"><g id="heroWrap" opacity="0"><image id="heroImg" href="hero.svg" preserveAspectRatio="xMidYMid slice"/></g></g>
  <g id="solid" opacity="0">{word("wm3", "#14151C", "none")}</g>
  <g clip-path="url(#tagClip)">
    <line id="tagLine" stroke="#6558F5" stroke-width="3" stroke-linecap="round"/>
    <text id="tag" class="tag"><tspan fill="#14151C">Less admin.</tspan><tspan dx="14" fill="#6558F5">More selling time.</tspan></text>
  </g>
</g>
</svg>
<script>
const T = parseFloat((location.hash.match(/t=([0-9.]+)/)||[])[1]||'5.2');
const clamp=x=>Math.max(0,Math.min(1,x));
const ease=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
function draw(){{
  document.querySelectorAll('.ln').forEach((p,i)=>{{const L=p.getTotalLength();p.style.strokeDasharray=L;p.style.strokeDashoffset=L*(1-ease(clamp((T-0.05-i*0.03)/1.25)));}});
  document.querySelectorAll('.st').forEach((p,i)=>{{const L=p.getTotalLength(),seg=90;p.style.strokeDasharray=seg+' '+(L+seg);const st=0.9+i*0.15;
    p.style.strokeDashoffset=T<st?seg:seg-((T-st)*L/1.5)%(L+seg*2);p.style.strokeOpacity=T<st?0:0.9;}});
  const r=ease(clamp((T-2.3)/1.2));
  document.getElementById('panelMask').setAttribute('fill-opacity',(1-r).toFixed(3));
  document.getElementById('shadowRect').setAttribute('opacity',(1-r).toFixed(3));
  document.getElementById('flow').setAttribute('opacity',(1-r).toFixed(3));
  document.getElementById('solid').setAttribute('opacity',r.toFixed(3));
  const wm=document.getElementById('wm1');
  // artwork inside "leap", as on the homepage (mirrored, zoomed)
  const sx=wm.getStartPositionOfChar(4).x, ex=wm.getEndPositionOfChar(7).x;
  const yT={BASE}-0.98*{FS}, yB={BASE}+0.30*{FS}, cx=(sx+ex)/2, cy=(yT+yB)/2;
  const hi=document.getElementById('heroImg');
  hi.setAttribute('x',sx);hi.setAttribute('y',yT);hi.setAttribute('width',ex-sx);hi.setAttribute('height',yB-yT);
  hi.setAttribute('transform',`translate(${{cx}} ${{cy}}) scale(-2.2 2.2) translate(${{-cx}} ${{-cy}})`);
  document.getElementById('heroWrap').setAttribute('opacity',r.toFixed(3));
  // tagline runs out of the descender of the final "p"
  const pBox=wm.getExtentOfChar(7);
  const stemX=pBox.x+0.215*{FS};               // right edge of the p's stem
  const tipY={BASE}+0.205*{FS};                // bottom of the descender
  const tag=document.getElementById('tag'), line=document.getElementById('tagLine');
  tag.setAttribute('x',stemX+16); tag.setAttribute('y',tipY);
  const tagEnd=stemX+16+tag.getComputedTextLength()+14;
  line.setAttribute('x1',stemX-2);line.setAttribute('x2',stemX+8);line.setAttribute('y1',tipY-8);line.setAttribute('y2',tipY-8);
  line.setAttribute('stroke-opacity','0');
  // centre wordmark + tagline on the canvas; keep the panel fixed to the canvas
  const left={X0}, right=tagEnd-14, top={BASE}-0.74*{FS}, bottom=tipY;
  const dx={CW}/2-(left+right)/2, dy={CH}/2-(top+bottom)/2;
  document.getElementById('all').setAttribute('transform',`translate(${{dx}} ${{dy}})`);
  document.querySelectorAll('.fixed').forEach(e=>e.setAttribute('transform',`translate(${{-dx}} ${{-dy}})`));
  const k=ease(clamp((T-3.5)/0.9));
  const clip=document.getElementById('tagClipRect');clip.setAttribute('x',stemX-4);clip.setAttribute('width',(tagEnd-stemX+8)*k);
  document.body.setAttribute('data-ready','1');
}}
document.fonts.ready.then(draw);
</script>
</body></html>"""
open("og-simple.html", "w", encoding="utf-8").write(html)
print("ok")
