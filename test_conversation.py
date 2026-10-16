import pytest
import api
from test_web import web, connecter


@pytest.mark.parametrize("fournisseur", ["gemini", "openai", "groq"])
def test_reponse_generale(web, monkeypatch, fournisseur):
    connecter(web)
    cid = web.client.post('/api/conversations').json()['id']
    monkeypatch.setattr(web.chat, 'generer_sql', lambda *a, **kw: api.ReponseNaturelle(texte='Bonjour ! Comment puis-je vous aider ?'))
    def interdit(*a, **kw):
        raise AssertionError('Aucune requete metier attendue')
    monkeypatch.setattr(web.S, 'run_query', interdit)
    r = web.client.post('/api/ask', json=dict(conv_id=cid, question='Bonjour', fournisseur=fournisseur, veut_reponse=False))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['reponse'].startswith('Bonjour')
    assert d['sql_genere'] is None and d['resultats'] is None
    assert d['texte_en_attente'] is False
    historique = web.client.get('/api/conversations/' + cid).json()['messages']
    assert historique[-1]['reponse'] == d['reponse']


@pytest.mark.parametrize('payload', ['{}', '{"sql":"SELECT 1","reponse":"Bonjour"}', '{"reponse":"   "}'])
def test_sortie_ambigue_refusee(payload):
    with pytest.raises(ValueError):
        api.SQLGenere.model_validate_json(payload)


@pytest.mark.parametrize('fournisseur', ['gemini', 'openai'])
def test_decodage_naturel(monkeypatch, fournisseur):
    from types import SimpleNamespace
    texte = '{"sql":null,"reponse":"Un bail est un contrat de location."}'
    monkeypatch.setattr(api, '_appeler_openai', lambda *a, **kw: texte)
    monkeypatch.setattr(api, '_appeler_et_journaliser', lambda *a, **kw: SimpleNamespace(text=texte))
    r = api.generer_sql("Explique un bail", "schema", [], fournisseur=fournisseur)
    assert isinstance(r, api.ReponseNaturelle)


def test_relance_conserve_definitions_des_criteres_precedents(web, monkeypatch):
    connecter(web)
    cid = web.client.post('/api/conversations').json()['id']
    web.client.post('/api/ask', json=dict(conv_id=cid, question='Liste des clients présents'))
    contextes = []
    monkeypatch.setattr(web.chat, 'contexte_dictionnaire',
                        lambda path, schema, question: contextes.append(question) or '')
    r = web.client.post('/api/ask', json=dict(conv_id=cid, question='Parmi ceux-là, donne les identifiants'))
    assert r.status_code == 200, r.text
    assert 'clients présents' in contextes[-1]
    assert 'Parmi ceux-là' in contextes[-1]
