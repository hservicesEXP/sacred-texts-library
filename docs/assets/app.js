
const $=s=>document.querySelector(s);let index=[],roots={},lemmas={};
async function init(){try{[index,roots,lemmas]=await Promise.all([fetch("data/index.json").then(r=>r.json()),fetch("data/roots.json").then(r=>r.json()),fetch("data/lemmas.json").then(r=>r.json())]);$("#searchStatus").textContent=`${index.length.toLocaleString("it-IT")} versetti indicizzati`;}catch(e){$("#searchStatus").textContent="Indice non disponibile";}renderSuras();registerSW();}
function renderSuras(){const g=$("#suraGrid");g.innerHTML=index.filter(x=>x.v===1).map(x=>`<a class="sura" href="reader.html?surah=${x.s}&ref=${x.r}"><strong>${x.s}</strong><span>${x.s}. ${x.n||""}</span><em>Apri la sura</em></a>`).join("");}
function norm(s){return s.normalize("NFD").replace(/[\u064B-\u065F\u0670\u06D6-\u06ED]/g,"").normalize("NFC").toLowerCase();}
function search(q,mode){q=q.trim();if(!q)return[];if(mode==="ref"){let m=q.match(/^(\d{1,3}):(\d{1,3})$/);return m?index.filter(x=>x.s==+m[1]&&x.v==+m[2]):[]}if(mode==="root"){return ((roots[q]||{}).refs||[]).map(r=>index.find(x=>x.r===r)).filter(Boolean)}if(mode==="lemma"){return (lemmas[q]||[]).map(r=>index.find(x=>x.r===r)).filter(Boolean)}const n=norm(q);return index.filter(x=>norm(x.t).includes(n)).slice(0,100);}
$("#searchForm")?.addEventListener("submit",e=>{e.preventDefault();const q=$("#query").value,mode=$("#searchMode").value,res=search(q,mode),box=$("#results");box.innerHTML=res.length?res.map(x=>`<a class="result" href="reader.html?ref=${x.r}"><small>${x.r}</small><p>${x.t}</p></a>`).join(""):`<div class="muted">Nessun risultato.</div>`;});
$("#randomBtn")?.addEventListener("click",()=>{if(!index.length)return;const x=index[Math.floor(Math.random()*index.length)];location.href=`reader.html?ref=${x.r}`});
$("#scholarBtn")?.addEventListener("click",()=>$("#scholarDialog").showModal());
function enterIntro(){const i=$("#intro");if(!i)return; i.classList.add("open");setTimeout(()=>i.classList.add("hidden"),1250);sessionStorage.setItem("introSeen","1")}
$("#enter")?.addEventListener("click",enterIntro);$("#skipIntro")?.addEventListener("click",()=>{$("#intro").classList.add("hidden");sessionStorage.setItem("introSeen","1")});if($("#intro")&&sessionStorage.getItem("introSeen")==="1")$("#intro").classList.add("hidden");
function registerSW(){if("serviceWorker"in navigator)navigator.serviceWorker.register("sw.js").catch(()=>{});}
init();
