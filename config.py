"""Charge la configuration avant les modules utilisant les variables d'environnement."""
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def chemin(variable, defaut):
    valeur = Path(os.environ.get(variable) or defaut).expanduser()
    return (valeur if valeur.is_absolute() else ROOT / valeur).resolve()
