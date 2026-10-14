'use strict';

function libelleColonne(colonne){
  return ({Prenom:'Prénom',Age:'Âge',Residence:'Résidence',Etage:'Étage',Dernier_contact:'Dernier contact',Telephone:'Téléphone',Raison_sociale:'Raison sociale',Type_client:'Type de client',Nombre_lots:'Lots'})[colonne]||colonne.replaceAll('_',' ');
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
  if(message.id&&resultat.localisation_demandee===true){
    const bouton=boutonAction('Localiser les résultats','carte',true);
    bouton.onclick=()=>window.open('/carte?message_id='+encodeURIComponent(message.id),'_blank','noopener');
    const barre=document.createElement('div');barre.className='result-actions';barre.appendChild(bouton);node.insertBefore(barre,node.querySelector('.tw'));
  }
  const table=node.querySelector('table');if(!table)return;
  const norm=c=>c.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z]/g,'');
  const emailCol=resultat.columns.find(c=>['email','mailoccupant','mailclient','mailsyndic','mailtiers','mail'].includes(norm(c)));
  const telCol=resultat.columns.find(c=>['telephone','telephoneoccupant','telephoneclient','tel','numerotelephone'].includes(norm(c)));
  if(!emailCol&&!telCol)return;
  const th=document.createElement('th');th.textContent='Contacter';table.querySelector('thead tr').appendChild(th);
  [...table.querySelectorAll('tbody tr')].forEach((tr,i)=>{
    const row=resultat.rows[i],td=document.createElement('td');td.className='contact-cell';
    const email=String(row[emailCol]??'').trim(),brutTel=String(row[telCol]??'').trim();
    const tel=/^[+\d\s().-]+$/.test(brutTel)?brutTel.replace(/[^+\d]/g,''):'';
    const morale=resultat.columns.some(c=>norm(c)==='raisonsociale');
    const corps=morale?'Bonjour,\n\nNous souhaitons faire un point avec votre structure concernant les locaux que vous occupez. Pourriez-vous contacter votre interlocuteur habituel chez Aiguillon ?\n\nBien cordialement,\nVotre équipe de proximité':'Bonjour,\n\nNous souhaitons prendre de vos nouvelles et vérifier si vous avez besoin d’un accompagnement. Pourriez-vous contacter votre interlocuteur habituel chez Aiguillon ?\n\nBien cordialement,\nVotre équipe de proximité';
    if(/^[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+$/.test(email)){
      const objet=morale?'Prise de contact — votre équipe de proximité':'Prise de nouvelles — votre équipe de proximité';
      const bouton=boutonAction('Mail','mail');
      bouton.onclick=()=>preparerMessage('email',email,objet,corps,'mailto:'+encodeURIComponent(email));td.appendChild(bouton);
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

