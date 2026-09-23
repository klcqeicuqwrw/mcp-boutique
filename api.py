import json
import os
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()  # charge automatiquement les variables depuis le fichier .env

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "Variable d'environnement GEMINI_API_KEY manquante. "
        "Récupère une clé gratuite sur aistudio.google.com puis fais : "
        "$env:GEMINI_API_KEY=\"ta_cle\""
    )

client = genai.Client(api_key=GEMINI_API_KEY)

MAX_ROWS = 500
DATABASE_PATH = Path(
    os.environ.get("SQLITE_DB_PATH", "boutique.db")
).expanduser().resolve()

app = FastAPI(title="API Boutique - Langage naturel vers SQL")


# ---------------------------------------------------------------------------
# Accès base de données (repris de server.py)
# ---------------------------------------------------------------------------

def _connect_read_only() -> sqlite3.Connection:
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Base SQLite introuvable: {DATABASE_PATH}. "
            "Définissez SQLITE_DB_PATH ou créez boutique.db."
        )
    connection = sqlite3.connect(f"{DATABASE_PATH.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _remove_leading_comments(query: str) -> str:
    remaining = query.lstrip()
    while remaining.startswith("--") or remaining.startswith("/*"):
        if remaining.startswith("--"):
            end = remaining.find("\n")
            if end == -1:
                return ""
            remaining = remaining[end + 1 :].lstrip()
            continue
        end = remaining.find("*/", 2)
        if end == -1:
            return ""
        remaining = remaining[end + 2 :].lstrip()
    return remaining


def _validate_read_query(query: str) -> str:
    query = _remove_leading_comments(query.strip())
    if not query:
        raise ValueError("La requête SQL ne peut pas être vide.")
    if ";" in query.rstrip(";"):
        raise ValueError("Une seule requête SQL est autorisée.")
    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", query, re.IGNORECASE):
        raise ValueError("Seules les requêtes SELECT, WITH et EXPLAIN sont autorisées.")
    return query.rstrip(";").strip()


def obtenir_schema() -> str:
    with closing(_connect_read_only()) as connection:
        objects = connection.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE type IN ('table', 'view', 'index')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()
    return json.dumps([dict(row) for row in objects], ensure_ascii=False, indent=2)


def executer_requete_sql(requete: str) -> dict:
    safe_query = _validate_read_query(requete)
    try:
        with closing(_connect_read_only()) as connection:
            cursor = connection.execute(safe_query)
            columns = [d[0] for d in cursor.description or []]
            rows = cursor.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as error:
        raise RuntimeError(f"Erreur SQLite pendant l'exécution: {error}") from error

    truncated = len(rows) > MAX_ROWS
    if truncated:
        rows = rows[:MAX_ROWS]

    return {
        "columns": columns,
        "rows": [dict(zip(columns, row)) for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }


# ---------------------------------------------------------------------------
# Appels Gemini
# ---------------------------------------------------------------------------

def _appeler_gemini_avec_retry(contents: str, config: types.GenerateContentConfig, tentatives: int = 3):
    derniere_erreur = None
    for essai in range(tentatives):
        try:
            return client.models.generate_content(
                model=GEMINI_MODEL, contents=contents, config=config
            )
        except Exception as error:
            derniere_erreur = error
            message = str(error)
            if "503" in message or "429" in message or "UNAVAILABLE" in message:
                time.sleep(1.5 * (essai + 1))
                continue
            raise
    raise derniere_erreur


def generer_sql(question: str, schema: str, historique: list) -> str:
    # Construction du contexte à partir des 6 derniers messages (3 derniers échanges)
    contexte_str = ""
    if historique:
        messages_recents = historique[-6:]
        lignes = [f"{msg.role.capitalize()}: {msg.content}" for msg in messages_recents]
        contexte_str = "Historique de la conversation (pour contexte) :\n" + "\n".join(lignes) + "\n\n"

    prompt = (
        "Voici le schéma d'une base SQLite (tables, colonnes, clés étrangères) :\n"
        f"{schema}\n\n"
        f"{contexte_str}"
        f"Question actuelle de l'utilisateur : {question}\n\n"
        "Génère UNE SEULE requête SQL de lecture (SELECT, WITH ou EXPLAIN uniquement) "
        "qui répond à cette question, adaptée exactement à ce schéma. "
        "Ne mets aucun point-virgule à la fin."
    )
    response = _appeler_gemini_avec_retry(
        prompt,
        types.GenerateContentConfig(
            temperature=0,
            system_instruction=(
                "Tu es un générateur de SQL SQLite. Tu réponds uniquement avec un "
                "objet JSON de la forme {\"sql\": \"...\"}, sans aucun texte autour."
            ),
            response_mime_type="application/json",
        ),
    )
    payload = json.loads(response.text)
    return payload["sql"]


def formuler_reponse(question: str, resultats: dict) -> str:
    prompt = (
        f"Question de l'utilisateur : {question}\n\n"
        f"Résultats de la requête SQL (JSON) : {json.dumps(resultats, ensure_ascii=False)}\n\n"
        "Formule une réponse très courte en français en te basant sur ces résultats. "
        "RÈGLE STRICTE : NE FAIS PAS de liste détaillée des données. "
        "Si le résultat est un chiffre ou une réponse unique (ex: un total, un compte), donne-le directement. "
        "S'il y a plusieurs lignes, fais uniquement une courte phrase d'introduction globale "
        "(ex: 'Voici les clients correspondants :', 'J'ai trouvé X commandes :') puisque "
        "les données détaillées seront affichées dans un tableau visuel juste en dessous."
    )
    response = _appeler_gemini_avec_retry(
        prompt, types.GenerateContentConfig(temperature=0.2)
    )
    return response.text


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class MessageHistorique(BaseModel):
    role: str
    content: str

class Question(BaseModel):
    question: str
    historique: List[MessageHistorique] = []
    veut_reponse: bool = True
    veut_tableau: bool = True

class Reponse(BaseModel):
    reponse: str
    sql_genere: str
    resultats: dict


@app.post("/ask", response_model=Reponse)
def ask(payload: Question) -> Reponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    schema = obtenir_schema()

    try:
        sql = generer_sql(payload.question, schema, payload.historique)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Erreur Gemini (génération SQL): {error}") from error

    try:
        resultats = executer_requete_sql(sql)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail=f"Requête invalide: {error}") from error

    reponse_nl = ""
    # On génère la réponse textuelle uniquement si l'utilisateur l'a demandé
    if payload.veut_reponse:
        try:
            reponse_nl = formuler_reponse(payload.question, resultats)
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"Erreur Gemini (formulation): {error}") from error

    return Reponse(reponse=reponse_nl, sql_genere=sql, resultats=resultats)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "database": str(DATABASE_PATH), "model": GEMINI_MODEL}


PAGE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Assistant Boutique</title>
<style>
  :root {
    --bg: #f7f7f8;
    --sidebar-bg: #1e1e2e;
    --sidebar-text: #d8d8e0;
    --accent: #6366f1;
    --accent-dark: #4f46e5;
    --bubble-user: #6366f1;
    --bubble-assistant: #ffffff;
    --border: #e5e5e8;
    --text: #1f1f28;
    --text-muted: #7a7a85;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  /* Sidebar */
  #sidebar {
    width: 260px;
    background: var(--sidebar-bg);
    color: var(--sidebar-text);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }
  #sidebar-header {
    padding: 20px 16px;
    font-weight: 600;
    font-size: 15px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  #sidebar-header .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
  #new-chat {
    margin: 12px;
    padding: 10px 12px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: var(--sidebar-text);
    cursor: pointer;
    font-size: 14px;
    text-align: left;
  }
  #new-chat:hover { background: rgba(255,255,255,0.1); }
  #history { flex: 1; overflow-y: auto; padding: 4px 8px; }
  .history-item {
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 13px;
    color: var(--sidebar-text);
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 2px;
  }
  .history-item:hover { background: rgba(255,255,255,0.08); }
  .history-item.active { background: rgba(99,102,241,0.25); color: #fff; }

  /* Main */
  #main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  #topbar {
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    font-weight: 600;
    background: #fff;
  }
  #thread { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 18px; }

  .msg { max-width: 720px; display: flex; flex-direction: column; gap: 6px; }
  .msg.user { align-self: flex-end; align-items: flex-end; }
  .msg.assistant { align-self: flex-start; align-items: flex-start; }

  .bubble { padding: 12px 16px; border-radius: 14px; font-size: 15px; line-height: 1.5; }
  .msg.user .bubble { background: var(--bubble-user); color: #fff; border-bottom-right-radius: 4px; }
  .msg.assistant .bubble { background: var(--bubble-assistant); border: 1px solid var(--border); border-bottom-left-radius: 4px; }

  .sql-note {
    font-family: "SF Mono", Consolas, monospace;
    font-size: 12px;
    color: var(--text-muted);
    background: #f1f1f4;
    border-radius: 6px;
    padding: 6px 10px;
    max-width: 720px;
  }

  table { border-collapse: collapse; width: 100%; margin-top: 4px; font-size: 13px; background: #fff; }
  th, td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
  th { background: #f1f1f4; font-weight: 600; }

  #input-bar { padding: 16px 24px; border-top: 1px solid var(--border); background: #fff; }
  #options { display: flex; gap: 15px; margin: 0 auto 10px auto; max-width: 760px; font-size: 14px; color: var(--text-muted); }
  #form { display: flex; gap: 10px; max-width: 760px; margin: 0 auto; }
  #question {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: 24px;
    font-size: 15px;
    outline: none;
  }
  #question:focus { border-color: var(--accent); }
  #form button {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 24px;
    padding: 0 22px;
    font-size: 15px;
    cursor: pointer;
  }
  #form button:hover { background: var(--accent-dark); }
  #form button:disabled { opacity: 0.5; cursor: default; }

  .typing { color: var(--text-muted); font-style: italic; font-size: 14px; }
  .error-bubble { background: #fef2f2; border: 1px solid #fecaca; color: #b00020; }
  .empty-state { margin: auto; text-align: center; color: var(--text-muted); }
</style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-header"><span class="dot"></span> Assistant Boutique</div>
  <button id="new-chat">+ Nouvelle conversation</button>
  <div id="history"></div>
</div>

<div id="main">
  <div id="topbar">Base de données boutique</div>
  <div id="thread"><div class="empty-state">Pose une question sur tes clients, commandes, produits...</div></div>
  <div id="input-bar">
    <div id="options">
      <label><input type="checkbox" id="check-reponse" checked> Générer une réponse texte</label>
      <label><input type="checkbox" id="check-tableau" checked> Afficher le tableau de données</label>
    </div>
    <form id="form">
      <input id="question" placeholder="Ex : Quels sont mes clients VIP ?" autocomplete="off" required>
      <button type="submit">Envoyer</button>
    </form>
  </div>
</div>

<script>
const thread = document.getElementById('thread');
const form = document.getElementById('form');
const input = document.getElementById('question');
const historyEl = document.getElementById('history');
const newChatBtn = document.getElementById('new-chat');
const checkReponse = document.getElementById('check-reponse');
const checkTableau = document.getElementById('check-tableau');

const STORAGE_KEY = 'assistant-boutique-conversations';
const EMPTY_STATE = '<div class="empty-state">Pose une question sur tes clients, commandes, produits...</div>';

// --- Persistance (localStorage) ---------------------------------------

function chargerConversations() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function sauvegarderConversations() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

let conversations = chargerConversations(); 
let conversationActiveId = null;

// --- Gestion des conversations ------------------------------------------

function nouvelleConversation() {
  const conv = { id: crypto.randomUUID(), titre: null, messages: [] };
  conversations.unshift(conv);
  conversationActiveId = conv.id;
  sauvegarderConversations();
  renderHistory();
  renderThread();
  input.focus();
}

function conversationCourante() {
  return conversations.find(c => c.id === conversationActiveId);
}

function ouvrirConversation(id) {
  conversationActiveId = id;
  renderHistory();
  renderThread();
}

function renderHistory() {
  historyEl.innerHTML = '';
  conversations.forEach((conv) => {
    const item = document.createElement('div');
    item.className = 'history-item' + (conv.id === conversationActiveId ? ' active' : '');
    const titre = conv.titre || (conv.messages[0] ? conv.messages[0].question : 'Nouvelle conversation');
    item.textContent = titre;
    item.title = titre;
    item.addEventListener('click', () => ouvrirConversation(conv.id));
    historyEl.appendChild(item);
  });
}

function renderThread() {
  const conv = conversationCourante();
  thread.innerHTML = '';
  if (!conv || conv.messages.length === 0) {
    thread.innerHTML = EMPTY_STATE;
    return;
  }
  conv.messages.forEach(m => {
    addUserBubble(m.question, false);
    if (m.erreur) {
      addAssistantBubble({ reponse: m.erreur }, true, false);
    } else {
      addAssistantBubble(m, false, false);
    }
  });
  thread.scrollTop = thread.scrollHeight;
}

// --- Rendu des bulles ----------------------------------------------------

function clearEmptyState() {
  const empty = thread.querySelector('.empty-state');
  if (empty) empty.remove();
}

function addUserBubble(text, scroll = true) {
  clearEmptyState();
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  thread.appendChild(div);
  if (scroll) thread.scrollTop = thread.scrollHeight;
}

function addAssistantBubble(msg, isError = false, scroll = true) {
  const div = document.createElement('div');
  div.className = 'msg assistant';

  let tableHtml = '';
  // On affiche le tableau seulement si l'utilisateur l'a demandé (ou s'il n'y a pas d'info, par compatibilité)
  if (msg.veut_tableau !== false && msg.resultats && msg.resultats.rows && msg.resultats.rows.length > 0) {
    const cols = msg.resultats.columns;
    tableHtml = '<table><thead><tr>' + cols.map(c => `<th>${escapeHtml(c)}</th>`).join('') + '</tr></thead><tbody>';
    msg.resultats.rows.forEach(row => {
      tableHtml += '<tr>' + cols.map(c => `<td>${escapeHtml(String(row[c] ?? ''))}</td>`).join('') + '</tr>';
    });
    tableHtml += '</tbody></table>';
  }

  let htmlContent = '';
  
  if (msg.reponse) {
     htmlContent += `<div class="bubble ${isError ? 'error-bubble' : ''}">${escapeHtml(msg.reponse)}</div>`;
  }
  htmlContent += tableHtml;
  
  if (msg.sql_genere) {
     htmlContent += `<div class="sql-note">${escapeHtml(msg.sql_genere)}</div>`;
  }

  if (!msg.reponse && !tableHtml && !isError) {
      htmlContent = `<div class="bubble"><em>Requête exécutée (réponse et tableau masqués).</em></div>` + htmlContent;
  }

  div.innerHTML = htmlContent;
  thread.appendChild(div);
  if (scroll) thread.scrollTop = thread.scrollHeight;
}

function addTyping() {
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = 'typing';
  div.innerHTML = '<div class="typing">Recherche en cours...</div>';
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById('typing');
  if (el) el.remove();
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// --- Événements ------------------------------------------------------------

newChatBtn.addEventListener('click', nouvelleConversation);

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  if (!conversationActiveId || !conversationCourante()) {
    nouvelleConversation();
  }
  const conv = conversationCourante();
  if (conv.titre === null) conv.titre = question;

  const veutReponse = checkReponse.checked;
  const veutTableau = checkTableau.checked;

  addUserBubble(question);
  input.value = '';
  input.disabled = true;
  form.querySelector('button').disabled = true;
  addTyping();

  // Construction de l'historique pour l'API
  const historiqueAEnvoyer = conv.messages.flatMap(m => [
      { role: "user", content: m.question },
      { role: "assistant", content: m.reponse || "(Tableau généré sans texte)" }
  ]);

  let entree = { question, veut_tableau: veutTableau };

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
          question: question,
          historique: historiqueAEnvoyer,
          veut_reponse: veutReponse,
          veut_tableau: veutTableau
      })
    });
    
    const data = await res.json();
    removeTyping();

    if (!res.ok) {
      entree.erreur = data.detail || 'Erreur inconnue';
      addAssistantBubble({ reponse: entree.erreur }, true);
    } else {
      entree.reponse = data.reponse;
      entree.sql_genere = data.sql_genere;
      entree.resultats = data.resultats;
      addAssistantBubble(entree);
    }
  } catch (err) {
    removeTyping();
    entree.erreur = 'Erreur réseau : ' + err;
    addAssistantBubble({ reponse: entree.erreur }, true);
  } finally {
    conv.messages.push(entree);
    sauvegarderConversations();
    renderHistory();
    input.disabled = false;
    form.querySelector('button').disabled = false;
    input.focus();
  }
});

// --- Démarrage ---------------------------------------------------------

if (conversations.length > 0) {
  conversationActiveId = conversations[0].id;
}
renderHistory();
renderThread();
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE_HTML