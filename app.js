const entities = [
  {id:'S1-10001',name:'Copper Kettle Tea Room',address:'18 Garden Road, Jaipur 302001',country:'India'},
  {id:'S1-10002',name:'Pinecrest Bike Works',address:'250 River Street, Portland OR 97201',country:'US'},
  {id:'S1-10003',name:'Atelier Lumiere SAS',address:'20 Avenue Victor Hugo, Paris 75116',country:'France'},
  {id:'S1-10004',name:'Fresh Fields Market',address:'73 Hill Avenue, Denver CO 80203',country:'US'},
  {id:'S1-10005',name:'Meadowbrook Animal Hospital',address:'4 School Road, Kochi 682001',country:'India'},
  {id:'S1-10006',name:'Redwood Web Design Studio',address:'99 Mission Street, San Francisco CA 94105',country:'US'},
  {id:'S1-10007',name:'Golden Gate Tailors',address:'15 Church Lane, Delhi 110001',country:'India'},
  {id:'S1-10008',name:'Willow Creek Hardware',address:'32 Main Street, Vancouver BC V6B 1A1',country:'Canada'},
  {id:'S1-10009',name:'Blue Moon Yoga Center',address:'6 High Street, Manchester M1 1AB',country:'UK'},
  {id:'S1-10010',name:'Citrus Grove Juice Bar',address:'81 Palm Avenue, Miami FL 33130',country:'US'}
];
const sources = [
  [
    [{id:'S2-10001',name:'Copper Kettle Tea Room',address:'18 Garden Rd, Jaipur 302001',score:'99%',matched:true},{id:'S3-10001',name:'Copper Kettle Cafe',address:'18 Garden Road Jaipur',score:'88%',matched:true},{id:'S3-10005',name:'Meadowbrook Animal Hospital',address:'4 School Road Kochi',score:'12%',matched:false}],
    [{id:'S2-10002',name:'Pinecrest Bicycle Works',address:'250 River St, Portland OR 97201',score:'96%',matched:true},{id:'S3-10002',name:'Pinecrest Bike Works',address:'250 River Street Portland',score:'97%',matched:true},{id:'S3-10006',name:'Redwood Web Design',address:'99 Mission Street San Francisco',score:'19%',matched:false}],
    [{id:'S2-10003',name:'Atelier Lumière',address:'20 Avenue Victor Hugo, Paris 75116',score:'98%',matched:true},{id:'S3-10003',name:'Atelier Lumiere SAS',address:'20 Av Victor Hugo, Paris',score:'97%',matched:true},{id:'S3-10004',name:'Fresh Fields Market',address:'73 Hill Avenue Denver',score:'8%',matched:false}],
    [{id:'S2-10004',name:'Fresh Fields Grocery Market',address:'73 Hill Ave, Denver CO 80203',score:'95%',matched:true},{id:'S3-10004',name:'Fresh Fields Market',address:'73 Hill Avenue Denver',score:'97%',matched:true},{id:'S2-10003',name:'Atelier Lumière',address:'20 Avenue Victor Hugo, Paris 75116',score:'11%',matched:false}],
    [{id:'S2-10005',name:'Meadowbrook Veterinary Hospital',address:'4 School Rd, Kochi 682001',score:'94%',matched:true},{id:'S3-10005',name:'Meadowbrook Animal Hospital',address:'4 School Road Kochi',score:'99%',matched:true},{id:'S3-10001',name:'Copper Kettle Cafe',address:'18 Garden Road Jaipur',score:'13%',matched:false}],
    [{id:'S2-10006',name:'Redwood Digital Design Studio',address:'99 Mission St, San Francisco CA 94105',score:'96%',matched:true},{id:'S3-10006',name:'Redwood Web Design',address:'99 Mission Street San Francisco',score:'93%',matched:true},{id:'S2-10011',name:'Cedar Ridge Landscaping',address:'700 Pine Street, Dallas TX 75201',score:'9%',matched:false}],
    [{id:'S2-10007',name:'Golden Gate Tailoring',address:'15 Church Ln, Delhi 110001',score:'95%',matched:true},{id:'S3-10007',name:'Golden Gate Tailors',address:'15 Church Lane Delhi',score:'99%',matched:true}],
    [{id:'S2-10008',name:'Willow Creek Hardware Store',address:'32 Main St, Vancouver BC V6B 1A1',score:'96%',matched:true},{id:'S3-10008',name:'Willow Creek Hardware',address:'32 Main Street Vancouver',score:'98%',matched:true},{id:'S3-10002',name:'Pinecrest Bike Works',address:'250 River Street Portland',score:'10%',matched:false}],
    [{id:'S2-10009',name:'Blue Moon Yoga Centre',address:'6 High St, Manchester M1 1AB',score:'96%',matched:true},{id:'S3-10009',name:'Blue Moon Yoga Center',address:'6 High Street Manchester',score:'99%',matched:true}],
    [{id:'S2-10010',name:'Citrus Grove Juice Bar',address:'81 Palm Ave, Miami FL 33130',score:'99%',matched:true},{id:'S3-10010',name:'Citrus Grove Juice Bar',address:'81 Palm Avenue Miami',score:'98%',matched:true},{id:'S3-10004',name:'Fresh Fields Market',address:'73 Hill Avenue Denver',score:'12%',matched:false}]
  ]
];
const entityButtons = document.querySelector('#entity-buttons');
const detail = document.querySelector('#match-detail');
function renderList(active=0){entityButtons.innerHTML=entities.map((e,i)=>`<button class="entity-button ${i===active?'active':''}" data-index="${i}"><span class="entity-avatar">${String(i+1).padStart(2,'0')}</span><span class="entity-button-text"><b>${e.name}</b><small>${e.id}</small></span><span class="entity-button-count">${sources[0][i].filter(x=>x.matched).length} ↗</span></button>`).join('');entityButtons.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>renderDetail(Number(b.dataset.index))));}
function renderDetail(index){renderList(index);const e=entities[index], rows=sources[0][index], matches=rows.filter(x=>x.matched).length;detail.innerHTML=`<div class="detail-top"><div><span class="detail-kicker">REFERENCE ENTITY · ${e.id}</span><h3>${e.name}</h3><span class="detail-address">${e.address}</span></div><span class="detail-country">◎ &nbsp; ${e.country}</span></div><div class="detail-summary"><span class="summary-item"><b class="summary-number">${rows.length}</b> candidates</span><span class="summary-item"><b class="summary-number">${matches}</b> selected matches</span><span class="summary-item">Sources 2 + 3</span></div><table class="candidate-table"><thead><tr><th>RECORD ID</th><th>BUSINESS RECORD</th><th>SOURCE</th><th>SIMILARITY</th><th>DECISION</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.id}</td><td><div class="candidate-name">${r.name}</div><div class="candidate-address">${r.address}</div></td><td><span class="source-chip">${r.id.slice(0,2)}</span></td><td><span class="similarity">${r.score}</span></td><td><span class="status-chip ${r.matched?'':'other'}">${r.matched?'✓ MATCH':'CANDIDATE'}</span></td></tr>`).join('')}</tbody></table>`;}
renderDetail(0);
document.querySelector('.menu-toggle').addEventListener('click',e=>{const nav=document.querySelector('.nav-links');nav.classList.toggle('open');e.currentTarget.setAttribute('aria-expanded',String(nav.classList.contains('open')))});
document.querySelectorAll('.nav-links a').forEach(a=>a.addEventListener('click',()=>{document.querySelector('.nav-links').classList.remove('open');document.querySelector('.menu-toggle').setAttribute('aria-expanded','false')}));
