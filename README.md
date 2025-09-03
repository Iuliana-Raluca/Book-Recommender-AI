# 📚 Book Recommender with Summaries

An intelligent book recommendation app that uses OpenAI's LLMs for smart suggestions, summaries, text-to-speech, and AI-generated covers.

---

## 🚀 Features

-  **Semantic Search** with OpenAI Embeddings + ChromaDB
-  **LLM-Powered Summarization** via GPT-4 with function calling
-  **Text-to-Speech**: Uses GPT-4o streaming voice generation
-  **Book Cover Generator**: DALL·E-style prompts for covers
-  **Moderation Layer**: API + fallback LLM-based filtering
-  **Modern UI** with Gradio 
-  **Context-Aware Recommendations** by theme/topic/title
-  Optional CLI, REST API, or Flask server
---

## ⚙️ Quickstart

```bash
# Clone the repository
git clone https://github.com/Iuliana-Raluca/Book-Recommender-AI.git
cd Book-Recommender-AI

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate     

# Add OpenAI key
echo OPENAI_API_KEY=sk-... > .env

# Install dependencies
pip install -r requirements.txt

# Run the Gradio UI
python src/app.py
```

---

## 📂 Project Structure

```
book-recommender/
├── src/
│   ├── app.py              # Gradio UI
│   ├── main.py             # LLM logic, function calling, RAG
│   ├── tool.py             # Image + audio generation, tools
│   ├── index.py            # Flask-style UI fallback
│   ├── data/
│   │   └── book_summaries.json  # Titles, summaries, themes
│   └── db/                 # ChromaDB persistent vector store
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🧠 How Embedding + LLM Work

- Book summaries are embedded using `text-embedding-3-small`
- Queries are converted into vector form via OpenAI
- ChromaDB retrieves most similar summaries 
- GPT-4 model uses context + user query to recommend and explain
- If exact title mentioned → direct summary retrieval 

---

## 🎧 Text-to-Speech

- Model: `gpt-4o-mini-tts`
- Voice: `nova`, `shimmer`, etc.
- Streamed directly to .mp3 via `with_streaming_response`

---

## 🖼️ Book Cover Generation

- Model: OpenAI `gpt-4.1-mini` 
- Prompted by: `"Create a book cover for the novel {title}"`
- Output: base64 or file saved and previewed in Gradio

---

## 🔐 Requirements

- Python 3.9+
- OpenAI API key
- ChromaDB (local persistent vector store)

---

## Example Usage

```text
User: Recommend me a book about fantasy and friendship.
Bot: I suggest *The Hobbit* for its magical quest and themes...
       Summary...
       Click to generate a cover
       Click to hear the summary
```
