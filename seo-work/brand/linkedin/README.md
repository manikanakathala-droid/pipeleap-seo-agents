# LinkedIn company page banner

`pipeleap-linkedin-banner.png`: 2256 × 382 (2× LinkedIn's 1128 × 191 cover size, so it stays sharp on high-resolution screens).

- Headline "Less admin. More selling time." and the line "Sales productivity platform · works with the tools you already own", in the site's Stack Sans fonts and colours.
- The converging light streams from the share image fade in on the right.
- The left ~280px is kept empty because LinkedIn places the page logo over the bottom-left corner on desktop; the text sits in the centre, which stays visible when phones crop the sides.

Re-render: `python make_linkedin_banner.py`, then
`chrome --headless=new --hide-scrollbars --force-device-scale-factor=2 --window-size=1128,191 --virtual-time-budget=4000 --screenshot=pipeleap-linkedin-banner.png file:///<abs path>/linkedin-banner.html`
