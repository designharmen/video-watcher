# Video izleme talimatı

Kullanıcı (Haris) bir video linki ya da dosyası verdiğinde videoyu **kendin izle** ve içeriğini detaylı analiz et. Ona adım yaptırma.

## Yol seçimi

- **Shell'den videoya erişim varsa** (yerel makine / açık ağ): `python -m videowatcher.watch "<URL veya dosya>"` → `watched/<id>/watch.md`, `contact_sheet_*.jpg` (20 karelik sayfalar), önemli `frames/*.jpg` dosyalarını oku/aç.
- **Shell YouTube'a erişemiyorsa** (bulut çalışma alanı, 403): **tarayıcı modu** — uygulama içi tarayıcıda (yoksa Claude in Chrome) linki aç:
  1. `browser/01_meta_captions.js` içeriğini sayfada javascript olarak çalıştır → başlık, kanal, süre, açıklama, zaman damgalı konuşma metni.
  2. `browser/02_contact_sheet.js` çalıştır, ekran görüntüsü al → 20 karelik zaman damgalı ızgara (bir sayfa). Kare yoğunluğu:
     - ≤ 3 dk: tek sayfa yeter.
     - 3–20 dk: ~10 sn'de bir kare → `window.VW_FROM / VW_TO` ile 200 sn'lik pencereler, sayfa sayfa.
     - 20 dk–2 sa: ~15 sn'de bir kare → 300 sn'lik pencereler (1 saat ≈ 12 sayfa, 240 kare). Konuşma metni ana kaynak; kareler ekranda ne gösterildiğini doğrular.
     - Konuşmada ekrana atıf yapılan anlar ("burada görüyorsunuz", kod, tablo, repo adı) için `window.VW_TIMES=[...]` ile hedefli kareler al; küçük yazı için `window.VW_CROP=[y,h]` ile kırpıp büyüt.
  3. Bitince `document.getElementById('__vw')?.remove()`.
  - Altyazı yoksa: konuşmayı duyamadığını açıkça söyle; ekrandaki yazılar + açıklama + kareler üzerinden analiz et.
  - Instagram/TikTok/X: aynı `02` betiği sayfadaki `<video>` ile çalışır; meta için `get_page_text` kullan.

## Aktarım (Türkçe)

1. Videonun konusu ve kimin yaptığı (1–2 cümle).
2. Zaman sırasıyla ne gösterildiği ve söylendiği; ekrandaki önemli yazılar, rakamlar, arayüzler.
3. Bahsedilen her araç/repo/ürün: tam adı, repo yolu veya linki (gerekirse web'de doğrula).
4. Haris'in işine (mimarlık, BIM/Revit, HARSAY GROUP, yazılım) somut etkisi: hangisi işe yarar, neden.
5. Videonun iddialarında abartı/eksik varsa belirt.
