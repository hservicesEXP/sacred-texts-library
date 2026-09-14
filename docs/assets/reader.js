(() => {
  'use strict';
  const $=s=>document.querySelector(s), params=new URLSearchParams(location.search);
  const refParam=params.get('ref'), surahParam=params.get('surah');
  let surah=Math.max(1,Math.min(114,Number(surahParam||refParam?.split(':')[0]||1)||1));
  let ref=refParam, data=null, activeRef=null;
  const names=['','الفاتحة','البقرة','آل عمران','النساء','المائدة','الأنعام','الأعراف','الأنفال','التوبة','يونس','هود','يوسف','الرعد','إبراهيم','الحجر','النحل','الإسراء','الكهف','مريم','طه','الأنبياء','الحج','المؤمنون','النور','الفرقان','الشعراء','النمل','القصص','العنكبوت','الروم','لقمان','السجدة','الأحزاب','سبأ','فاطر','يس','الصافات','ص','الزمر','غافر','فصلت','الشورى','الزخرف','الدخان','الجاثية','الأحقاف','محمد','الفتح','الحجرات','ق','الذاريات','الطور','النجم','القمر','الرحمن','الواقعة','الحديد','المجادلة','الحشر','الممتحنة','الصف','الجمعة','المنافقون','التغابن','الطلاق','التحريم','الملك','القلم','الحاقة','المعارج','نوح','الجن','المزمل','المدثر','القيامة','الإنسان','المرسلات','النبأ','النازعات','عبس','التكوير','الإنفطار','المطففين','الإنشقاق','البروج','الطارق','الأعلى','الغاشية','الفجر','البلد','الشمس','الليل','الضحى','الشرح','التين','العلق','القدر','البينة','الزلزلة','العاديات','القارعة','التكاثر','العصر','الهمزة','الفيل','قريش','الماعون','الكوثر','الكافرون','النصر','المسد','الإخلاص','الفلق','الناس'];
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const getStore=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}};
  const putStore=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch{}};
  const url=()=>new URL(`data/${surah}.json?v=4`,document.baseURI);
  async function load(){
    $('#suraTitle').textContent='Caricamento…';
    try{const r=await fetch(url(),{cache:'no-store'});if(!r.ok)throw Error(`HTTP ${r.status}`);data=await r.json();
      $('#suraNumber').textContent=`SURA ${surah}`;$('#suraTitle').textContent=data.name||names[surah];$('#suraMeta').textContent=`${data.ayas.length} versetti · testo arabo Uthmani · fonte e metodologia in Codicologo`;renderNav();render();
      if(ref){const target=document.getElementById(`v-${ref.replace(':','-')}`);if(target)setTimeout(()=>target.scrollIntoView({block:'center'}),120)}
    }catch(e){console.error(e);$('#suraTitle').textContent='Impossibile caricare la sura';$('#suraMeta').textContent='Controlla la connessione e ricarica la pagina.';}
  }
  function renderNav(){ $('#suraSelect').innerHTML=Array.from({length:114},(_,i)=>`<option value="${i+1}" ${i+1===surah?'selected':''}>${i+1}. ${esc(names[i+1])}</option>`).join(''); }
  function render(){
    const box=$('#verses'); if(!box||!data)return;
    box.innerHTML=data.ayas.map(a=>{const words=(a.words||[]).map((w,i)=>`<span class="word" tabindex="0" role="button" data-v="${a.v}" data-w="${w.n??i+1}">${esc(w.text)}</span>`).join(' ');return `<article class="verse" id="v-${surah}-${a.v}" data-ref="${surah}:${a.v}"><div class="verse-ref"><span>${surah}:${a.v}</span><div class="verse-tools"><button class="ghost" data-act="copy" data-v="${a.v}" type="button">Copia</button><button class="ghost" data-act="speak" data-v="${a.v}" type="button">Ascolta</button><button class="ghost" data-act="note" data-v="${a.v}" type="button">Nota</button><button class="ghost" data-act="bookmark" data-v="${a.v}" type="button">Segna</button></div></div><div class="verse-text" lang="ar" dir="rtl">${words||esc(a.text)}</div></article>`}).join('');
    box.onclick=handleClick;box.onkeydown=e=>{if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('word')){e.preventDefault();showMorph(+e.target.dataset.v,+e.target.dataset.w)}};updateBookmarkButtons();
  }
  const verse=v=>data?.ayas.find(a=>a.v===v);
  async function copy(text){try{await navigator.clipboard.writeText(text);return true}catch{const t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();const ok=document.execCommand('copy');t.remove();return ok}}
  function handleClick(e){const w=e.target.closest('.word'),b=e.target.closest('button');if(w){showMorph(+w.dataset.v,+w.dataset.w);return}if(!b)return;const v=+b.dataset.v,a=verse(v);if(b.dataset.act==='speak')speak(a?.text||'');if(b.dataset.act==='copy')copy(a?.text||'').then(ok=>{b.textContent=ok?'Copiato':'Copia'});if(b.dataset.act==='note')openNote(v);if(b.dataset.act==='bookmark')toggleBookmark(`${surah}:${v}`)}
  function showMorph(v,wi){const a=verse(v),w=a?.words?.find(x=>x.n===wi);if(!w)return;$('#morphTitle').textContent=`${surah}:${v} · parola ${wi}`;const seg=w.segments||[];$('#morphBody').innerHTML=`<div class="morph-word" lang="ar" dir="rtl">${esc(w.text)}</div>`+(seg.length?seg.map(s=>`<div class="morph-row"><div><div class="tag">${esc(s.pos||s.tag||'—')}</div></div><div><div>Forma: <code>${esc(s.form||'—')}</code></div><div>Lemma: <code>${esc(s.lemma||'—')}</code></div><div>Radice: <code>${esc(s.root||'—')}</code></div><div class="muted">${esc(s.features||'')}</div></div></div>`).join(''):'<p class="muted">Non è presente un’annotazione morfologica per questa posizione nel corpus.</p>');$('#morphDialog').showModal()}
  function speak(text){if(!('speechSynthesis'in window)){alert('Sintesi vocale non disponibile su questo dispositivo.');return}speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='ar';speechSynthesis.speak(u)}
  function toggleBookmark(r){let a=getStore('quran-bookmarks',[]);a=a.includes(r)?a.filter(x=>x!==r):[...a,r];putStore('quran-bookmarks',a);updateBookmarkButtons()}
  function updateBookmarkButtons(){const set=new Set(getStore('quran-bookmarks',[]));document.querySelectorAll('[data-act="bookmark"]').forEach(b=>{const r=`${surah}:${b.dataset.v}`,yes=set.has(r);b.textContent=yes?'Salvato':'Segna';b.setAttribute('aria-pressed',yes)})}
  function openNote(v){activeRef=`${surah}:${v}`;const n=getStore('quran-notes',{})[activeRef]||'';$('#noteRef').textContent=activeRef;$('#noteText').value=n;$('#deleteNote').style.visibility=n?'visible':'hidden';$('#noteDialog').showModal()}
  $('#noteForm')?.addEventListener('submit',e=>{e.preventDefault();const n=getStore('quran-notes',{}),text=$('#noteText').value.trim();if(text)n[activeRef]=text;else delete n[activeRef];putStore('quran-notes',n);$('#noteDialog').close()});
  $('#noteClose')?.addEventListener('click',()=>$('#noteDialog').close());$('#deleteNote')?.addEventListener('click',()=>{$('#noteText').value='';$('#noteForm').requestSubmit()});
  $('#suraSelect')?.addEventListener('change',e=>location.href=`reader.html?surah=${e.target.value}`);
  $('#jumpBtn')?.addEventListener('click',()=>{const v=+$('#verseJump').value,el=document.getElementById(`v-${surah}-${v}`);if(!el)return;ref=`${surah}:${v}`;history.replaceState(null,'',`reader.html?ref=${encodeURIComponent(ref)}`);el.scrollIntoView({behavior:'smooth',block:'center'});el.classList.add('flash');setTimeout(()=>el.classList.remove('flash'),1400)});
  $('#prevSura')?.addEventListener('click',()=>{if(surah>1)location.href=`reader.html?surah=${surah-1}`});$('#nextSura')?.addEventListener('click',()=>{if(surah<114)location.href=`reader.html?surah=${surah+1}`});
  $('#bookmarkCurrent')?.addEventListener('click',()=>refParam?toggleBookmark(refParam):alert('Apri un versetto specifico per usare questo comando.'));
  $('#showNotes')?.addEventListener('click',()=>{const n=getStore('quran-notes',{}),b=getStore('quran-bookmarks',[]),keys=[...new Set([...Object.keys(n),...b])].sort((a,z)=>a.localeCompare(z,undefined,{numeric:true}));$('#localList').innerHTML=keys.length?keys.map(r=>`<div class="notes-item"><a href="reader.html?ref=${encodeURIComponent(r)}">${r}</a>${n[r]?`<div>${esc(n[r])}</div>`:'<div class="muted">Segnalibro</div>'}</div>`).join(''):'<p class="muted">Nessuna nota o segnalibro locale.</p>';$('#localDialog').showModal()});
  $('#fontUp')?.addEventListener('click',()=>document.documentElement.style.setProperty('--reader-scale','clamp(2rem,5.4vw,2.9rem)'));$('#fontDown')?.addEventListener('click',()=>document.documentElement.style.setProperty('--reader-scale','clamp(1.55rem,4vw,2.2rem)'));$('#theme')?.addEventListener('click',()=>document.body.classList.toggle('dark'));
  if('serviceWorker'in navigator)navigator.serviceWorker.register('sw.js?v=4').then(r=>r.update()).catch(console.warn);load();
})();
