import sqlite3
from pathlib import Path

from dictionnaire import lire_dictionnaire, contexte_dictionnaire

ROOT = Path(__file__).parent
DICO = ROOT / "Dictionnaire_donnees_DWH_fictive_SQLite.md"


def test_dictionnaire_reel_couvre_base_et_marque_donnees_sensibles():
    dico = lire_dictionnaire(DICO)
    with sqlite3.connect((ROOT / "DWH_fictive_10000_lignes.sqlite").resolve().as_uri() + "?mode=ro", uri=True) as c:
        tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        assert len(tables) == len(dico) == 28
        for t in tables:
            assert {r[1].lower() for r in c.execute(f'PRAGMA table_info("{t}")')} == {x["nom"].lower() for x in dico[t.lower()]["colonnes"]}
    assert {"nom_occupant", "prenom_occupant", "mail_occupant", "telephone_occupant"} <= dico["occupant"]["rgpd"]
    assert "nom_prenom_client" in dico["client"]["rgpd"]


def test_contexte_filtre_et_borne():
    texte = contexte_dictionnaire(DICO, {"client": {"indicateur_statut_presence"}}, "Clients présents", limite=3000)
    assert "Indicateur_statut_presence" in texte
    assert "Nom_prenom_client" not in texte and "Occupant" not in texte
    assert len(texte) <= 3000


def test_ancien_format_tableau(tmp_path):
    p = tmp_path / "d.md"
    p.write_text("### Exemple\n| Colonne | Type | Clés | Description |\n|---|---|---|---|\n| `nom` | TEXT | RGPD | Nom |", encoding="utf-8")
    assert lire_dictionnaire(p)["exemple"]["rgpd"] == {"nom"}


def test_mcp_protege_les_colonnes_du_dictionnaire_reel(monkeypatch, tmp_path):
    import server
    import pytest
    monkeypatch.setattr(server, "DB_PATH", ROOT / "DWH_fictive_10000_lignes.sqlite")
    monkeypatch.setattr(server, "DICO_PATH", DICO)
    monkeypatch.setattr(server, "BLOQUER_RGPD", True)
    monkeypatch.setattr(server, "TABLES_AUTORISEES", set())
    monkeypatch.setattr(server, "_dico_cache", None)
    monkeypatch.setattr(server, "_dico_mtime", None)
    monkeypatch.setattr(server, "JOURNAL_PATH", tmp_path / "journal.log")
    assert not server.verifier_demarrage()
    for col in ("Nom_occupant", "Mail_occupant", "Telephone_occupant"):
        with pytest.raises(PermissionError):
            server._executer(f"SELECT {col} FROM Occupant", "test")
    assert server._executer("SELECT COUNT(*) AS n FROM Occupant", "test")["rows"] == [{"n": 400}]
