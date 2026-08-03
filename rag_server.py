"""
rag_server.py — RAG proxy server for the Kenya MSME Advisor.
"""
import pickle
from pathlib import Path

import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

INDEX_PATH = Path("rag_index.pkl")
LLAMA_SERVER_URL = "http://localhost:8090"
TOP_K = 4
MIN_SIMILARITY = 0.05
PORT = 8091

app = Flask(__name__)
CORS(app)

print("Loading RAG index...")
with open(INDEX_PATH, "rb") as f:
    index = pickle.load(f)
vectorizer = index["vectorizer"]
matrix = index["matrix"]
chunks = index["chunks"]
print(f"Loaded {len(chunks)} chunks from {INDEX_PATH}")

SCOPE_INSTRUCTION = (
    "You are Rafiki wa Biashara, an assistant specifically built to help Kenyan "
    "MSME (micro, small, and medium enterprise) owners with tax, registration, "
    "financing, and regulatory compliance in Kenya.\n\n"
    "SCOPE RULES:\n"
    "1. If the question is clearly about a country OTHER than Kenya (e.g. Ethiopia, "
    "DRC, Tanzania), do not apply Kenyan rules or figures to it — say plainly you're "
    "built specifically for Kenya and don't have reliable information for other "
    "countries.\n"
    "2. If the question is clearly unrelated to business/tax/regulatory topics "
    "entirely (general trivia, opinions, non-business topics), redirect to Kenyan "
    "MSME matters instead of answering from general knowledge.\n"
    "3. For questions ABOUT KENYA and Kenyan MSMEs: answer normally using both the "
    "retrieved source material below (if present and relevant) AND your own trained "
    "knowledge of Kenyan regulations. Do NOT refuse or claim you lack information "
    "just because no source material was retrieved for this specific turn — only "
    "say you lack information if you genuinely don't know the answer, not by default.\n"
    "4. Only use retrieved material when it actually pertains to the question; ignore "
    "it if it doesn't.\n\n"
    "FORMATTING RULES:\n"
    "- Use **bold** for key terms, amounts, deadlines, and agency names.\n"
    "- Use bullet points or numbered lists whenever an answer has 2 or more distinct "
    "items, steps, or requirements — never bury multiple items in a single paragraph.\n"
    "- Use short section headers (as plain bold text, not markdown #) to break up "
    "longer answers into logical groups (e.g. **Registration**, **Tax Obligations**, "
    "**Next Steps**).\n"
    "- Keep genuinely simple, single-point answers as plain sentences — do not force "
    "structure onto a one-line answer.\n"
    "- Never write a long unbroken paragraph when the content has a natural list or "
    "step-by-step shape."
)


def retrieve(query: str, top_k: int = TOP_K):
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, matrix).flatten()
    top_indices = sims.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        score = float(sims[idx])
        if score < MIN_SIMILARITY:
            continue
        results.append({
            "text": chunks[idx]["text"],
            "kb": chunks[idx]["kb"],
            "source": chunks[idx]["source"],
            "score": score,
        })
    return results


def build_retrieval_query(messages, current_query):
    """Combine the current question with the prior user turn for context,
    so short follow-ups like 'what about Kenya?' retrieve meaningfully."""
    user_turns = [m["content"] for m in messages if m.get("role") == "user"]
    if len(user_turns) >= 2:
        return user_turns[-2] + " " + current_query
    return current_query


def build_context_block(retrieved):
    parts = [SCOPE_INSTRUCTION]
    if retrieved:
        parts.append("\n\nRELEVANT SOURCE MATERIAL (use if it genuinely pertains to the question):\n")
        for i, r in enumerate(retrieved, 1):
            parts.append(f"[Source {i} — {r['kb']}]\n{r['text']}\n")
    return "\n".join(parts)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "chunks_loaded": len(chunks)})


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    payload = request.get_json()
    messages = payload.get("messages", [])

    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        return jsonify({"error": "no user message found"}), 400
    query = user_messages[-1]["content"]

    retrieval_query = build_retrieval_query(messages, query)
    retrieved = retrieve(retrieval_query)
    context_block = build_context_block(retrieved)

    augmented_messages = list(messages)
    insert_at = len(augmented_messages) - 1
    augmented_messages.insert(insert_at, {
        "role": "system",
        "content": context_block,
    })

    if retrieved:
        print(f"[RAG] Query: {query[:80]!r} (retrieval query: {retrieval_query[:80]!r}) — "
              f"retrieved {len(retrieved)} chunks (top score {retrieved[0]['score']:.3f}) "
              f"from: {', '.join(sorted(set(r['kb'] for r in retrieved)))}")
    else:
        print(f"[RAG] Query: {query[:80]!r} — no relevant chunks found above threshold")

    forward_payload = dict(payload)
    forward_payload["messages"] = augmented_messages

    resp = requests.post(
        f"{LLAMA_SERVER_URL}/v1/chat/completions",
        json=forward_payload,
        stream=payload.get("stream", False),
    )

    if payload.get("stream"):
        return Response(resp.iter_content(chunk_size=None), content_type=resp.headers.get("content-type"))
    return jsonify(resp.json())


if __name__ == "__main__":
    print(f"RAG proxy server starting on port {PORT}")
    print(f"Forwarding to llama-server at {LLAMA_SERVER_URL}")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
