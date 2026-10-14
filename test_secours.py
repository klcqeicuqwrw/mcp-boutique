"""Secours IA borné, résultats vides et permissions : aucun appel réseau."""
from types import SimpleNamespace

import pytest
import api
from test_web import web, connecter


def envoyer(web, question="Liste des clients"):
    connecter(web)
    cid = web.client.post('/api/conversations').json()['id']
    return web.client.post('/api/ask', json=dict(conv_id=cid, question=question))


def configurer(web, monkeypatch, premier, second):
    appels = []
    def generer(question, schema, historique, **kw):
        fournisseur = kw.get('fournisseur', 'gemini')
        appels.append(dict(kw, fournisseur=fournisseur, schema=schema, historique=historique))
        valeur = second if fournisseur == 'openai' else premier
        if isinstance(valeur, Exception):
            raise valeur
        return valeur
    monkeypatch.setattr(web.chat, 'generer_sql', generer)
    return appels


@pytest.mark.parametrize('fournisseur', ['gemini', 'openai'])
def test_selection_exclusive(web, monkeypatch, fournisseur):
    appels = configurer(web, monkeypatch, 'SELECT ID_client FROM Client', 'SELECT ID_client FROM Client')
    connecter(web)
    cid = web.client.post('/api/conversations').json()['id']
    r = web.client.post('/api/ask', json=dict(conv_id=cid, question='Liste des clients', fournisseur=fournisseur))
    assert r.status_code == 200, r.text
    assert [a['fournisseur'] for a in appels] == [fournisseur]
    assert r.json()['resultats']['fournisseur_ia'] == fournisseur


@pytest.mark.parametrize('sql', [RuntimeError('Indisponible'), 'SELECT colonne_inconnue FROM Client'])
def test_erreur_sans_secours(web, monkeypatch, sql):
    appels = configurer(web, monkeypatch, sql, 'SELECT ID_client FROM Client')
    assert envoyer(web).status_code == 502
    assert len(appels) == 1


def test_vide_sans_secours(web, monkeypatch):
    appels = configurer(web, monkeypatch, "SELECT ID_client FROM Client WHERE ID_client='absent'", RuntimeError('Inutile'))
    r = envoyer(web)
    assert r.status_code == 200 and r.json()['resultats']['rows'] == []
    assert len(appels) == 1


def test_permissions(web, monkeypatch):
    appels = configurer(web, monkeypatch, 'SELECT Montant_HT FROM Commande', 'SELECT ID_client FROM Client')
    assert envoyer(web).status_code == 403
    assert len(appels) == 1


def test_fournisseur_invalide(web):
    connecter(web)
    cid = web.client.post('/api/conversations').json()['id']
    assert web.client.post('/api/ask', json=dict(conv_id=cid, question='Liste', fournisseur='autre')).status_code == 422


def test_cache_separe_par_fournisseur(web, monkeypatch):
    appels = configurer(web, monkeypatch, 'SELECT ID_client FROM Client', 'SELECT ID_client FROM Client')
    connecter(web)
    for fournisseur in ['gemini', 'openai', 'gemini']:
        cid = web.client.post('/api/conversations').json()['id']
        r = web.client.post('/api/ask', json=dict(conv_id=cid, question='Liste des clients', fournisseur=fournisseur))
        assert r.status_code == 200
    assert [a['fournisseur'] for a in appels] == ['gemini', 'openai']


def test_contrat_openai_et_journal(monkeypatch):
    demandes, journaux = [], []
    def create(**kw):
        demandes.append(kw)
        return SimpleNamespace(output_text='{"sql":"SELECT 1"}', status='completed',
                               usage=SimpleNamespace(input_tokens=20, output_tokens=5, total_tokens=25))
    monkeypatch.setattr(api, 'obtenir_client_openai', lambda: SimpleNamespace(responses=SimpleNamespace(create=create)))
    sql = api.generer_sql('Compte', 'Schema autorisé', [], fournisseur='openai', log=lambda **kw: journaux.append(kw), verification='Résultat vide')
    assert sql == 'SELECT 1'
    assert demandes[0]['store'] is False
    assert demandes[0]['text']['format']['strict'] is True
    assert 'Ne retire aucun filtre' in demandes[0]['input']
    assert journaux[0]['model'].startswith('openai/') and journaux[0]['total_tokens'] == 25


@pytest.mark.parametrize('contenu,statut', [('', 'completed'), ('Texte partiel', 'incomplete'), ('  ', 'completed')])
def test_refus_ou_sortie_incomplete_non_exploitee(monkeypatch, contenu, statut):
    monkeypatch.setattr(api, 'obtenir_client_openai', lambda: SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: SimpleNamespace(output_text=contenu, status=statut, usage=None))))
    logs = []
    with pytest.raises(ValueError):
        api.generer_sql('Question', 'Schema', [], fournisseur='openai', log=lambda **kw: logs.append(kw))
    assert len(logs) == 1 and logs[0]['erreur']


def test_client_openai_sans_retries_et_delai(monkeypatch):
    import openai
    configurations = []
    monkeypatch.setenv('OPENAI_API_KEY', 'cle-factice-non-utilisee')
    monkeypatch.setenv('OPENAI_TIMEOUT_SECONDS', '25')
    monkeypatch.setattr(api, 'client_openai', None)
    monkeypatch.setattr(openai, 'OpenAI', lambda **kw: configurations.append(kw) or object())
    api.obtenir_client_openai()
    assert configurations[0]['max_retries'] == 0 and configurations[0]['timeout'] == 25


def test_synthese_sans_secours(monkeypatch):
    def erreur(*a, **kw):
        raise RuntimeError('Gemini')
    monkeypatch.setattr(api, '_appeler_et_journaliser', erreur)
    appels = []
    monkeypatch.setattr(api, '_appeler_openai', lambda *a, **kw: appels.append(a))
    r = dict(columns=['nombre'], rows=[{'nombre': 2}], row_count=1, truncated=False)
    with pytest.raises(RuntimeError):
        api.formuler_reponse('Explique le resultat', r, sql='SELECT 2 AS nombre')
    assert appels == []
