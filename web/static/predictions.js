'use strict';

const eurosPrediction=v=>new Intl.NumberFormat('fr-FR',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(v);
const moisPrediction=v=>new Intl.DateTimeFormat('fr-FR',{month:'long',year:'numeric',timeZone:'Europe/Paris'}).format(new Date(v+'T12:00:00Z'));

function limitesPrediction(limites){return '<details class="prediction-method"><summary>Méthode, qualité des données et limites</summary><ul>'+limites.map(t=>'<li>'+esc(t)+'</li>').join('')+'</ul></details>'}

async function ouvrirPredictions(au=dateMetier()){
  const v=panneau('Prévisions expérimentales');
  $('workspace-body').innerHTML='<p class="workspace-intro" role="status">Analyse des historiques et entraînement des modèles locaux…</p>';
  try{
    const d=await api('/api/espace/predictions?au='+encodeURIComponent(au));if(v!==panneauVersion)return;
    const body=$('workspace-body');body.innerHTML=`<p class="prediction-notice">Prototype sur données fictives. Ces estimations servent à explorer les données et à préparer une vérification humaine.</p><label class="reference-date">Date de référence <input type="date" id="predictions-date" value="${esc(d.au)}"></label><p class="workspace-intro prediction-local">Calculs réalisés sur le serveur de l’application, selon vos droits d’accès.</p>`;
    $('predictions-date').onchange=e=>{if(e.target.value)ouvrirPredictions(e.target.value)};
    afficherImpayes(body,d.impayes,v);
    afficherEquipements(body,d.equipements,d.au);
  }catch(x){erreurPanneau(v,x)}
}

function afficherImpayes(body,p,v){
  const section=document.createElement('section');section.className='prediction-section';section.innerHTML='<h3>Évolution des impayés</h3>';
  if(!p.disponible){const msg=document.createElement('p');msg.className='workspace-empty';msg.textContent=p.raison;section.appendChild(msg);body.appendChild(section);return}
  section.innerHTML+=`<p class="prediction-period">${p.projection_historique?'Projection historique':'Projection à un mois'} · ${esc(moisPrediction(p.mois_projection))}</p>${p.projection_historique?'<p class="prediction-caution">Les historiques sont anciens : cette projection porte sur le mois suivant les dernières données comparables, pas sur le prochain mois actuel.</p>':''}<div class="prediction-metrics"><div><small>Impayés projetés</small><strong>${esc(eurosPrediction(p.montant_prevu))}</strong><span>${p.variation_euros>=0?'+':''}${esc(eurosPrediction(p.variation_euros))}${p.variation_pourcent!=null?' · '+esc(p.variation_pourcent)+' %':''}</span></div><div><small>Dernier mois comparable</small><strong>${esc(eurosPrediction(p.montant_actuel))}</strong><span>${esc(moisPrediction(p.mois_base))}</span></div><div><small>Périmètre fixe</small><strong>${esc(p.clients)}</strong><span>clients présents sur les mois comparés</span></div></div>`;
  const graph=document.createElement('div');graph.className='prediction-chart';section.appendChild(graph);
  const tableau=document.createElement('div');tableau.className='tw';tableau.innerHTML=`<table><thead><tr><th>Mois</th><th>Nature</th><th>Impayés du périmètre</th></tr></thead><tbody>${p.historique.map(r=>`<tr><td>${esc(moisPrediction(r.mois))}</td><td>Historique fictif</td><td>${esc(eurosPrediction(r.montant))}</td></tr>`).join('')}<tr class="prediction-row"><td>${esc(moisPrediction(p.mois_projection))}</td><td>Projection du modèle</td><td>${esc(eurosPrediction(p.montant_prevu))}</td></tr></tbody></table>`;section.appendChild(tableau);
  const validation=document.createElement('p');validation.className='prediction-validation';
  validation.textContent=p.validation.disponible?`Test chronologique sur ${p.validation.observations} transitions vers ${moisPrediction(p.validation.mois)} : erreur moyenne ${eurosPrediction(p.validation.erreur_moyenne_euros)} par client, contre ${eurosPrediction(p.validation.erreur_reference_euros)} en conservant l’impayé inchangé. ${p.validation.ameliore_reference?'Amélioration sur ce seul test ; elle reste à confirmer.':'Le modèle ne fait pas mieux que cette référence.'}`:p.validation.raison;
  section.appendChild(validation);
  section.insertAdjacentHTML('beforeend',limitesPrediction([p.methode+' ; '+p.transitions_apprentissage+' transitions pour l’apprentissage.', 'Variables autorisées : '+p.variables.map(libelleColonne).join(', ')+'.',...p.limites]));
  const details=document.createElement('details');details.className='prediction-method';details.innerHTML=`<summary>Couverture des mois et contrôle des données</summary><div class="tw"><table><thead><tr><th>Mois</th><th>Clients observés</th><th>Couverture comparable</th></tr></thead><tbody>${p.audit.couverture_mensuelle.map(r=>`<tr><td>${esc(moisPrediction(r.mois))}</td><td>${esc(r.clients)}</td><td>${r.retenu?'Retenue':'Écartée'}</td></tr>`).join('')}</tbody></table></div><p>${esc(p.audit.lignes_invalides)} ligne(s) invalide(s) et ${esc(p.audit.client_mois_contradictoires)} couple(s) client/mois contradictoire(s) exclus.</p>`;section.appendChild(details);
  body.appendChild(section);
  (async()=>{try{await loadChart();if(v!==panneauVersion||!graph.isConnected)return;const cv=document.createElement('canvas');cv.setAttribute('role','img');cv.setAttribute('aria-label','Historique et projection des impayés, également disponibles dans le tableau');graph.appendChild(cv);
    const base=p.historique.map(r=>r.montant),projection=Array(base.length-1).fill(null).concat([base.at(-1),p.montant_prevu]);
    new Chart(cv,{type:'line',data:{labels:p.historique.map(r=>moisPrediction(r.mois)).concat(moisPrediction(p.mois_projection)),datasets:[{label:'Historique fictif (€)',data:base.concat(null),borderColor:'#1E1214',backgroundColor:'#1E1214',tension:0},{label:'Projection expérimentale (€)',data:projection,borderColor:'#E62A00',backgroundColor:'#E62A00',borderDash:[6,5],tension:0}]},options:{responsive:true,animation:false,maintainAspectRatio:false,scales:{y:{beginAtZero:true}},plugins:{legend:{position:'bottom'}}}});
  }catch{graph.textContent='Courbe indisponible. Les valeurs restent consultables dans le tableau.'}})();
}

function afficherEquipements(body,p,au){
  const section=document.createElement('section');section.className='prediction-section';section.innerHTML='<h3>Équipements : priorité de contrôle</h3>';
  if(!p.disponible){const msg=document.createElement('p');msg.className='workspace-empty';msg.textContent=p.raison;section.appendChild(msg);if(p.audit){const note=document.createElement('p');note.className='workspace-note';note.textContent=`${p.audit.signaux_rapproches||0} signalement(s) de panne rapproché(s). Il faut des pannes datées et rattachées à un équipement pour estimer un risque fiable.`;section.appendChild(note)}body.appendChild(section);return}
  const directs=p.mode_labels==='directs';
  section.innerHTML+=`<p class="prediction-period">Horizon exploratoire : 90 jours après le ${esc(formatDate(p.date_reference_modele||au))}, jusqu’au ${esc(formatDate(p.jusqu_au))}</p><p class="prediction-caution">L’indice classe les équipements entre eux. Un indice de 90 n’est pas une probabilité de panne de 90 %. ${directs?'Le modèle utilise des pannes datées liées à chaque équipement et des périodes de suivi explicites. Ces historiques sont simulés.':'Le modèle apprend des signalements rapprochés, pas des pannes certifiées.'}</p><div class="prediction-metrics"><div><small>Équipements comparables</small><strong>${esc(p.equipements_estimables)}</strong><span>éligibles à l’indice expérimental</span></div><div><small>Non estimables</small><strong>${esc(p.equipements_non_estimables)}</strong><span>hors périmètre ou données insuffisantes</span></div><div><small>${directs?'Pannes simulées liées':'Signaux rapprochés'}</small><strong>${esc(p.audit.signaux_rapproches)}</strong><span>${directs?'Suivi couvert jusqu’au '+esc(formatDate(p.audit.fin_observation)):'Dernière intervention : '+esc(formatDate(p.audit.derniere_intervention))}</span></div></div>`;
  const validation=document.createElement('p');validation.className='prediction-validation';validation.textContent=p.validation.disponible?`Test du ${formatDate(p.validation.debut)} au ${formatDate(p.validation.fin)} : AUC ${p.validation.auc}, sur ${p.validation.observations} observations et ${p.validation.signaux_positifs} cas positifs. ${directs?'Cette mesure porte sur les pannes simulées ; elle ne démontre pas la fiabilité sur des équipements réels.':'Cette mesure porte sur le signal indirect, pas sur une probabilité de panne physique.'}`:'Qualité prédictive non établie : '+p.validation.raison;section.appendChild(validation);
  COLONNES_ESPACE.Prediction_equipement=['ID_equipement','Libelle_type_equipement','Age_equipement','Indice_priorite','Signaux_365_jours','Dernier_signal'];
  section.appendChild(tableauEspace(p.resultats,'Prediction_equipement'));
  const details=document.createElement('details');details.className='prediction-method';details.innerHTML=`<summary>Types d’équipement couverts</summary><div class="tw"><table><thead><tr><th>Type</th><th>Inventaire</th><th>Éligibles à l’indice</th></tr></thead><tbody>${p.couverture.map(r=>`<tr><td>${esc(r.type)}</td><td>${esc(r.total)}</td><td>${esc(r.estimables)}</td></tr>`).join('')}</tbody></table></div>`;section.appendChild(details);
  section.insertAdjacentHTML('beforeend',limitesPrediction([p.methode+' ; '+p.exemples_apprentissage+' observations équipement/période.', 'Variables : âge, type, signaux des 90 et 365 derniers jours, délai depuis le dernier signal.',...p.limites]));
  body.appendChild(section);
}
$('predictions-open').onclick=()=>ouvrirPredictions();
