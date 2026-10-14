"""Ajout reproductible de 12 personnes morales dans la base fictive."""
from datetime import datetime
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "DWH_fictive_10000_lignes.sqlite"
DICO = ROOT / "Dictionnaire_donnees_DWH_fictive_SQLite.md"
ENTITES = [
    ("Association Demo Solidarite Habitat", "Association", "Accompagnement social"),
    ("Association Demo Passerelle", "Association", "Hebergement accompagne"),
    ("Association Demo Vie de Quartier", "Association", "Animation de quartier"),
    ("Association Demo Tremplin", "Association", "Insertion professionnelle"),
    ("SCI Demo Les Tilleuls", "SCI", "Gestion immobiliere"),
    ("SCI Demo Horizon", "SCI", "Gestion immobiliere"),
    ("SCI Demo Les Jardins", "SCI", "Gestion immobiliere"),
    ("SCI Demo Bellevue", "SCI", "Gestion immobiliere"),
    ("SARL Demo Habitat Services", "SARL", "Logement de salaries"),
    ("SARL Demo Proximite", "SARL", "Logement de salaries"),
    ("SAS Demo Mobilite", "SAS", "Logement temporaire de salaries"),
    ("SAS Demo Residence", "SAS", "Logement de salaries"),
]


def inserer(c, table, valeurs):
    colonnes = ','.join('"' + col + '"' for col in valeurs)
    c.execute(f'INSERT INTO "{table}" ({colonnes}) VALUES ({",".join("?" for _ in valeurs)})', tuple(valeurs.values()))


def dictionnaire(c):
    texte = DICO.read_text(encoding="utf-8")
    for table in ("Client", "Occupant", "Client_lot_pivot"):
        motif = rf"(^## {table}\s*\n)(.*?)(?=^## |\Z)"
        def section(m):
            bloc = m[2]
            total = c.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            bloc = re.sub(r"Nombre de lignes : \d+", f"Nombre de lignes : {total}", bloc, count=1)
            def colonne(cm):
                nom, typ, suite = cm[1], cm[2], cm[3]
                nulls, distincts = c.execute(f'SELECT SUM("{nom}" IS NULL), COUNT(DISTINCT "{nom}") FROM "{table}"').fetchone()
                entete = f'- {nom} — Type SQLite : {typ}. NULL observés : {"oui" if nulls else "non"} ({nulls}/{total}). Valeurs distinctes non NULL : {distincts}.'
                if nom in ("Libelle_type_client", "Code_type_client", "Libelle_activite_client", "Type_personne", "Libelle_forme_juridique_occupant"):
                    valeurs = c.execute(f'SELECT "{nom}", COUNT(*) FROM "{table}" WHERE "{nom}" IS NOT NULL GROUP BY 1 ORDER BY COUNT(*) DESC, 1').fetchall()
                    ligne = '   Valeurs observées (effectif) : ' + ' ; '.join(f'{v} ({n})' for v, n in valeurs)
                    suite = re.sub(r'^   Valeurs observées[^\n]*', lambda _: ligne, suite, flags=re.M)
                    if 'Valeurs observées' not in suite:
                        suite = suite.rstrip() + '\n' + ligne + '\n'
                if nom == "Nom_prenom_client":
                    suite = suite.replace('Description : Nom et prénom', 'Description : Nom et prénom pour une personne physique, raison sociale pour une personne morale')
                return entete + suite
            bloc = re.sub(r'^- (\w+) — Type SQLite : ([^.]+)\.[^\n]*(\n.*?)(?=^- |\Z)', colonne, bloc, flags=re.M | re.S)
            return m[1] + bloc
        texte = re.sub(motif, section, texte, flags=re.M | re.S)
    return texte


def main():
    sauvegardes = ROOT / ".backups"
    sauvegardes.mkdir(exist_ok=True)
    backup = sauvegardes / f'personnes-morales-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite'
    with sqlite3.connect(BASE) as c:
        with sqlite3.connect(backup) as destination:
            c.backup(destination)
        c.execute('BEGIN IMMEDIATE')
        avant = c.execute('SELECT COUNT(*) FROM Client').fetchone()[0]
        ajoutes = 0
        for i, (nom, forme, activite) in enumerate(ENTITES, 1):
            code = f'{990000 + i:06d}'
            societe = ("AJ", "AC", "BSH", "MF1")[(i - 1) % 4]
            ident = f'{societe}-{code}'
            if c.execute('SELECT 1 FROM Client WHERE ID_client=?', (ident,)).fetchone():
                existant = c.execute('SELECT Nom_prenom_client, Libelle_type_client FROM Client WHERE ID_client=?', (ident,)).fetchone()
                assert existant == (nom, 'Personne morale'), f'Identifiant deja utilise : {ident}'
                continue
            lot = c.execute('SELECT ID_lot FROM Lot WHERE Code_societe=? ORDER BY ID_lot LIMIT 1 OFFSET ?', (societe, (i - 1) // 4)).fetchone()[0]
            lien = f'CLT-{ident}-LOT-{lot}'
            date = '2026-10-14 12:00:00.000'
            inserer(c, 'Client', dict(ID_client_lot=lien, ID_client=ident, Code_societe=societe, Code_client=code,
                Nom_prenom_client=nom, Libelle_activite_client=activite, Code_type_client='PM', Libelle_type_client='Personne morale',
                Date_debut_occupation='2026-10-14', Date_fin_occupation='2099-12-31', Indicateur_statut_presence='Présent', Date_actualisation=date))
            inserer(c, 'Client_lot_pivot', dict(ID_client_lot=lien, ID_client=ident, ID_lot=lot, Type_pivot='CLT-LOT', Date_actualisation=date))
            inserer(c, 'Occupant', dict(ID_occupant=f'{ident}-OCC-0001', ID_client=ident, Code_societe=societe, Code_client=code,
                Code_occupant=f'PM{i:04d}', Type_personne='Morale', Libelle_forme_juridique_occupant=forme,
                Raison_sociale_occupant=nom, Qualification_occupant='Occupant', Indicateur_rattachement_client='Oui',
                Date_debut_rattachement_client='2026-10-14', Date_fin_rattachement_client='2099-12-31',
                Mail_occupant=f'demo-pm-{i:02d}@example.invalid', Date_actualisation=date))
            ajoutes += 1
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert c.execute('SELECT COUNT(*) FROM Client').fetchone()[0] == avant + ajoutes
        assert c.execute("SELECT COUNT(*) FROM Client c JOIN Occupant o ON o.ID_client=c.ID_client JOIN Client_lot_pivot p ON p.ID_client_lot=c.ID_client_lot JOIN Lot l ON l.ID_lot=p.ID_lot WHERE c.Code_type_client='PM' AND o.Type_personne='Morale' AND o.Raison_sociale_occupant=c.Nom_prenom_client").fetchone()[0] == len(ENTITES)
        texte = dictionnaire(c)
        c.commit()
    DICO.write_text(texte, encoding="utf-8")
    print(f'{ajoutes} personnes morales ajoutees ; relations et integrite verifiees.')
    print(f'Sauvegarde : {backup}')


if __name__ == '__main__':
    main()
