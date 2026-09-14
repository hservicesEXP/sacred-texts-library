(() => {
  'use strict';

  const $ = s => document.querySelector(s);
  let index = [], roots = null, lemmas = null, concepts = null, loaded = false;

  const suraNames = ['', 'Al-Fatiha','Al-Baqarah','Ali Imran','An-Nisa','Al-Ma’idah','Al-An’am','Al-A’raf','Al-Anfal','At-Tawbah','Yunus','Hud','Yusuf','Ar-Ra’d','Ibrahim','Al-Hijr','An-Nahl','Al-Isra','Al-Kahf','Maryam','Ta-Ha','Al-Anbiya','Al-Hajj','Al-Mu’minun','An-Nur','Al-Furqan','Ash-Shu’ara','An-Naml','Al-Qasas','Al-Ankabut','Ar-Rum','Luqman','As-Sajdah','Al-Ahzab','Saba','Fatir','Ya-Sin','As-Saffat','Sad','Az-Zumar','Ghafir','Fussilat','Ash-Shura','Az-Zukhruf','Ad-Dukhan','Al-Jathiyah','Al-Ahqaf','Muhammad','Al-Fath','Al-Hujurat','Qaf','Adh-Dhariyat','At-Tur','An-Najm','Al-Qamar','Ar-Rahman','Al-Waqi’ah','Al-Hadid','Al-Mujadilah','Al-Hashr','Al-Mumtahanah','As-Saff','Al-Jumu’ah','Al-Munafiqun','At-Taghabun','At-Talaq','At-Tahrim','Al-Mulk','Al-Qalam','Al-Haqqah','Al-Ma’arij','Nuh','Al-Jinn','Al-Muzzammil','Al-Muddaththir','Al-Qiyamah','Al-Insan','Al-Mursalat','An-Naba','An-Nazi’at','Abasa','At-Takwir','Al-Infitar','Al-Mutaffifin','Al-Inshiqaq','Al-Buruj','At-Tariq','Al-A’la','Al-Ghashiyah','Al-Fajr','Al-Balad','Ash-Shams','Al-Layl','Ad-Duha','Ash-Sharh','At-Tin','Al-Alaq','Al-Qadr','Al-Bayyinah','Az-Zalzalah','Al-Adiyat','Al-Qari’ah','At-Takathur','Al-Asr','Al-Humazah','Al-Fil','Quraysh','Al-Ma’un','Al-Kawthar','Al-Kafirun','An-Nasr','Al-Masad','Al-Ikhlas','Al-Falaq','An-Nas'];
  const arabicNames = ['', 'الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الإنفطار','المطففين','الإنشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];

  const DIACRITICS = /[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g;
  const norm = s => String(s || '').normalize('NFD').replace(DIACRITICS,'').replace(/[إأآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ؤ/g,'و').replace(/ئ/g,'ي').replace(/ة/g,'ه').toLowerCase().normalize('NFC');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const setStatus = (t, k = '') => { const e = $('#searchStatus'); if (e) { e.textContent = t; e.className = `status ${k}`; } };

  function dataCandidates(name) {
    const base = new URL('data/', document.baseURI);
    return [
      `${name}.json`,
      `quran/${name}.json`,
      `surahs/${name}.json`,
      `surah/${name}.json`
    ].map(x => new URL(x, base));
  }

  async function get(name) {
    const errors = [];
    for (const url of dataCandidates(name)) {
      try {
        const r = await fetch(url, { cache: 'no-store', credentials: 'same-origin' });
        if (!r.ok) { errors.push(`${r.status} ${url.pathname}`); continue; }
        return await r.json();
      } catch (e) { errors.push(`${e.message || e} ${url.pathname}`); }
    }
    throw Error(`${name}: nessun percorso dati valido (${errors.join(' | ')})`);
  }

  async function loadIndex() {
    setStatus('Caricamento indice…');
    try {
      const candidates = [
        new URL('data/index.json', document.baseURI),
        new URL('data/quran/index.json', document.baseURI),
        new URL('data/search/index.json', document.baseURI)
      ];
      let raw, last;
      for (const u of candidates) {
        try {
          const r = await fetch(u, { cache: 'no-store', credentials: 'same-origin' });
          if (!r.ok) throw Error(`HTTP ${r.status}`);
          raw = await r.json(); break;
        } catch (e) { last = e; }
      }
      if (!raw) throw last || Error('Indice non trovato');

      index = Array.isArray(raw) ? raw : (raw.verses || raw.items || raw.index || []);
      if (!Array.isArray(index) || !index.length) throw Error('Indice Corano non valido');

      loaded = true;
      setStatus(`${index.length.toLocaleString('it-IT')} versetti · pronto`, 'ok');
      renderSuras();
    } catch (e) {
      console.error('[Quran search]', e);
      setStatus('Indice non disponibile', 'error');
      $('#retrySearch')?.removeAttribute('hidden');
    }
  }

  async function loadAux(kind) {
    if (kind === 'root' && !roots) roots = await get('roots.json');
    if (kind === 'lemma' && !lemmas) lemmas = await get('lemmas.json');
    if (kind === 'concept' && !concepts) concepts = await get('concepts.json');
  }

  const byRefs = refs => {
    const set = new Set(refs);
    return index.filter(x => set.has(x.r || x.ref));
  };

  function refResults(q) {
    const m = q.trim().match(/^(\d{1,3})\s*[:.]\s*(\d{1,3})$/);
    return m ? index.filter(x => (x.s ?? x.surah) === +m[1] && (x.v ?? x.verse) === +m[2]) : [];
  }

  function rootKey(q) {
    const raw = q.trim().replace(/[-–—_\s]/g,'');
    const aliases = { 'khlq':'xlq','rhm':'rHm','r-h-m':'rHm','ktb':'ktb','k-t-b':'ktb','slm':'slm','s-l-m':'slm','alh':'Alh' };
    return aliases[raw.toLowerCase()] || raw;
  }

  function nameKey(q) { return norm(q).replace(/[’'\-\s]/g,''); }

  function suraResults(q) {
    const k = nameKey(q);
    const hit = suraNames.findIndex((n,i) => i && nameKey(n) === k);
    if (hit > 0) return index.filter(x => (x.s ?? x.surah) === hit);
    const arab = arabicNames.findIndex((n,i) => i && nameKey(n) === k);
    return arab > 0 ? index.filter(x => (x.s ?? x.surah) === arab) : [];
  }

  async function doSearch(q, mode) {
    if (!loaded || !q.trim()) return [];
    if (mode === 'ref') return refResults(q);
    if (mode === 'root') { await loadAux('root'); return byRefs(roots[rootKey(q)]?.refs || []); }
    if (mode === 'lemma') { await loadAux('lemma'); const key = q.trim(); return byRefs(lemmas[key] || lemmas[norm(key)] || []); }
    if (/^\d{1,3}\s*[:.]\s*\d{1,3}$/.test(q.trim())) return refResults(q);

    const named = suraResults(q);
    if (named.length) return named;

    if (/^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s'-]*$/.test(q.trim())) {
      await loadAux('concept');
      const rs = concepts[norm(q)] || concepts[q.trim().toLocaleLowerCase('it-IT')];
      if (rs) {
        await loadAux('root');
        return byRefs([...new Set(rs.flatMap(k => roots[k]?.refs || []))]);
      }
    }

    const n = norm(q);
    return n ? index.filter(x => (x.q || x.text || '').includes(n)).slice(0, 120) : [];
  }

  async function renderSearch(q, mode) {
    const box = $('#results');
    if (!box) return;
    box.innerHTML = '<div class="loading-row"><span class="spinner"></span>Ricerca in corso…</div>';
    try {
      const res = await doSearch(q, mode);
      if (!res.length) {
        box.innerHTML = '<div class="empty"><strong>Nessun risultato</strong><span>Prova testo arabo, nome di sura, radice/lemma Buckwalter o un riferimento come 2:255.</span></div>';
        return;
      }
      box.innerHTML =
        `<div class="result-head"><strong>${res.length}${res.length === 120 ? '+' : ''} risultati</strong><span>${esc(q)}</span></div>` +
        res.map(x => {
          const r = x.r || x.ref || `${x.s || x.surah}:${x.v || x.verse}`;
          const s = x.s || x.surah;
          return `<a class="result-card" href="reader.html?ref=${encodeURIComponent(r)}"><div><span class="result-ref">${esc(r)}</span><span class="result-sura">${esc(suraNames[s] || '')} · ${esc(arabicNames[s] || '')}</span></div><p lang="ar" dir="rtl">${esc(x.t || x.text || '')}</p></a>`;
        }).join('');
    } catch (e) {
      console.error(e);
      box.innerHTML = '<div class="empty error-box"><strong>Ricerca non disponibile</strong><span>Un indice secondario non è riuscito a caricarsi. Riprova.</span></div>';
    }
  }

  function renderSuras() {
    const g = $('#suraGrid');
    if (!g || !index.length) return;
    const counts = Array(115).fill(0);
    index.forEach(x => { const s = +(x.s ?? x.surah); if (s >= 1 && s <= 114) counts[s]++; });
    g.innerHTML = Array.from({ length: 114 }, (_, i) => {
      const s = i + 1;
      return `<a class="sura-card reveal" href="reader.html?surah=${s}">
        <span class="sura-no">${String(s).padStart(3,'0')}</span>
        <span class="sura-name">${esc(suraNames[s])}</span>
        <span class="sura-ar" lang="ar" dir="rtl">${esc(arabicNames[s])}</span>
        <span class="sura-count">${counts[s]} ayat</span>
        <span class="sura-arrow">↗</span>
      </a>`;
    }).join('');
    observeReveals();
  }

  function runQuick(btn) {
    $('#query').value = btn.dataset.query;
    if (btn.dataset.mode) $('#searchMode').value = btn.dataset.mode;
    else if (/^\d/.test(btn.dataset.query)) $('#searchMode').value = 'ref';
    else $('#searchMode').value = 'text';
    $('#searchForm').requestSubmit();
  }

  $('#searchForm')?.addEventListener('submit', e => {
    e.preventDefault();
    if (!loaded) { setStatus('Indice ancora in caricamento', 'error'); return; }
    renderSearch($('#query').value, $('#searchMode').value);
  });

  document.querySelectorAll('[data-query]').forEach(b => b.addEventListener('click', () => runQuick(b)));
  $('#retrySearch')?.addEventListener('click', loadIndex);
  $('#randomBtn')?.addEventListener('click', () => {
    if (index.length) {
      const x = index[Math.floor(Math.random() * index.length)];
      location.href = `reader.html?ref=${encodeURIComponent(x.r || x.ref)}`;
    }
  });

  const openDialog = id => $(id)?.showModal();
  $('#keeperBtn')?.addEventListener('click', () => openDialog('#keeperDialog'));
  $('#keeperBtn2')?.addEventListener('click', () => openDialog('#keeperDialog'));
  $('#scholarBtn')?.addEventListener('click', () => openDialog('#scholarDialog'));

  function hideIntro() {
    const i = $('#intro');
    if (i) {
      i.classList.add('hidden');
      try { sessionStorage.setItem('introSeen', '1'); } catch {}
    }
  }

  $('#enter')?.addEventListener('click', () => {
    const i = $('#intro');
    i?.classList.add('open');
    setTimeout(hideIntro, 1350);
  });
  $('#skipIntro')?.addEventListener('click', hideIntro);

  try { if (sessionStorage.getItem('introSeen') === '1') hideIntro(); } catch {}

  function observeReveals() {
    const els = document.querySelectorAll('.reveal:not(.seen)');
    if (!('IntersectionObserver' in window)) { els.forEach(e => e.classList.add('seen')); return; }
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('seen'); io.unobserve(e.target); }
    }), { threshold: .08 });
    els.forEach(e => io.observe(e));
  }
  observeReveals();

  const scene = $('#scene');
  window.addEventListener('pointermove', e => {
    if (!scene || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const x = (e.clientX / innerWidth - .5) * 2, y = (e.clientY / innerHeight - .5) * 2;
    scene.style.setProperty('--mx', `${x * 10}deg`);
    scene.style.setProperty('--my', `${y * 7}deg`);
  }, { passive: true });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js?v=6', { updateViaCache: 'none' })
      .then(r => r.update()).catch(console.warn);
  }

  loadIndex();
})();
