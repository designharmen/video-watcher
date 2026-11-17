# video-watcher

Bir videoyu Claude'un **senin gördüğün gibi izleyebileceği** pakete çevirir: görüntü (zaman damgalı kareler + kontakt sayfası) ve ses (zaman damgalı konuşma metni) tek bir `watch.md` raporunda birleşir. Claude bu raporu ve kareleri okuyarak videoyu "izlemiş" olur.

## Kurulum

```bash
git clone https://github.com/designharmen/video-watcher.git
cd video-watcher
pip install -r requirements.txt        # ffmpeg ayrıca kurulu olmalı
```

## Kullanım

```bash
python -m videowatcher.watch "https://www.youtube.com/shorts/9vn-T9b-o6Q"
python -m videowatcher.watch video.mp4 --every 2          # yerel dosya, 2 sn'de bir kare (varsayılan: süreye göre 3/10/15 sn)
python -m videowatcher.watch URL --force-whisper          # altyazı yerine Whisper
```

Çıktı: `watched/<video-id>/`

| Dosya | İçerik |
|---|---|
| `watch.md` | Kare + o aralıkta söylenenler, zaman çizelgesi halinde |
| `frames/tXXXX.XXs.jpg` | Sahne değişimi ve sabit aralıkla alınan kareler |
| `contact_sheet_NN.jpg` | 20 karelik sayfalar (uzun videoda çok sayfa) |
| `transcript.txt` | Zaman damgalı konuşma metni |
| `meta.json` | Başlık, kanal, süre, açıklama |

## Claude ile

Claude Code / Claude masaüstünde repo klasöründe: *"şu videoyu izle ve özetle: URL"* — `CLAUDE.md` Claude'a aracı çalıştırıp `watch.md`, `contact_sheet_NN.jpg` sayfalarını ve kareleri okumasını söyler.

## Nasıl çalışır

1. **yt-dlp** videoyu ve (varsa) altyazıları indirir.
2. **ffmpeg** sahne değişimlerinde ve en az `--every` saniyede bir kare çıkarır.
3. Altyazı yoksa **faster-whisper** sesi yazıya döker.
4. Kareler ve metin zaman çizelgesinde eşleştirilir → `watch.md`.
