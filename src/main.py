import os
import json
import chromadb
import re
import functools
from typing import List
from openai import OpenAI
from tool import get_summary_by_title


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Setează OPENAI_API_KEY în mediul de lucru.")


DB_PATH = os.path.abspath(os.path.join(__file__, "..", "db"))
chroma_client = chromadb.PersistentClient(path=DB_PATH)

try:
    collection = chroma_client.create_collection(name="book_summaries")
except Exception:
    collection = chroma_client.get_collection(name="book_summaries")


DATA_PATH = os.path.abspath(os.path.join(__file__, "..", "data", "book_summaries.json"))
with open(DATA_PATH, "r", encoding="utf-8") as f:
    all_rec = json.load(f)

TITLES = set(rec["title"].lower() for rec in all_rec)

def _load_themes() -> set:
    themes = set()
    for rec in all_rec:
        summary = rec.get("summary", "")
        if "Teme:" in summary:
            for t in summary.split("Teme:")[1].split(","):
                themes.add(t.strip().lower())
    return themes

THEMES = _load_themes()


def ingest_if_empty():
    if collection.count() > 0:
        return
    docs = []
    for rec in all_rec:
        docs.append({
            "id": rec["title"],
            "text": rec["summary"],
            "metadata": {"title": rec["title"]}
        })
    texts = [d["text"] for d in docs]
    ids = [d["id"] for d in docs]
    metas = [d["metadata"] for d in docs]
    vectors = []
    for text in texts:
        resp = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        vec = resp.data[0].embedding
        vectors.append(vec)
    collection.add(documents=texts, metadatas=metas, ids=ids, embeddings=vectors)

ingest_if_empty()


def embed_query(text: str) -> List[float]:
    resp = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return resp.data[0].embedding

def normalize(text: str) -> str:
    return text.lower().replace("„", "").replace("”", "").replace("«", "").replace("»", "").replace('"', "").strip()

def recommend(query: str, k: int = 10) -> str:
    q_lower = query.lower().strip()
    for title in TITLES:
        if title in q_lower and q_lower.startswith(("ce este", "descrie", "cine este")):
            return get_summary_by_title(title.title())

    q_vec = embed_query(query)
    results = collection.query(query_embeddings=[q_vec], n_results=k, include=["documents", "distances"])
    docs = results["documents"][0]
    ids = results["ids"][0]
    distances = results["distances"][0]

    THRESHOLD = 1.3
    if not ids or distances[0] > THRESHOLD:
        return f"Îmi pare rău, nu am găsit cărți relevante pentru «{query}» în baza mea de date."

    context = "\n\n".join(f"- **{t}**: {s}" for t, s in zip(ids, docs))
    prompt = (
        f"Am următoarele rezumate de cărți:\n{context}\n\n"
        f"Întrebare: «{query}»\n"
        "Recomandă-mi cel mai potrivit titlu și explică pe scurt de ce. "
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Ești un asistent care recomandă cărți și poate oferi rezumate detaliate. "
                "Dacă mesajul utilizatorului conține limbaj nepotrivit, roagă-l să reformuleze."
            )
        },
        {"role": "user", "content": prompt}
    ]

    functions = [
        {
            "name": "get_summary_by_title",
            "description": "Returnează rezumatul complet pentru un titlu exact din baza locală",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Titlul cărții pentru care se cere rezumatul"
                    }
                },
                "required": ["title"]
            }
        }
    ]

    resp = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        functions=functions,
        function_call="auto"
    )

    msg = resp.choices[0].message

    # dacă a fost apelat tool-ul
    if msg.function_call:
        args = json.loads(msg.function_call.arguments)
        summary = get_summary_by_title(args["title"])
        followup = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                *messages,
                {"role": "assistant", "function_call": msg.function_call},
                {"role": "function", "name": "get_summary_by_title", "content": summary}
            ]
        )
        return followup.choices[0].message.content.strip()

    # fallback dacă titlul apare dar fără function_call
    if msg.content:
        response_text = msg.content.strip()
        cleaned_text = normalize(response_text)
        for title in TITLES:
            if normalize(title) in cleaned_text and distances[0] <= THRESHOLD:
                summary = get_summary_by_title(title)
                return f"{response_text}\n\n📘 **Rezumat pentru «{title}»**:\n{summary}"
        return response_text

    return "Am întâmpinat o problemă în procesarea întrebării tale."


def gpt_moderation_check(user_input: str) -> bool:
    prompt = (
        "Evaluează dacă următorul mesaj conține limbaj ofensator sau nepotrivit pentru un asistent literar. "
        "Răspunde doar cu DA sau NU.\n\n"
        f"Mesaj: {user_input}"
    )
    resp = openai_client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "Ești un filtru automat de moderare."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    answer = resp.choices[0].message.content.strip().lower()
    return answer in ["nu", "no"]


def respond(user_input: str) -> str:
    if not gpt_moderation_check(user_input):
        return "Te rog să reformulezi întrebarea într-un mod adecvat."
    return recommend(user_input)
