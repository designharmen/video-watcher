// video-watcher · tarayıcı modu · adım 1: meta + zaman damgalı konuşma metni
// YouTube video/Shorts sayfasında javascript ile çalıştırılır. Altyazı isteği YouTube'un
// "pot" jetonunu gerektirdiği için önce oynatıcının altyazısını açtırır, sonra o isteği tekrar okur.
const sleep = ms => new Promise(r => setTimeout(r, ms));
const id = (location.pathname.match(/shorts\/([\w-]+)/) || [])[1] || new URLSearchParams(location.search).get('v');
const html = await fetch('/watch?v=' + id).then(r => r.text());
const pr = JSON.parse(html.match(/ytInitialPlayerResponse\s*=\s*(\{.+?\});(?:var|<\/script>)/s)[1]);
const vd = pr.videoDetails;
const tracks = (pr.captions?.playerCaptionsTracklistRenderer?.captionTracks || []).map(c => c.languageCode + (c.kind ? '(' + c.kind + ')' : ''));
const v = [...document.querySelectorAll('video')].find(x => x.duration > 0);
const findCap = () => performance.getEntriesByType('resource').map(e => e.name).find(n => n.includes('timedtext') && n.includes('pot='));
if (v) { v.muted = true; await v.play().catch(() => {}); }
// altyazı tercihi zaten açıksa oynatıcı isteği kendisi atar; kapatmamak için önce bekle
for (let i = 0; i < 4 && !findCap(); i++) await sleep(500);
if (!findCap() && tracks.length) {
  // düğmeye tıklamak her zaman çalışmıyor; oynatıcı API'si güvenilir
  const p = document.querySelector('#movie_player, #shorts-player');
  try { p.loadModule?.('captions'); p.setOption?.('captions', 'track', { languageCode: 'en' }); } catch (e) {}
  await sleep(1500);
  if (!findCap()) { try { p.toggleSubtitlesOn ? p.toggleSubtitlesOn() : p.toggleSubtitles(); } catch (e) { document.querySelector('.ytp-subtitles-button')?.click(); } }
  for (let i = 0; i < 16 && !findCap(); i++) await sleep(500);
}
let transcript = '(altyazı yok)';
const u = findCap();
if (u) {
  const d = await fetch(u).then(r => r.json());
  transcript = d.events.filter(e => e.segs && !e.aAppend)
    .map(e => '[' + (e.tStartMs / 1000).toFixed(1) + 's] ' + e.segs.map(s => s.utf8).join('').replace(/\n/g, ' ')).join('\n');
}
({ id, title: vd.title, author: vd.author, seconds: +vd.lengthSeconds, views: vd.viewCount,
   description: vd.shortDescription, keywords: vd.keywords, captionTracks: tracks, transcript });
