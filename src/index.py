import os
import openai
import chromadb
from typing import List

openai.api_key = os.getenv("OPENAI_API_KEY")
assert openai.api_key, "Setează OPENAI_API_KEY în mediu."

CLIENT = chromadb.PersistentClient(path=os.path.abspath(os.path.join(__file__, "..", "..", "db")))
COLL   = CLIENT.get_collection(name="book_summaries")

def embed_query(text: str) -> List[float]:
    resp = openai.Embedding.create(model="text-embedding-3-small", input=text)
    return resp.data[0].embedding

def recommend(query: str, k: int = 5) -> str:
    q_vec   = embed_query(query)
    results = COLL.query(query_embeddings=[q_vec], n_results=k)
    docs    = results["documents"][0]
    ids     = results["ids"][0]

    if not ids or all(not d.strip() for d in docs):
        return (
            f"Îmi pare rău, nu am găsit cărți relevante pentru «{query}» în baza mea de date.\n"
            "Poți încerca o altă temă sau un alt gen literar?"
        )

    context = "\n\n".join(f"- {title}: {summary}" for title, summary in zip(ids, docs))
    prompt = (
        f"Am următoarele rezumate de cărți:\n{context}\n\n"
        f"Întrebare: «{query}»\n"
        "Te rog să răspunzi conversational recomandând titlurile potrivite și motivând pe scurt."
    )

    chat = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Ești un asistent care recomandă cărți."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.7,
        max_tokens=300
    )
    return chat.choices[0].message.content.strip()


if __name__ == "__main__":
    query = input("Intrebare> ").strip()
    response = recommend(query)
    print("\n" + response)
