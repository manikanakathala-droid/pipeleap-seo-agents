# Share image and animation

Source for the link-preview image (currently `www.pipeleap.com/assets/og-pipeleap-2026-11-21.png`) and `assets/pipeleap-share.mp4` / `.gif` (animated version for posts, Slack, email).

**Current design (since 2026-11-21): `make_simple.py`** writes `og-simple.html`: only the wordmark ("Pipe" solid, "leap" filled with hero.svg) and the tagline "Less admin. More selling time." running from the descender of the final p. Render it exactly as below, using `og-simple.html` in place of `og-anim.html` and `--virtual-time-budget=4000`. Timeline: 0–2.3s streams converge on a wide panel; 2.3–3.5s the panel dissolves into the wordmark; 3.5–4.4s the tagline draws out from the p; hold to 5.2s.

Previous design: `make_anim_html.py` writes `og-anim.html`, a 1200×630 page whose state is set by `#t=<seconds>` (0 to 5.2). Copy `hero.svg` and `favicon.svg` from the site repo next to it, then render and encode:

```bash
python make_anim_html.py
mkdir frames
for i in $(seq 0 103); do
  t=$(awk "BEGIN{printf \"%.3f\", $i/20}")
  chrome --headless=new --hide-scrollbars --window-size=1200,630 --virtual-time-budget=3000 \
    --screenshot="frames/f$(printf %03d $i).png" "file:///<abs path>/og-anim.html#t=$t"
done
ffmpeg -framerate 20 -i frames/f%03d.png -vf "tpad=stop_mode=clone:stop_duration=1.5" -c:v libx264 -pix_fmt yuv420p -crf 18 pipeleap-share.mp4
ffmpeg -framerate 20 -i frames/f%03d.png -vf "tpad=stop_mode=clone:stop_duration=1.5,split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse" -loop 0 pipeleap-share.gif
cp frames/f103.png og-image.png   # final frame = link-preview image
```

Timeline: 0–2.4s streams draw in and converge; 2.4–3.6s the panel dissolves and the homepage wordmark resolves ("Pipe" solid, "leap" filled with hero.svg, mirrored, zoomed 2.4×); hold to 5.2s. Link previews on LinkedIn/X/Facebook are static, so the final frame is the og:image.

## Changing the image: always use a new filename

LinkedIn (and other platforms) cache preview images by URL, so replacing the file at the same URL keeps showing the old image even after Post Inspector. Save each new version under a new dated name (for example `assets/og-pipeleap-YYYY-MM-DD.png`), point `og:image` and `twitter:image` on every page at it, then run the homepage through linkedin.com/post-inspector.
