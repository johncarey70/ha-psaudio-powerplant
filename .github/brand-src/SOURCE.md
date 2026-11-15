# Official PS Audio logo sources

The brand icons are built from the official PS Audio sine-wave mark used on [psaudio.com](https://www.psaudio.com/):

- Black (site header logo, favicon, and JSON-LD `"logo"`; for light backgrounds):
  https://www.psaudio.com/cdn/shop/files/ps-logo-icon-black.png?v=1758450286
- White (same artwork, for dark backgrounds):
  https://www.psaudio.com/cdn/shop/files/ps-logo-icon.png

Original assets are 270×270 RGBA PNGs. This folder stores base64 copies so they can be committed as text. `.github/scripts/make_brand_icons.py` decodes them and resizes to the Home Assistant brand sizes (256×256 and 512×512).

`logo.png` / `logo@2x.png` are omitted because the official mark is square; Home Assistant uses the icon as the logo fallback.
