'use strict';

const PATRIMAGE_URL='https://app.powerbi.com/groups/me/apps/e8d55373-ef61-4cba-acd1-df4ea86142bc/reports/27c8ca41-70d4-4671-9335-a9877420d8a9/873b06b26127a693a7e0?ctid=a957327b-1840-4e74-be27-90218a7a2be5&experience=power-bi&chromeless=true';

const TYPES_FICHE={id_client:'client',id_lot:'lot',id_patrimoine:'patrimoine',id_commande:'commande',id_affaire:'affaire',id_diagnostic:'diagnostic',id_occupant:'occupant',id_copropriete:'copropriete'};
const NOMS_FICHE={client:'Fiche client',lot:'Fiche logement',patrimoine:'Fiche résidence',commande:'Fiche commande',affaire:'Fiche affaire',diagnostic:'Fiche diagnostic',occupant:'Fiche occupant',copropriete:'Fiche copropriété'};
let panneauVersion=0;

function dateMetier(){return new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Paris',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())}
function formatDate(v){if(!v)return 'Non renseignée';const d=String(v).slice(0,10).split('-');return d.length===3?d.reverse().join('/'):String(v)}
function lienSur(v){try{const u=new URL(String(v));return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null}catch{return null}}
function lienBouton(titre,url){const a=document.createElement('a');a.className='tool-link';a.textContent=titre+' ↗';a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a}
function nettoyerCourbes(node){if(node&&typeof Chart!=='undefined')node.querySelectorAll('canvas').forEach(c=>Chart.getChart(c)?.destroy())}

function panneau(titre){
  let d=$('workspace-dialog');
  if(!d){d=document.createElement('dialog');d.id='workspace-dialog';d.setAttribute('aria-labelledby','workspace-title');d.innerHTML='<div class="workspace-header"><div><small>MON ESPACE COLLABORATEUR</small><h2 id="workspace-title"></h2></div><button type="button" id="workspace-close" aria-label="Fermer le panneau">✕</button></div><div id="workspace-body"></div>';document.body.appendChild(d);$('workspace-close').onclick=()=>d.close();d.addEventListener('close',()=>{if(!d.open)panneauVersion++})}
  nettoyerCourbes($('workspace-body'));
  $('workspace-title').textContent=titre;$('workspace-body').innerHTML='<p role="status">Chargement…</p>';
  if(!d.open)d.showModal();
  return ++panneauVersion;
}
function erreurPanneau(version,x){if(version===panneauVersion)$('workspace-body').innerHTML=erreurHTML(x.message)}
function erreurAction(b,x){const parent=b.parentElement;parent.querySelector(':scope > .incident')?.remove();parent.insertAdjacentHTML('beforeend',erreurHTML(x.message))}

function ajouterOutilsResultat(node,message){
  const r=message.resultats;
  if(message.id&&message.question){
    const barre=document.createElement('div');barre.className='result-tools';
    const b=document.createElement('button');b.type='button';b.textContent='☆ Enregistrer la recherche';
    b.onclick=async()=>{b.disabled=true;try{await api('/api/espace/favoris','POST',{label:message.question.slice(0,120),question:message.question});b.textContent='★ Recherche enregistrée'}catch(x){erreurAction(b,x);b.disabled=false}};
    barre.appendChild(b);node.appendChild(barre);
  }
  const table=node.querySelector('table');if(!table)return;
  const ids=r.columns.filter(c=>TYPES_FICHE[c.toLowerCase()]);
  const liens=r.columns.filter(c=>/^lien_/i.test(c));
  const geo=r.columns.some(c=>['latitude','adresse_complete','adresse'].includes(c.toLowerCase()));
  if(!ids.length&&!liens.length&&!geo)return;
  const th=document.createElement('th');th.textContent='Actions';table.querySelector('thead tr').appendChild(th);
  [...table.querySelectorAll('tbody tr')].forEach((tr,i)=>{
    const row=r.rows[i],td=document.createElement('td');td.className='tools-cell';
    const outils=outilsLigne(row,ids,liens);td.appendChild(outils);
    if(!outils.children.length)td.textContent='—';tr.appendChild(td);
  });
}

function outilsLigne(row,ids=Object.keys(row).filter(c=>TYPES_FICHE[c.toLowerCase()]),liens=Object.keys(row).filter(c=>/^lien_/i.test(c))){
  const outils=document.createElement('div');outils.className='row-tools';
  if(ids.some(c=>row[c]!=null&&row[c]!==''))outils.appendChild(lienBouton('Ouvrir dans Patrimage',PATRIMAGE_URL));
  const deja=new Set();
  liens.forEach(c=>{if(/google_maps|google_earth/i.test(c))return;const url=lienSur(row[c]);if(!url||deja.has(url))return;deja.add(url);const titre=/ged/i.test(c)?'Ouvrir la GED':/diagnostic/i.test(c)&&!/ikos/i.test(c)?'Ouvrir le diagnostic':/ikos/i.test(c)?'Ouvrir dans IKOS':'Ouvrir le document';outils.appendChild(lienBouton(titre,url))});
  const col=['id_patrimoine','id_lot','id_client','id_occupant','id_affaire','id_diagnostic','id_copropriete','id_commande'].map(c=>ids.find(x=>x.toLowerCase()===c)).find(c=>c&&row[c]!=null&&row[c]!==''&&!String(row[c]).includes(','));
  if(col){const type=TYPES_FICHE[col.toLowerCase()];outils.appendChild(lienBouton('Voir sur la carte',`/carte?type_entite=${type}&identifiant=${encodeURIComponent(row[col])}`))}
  else if(row.Latitude!=null&&row.Longitude!=null){const lat=Number(String(row.Latitude).replace(',','.')),lon=Number(String(row.Longitude).replace(',','.'));if(Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180&&(lat!==0||lon!==0))outils.appendChild(lienBouton('Voir sur la carte',`/carte?latitude=${encodeURIComponent(lat)}&longitude=${encodeURIComponent(lon)}`))}
  return outils;
}

const COLONNES_ESPACE={
  Client:['Nom_prenom_client','Libelle_type_client','Libelle_activite_client','Indicateur_statut_presence'],
  Lot:['Code_lot','Libelle_type_lot','Libelle_usage_lot','Etage','Surface_habitable','Libelle_etat_actuel'],
  Patrimoine:['Libelle_patrimoine','Libelle_commune','Code_postal','Adresse_complete'],
  Occupant:['Raison_sociale_occupant','Nom_occupant','Prenom_occupant','Type_personne','Telephone_occupant','Mail_occupant'],
  Bail:['Libelle_type_bail','Indicateur_occupation_active','Date_reception_preavis','Date_fin_occupation_lot'],
  Affaire:['Libelle_objet_affaire','Libelle_etat_affaire','Date_ouverture','Date_theorique_cloture','Code_collaborateur_suivi'],
  Commande:['Numero_commande','Libelle_objet_commande_1','Libelle_tiers','Taux_execution_commande','Date_fin_execution_commande','Montant_TTC'],
  Diagnostic:['Libelle_diagnostic','Famille_diagnostic','Date_fin_diagnostic','Indicateur_diagnostic_perime'],
  Collaborateur:['Nom_prenom_collaborateur','Libelle_fonction','Mail_collaborateur'],
  Copropriete:['Nom_copropriete','Nom_syndic','Etat_mandat_copropriete','Date_fin_mandat_copropriete','Tel_syndic','Mail_syndic'],
  Releve_compte_client_historique:['Annee_mois','Montant_impaye','Montant_loyer','Montant_charges','Montant_paiement_moins_remboursement'],
  Contentieux_client_historique:['Annee_mois','Libelle_procedure','Libelle_etape_procedure','Date_prescription'],
  Equipement:['Libelle_type_equipement','Marque','Modele','Date_installation','Indicateur_activite'],
  Intervention:['Libelle_intervention','Date_realisation_intervention','Montant_total_TTC','Livrable_attendu','Indicateur_livrable_valide']
};
function tableauEspace(r,table,reference=''){
  const wrap=document.createElement('div');wrap.className='workspace-result';
  if(!r.rows.length){wrap.textContent='Aucun élément dans les données accessibles.';return wrap}
  let cols=(COLONNES_ESPACE[table]||r.columns.filter(c=>!/^ID_/i.test(c))).filter(c=>r.columns.includes(c));if(!cols.length)cols=r.columns.slice(0,6);
  wrap.innerHTML=`<p class="result-count">${r.row_count} ligne${r.row_count>1?'s':''} affichée${r.row_count>1?'s':''}${r.truncated?' — liste limitée aux 100 premières':''}</p><div class="tw"><table><thead><tr>${cols.map(c=>`<th>${esc(libelleColonne(c))}</th>`).join('')}</tr></thead><tbody>${r.rows.map(row=>`<tr>${cols.map(c=>`<td>${esc(row[c]??'—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  ajouterActions(wrap,{resultats:r,reference});return wrap;
}

async function ouvrirFiche(type,identifiant){
  const v=panneau(NOMS_FICHE[type]||'Fiche');
  try{const d=await api(`/api/espace/fiche/${encodeURIComponent(type)}?identifiant=${encodeURIComponent(identifiant)}`);if(v!==panneauVersion)return;
    const body=$('workspace-body');body.innerHTML=`<p class="workspace-intro">Référence : ${esc(d.identifiant)} · Informations accessibles à votre service.</p>`;
    const premier=d.sections[0].resultats.rows[0];
    const nom=premier.Nom_prenom_client||premier.Raison_sociale_occupant||premier.Libelle_patrimoine||premier.Nom_copropriete||premier.Libelle_objet_affaire||premier.Libelle_objet_commande_1;
    if(nom){const h=document.createElement('h3');h.className='dossier-name';h.textContent=nom;body.appendChild(h)}
    const actualisation=premier.Date_actualisation;
    if(actualisation){const p=document.createElement('p');p.className='data-date';p.textContent='Données actualisées le '+formatDate(actualisation);body.appendChild(p)}
    d.sections.forEach((section,i)=>{
      const details=document.createElement('details');details.className='dossier-section';details.open=i===0||section.table==='Collaborateur'||section.table==='Occupant'||section.table==='Releve_compte_client_historique';
      const summary=document.createElement('summary');summary.textContent=section.titre+' · '+section.resultats.row_count+(section.resultats.truncated?'+':'');details.appendChild(summary);
      details.appendChild(tableauEspace(section.resultats,section.table,identifiant));
      if(i===0){const tout=document.createElement('details');tout.className='all-fields';tout.innerHTML='<summary>Tous les champs accessibles</summary>'+section.resultats.rows.map(row=>'<dl>'+section.resultats.columns.map(c=>`<div><dt>${esc(libelleColonne(c))}</dt><dd>${esc(row[c]??'—')}</dd></div>`).join('')+'</dl>').join('');details.appendChild(tout)}
      if(section.table==='Releve_compte_client_historique')ajouterEvolution(details,section.resultats);
      body.appendChild(details);
    });
    const p=document.createElement('p');p.className='workspace-note';p.textContent='Les rubriques liées apparaissent selon vos droits. Les liens IKOS et documentaires utilisent les adresses présentes dans la base ; les exemples fictifs peuvent être indisponibles.';body.appendChild(p);
  }catch(x){erreurPanneau(v,x)}
}

function ajouterEvolution(node,r){
  if(!r.columns.includes('Annee_mois'))return;
  const ys=['Montant_impaye','Montant_loyer','Montant_paiement_moins_remboursement'].filter(c=>r.columns.includes(c));if(!ys.length||r.rows.length<2)return;
  const b=document.createElement('button');b.type='button';b.className='evolution-button';b.textContent='Afficher l’évolution du compte';node.appendChild(b);
  b.onclick=async()=>{
    b.disabled=true;
    try{const mois=new Map();for(const row of r.rows){const m=row.Annee_mois;if(!m)continue;const old=mois.get(m);if(old&&ys.some(c=>old[c]!==row[c]))throw new Error('Plusieurs valeurs existent pour le même mois. Consultez le tableau pour éviter une courbe ambiguë.');mois.set(m,row)}
      await loadChart();if(!node.isConnected)return;
      const box=document.createElement('div');box.className='account-chart';const cv=document.createElement('canvas');cv.setAttribute('role','img');cv.setAttribute('aria-label','Évolution mensuelle des montants, également disponibles dans le tableau');box.appendChild(cv);node.appendChild(box);
      const lignes=[...mois.values()].sort((a,b)=>String(a.Annee_mois).localeCompare(String(b.Annee_mois)));
      new Chart(cv,{type:'line',data:{labels:lignes.map(x=>formatDate(x.Annee_mois)),datasets:ys.map((c,i)=>({label:libelleColonne(c)+' (€)',data:lignes.map(x=>x[c]==null?null:Number(x[c])),borderColor:PAL[i],backgroundColor:PAL[i],tension:.2}))},options:{responsive:true,plugins:{legend:{position:'bottom'}}}});
      b.textContent='Évolution affichée'+(r.truncated?' (historique limité)':'');
    }catch(x){erreurAction(b,x);b.disabled=false}
  };
}

async function ouvrirTaches(au=dateMetier()){
  const v=panneau('À traiter');
  try{const d=await api('/api/espace/a-traiter?au='+encodeURIComponent(au));if(v!==panneauVersion)return;
    const body=$('workspace-body');body.innerHTML=`<p class="workspace-intro">Vos échéances et dossiers à examiner, selon les droits de votre service. Aucune action n’est envoyée automatiquement.</p><label class="reference-date">Date de référence <input type="date" id="tasks-date" value="${esc(d.au)}"></label><div class="task-grid"></div><div id="task-results"></div>`;
    $('tasks-date').onchange=e=>{if(e.target.value)ouvrirTaches(e.target.value)};
    d.cartes.forEach(c=>{const b=document.createElement('button');b.type='button';b.className='task-card';b.disabled=!c.disponible;b.innerHTML=`<span>${esc(c.titre)}</span><strong>${c.disponible?esc(c.total):'—'}</strong><small>${c.disponible?esc(c.description):'Données non accessibles à votre service.'}</small>${c.actualisation?`<small class="data-date">Données au ${esc(formatDate(c.actualisation))}</small>`:''}`;b.onclick=()=>chargerTache(c.code,d.au,v,b);body.querySelector('.task-grid').appendChild(b)});
  }catch(x){erreurPanneau(v,x)}
}
let tacheVersion=0;
async function chargerTache(code,au,v,b){
  const request=++tacheVersion,target=$('task-results');target.innerHTML='<p role="status">Chargement des dossiers…</p>';
  document.querySelectorAll('.task-card').forEach(x=>x.classList.toggle('selected',x===b));
  try{const d=await api(`/api/espace/a-traiter?au=${encodeURIComponent(au)}&categorie=${encodeURIComponent(code)}`);if(v!==panneauVersion||request!==tacheVersion)return;const c=d.cartes[0];target.innerHTML=`<h3>${esc(c.titre)}</h3><p>${esc(c.description)}</p>`;
    if(!c.disponible){target.appendChild(document.createTextNode('Ces données ne sont plus accessibles.'));return}
    const tables={affaires:'Affaire',commandes:'Commande',diagnostics:'Diagnostic',departs:'Bail',mandats:'Copropriete',comptes:'Releve_compte_client_historique'};target.appendChild(tableauEspace(c.resultats,tables[code]));target.scrollIntoView({block:'nearest'});
  }catch(x){if(v===panneauVersion&&request===tacheVersion)target.innerHTML=erreurHTML(x.message)}
}

async function ouvrirFavoris(){
  const v=panneau('Mes recherches favorites');
  try{const favoris=await api('/api/espace/favoris');if(v!==panneauVersion)return;const body=$('workspace-body');body.innerHTML='<p class="workspace-intro">Retrouvez vos recherches et relancez-les avec les données et droits actuels. Le fournisseur sélectionné dans le chat sera utilisé.</p>';
    if(!favoris.length){body.insertAdjacentHTML('beforeend','<div class="workspace-empty">Aucune recherche enregistrée. Sous une réponse du chat, cliquez sur « Enregistrer la recherche ».</div>');return}
    favoris.forEach(f=>{const item=document.createElement('div');item.className='favorite-item';const texte=document.createElement('div');const h=document.createElement('strong');h.textContent=f.label;const p=document.createElement('p');p.textContent=f.question;texte.append(h,p);item.appendChild(texte);
      const run=document.createElement('button');run.type='button';run.textContent='Relancer ↗';run.onclick=()=>{if(sending){run.textContent='Attendez la réponse en cours';return}$('workspace-dialog').close();$('q').value=f.question;$('f').requestSubmit()};
      const del=document.createElement('button');del.type='button';del.className='favorite-delete';del.textContent='Supprimer';del.onclick=async()=>{del.disabled=true;try{await api('/api/espace/favoris/'+f.id,'DELETE');ouvrirFavoris()}catch(x){del.disabled=false;erreurAction(del,x)}};
      item.append(run,del);body.appendChild(item)});
  }catch(x){erreurPanneau(v,x)}
}
$('tasks-open').onclick=()=>ouvrirTaches();$('favorites-open').onclick=()=>ouvrirFavoris();
