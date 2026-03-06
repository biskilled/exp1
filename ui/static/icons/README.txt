Add the following PNG icon files to this directory:
  icon-72.png   (72x72)
  icon-96.png   (96x96)
  icon-128.png  (128x128)
  icon-192.png  (192x192)  ← required for Android PWA install
  icon-512.png  (512x512)  ← required for splash screen

Generate from a single 1024x1024 source image:
  ImageMagick: convert icon.png -resize 192x192 icon-192.png
  Tauri CLI:   npm run tauri icon icon.png
  Online:      https://realfavicongenerator.net
