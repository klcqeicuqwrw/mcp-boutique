from types import SimpleNamespace as NS

import pytest
import api
from boutique.erreurs import erreur_ia
from test_web import web, connecter


def faux_client(monkeypatch, contenu, fin="stop"):
    appels = []
    def create(**kw):
        appels.append(kw)
        return NS(choices=[NS(message=NS(content=contenu), finish_reason=fin)],
                  usage=NS(prompt_tokens=10, completion_tokens=5, total_tokens=15))
    monkeypatch.setattr(api, "obtenir_client_groq", lambda: NS(chat=NS(completions=NS(create=create))))
    return appels


@pytest.mark.parametrize("contenu, naturel", [('{"sql":"SELECT 1","reponse":null}', False),
                                             ('{"sql":null,"reponse":"Bonjour !"}', True)])
def test_generation_et_journal(monkeypatch, contenu, naturel):
    appels = faux_client(monkeypatch, contenu)
    logs = []
    r = api.generer_sql("Question", "Schema", [], fournisseur="groq", log=lambda **kw: logs.append(kw))
    assert isinstance(r, api.ReponseNaturelle) == naturel
    assert appels[0]["response_format"] == {"type": "json_object"}
    assert appels[0]["messages"][0]["role"] == "system"
    assert logs[0]["model"].startswith("groq/")
    assert logs[0]["total_tokens"] == 15


def test_synthese_utilise_groq(monkeypatch):
    appels = faux_client(monkeypatch, "Il y a deux clients.")
    r = api.formuler_reponse("Explique le resultat", dict(columns=["n"], rows=[{"n": 2}],
                             row_count=1, fournisseur_ia="groq"), sql="SELECT COUNT(*) AS n FROM Client")
    assert r == "Il y a deux clients."
    assert "response_format" not in appels[0]


@pytest.mark.parametrize("contenu, fin", [("", "stop"), ('{"sql":"SELECT 1"}', "length"),
                                        ('{"sql":"SELECT 1","reponse":"Bonjour"}', "stop")])
def test_sorties_inexploitables(monkeypatch, contenu, fin):
    faux_client(monkeypatch, contenu, fin)
    with pytest.raises(ValueError):
        api.generer_sql("Question", "Schema", [], fournisseur="groq")


def test_configuration(monkeypatch):
    import openai
    configurations = []
    monkeypatch.setattr(api, "client_groq", None)
    monkeypatch.setenv("GROQ_API_KEY", "cle-test")
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "25")
    monkeypatch.setattr(openai, "OpenAI", lambda **kw: configurations.append(kw) or object())
    api.obtenir_client_groq()
    assert configurations == [dict(api_key="cle-test", base_url="https://api.groq.com/openai/v1",
                                    timeout=25, max_retries=0)]


def test_parcours_http_et_permissions(web, monkeypatch):
    connecter(web)
    cid = web.client.post('/api/conversations').json()['id']
    fournisseurs = []
    def generer(*a, **kw):
        fournisseurs.append(kw['fournisseur'])
        return 'SELECT Montant_HT FROM Commande'
    monkeypatch.setattr(web.chat, 'generer_sql', generer)
    r = web.client.post('/api/ask', json=dict(conv_id=cid, question='Liste des commandes', fournisseur='groq'))
    assert r.status_code == 403
    assert fournisseurs == ['groq']


def test_erreur_groq_sans_secret():
    exc = RuntimeError("GROQ_API_KEY manquante gsk_secret")
    message = erreur_ia(exc, 'groq')
    assert 'Groq' in message and 'gsk_secret' not in message


def test_contexte_compact_conserve_schema_et_borne_prompt(monkeypatch):
    # Grand schéma entièrement fictif : toutes ses colonnes doivent rester disponibles.
    schema = '\n'.join(f'Table_{i}(' + ', '.join(f'Colonne_{j} TEXT' for j in range(25)) + ')'
                       for i in range(29))
    hist = [api.MessageHistorique(role=role, content='x' * 4000)
            for role in ('user', 'assistant')]
    appels = faux_client(monkeypatch, '{"sql":"SELECT Colonne_0 FROM Table_0","reponse":null}')
    api.generer_sql('Liste Table_0', schema, hist, dictionnaire='Definition autorisee\n' * 900,
                    fournisseur='groq')
    messages = appels[0]['messages']
    prompt = messages[1]['content']
    assert len(prompt) + len(messages[0]['content']) < 20000
    for i in range(29):
        assert f'Table_{i}(' in prompt
    for j in range(25):
        assert f'Colonne_{j}' in prompt
    assert 'échange absent' in prompt
    assert appels[0]['max_completion_tokens'] == 1024


def test_question_trop_longue_ne_perd_pas_de_texte(monkeypatch):
    def interdit():
        raise AssertionError('Aucun appel reseau attendu')
    monkeypatch.setattr(api, 'obtenir_client_groq', interdit)
    with pytest.raises(api.ContexteGroqTropLong):
        api.generer_sql('question' * 4000, 'Exemple(id INTEGER)', [], fournisseur='groq')


def test_diagnostic_413_et_contexte():
    exc = RuntimeError('Request too large secret')
    exc.status_code = 413
    for erreur in (exc, api.ContexteGroqTropLong('secret')):
        message = erreur_ia(erreur, 'groq')
        assert 'taille de contexte' in message and 'Groq' in message
        assert 'secret' not in message
