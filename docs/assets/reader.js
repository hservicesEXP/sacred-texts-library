(() => {
  'use strict';

  const $ = s => document.querySelector(s);
  const params = new URLSearchParams(location.search);
  const refParam = params.get('ref');
  const surahParam = params.get('surah');

  let surah = Math.max(1, Math.min(114, Number(surahParam || refParam?.split(':')[0] || 1) || 1));
  let ref = refParam, data = null, activeRef = null;
  let loadToken = 0;

  const names = ['', 'الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الإنفطار','المطففين','الإنشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];

  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const getStore = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
  const putStore = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };

  function setStatus(message, error = false) {
    const meta = $('#suraMeta');
    if (meta) {
      meta.textContent = message;
      meta.classList.toggle('load-error', !!error);
    }
  }

  function dataCandidates(n) {
    const p = String(n);
    const z = String(n).padStart(3, '0');
    const base = new URL('./', document.baseURI);
    const surah = p;
    const primary = `data/${surah}.json`;
    return [
      primary,
      `data/${z}.json`,
      `data/surah_${p}.json`,
      `data/surah_${z}.json`,
      `data/surahs/${p}.json`,
      `data/surahs/${z}.json`,
      `data/surah/surah_${p}.json`,
      `data/surah/surah_${z}.json`,
      `data/quran/${p}.json`,
      `data/quran/${z}.json`,
      `data/quran/surah_${p}.json`,
      `data/quran/surah_${z}.json`
    ].map(x => new URL(x, base));
  }

  async function fetchJson(url) {
    const r = await fetch(url, { cache: 'no-store', credentials: 'same-origin' });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText} · ${url.pathname}`);
    const json = await r.json();
    if (!json || typeof json !== 'object') throw new Error(`JSON non valido · ${url.pathname}`);
    return json;
  }

  function normalizeSurah(raw, n) {
    let ayas = raw.ayas || raw.ayahs || raw.verses || raw.data?.ayas || raw.data?.ayahs || raw.data?.verses;
    if (!Array.isArray(ayas) && Array.isArray(raw)) ayas = raw;
    if (!Array.isArray(ayas)) throw new Error('Struttura dati: array dei versetti non trovato');

    ayas = ayas.map((a, i) => ({
      ...a,
      v: Number(a.v ?? a.verse ?? a.number ?? a.verseNumber ?? i + 1),
      text: a.text ?? a.arabic ?? a.text_uthmani ?? a.aya ?? ''
    })).filter(a => Number.isFinite(a.v));

    return {
      ...raw,
      name: raw.name || raw.name_ar || raw.nameArabic || names[n],
      ayas
    };
  }

  async function load() {
    const token = ++loadToken;
    const tried = [];

    try {
      $('#suraTitle').textContent = 'Caricamento…';
      $('#suraNumber').textContent = `SURA ${surah}`;

      let lastError;
      for (const u of dataCandidates(surah)) {
        try {
          tried.push(u.pathname);
          const raw = await fetchJson(u);
          data = normalizeSurah(raw, surah);
          break;
        } catch (e) {
          lastError = e;
        }
      }

      if (token !== loadToken || !data) {
        throw lastError || new Error('Nessun file dati trovato');
      }

      $('#suraTitle').textContent = data.name || names[surah];
      setStatus(`${data.ayas.length} versetti · testo arabo Uthmani · analisi morfologica disponibile dove presente`);
      renderNav();
      render();
      if (refParam) focusRef(refParam);

      // Keep the exact working source discoverable for diagnostics.
      document.documentElement.dataset.quranDataReady = '1';
    } catch (e) {
      console.error('[Quran reader] caricamento fallito', e);
      document.documentElement.dataset.quranDataReady = '0';
      $('#suraTitle').textContent = 'Impossibile caricare la sura';
      setStatus('Dati della sura non raggiungibili. Verifica che i JSON siano inclusi nel deploy GitHub Pages.', true);
      const box = $('#verses');
      if (box) {
        box.innerHTML = `<div class="empty error-box">
          <strong>Dati non disponibili</strong>
          <span>Il lettore ha provato ${tried.length} percorsi senza trovare un JSON valido.</span>
          <button class="ghost" type="button" id="retryReader">Riprova</button>
        </div>`;
        $('#retryReader')?.addEventListener('click', load, { once: true });
      }
    }
  }

  function renderNav() {
    $('#suraSelect').innerHTML = Array.from({ length: 114 }, (_, i) =>
      `<option value="${i + 1}" ${i + 1 === surah ? 'selected' : ''}>${i + 1}. ${esc(names[i + 1])}</option>`
    ).join('');
  }

  function render() {
    const box = $('#verses');
    if (!box || !data) return;

    box.innerHTML = data.ayas.map(a => {
      const words = (a.words || []).map((w, i) =>
        `<span class="word" tabindex="0" role="button" data-v="${a.v}" data-w="${w.n ?? i + 1}" title="Apri morfologia">${esc(w.text)}</span>`
      ).join(' ');

      return `<article class="verse" id="v-${surah}-${a.v}" data-ref="${surah}:${a.v}">
        <div class="verse-ref">
          <span>${surah}:${a.v}</span>
          <div class="verse-tools">
            <button class="ghost" data-act="copy" data-v="${a.v}" type="button">Copia</button>
            <button class="ghost" data-act="speak" data-v="${a.v}" type="button">Ascolta</button>
            <button class="ghost" data-act="note" data-v="${a.v}" type="button">Nota</button>
            <button class="ghost" data-act="bookmark" data-v="${a.v}" type="button">Segna</button>
          </div>
        </div>
        <div class="verse-text" lang="ar" dir="rtl">${words || esc(a.text)}</div>
      </article>`;
    }).join('');

    box.onclick = handleClick;
    box.onkeydown = e => {
      if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('word')) {
        e.preventDefault();
        showMorph(+e.target.dataset.v, +e.target.dataset.w);
      }
    };
    updateBookmarkButtons();
  }

  const verse = v => data?.ayas.find(a => a.v === v);

  function focusRef(r) {
    const m = String(r).match(/^(\d+):(\d+)$/);
    if (!m) return;
    const target = document.getElementById(`v-${m[1]}-${m[2]}`);
    if (target) {
      setTimeout(() => {
        target.scrollIntoView({ block: 'center', behavior: 'smooth' });
        target.classList.add('flash');
        setTimeout(() => target.classList.remove('flash'), 1500);
      }, 120);
    }
  }

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const t = document.createElement('textarea');
      t.value = text;
      document.body.appendChild(t);
      t.select();
      const ok = document.execCommand('copy');
      t.remove();
      return ok;
    }
  }

  function handleClick(e) {
    const w = e.target.closest('.word');
    const b = e.target.closest('button');
    if (w) return showMorph(+w.dataset.v, +w.dataset.w);
    if (!b) return;

    const v = +b.dataset.v, a = verse(v);
    if (b.dataset.act === 'speak') speak(a?.text || '');
    if (b.dataset.act === 'copy') copy(a?.text || '').then(ok => {
      b.textContent = ok ? 'Copiato' : 'Copia';
      setTimeout(() => b.textContent = 'Copia', 1200);
    });
    if (b.dataset.act === 'note') openNote(v);
    if (b.dataset.act === 'bookmark') toggleBookmark(`${surah}:${v}`);
  }

  function showMorph(v, wi) {
    const a = verse(v), w = a?.words?.find(x => x.n === wi);
    if (!w) return;
    $('#morphTitle').textContent = `${surah}:${v} · parola ${wi}`;
    const seg = w.segments || [];
    $('#morphBody').innerHTML =
      `<div class="morph-word" lang="ar" dir="rtl">${esc(w.text)}</div>` +
      (seg.length
        ? seg.map(s => `<div class="morph-row"><div><div class="tag">${esc(s.pos || s.tag || '—')}</div></div>
          <div><div>Forma: <code>${esc(s.form || '—')}</code></div>
          <div>Lemma: <code>${esc(s.lemma || '—')}</code></div>
          <div>Radice: <code>${esc(s.root || '—')}</code></div>
          <div class="muted">${esc(s.features || '')}</div></div></div>`).join('')
        : '<p class="muted">Non è presente un’annotazione morfologica per questa posizione nel corpus.</p>');
    $('#morphDialog').showModal();
  }

  function speak(text) {
    if (!('speechSynthesis' in window)) {
      alert('Sintesi vocale non disponibile su questo dispositivo.');
      return;
    }
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'ar';
    speechSynthesis.speak(u);
  }

  function toggleBookmark(r) {
    let a = getStore('quran-bookmarks', []);
    a = a.includes(r) ? a.filter(x => x !== r) : [...a, r];
    putStore('quran-bookmarks', a);
    updateBookmarkButtons();
  }

  function updateBookmarkButtons() {
    const set = new Set(getStore('quran-bookmarks', []));
    document.querySelectorAll('[data-act="bookmark"]').forEach(b => {
      const yes = set.has(`${surah}:${b.dataset.v}`);
      b.textContent = yes ? 'Salvato' : 'Segna';
      b.setAttribute('aria-pressed', yes);
    });
  }

  function openNote(v) {
    activeRef = `${surah}:${v}`;
    const n = getStore('quran-notes', {})[activeRef] || '';
    $('#noteRef').textContent = activeRef;
    $('#noteText').value = n;
    $('#deleteNote').style.visibility = n ? 'visible' : 'hidden';
    $('#noteDialog').showModal();
  }

  $('#noteForm')?.addEventListener('submit', e => {
    e.preventDefault();
    const n = getStore('quran-notes', {}), text = $('#noteText').value.trim();
    if (text) n[activeRef] = text; else delete n[activeRef];
    putStore('quran-notes', n);
    $('#noteDialog').close();
  });
  $('#noteClose')?.addEventListener('click', () => $('#noteDialog').close());
  $('#deleteNote')?.addEventListener('click', () => {
    $('#noteText').value = '';
    $('#noteForm').requestSubmit();
  });

  $('#suraSelect')?.addEventListener('change', e => {
    location.href = `reader.html?surah=${e.target.value}`;
  });

  $('#jumpBtn')?.addEventListener('click', () => {
    const v = +$('#verseJump').value;
    if (!v || !verse(v)) return;
    ref = `${surah}:${v}`;
    history.replaceState(null, '', `reader.html?ref=${encodeURIComponent(ref)}`);
    focusRef(ref);
  });

  $('#verseJump')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') $('#jumpBtn')?.click();
  });

  $('#prevSura')?.addEventListener('click', () => {
    if (surah > 1) location.href = `reader.html?surah=${surah - 1}`;
  });
  $('#nextSura')?.addEventListener('click', () => {
    if (surah < 114) location.href = `reader.html?surah=${surah + 1}`;
  });
  $('#bookmarkCurrent')?.addEventListener('click', () =>
    refParam ? toggleBookmark(refParam) : alert('Apri un versetto specifico per usare questo comando.')
  );

  $('#showNotes')?.addEventListener('click', () => {
    const n = getStore('quran-notes', {}), b = getStore('quran-bookmarks', []);
    const keys = [...new Set([...Object.keys(n), ...b])].sort((a, z) => a.localeCompare(z, undefined, { numeric: true }));
    $('#localList').innerHTML = keys.length
      ? keys.map(r => `<div class="notes-item"><a href="reader.html?ref=${encodeURIComponent(r)}">${r}</a>${n[r] ? `<div>${esc(n[r])}</div>` : '<div class="muted">Segnalibro</div>'}</div>`).join('')
      : '<p class="muted">Nessuna nota o segnalibro locale.</p>';
    $('#localDialog').showModal();
  });

  const readerScale = getStore('quran-reader-scale', 'normal');
  if (readerScale === 'large') document.documentElement.style.setProperty('--reader-scale', 'clamp(2rem,5.4vw,2.9rem)');
  if (readerScale === 'small') document.documentElement.style.setProperty('--reader-scale', 'clamp(1.55rem,4vw,2.2rem)');

  $('#fontUp')?.addEventListener('click', () => {
    document.documentElement.style.setProperty('--reader-scale', 'clamp(2rem,5.4vw,2.9rem)');
    putStore('quran-reader-scale', 'large');
  });
  $('#fontDown')?.addEventListener('click', () => {
    document.documentElement.style.setProperty('--reader-scale', 'clamp(1.55rem,4vw,2.2rem)');
    putStore('quran-reader-scale', 'small');
  });
  $('#theme')?.addEventListener('click', () => document.body.classList.toggle('dark'));

  window.addEventListener('scroll', () => {
    const h = document.documentElement.scrollHeight - innerHeight;
    const p = h <= 0 ? 0 : Math.max(0, Math.min(1, scrollY / h));
    const bar = $('#progressBar');
    if (bar) bar.style.width = `${p * 100}%`;
  }, { passive: true });

  // Avoid a stale service worker trapping a broken release. The SW itself is
  // versioned and updated; unregistering old versions is a one-time migration.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations?.().then(regs => {
      regs.filter(r => /sacred-texts-library|sacred-quran/i.test(r.scope)).forEach(r => r.update().catch(() => {}));
    }).catch(() => {});
    navigator.serviceWorker.register('sw.js?v=6', { updateViaCache: 'none' })
      .then(r => r.update())
      .catch(console.warn);
  }

  load();
})();
