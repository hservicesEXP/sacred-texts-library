(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const DATA = new URL('data/', document.baseURI);
  let index = [], roots = null, lemmas = null, concepts = null, loaded = false;
  const suraNames = ['', 'Al-Fatiha','Al-Baqarah','Ali Imran','An-Nisa','Al-Ma’idah','Al-An’am','Al-A’raf','Al-Anfal','At-Tawbah','Yunus','Hud','Yusuf','Ar-Ra’d','Ibrahim','Al-Hijr','An-Nahl','Al-Isra','Al-Kahf','Maryam','Ta-Ha','Al-Anbiya','Al-Hajj','Al-Mu’minun','An-Nur','Al-Furqan','Ash-Shu’ara','An-Naml','Al-Qasas','Al-Ankabut','Ar-Rum','Luqman','As-Sajdah','Al-Ahzab','Saba','Fatir','Ya-Sin','As-Saffat','Sad','Az-Zumar','Ghafir','Fussilat','Ash-Shura','Az-Zukhruf','Ad-Dukhan','Al-Jathiyah','Al-Ahqaf','Muhammad','Al-Fath','Al-Hujurat','Qaf','Adh-Dhariyat','At-Tur','An-Najm','Al-Qamar','Ar-Rahman','Al-Waqi’ah','Al-Hadid','Al-Mujadilah','Al-Hashr','Al-Mumtahanah','As-Saff','Al-Jumu’ah','Al-Munafiqun','At-Taghabun','At-Talaq','At-Tahrim','Al-Mulk','Al-Qalam','Al-Haqqah','Al-Ma’arij','Nuh','Al-Jinn','Al-Muzzammil','Al-Muddaththir','Al-Qiyamah','Al-Insan','Al-Mursalat','An-Naba','An-Nazi’at','Abasa','At-Takwir','Al-Infitar','Al-Mutaffifin','Al-Inshiqaq','Al-Buruj','At-Tariq','Al-A’la','Al-Ghashiyah','Al-Fajr','Al-Balad','Ash-Shams','Al-Layl','Ad-Duha','Ash-Sharh','At-Tin','Al-Alaq','Al-Qadr','Al-Bayyinah','Az-Zalzalah','Al-Adiyat','Al-Qari’ah','At-Takathur','Al-Asr','Al-Humazah','Al-Fil','Quraysh','Al-Ma’un','Al-Kawthar','Al-Kafirun','An-Nasr','Al-Masad','Al-Ikhlas','Al-Falaq','An-Nas'];
  const arabicNames = ['', 'الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الإنفطار','المطففين','الإنشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];
  const norm = s => String(s || '').normalize('NFD').replace(/[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/g,'').replace(/[إأآٱ]/g,'ا').replace(/ى/g,'ي').replace(/ؤ/g,'و').replace(/ئ/g,'ي').replace(/ة/g,'ه').toLowerCase().normalize('NFC');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const setStatus = (t,k='') => { const e=$('#searchStatus'); if(e){e.textContent=t;e.className='status '+k;} };
  async function get(name){ const r=await fetch(new URL(`${name}?v=4`, DATA), {cache:'no-store'}); if(!r.ok) throw Error(`${name}: HTTP ${r.status}`); return r.json(); }
  async function loadIndex(){
    setStatus('Caricamento indice…');
    try { index = await get('index.json'); loaded=true; setStatus(`${index.length.toLocaleString('it-IT')} versetti · pronto`,'ok'); renderSuras(); }
    catch(e){ console.error(e); setStatus('Indice non disponibile','error'); $('#retrySearch')?.removeAttribute('hidden'); }
  }
  async function loadAux(kind){
    if(kind==='root' && !roots) roots=await get('roots.json');
    if(kind==='lemma' && !lemmas) lemmas=await get('lemmas.json');
    if(kind==='concept' && !concepts) concepts=await get('concepts.json');
  }
  const byRefs = refs => { const set=new Set(refs); return index.filter(x=>set.has(x.r)); };
  function refResults(q){ const m=q.trim().match(/^(\d{1,3})\s*[:.]\s*(\d{1,3})$/); return m ? index.filter(x=>x.s===+m[1]&&x.v===+m[2]) : []; }
  function rootKey(q){ return q.trim().replace(/[-–—_\s]/g,''); }
  function suraResults(q){ const k=nameKey(q); const hit=suraNames.findIndex((n,i)=>i && nameKey(n)===k); return hit>0 ? index.filter(x=>x.s===hit) : []; }
  async function doSearch(q,mode){
    if(!loaded || !q.trim()) return [];
    if(mode==='ref') return refResults(q);
    if(mode==='root'){ await loadAux('root'); const key=rootKey(q); return byRefs(roots[key]?.refs||[]); }
    if(mode==='lemma'){ await loadAux('lemma'); return byRefs(lemmas[q.trim()]||[]); }
    if(/^\d{1,3}\s*[:.]\s*\d{1,3}$/.test(q.trim())) return refResults(q);
    const named=suraResults(q); if(named.length) return named;
    const latin=/[A-Za-zÀ-ÿ]/.test(q); if(latin){ await loadAux('concept'); const rs=concepts[norm(q)]||concepts[q.trim().toLocaleLowerCase('it-IT')]; if(rs){ if(!roots) await loadAux('root'); return byRefs([...new Set(rs.flatMap(k=>roots[k]?.refs||[]))]); } }
    const n=norm(q); if(!n) return [];
    return index.filter(x=>x.q.includes(n)).slice(0,120);
  }
  async function renderSearch(q,mode){
    const box=$('#results'); if(!box) return; box.innerHTML='<div class="loading-row">Ricerca in corso…</div>';
    try { const res=await doSearch(q,mode); if(!res.length){box.innerHTML='<div class="empty"><strong>Nessun risultato</strong><span>Prova una parola araba, una radice/lemma Buckwalter o un riferimento come 2:255.</span></div>';return;} box.innerHTML=`<div class="result-head"><strong>${res.length}${res.length===120?'+':''} risultati</strong><span>${esc(q)}</span></div>`+res.map(x=>`<a class="result-card" href="reader.html?ref=${encodeURIComponent(x.r)}"><div><span class="result-ref">${x.r}</span><span class="result-sura">${esc(suraNames[x.s])} · ${esc(arabicNames[x.s])}</span></div><p lang="ar" dir="rtl">${esc(x.t)}</p></a>`).join(''); }
    catch(e){console.error(e);box.innerHTML='<div class="empty error-box"><strong>Ricerca non disponibile</strong><span>Un indice opzionale non è riuscito a caricarsi. Riprova.</span></div>';}
  }
  function renderSuras(){ const g=$('#suraGrid'); if(!g||!index.length)return; const counts=Array(115).fill(0),first={}; index.forEach(x=>{counts[x.s]++;first[x.s]??=x}); g.innerHTML=Array.from({length:114},(_,i)=>{const s=i+1,x=first[s];return `<a class="sura-card" href="reader.html?surah=${s}"><span class="sura-no">${String(s).padStart(3,'0')}</span><span class="sura-name">${esc(suraNames[s])}</span><span class="sura-ar" lang="ar" dir="rtl">${esc(arabicNames[s])}</span><span class="sura-count">${counts[s]} ayat</span></a>`}).join(''); }
  function runQuick(btn){ $('#query').value=btn.dataset.query; if(btn.dataset.mode) $('#searchMode').value=btn.dataset.mode; else if(/^\d/.test(btn.dataset.query)) $('#searchMode').value='ref'; else $('#searchMode').value='text'; $('#searchForm').requestSubmit(); }
  $('#searchForm')?.addEventListener('submit',e=>{e.preventDefault(); if(!loaded){setStatus('Indice ancora in caricamento','error');return;} renderSearch($('#query').value,$('#searchMode').value);});
  document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>runQuick(b)));
  $('#retrySearch')?.addEventListener('click',loadIndex);
  $('#randomBtn')?.addEventListener('click',()=>{if(index.length){const x=index[Math.floor(Math.random()*index.length)];location.href=`reader.html?ref=${encodeURIComponent(x.r)}`;}});
  const openDialog=id=>$(id)?.showModal(); $('#keeperBtn')?.addEventListener('click',()=>openDialog('#keeperDialog')); $('#keeperBtn2')?.addEventListener('click',()=>openDialog('#keeperDialog')); $('#scholarBtn')?.addEventListener('click',()=>openDialog('#scholarDialog'));
  function hideIntro(){const i=$('#intro');if(i){i.classList.add('hidden');try{sessionStorage.setItem('introSeen','1')}catch{}}}
  $('#enter')?.addEventListener('click',()=>{const i=$('#intro');i?.classList.add('open');setTimeout(hideIntro,900)}); $('#skipIntro')?.addEventListener('click',hideIntro);
  try{if(sessionStorage.getItem('introSeen')==='1')hideIntro()}catch{}
  if('serviceWorker' in navigator){navigator.serviceWorker.register('sw.js?v=4').then(r=>r.update()).catch(console.warn)}
  loadIndex();
})();
