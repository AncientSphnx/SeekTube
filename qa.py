from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# -----------------------------
# PROMPT (Phase 5 – Improved)
# -----------------------------
PROMPT_TEMPLATE = """
You are answering a question using transcript excerpts from a YouTube video.

STRICT RULES (DO NOT VIOLATE):
- Use ONLY information explicitly stated in the transcript.
- Do NOT infer, assume, or guess.
- Do NOT explain rules or reasoning.
- Do NOT add commentary.
- Output ONLY the final answer sentence.

If the transcript does not explicitly state the answer, output EXACTLY:
"The video does not mention this."

Transcript excerpts:
{context}

Question:
{question}

Final Answer (one sentence only):
"""


# -----------------------------
# Vector Store Loader
# -----------------------------
def load_vectorstore(persist_dir="data/vectordb"):
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding
    )

# -----------------------------
# Retriever
# -----------------------------
def get_retriever(vectordb, k=4):
    return vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

# -----------------------------
# Context Compression
# -----------------------------
def build_context(source_documents):
    blocks = []
    for doc in source_documents:
        clean_text = doc.page_content.strip()
        blocks.append(f"- {clean_text}")
    return "\n".join(blocks)

# -----------------------------
# Timestamp Ranking
# -----------------------------
def extract_ranked_timestamps(source_documents, max_results=3):
    seen = set()
    timestamps = []

    for doc in source_documents:
        start = int(doc.metadata["start_time"])
        key = (doc.metadata["video_id"], start)

        if key not in seen:
            seen.add(key)
            timestamps.append({
                "video_id": doc.metadata["video_id"],
                "start_time": start,
                "end_time": int(doc.metadata["end_time"])
            })

    timestamps.sort(key=lambda x: x["start_time"])
    return timestamps[:max_results]

# -----------------------------
# QA Chain Builder
# -----------------------------
def build_qa_chain(retriever):
    llm = Ollama(
        model="phi",
        temperature=0
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=PROMPT_TEMPLATE
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

# -----------------------------
# Main QA Function (API-Ready)
# -----------------------------
def ask_question(question):
    vectordb = load_vectorstore()
    retriever = get_retriever(vectordb)
    qa_chain = build_qa_chain(retriever)

    # Correct invocation (no deprecation warning)
    result = qa_chain.invoke({"query": question})

    answer = result["result"]
    source_docs = result["source_documents"]

    timestamps = extract_ranked_timestamps(source_docs)

    response = {
        "answer": answer,
        "timestamps": [
            {
                "video_id": t["video_id"],
                "start_time": t["start_time"],
                "url": f"https://www.youtube.com/watch?v={t['video_id']}&t={t['start_time']}s"
            }
            for t in timestamps
        ]
    }

    return response

# -----------------------------
# CLI Test
# -----------------------------
if __name__ == "__main__":
    question = "Who is the narrator?"
    response = ask_question(question)

    print("\nAnswer:")
    print(response["answer"])

    print("\nTimestamps:")
    for t in response["timestamps"]:
        print(t["url"])
