
import os
import json
import openai
import chromadb
import gradio as gr
from chromadb.config import Settings
from typing import List
import functools
from tool import get_summary_by_title
import json
import re

# Definitia tool-ului pentru Function Calling
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

#  Configurare API si client ChromaDB 
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Setează OPENAI_API_KEY în mediul de lucru.")

DB_PATH = os.path.abspath(os.path.join(__file__, "..", "db"))
client = chromadb.PersistentClient(path=DB_PATH)

try:
    collection = client.create_collection(name="book_summaries")
except Exception:
    collection = client.get_collection(name="book_summaries")

DATA_PATH = os.path.abspath(os.path.join(__file__, "..", "data", "book_summaries.json"))
with open(DATA_PATH, "r", encoding="utf-8") as f:
    all_rec = json.load(f)

# Titlurile exacte pe care le avem
TITLES = set(rec["title"].lower() for rec in all_rec)

# Dacă ai funcția _load_themes sau Themes global, păstreaz-o
def _load_themes() -> set:
    themes = set()
    for rec in all_rec:
        summary = rec.get("summary","")
        if "Teme:" in summary:
            for t in summary.split("Teme:")[1].split(","):
                themes.add(t.strip().lower())
    return themes

THEMES = _load_themes()

def ingest_if_empty():
    if collection.count() > 0:
        return  

    data_path = os.path.abspath(os.path.join(__file__, "..", "data", "book_summaries.json"))
    with open(data_path, "r", encoding="utf-8") as f:
        all_rec = json.load(f)

    docs = []
    for rec in all_rec:
        docs.append({
            "id": rec["title"],
            "text": rec["summary"],
            "metadata": {"title": rec["title"]}
        })

    # Generarea embedding-urilor
    texts = [d["text"] for d in docs]
    ids   = [d["id"]   for d in docs]
    metas = [d["metadata"] for d in docs]
    vectors: List[List[float]] = []
    for text in texts:
        resp = openai.Embedding.create(
            model="text-embedding-3-small",
            input=text
        )
        vec = resp["data"][0]["embedding"]
        vectors.append(vec)

    collection.add(
        documents=texts,
        metadatas=metas,
        ids=ids,
        embeddings=vectors
    )


ingest_if_empty()

@functools.lru_cache(maxsize=1)
def _load_themes() -> set:
  
    data_path = os.path.abspath(
        os.path.join(__file__, "..", "data", "book_summaries.json")
    )
    with open(data_path, "r", encoding="utf-8") as f:
        all_rec = json.load(f)

    themes = set()
    for rec in all_rec:
        summary = rec.get("summary", "")
        if "Teme:" in summary:
            raw = summary.split("Teme:")[1]
            for t in raw.split(","):
                themes.add(t.strip().lower())
    return themes

def embed_query(text: str) -> List[float]:
    resp = openai.Embedding.create(
        model="text-embedding-3-small",
        input=text
    )
    return resp["data"][0]["embedding"]

def recommend(query: str, k: int = 10) -> str:
    q_lower = query.lower().strip()

    for title in TITLES:
        if title in q_lower and q_lower.startswith(("ce este", "descrie", "cine este")):
            return get_summary_by_title(title.title())

    # RAG semantic
    q_vec = embed_query(query)
    results = collection.query(query_embeddings=[q_vec], n_results=k, include=["documents", "distances"])
    docs = results["documents"][0]
    ids = results["ids"][0]
    distances = results["distances"][0]

    # Fallback pe distanta
    THRESHOLD = 1.3
    if not ids or distances[0] > THRESHOLD:
        return (
            f"Îmi pare rău, nu am găsit cărți relevante pentru «{query}» în baza mea de date.\n"
            "Poți încerca o altă temă sau un alt gen literar?"
            
        )

    context = "\n\n".join(f"- **{t}**: {s}" for t, s in zip(ids, docs))
    prompt = (
        f"Am următoarele rezumate de cărți:\n{context}\n\n"
        f"Întrebare: «{query}»\n"
        "Recomandă-mi cel mai potrivit titlu și explică pe scurt de ce."
        "Daca din baza de date/lista de rezumate nicio carte nu corespunde query-ului utilizatorului, atunci nu vei apela funcția get_summary_by_title si nu vei mai pune alta intrebare"
    )

    messages = [
    {
        "role": "system",
        "content": (
            "Ești un asistent care recomandă cărți și poate oferi rezumate detaliate.\n"
            "Dacă mesajul utilizatorului conține cuvinte jignitoare, limbaj licențios sau ofensator, "
            "nu oferi nicio recomandare și roagă-l politicos să reformuleze într-un mod adecvat."
        )
    },
    {"role": "user", "content": prompt}
]

    #  Apel catre OpenAI cu function_call activ
    resp = openai.ChatCompletion.create(
        model="gpt-4.1-mini", 
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    msg = resp.choices[0].message

    #  Daca modelul cere explicit tool-ul
    if msg.get("function_call"):
        fn_name = msg["function_call"]["name"]
        args = json.loads(msg["function_call"]["arguments"])
        summary = get_summary_by_title(args["title"])
        followup = openai.ChatCompletion.create(
            model="gpt-4.1-mini",
            messages=[
                *messages,
                msg,
                {"role": "function", "name": fn_name, "content": summary}
            ]
        )
        return followup.choices[0].message.content.strip()

    if msg.get("content"):
        response_text = msg.content.strip()

        cleaned_text = response_text.lower().replace("„", "").replace("”", "").replace("«", "").replace("»", "").replace('"', '').strip()

        for title in TITLES:
            pattern = r'\b' + re.escape(title.lower()) + r'\b'
            if re.search(pattern, cleaned_text):
                summary = get_summary_by_title(title)
                return f"{response_text}\n\n**Rezumat pentru «{title}»**:\n{summary}"

        return response_text

    return "Am întâmpinat o problemă în procesarea întrebării tale."

def is_safe_input(text: str) -> bool:
    """
    Verifică dacă textul este sigur pentru LLM, folosind OpenAI Moderation API.
    Returnează True dacă e sigur, False dacă e flagat.
    """
    response = openai.Moderation.create(input=text)
    # print(json.dumps(response, indent=2))  
    return not response["results"][0]["flagged"]


def gpt_moderation_check(user_input: str) -> bool:
    """
    Folosește LLM pentru a detecta dacă întrebarea conține limbaj ofensator,
    vulgar sau nepotrivit pentru un chatbot educațional/literar.
    Returnează True dacă e sigur, False dacă e ofensator.
    """
    moderation_prompt = (
        "Evaluează dacă următorul mesaj conține limbaj vulgar, ofensator, jignitor sau inadecvat "
        "pentru un asistent literar. Răspunde doar cu DA sau NU.\n\n"
        f"Mesaj: {user_input}"
    )

    resp = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Ești un filtru automat de moderare."},
            {"role": "user", "content": moderation_prompt}
        ],
        temperature=0
    )

    answer = resp.choices[0].message.content.strip().lower()
    return answer in ["nu", "no"]

def respond(user_input: str) -> str:
    if not is_safe_input(user_input):
        return (
            "Mesajul tău a fost detectat ca având conținut nepotrivit.\n"
            "Te rugăm să reformulezi într-un mod respectuos și adecvat."
        )
    
    # fallback suplimentar cu LLM daca trece Moderation API
    if not gpt_moderation_check(user_input):
        return (
            "Te rog să formulezi întrebarea într-un mod adecvat. Nu pot răspunde la cereri "
            "care conțin limbaj ofensator sau nepotrivit."
        )
    
    return recommend(user_input)



iface = gr.Interface(
    fn=respond,
    inputs=gr.Textbox(lines=2, placeholder="Ex: Ce este 1984? Sau Vreau o carte despre libertate și control social…"),
    outputs="text",
    title="Book Recommender with Summaries",
    description="Întreabă despre titluri sau teme, primești recomandare și rezumat complet."
)


if __name__ == "__main__":
    iface.launch()
