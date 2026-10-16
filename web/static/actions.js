'use strict';

function libelleColonne(colonne){
  const noms={Prenom:'Prénom',Age:'Âge',Residence:'Résidence',Etage:'Étage',Dernier_contact:'Dernier contact',Derniere_ouverture_affaire:'Dernière ouverture d’affaire',Nombre_logements_DPE:'Logements avec ce DPE',Telephone:'Téléphone',Raison_sociale:'Raison sociale',Type_client:'Type de client',Nombre_lots:'Lots',Nom_prenom_client:'Client',Libelle_type_client:'Type de client',Libelle_activite_client:'Activité',Indicateur_statut_presence:'Présence',Raison_sociale_occupant:'Raison sociale',Nom_occupant:'Nom',Prenom_occupant:'Prénom',Type_personne:'Type de personne',Telephone_occupant:'Téléphone',Mail_occupant:'E-mail',Libelle_patrimoine:'Résidence',Libelle_commune:'Commune',Code_postal:'Code postal',Adresse_complete:'Adresse',Libelle_type_lot:'Type de logement',Libelle_usage_lot:'Usage',Surface_habitable:'Surface (m²)',Libelle_etat_actuel:'État',Libelle_objet_affaire:'Objet',Libelle_etat_affaire:'État',Date_ouverture:'Ouverture',Date_theorique_cloture:'Clôture prévue',Code_collaborateur_suivi:'Responsable du suivi',Numero_commande:'Commande',Libelle_objet_commande_1:'Objet',Libelle_tiers:'Prestataire',Taux_execution_commande:'Exécution (%)',Date_fin_execution_commande:'Fin prévue',Montant_TTC:'Montant TTC (€)',Libelle_diagnostic:'Diagnostic',Famille_diagnostic:'Famille',Date_fin_diagnostic:'Échéance',Indicateur_diagnostic_perime:'Périmé',Nom_prenom_collaborateur:'Collaborateur',Libelle_fonction:'Fonction',Mail_collaborateur:'E-mail',Nom_copropriete:'Copropriété',Nom_syndic:'Syndic',Etat_mandat_copropriete:'État du mandat',Date_fin_mandat_copropriete:'Fin du mandat',Tel_syndic:'Téléphone',Mail_syndic:'E-mail',Annee_mois:'Mois',Montant_impaye:'Impayé',Montant_loyer:'Loyer',Montant_charges:'Charges',Montant_paiement_moins_remboursement:'Paiements nets',Libelle_procedure:'Procédure',Libelle_etape_procedure:'Étape',Date_prescription:'Prescription',Date_reception_preavis:'Préavis reçu',Date_fin_occupation_lot:'Fin d’occupation',Indicateur_occupation_active:'Occupation',Libelle_type_bail:'Type de bail'};
  Object.assign(noms,{ID_equipement:'Référence équipement',Age_equipement:'Âge (années)',Indice_priorite:'Indice comparatif / 100',Signaux_365_jours:'Signaux sur 365 jours',Dernier_signal:'Dernier signal'});
  return noms[colonne]||colonne.replaceAll('_',' ');
}

function boutonAction(titre,icone,primaire=false){
  const chemins={mail:'M4 5h16v14H4z M4 6l8 6 8-6',telephone:'M7 3l3 5-2 2c2 3 3 4 6 6l2-2 5 3c-1 4-3 5-6 3C9 17 6 14 3 8c-1-3 0-5 4-5z',sms:'M4 4h16v12H9l-5 4z M8 8h8 M8 12h5',carte:'M12 21s7-7 7-12a7 7 0 0 0-14 0c0 5 7 12 7 12z M9 9a3 3 0 1 0 6 0 3 3 0 1 0-6 0'};
  const b=document.createElement('button');b.type='button';b.className='action-button'+(primaire?' action-primary':'');
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');
  const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',chemins[icone]);svg.appendChild(path);
  const label=document.createElement('span');label.textContent=titre;b.append(svg,label);return b;
}

function preparerMessage(type,destinataire,objet,corps,url){
  let dialogue=$('contact-dialog');
  if(!dialogue){
    dialogue=document.createElement('dialog');dialogue.id='contact-dialog';
    dialogue.innerHTML='<form method="dialog" class="contact-form"><div class="contact-header"><strong id="contact-title"></strong><button value="fermer" aria-label="Fermer">✕</button></div><p>Relisez le brouillon avant de l’ouvrir dans votre messagerie. Aucun message n’est envoyé par cette application.</p><label>Destinataire<input id="contact-destinataire" readonly></label><label id="contact-objet-label">Objet<input id="contact-objet"></label><label>Message<textarea id="contact-corps" rows="7"></textarea></label><div class="contact-footer"><button type="button" id="contact-copier">Copier le message</button><a id="contact-ouvrir" class="contact-action">Ouvrir ma messagerie ↗</a></div><span id="contact-status" role="status"></span></form>';
    document.body.appendChild(dialogue);
    $('contact-copier').onclick=async()=>{
      try{await navigator.clipboard.writeText($('contact-corps').value);$('contact-status').textContent='Message copié.';}
      catch{$('contact-corps').focus();$('contact-corps').select();$('contact-status').textContent='Sélectionnez puis copiez le message avec Ctrl+C.';}
    };
  }
  $('contact-title').textContent=type==='email'?'Préparer un e-mail':'Préparer un SMS';
  $('contact-destinataire').value=destinataire;$('contact-objet').value=objet;$('contact-corps').value=corps;
  $('contact-objet-label').hidden=type!=='email';$('contact-status').textContent='';
  $('contact-ouvrir').href=url;
  $('contact-ouvrir').onclick=()=>{
    $('contact-ouvrir').href=type==='email'?'mailto:'+encodeURIComponent(destinataire)+'?subject='+encodeURIComponent($('contact-objet').value)+'&body='+encodeURIComponent($('contact-corps').value):'sms:'+destinataire+'?body='+encodeURIComponent($('contact-corps').value);
  };
  dialogue.showModal();
}

function ajouterActions(node,message){
  const resultat=message.resultats;if(!resultat)return;
  ajouterOutilsResultat(node,message);
  if(message.id&&resultat.localisation_demandee===true){
    const bouton=boutonAction('Localiser les résultats','carte',true);
    bouton.onclick=()=>window.open('/carte?message_id='+encodeURIComponent(message.id),'_blank','noopener');
    const barre=document.createElement('div');barre.className='result-actions';barre.appendChild(bouton);node.insertBefore(barre,node.querySelector('.tw'));
  }
  const table=node.querySelector('table');if(!table)return;
  const norm=c=>c.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z]/g,'');
  const emailCols=resultat.columns.filter(c=>['email','mailoccupant','mailclient','mailsyndic','mailtiers','mailcollaborateur','mail'].includes(norm(c)));
  const telCols=resultat.columns.filter(c=>['telephone','telephoneoccupant','telephoneclient','telephonefixetiers','telephoneportabletiers','telsyndic','tel','numerotelephone'].includes(norm(c)));
  if(!emailCols.length&&!telCols.length)return;
  const th=document.createElement('th');th.textContent='Contacter';table.querySelector('thead tr').appendChild(th);
  [...table.querySelectorAll('tbody tr')].forEach((tr,i)=>{
    const row=resultat.rows[i],td=document.createElement('td');td.className='contact-cell';
    const emailCol=emailCols.find(c=>/^[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+$/.test(String(row[c]??'').trim()));
    const telCol=telCols.find(c=>/^[+\d\s().-]+$/.test(String(row[c]??'').trim())&&/^\+?\d{8,15}$/.test(String(row[c]).replace(/[^+\d]/g,'')));
    const email=String(row[emailCol]??'').trim(),brutTel=String(row[telCol]??'').trim();
    const tel=/^[+\d\s().-]+$/.test(brutTel)?brutTel.replace(/[^+\d]/g,''):'';
    const morale=resultat.columns.some(c=>norm(c).startsWith('raisonsociale'))||String(row.Type_personne||row.Libelle_type_client||'').toLowerCase().includes('morale');
    const corps=morale?'Bonjour,\n\nNous souhaitons faire un point avec votre structure concernant les locaux que vous occupez. Pourriez-vous contacter votre interlocuteur habituel chez Aiguillon ?\n\nBien cordialement,\nVotre équipe de proximité':'Bonjour,\n\nNous souhaitons prendre de vos nouvelles et vérifier si vous avez besoin d’un accompagnement. Pourriez-vous contacter votre interlocuteur habituel chez Aiguillon ?\n\nBien cordialement,\nVotre équipe de proximité';
    if(/^[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+$/.test(email)){
      const objet=morale?'Prise de contact — votre équipe de proximité':'Prise de nouvelles — votre équipe de proximité';
      const prestataire=norm(emailCol)==='mailtiers',collegue=norm(emailCol)==='mailcollaborateur';
      const bouton=boutonAction(prestataire?'Relancer le prestataire':collegue?'Contacter le collègue':'Mail','mail');
      const reference=row.Numero_commande||row.ID_commande||message.reference||'';
      const sujet=prestataire?'Suivi de commande '+reference:collegue?'Suivi du dossier '+reference:objet;
      const contenu=prestataire?`Bonjour,\n\nPouvez-vous nous informer de l’avancement de la commande ${reference} ?\nObjet : ${row.Libelle_objet_commande_1||'à préciser'}\nFin prévue : ${row.Date_fin_execution_commande||'à préciser'}\n\nMerci de nous confirmer les prochaines étapes.\n\nBien cordialement`:collegue?`Bonjour,\n\nJe souhaite faire un point sur le dossier ${reference}.\nPourrais-tu me recontacter à ce sujet ?\n\nMerci`:corps;
      bouton.onclick=()=>preparerMessage('email',email,sujet,contenu,'mailto:'+encodeURIComponent(email));td.appendChild(bouton);
    }
    if(/^\+?\d{8,15}$/.test(tel)){
      const appel=boutonAction('Appel','telephone');appel.onclick=()=>{location.href='tel:'+tel;};td.appendChild(appel);
      const texte=morale?'Bonjour, votre équipe Aiguillon souhaite faire un point avec votre structure. Merci de contacter votre interlocuteur habituel.':'Bonjour, votre équipe Aiguillon souhaite prendre de vos nouvelles. Merci de contacter votre interlocuteur habituel.';
      const bouton=boutonAction('SMS','sms');
      bouton.onclick=()=>preparerMessage('sms',tel,'',texte,'sms:'+tel);td.appendChild(bouton);
    }
    if(!td.children.length)td.textContent='Coordonnées à compléter';
    tr.appendChild(td);
  });
}

