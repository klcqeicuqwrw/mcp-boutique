import httpx
import pytest

from boutique.erreurs import erreur_ia
from test_web import web, connecter


@pytest.mark.parametrize('status,body,attendu', [
    (401,'invalid_api_key','clé API'),
    (403,'permission_denied','autorisation'),
    (404,'model_not_found','modèle'),
    (429,'credit_balance_exhausted','crédit API'),
    (429,'insufficient_quota','crédit API'),
    (429,'rate_limit_exceeded','limite de requêtes'),
    (503,'overloaded','panne temporaire'),
    (504,'DEADLINE_EXCEEDED','délai'),
    (400,'invalid request','rejeté'),
])
def test_diagnostic_sans_secret(status, body, attendu):
    exc=RuntimeError(body+' sk-secret-test /private/database.sqlite')
    exc.status_code=status
    message=erreur_ia(exc,'openai')
    assert attendu in message
    assert 'sk-secret' not in message and '/private' not in message


def test_reseau_configuration_sql_et_format():
    assert 'clé API est absente' in erreur_ia(RuntimeError('Variable GEMINI_API_KEY manquante.'),'gemini')
    assert 'connexion réseau' in erreur_ia(httpx.ConnectError('private-host'),'gemini')
    assert 'délai' in erreur_ia(httpx.ReadTimeout('secret'),'gemini')
    assert 'inexploitable' in erreur_ia(ValueError('bad json'),'gemini')
    assert 'base' in erreur_ia(RuntimeError('Erreur SQLite : no such column secret'),'gemini','sql')
    assert 'temps autorisé' in erreur_ia(RuntimeError('Requête trop longue'),'gemini','sql')


def test_credit_epuise_api_et_historique(web,monkeypatch):
    connecter(web)
    exc=RuntimeError('credit_balance_exhausted sk-secret')
    exc.status_code=429
    def echec(*a,**kw):
        raise exc
    monkeypatch.setattr(web.chat,'generer_sql',echec)
    cid=web.client.post('/api/conversations').json()['id']
    response=web.client.post('/api/ask',json=dict(conv_id=cid,question='Liste des clients',fournisseur='openai'))
    assert response.status_code==502
    assert 'crédit API' in response.json()['detail']
    historique=web.client.get('/api/conversations/'+cid).json()['messages'][0]
    assert historique['erreur']==response.json()['detail']
    assert 'sk-secret' not in response.text


def test_erreur_sql_ne_blame_pas_cle(web,monkeypatch):
    connecter(web)
    monkeypatch.setattr(web.chat,'generer_sql',lambda *a,**kw:'SELECT pas_de_colonne FROM Client')
    cid=web.client.post('/api/conversations').json()['id']
    response=web.client.post('/api/ask',json=dict(conv_id=cid,question='Liste des clients'))
    assert response.status_code==502
    assert 'requête produite' in response.json()['detail']
    assert 'clé API' not in response.text
