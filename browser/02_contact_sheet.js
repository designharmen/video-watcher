// video-watcher · tarayıcı modu · adım 2: kontakt sayfası (görüntüyü "görmek" için)
// Sayfadaki <video>'yu belirli anlara sarar, kareleri canvas'a çizer ve ekranın üstüne
// tam yükseklikte bir görsel olarak yerleştirir. Ardından ekran görüntüsü alınır.
// Değişkenler: N = kare sayısı (varsayılan 20), CROP = [y, h] video pikseli cinsinden kırpma
// (ör. [560, 330] alt yazı bandını büyütmek için), TIMES = belirli saniyeler listesi.
const N = window.VW_N || 20, CROP = window.VW_CROP || null, COLS = CROP ? 1 : 5;
const v = [...document.querySelectorAll('video')].find(x => x.duration > 0);
v.pause();
const times = window.VW_TIMES || Array.from({ length: N }, (_, i) => +(0.5 + i * (v.duration - 1) / (N - 1)).toFixed(1));
const vw = v.videoWidth, vh = v.videoHeight;
const sy = CROP ? CROP[0] : 0, sh = CROP ? CROP[1] : vh;
const W = CROP ? Math.min(vw, 900) : 160, H = Math.round(W * sh / vw), L = 14;
const c = document.createElement('canvas');
c.width = W * COLS; c.height = Math.ceil(times.length / COLS) * (H + L);
const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
for (let i = 0; i < times.length; i++) {
  v.currentTime = times[i];
  await new Promise(r => v.addEventListener('seeked', r, { once: true }));
  await new Promise(r => setTimeout(r, 150));
  const x = (i % COLS) * W, y = Math.floor(i / COLS) * (H + L);
  g.drawImage(v, 0, sy, vw, sh, x, y + L, W, H);
  g.fillStyle = '#000'; g.font = '11px sans-serif'; g.fillText(times[i] + 's', x + 3, y + 11);
}
document.getElementById('__vw')?.remove();
const img = new Image(); img.id = '__vw'; img.src = c.toDataURL('image/jpeg', 0.88);
Object.assign(img.style, { position: 'fixed', top: 0, left: 0, zIndex: 2147483647, maxHeight: '100vh', maxWidth: '100vw', background: '#fff' });
img.onclick = () => img.remove();
document.body.appendChild(img);
({ duration: v.duration, frames: times.length, sheet: c.width + 'x' + c.height });
// Temizlik: document.getElementById('__vw')?.remove()
