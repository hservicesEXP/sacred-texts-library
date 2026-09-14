(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  let verses = [];
  let roots = {};
  let lemmas = {};
  let concepts = {};
  let loaded = false;
  const suraNames = [
    '', 'Al-Fatiha','Al-Baqarah','Ali Imran','An-Nisa','Al-Ma’idah','Al-An’am','Al-A’raf','Al-Anfal','At-Tawbah','Yunus','Hud','Yusuf','Ar-Ra’d','Ibrahim','Al-Hijr','An-Nahl','Al-Isra','Al-Kahf','Maryam','Ta-Ha','Al-Anbiya','Al-Hajj','Al-Mu’minun','An-Nur','Al-Furqan','Ash-Shu’ara','An-Naml','Al-Qasas','Al-Ankabut','Ar-Rum','Luqman','As-Sajdah','Al-Ahzab','Saba','Fatir','Ya-Sin','As-Saffat','Sad','Az-Zumar','Ghafir','Fussilat','Ash-Shura','Az-Zukhruf','Ad-Dukhan','Al-Jathiyah','Al-Ahqaf','Muhammad','Al-Fath','Al-Hujurat','Qaf','Adh-Dhariyat','At-Tur','An-Najm','Al-Qamar','Ar-Rahman','Al-Waqi’ah','Al-Hadid','Al-Mujadilah','Al-Hashr','Al-Mumtahanah','As-Saff','Al-Jumu’ah','Al-Munafiqun','At-Taghabun','At-Talaq','At-Tahrim','Al-Mulk','Al-Qalam','Al-Haqqah','Al-Ma’arij','Nuh','Al-Jinn','Al-Muzzammil','Al-Muddaththir','Al-Qiyamah','Al-Insan','Al-Mursalat','An-Naba','An-Nazi’at','Abasa','At-Takwir','Al-Infitar','Al-Mutaffifin','Al-Inshiqaq','Al-Buruj','At-Tariq','Al-A’la','Al-Ghashiyah','Al-Fajr','Al-Balad','Ash-Shams','Al-Layl','Ad-Duha','Ash-Sharh','At-Tin','Al-Alaq','Al-Qadr','Al-Bayyinah','Az-Zalzalah','Al-Adiyat','Al-Qari’ah','At-Takathur','Al-Asr','Al-Humazah','Al-Fil','Quraysh','Al-Ma’un','Al-Kawthar','Al-Kafirun','An-Nasr','Al-Masad','Al-Ikhlas','Al-Falaq','An-Nas'
  ];

  function normArabic(s) {
    return String(s || '')
      .normalize('NFD')
      .replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g, '')
      .replace(/[إأآٱ]/g, 'ا')
      .replace(/ى/g, 'ي')
      .replace(/ؤ/g, 'و')
      .replace(/ئ/g, 'ي')
      .replace(/ة/g, 'ه')
      .toLowerCase()
      .normalize('NFC');
  }
  function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function setStatus(text, kind='') { const el=$('#searchStatus'); if(el){el.textContent=text; el.className='status '+kind;} }
  async function fetchJSON(path) {
    const r = await fetch(path + '?v=3', {cache:'no-store'});
    if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
    return r.json();
  }
  async function loadIndex() {
    try {
      [verses, roots, lemmas, concepts] = await Promise.all([
        fetchJSON('data/index.json'), fetchJSON('data/roots.json'), fetchJSON('data/lemmas.json'), fetchJSON('data/concepts.json')
      ]);
      loaded = true;
      setStatus(`${verses.length.toLocaleString('it-IT')} versetti · indice locale pronto`, 'ok');
    } catch (err) {
      console.error(err);
      setStatus('Indice non caricato · riprova', 'error');
      $('#retrySearch')?.removeAttribute('hidden');
    }
    renderSuras();
  }
  function renderSuras() {
    const g=$('#suraGrid'); if(!g || !verses.length) return;
    const first = new Map();
    verses.forEach(x => { if(!first.has(x.s)) first.set(x.s,x); });
    g.innerHTML = Array.from({length:114},(_,i)=>{
      const x=first.get(i+1); if(!x) return '';
      const count=verses.filter(v=>v.s===i+1).length;
      return `<a class="sura-card" href="reader.html?surah=${i+1}" aria-label="Apri ${esc(suraNames[i+1])}">
        <span class="sura-no">${i+1}</span><span class="sura-name">${esc(suraNames[i+1])}</span><span class="sura-ar" lang="ar" dir="rtl">${esc(x.n)}</span><span class="sura-count">${count} versetti</span></a>`;
    }).join('');
  }
  function refResults(q){ const m=q.match(/^(\d{1,3})\s*[:.]\s*(\d{1,3})$/); return m ? verses.filter(x=>x.s===+m[1]&&x.v===+m[2]) : []; }
  function normalizeRootInput(q){ const raw=q.trim().replace(/[-–—_\s]/g,''); const aliases={ 'khlq':'xlq','kh l q':'xlq','kh-l-q':'xlq','rhm':'rHm','r-h-m':'rHm','ktb':'ktb','k-t-b':'ktb','slm':'slm','s-l-m':'slm','Alh':'Alh' }; return aliases[raw]||raw; }
  function rootResults(q){ const key=normalizeRootInput(q); const r=(roots[key]?.refs||[]); const map=new Map(verses.map(x=>[x.r,x])); return r.map(x=>map.get(x)).filter(Boolean); }
  function conceptResults(q){ const key=q.trim().toLocaleLowerCase('it-IT'); const rs=concepts[key]||[]; const map=new Map(verses.map(x=>[x.r,x])); const refs=[...new Set(rs.flatMap(k=>roots[k]?.refs||[]))]; return refs.map(x=>map.get(x)).filter(Boolean); }
  function lemmaResults(q){ const key=q.trim(); const r=lemmas[key]||[]; const map=new Map(verses.map(x=>[x.r,x])); return r.map(x=>map.get(x)).filter(Boolean); }
  function search(q,mode){
    if(!loaded || !q.trim()) return [];
    if(mode==='ref') return refResults(q.trim());
    if(mode==='root') return rootResults(q);
    if(mode==='lemma') return lemmaResults(q);
    const n=normArabic(q); if(!n) return [];
    const latin=/[A-Za-zÀ-ÿ]/.test(q); if(latin){ const conceptual=conceptResults(q); if(conceptual.length) return conceptual.slice(0,120); }
    return verses.filter(x=>normArabic(x.t).includes(n)).slice(0,120);
  }
  function renderResults(res,q){
    const box=$('#results'); if(!box)return;
    if(!res.length){ box.innerHTML=`<div class="empty"><strong>Nessun risultato</strong><span>Prova una parola araba, una radice Buckwalter, un lemma o un riferimento come 2:255.</span></div>`; return; }
    box.innerHTML=`<div class="result-head"><strong>${res.length}${res.length===120?'+':''} risultati</strong><span>${esc(q)}</span></div>` + res.map(x=>`<a class="result-card" href="reader.html?ref=${encodeURIComponent(x.r)}"><div><span class="result-ref">${x.r}</span><span class="result-sura">${esc(suraNames[x.s]||x.n)}</span></div><p lang="ar" dir="rtl">${esc(x.t)}</p></a>`).join('');
  }
  $('#searchForm')?.addEventListener('submit',e=>{e.preventDefault(); if(!loaded){setStatus('Attendi il caricamento dell’indice','error');return;} const q=$('#query').value,mode=$('#searchMode').value; renderResults(search(q,mode),q);});
  $('#retrySearch')?.addEventListener('click',loadIndex);
  $('#randomBtn')?.addEventListener('click',()=>{if(!verses.length)return;const x=verses[Math.floor(Math.random()*verses.length)];location.href=`reader.html?ref=${encodeURIComponent(x.r)}`;});
  $('#scholarBtn')?.addEventListener('click',()=>$('#scholarDialog')?.showModal());
  function hideIntro(){ const i=$('#intro'); if(i){i.classList.add('hidden'); sessionStorage.setItem('introSeen','1');} }
  $('#enter')?.addEventListener('click',()=>{const i=$('#intro');i?.classList.add('open');setTimeout(hideIntro,950);});
  $('#skipIntro')?.addEventListener('click',hideIntro);
  if($('#intro') && sessionStorage.getItem('introSeen')==='1') hideIntro();
  if('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(console.warn);
  loadIndex();
})();
