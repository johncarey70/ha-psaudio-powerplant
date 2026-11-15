# Official PS Audio logo sources

The brand icons use the official PS Audio blue sine-wave mark (a rounded
blue square with a transparent wave cutout). That is the same mark shown
as the site icon for the official [PS Audio forum](https://forum.psaudio.com/)
(favicon and apple-touch-icon), which is what browsers display in search
suggestions.

Primary source, 1000×1000 palette PNG, official forum upload of
`PS-AUDIO-LOGO-BLUE.png`:

https://us1.discourse-cdn.com/flex015/uploads/psaudio/original/3X/f/0/f0618c574cd33d419ec538679491374dc01db460.png

A December 2022 post on the official forum identifies that file as the
copy of the then-current website logo at
`https://www.psaudio.com/wp-content/uploads/2019/09/PS-AUDIO-LOGO-BLUE.png`.
That WordPress path now 404s after the site moved to Shopify. The live
psaudio.com favicon is a later black-on-transparent shop file, not this
blue mark.

The same blue artwork is also used as the forum's published site icons:

- Apple touch icon (180×180 JPEG):
  https://us1.discourse-cdn.com/flex015/uploads/psaudio/optimized/1X/5ea5692ffa1b7e5a90ca80a87d985eb547288f31_2_180x180.jpg
- Favicon (32×32 PNG):
  https://us1.discourse-cdn.com/flex015/uploads/psaudio/optimized/1X/e6b5cf4be3836036972d47656bbbde7783769c6d_2_32x32.png

The high-resolution PNG is stored here as base64 so it can be committed
as text. `.github/scripts/make_brand_icons.py` decodes it and resizes to
the Home Assistant brand sizes (256×256 `icon.png` and 512×512
`icon@2x.png`). `dark_icon` / `dark_icon@2x` use the same official blue
asset. The wave and rounded-corner padding are transparent in the source,
so the wave reads light on a light UI and dark on a dark UI.

`logo.png` / `logo@2x.png` are omitted because the official mark is
square; Home Assistant uses the icon as the logo fallback.
