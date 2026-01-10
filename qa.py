from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
load_dotenv()


PROMPT_TEMPLATE = """
You are an assistant answering questions about a YouTube video.

You must follow these rules strictly:
1. Answer ONLY using the provided transcript context.
2. If the answer is not present, say "The video does not mention this."
3. Be concise and factual.
4. Do NOT add external knowledge.

Context:
{context}

Question:
{question}

Answer:
"""


def load_vectorstore(persist_dir="data/vectordb"):
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding
    )

def get_retriever(vectordb, k=4):
    return vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

def build_qa_chain(retriever):
    llm = Ollama(
        temperature=0,
        model="phi"
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

def ask_question(question):
    vectordb = load_vectorstore()
    retriever = get_retriever(vectordb)
    qa_chain = build_qa_chain(retriever)

    result = qa_chain(question)

    answer = result["result"]
    sources = result["source_documents"]

    timestamps = []
    for doc in sources:
        timestamps.append({
            "video_id": doc.metadata["video_id"],
            "start_time": doc.metadata["start_time"],
            "end_time": doc.metadata["end_time"]
        })

    return answer, timestamps


if __name__ == "__main__":
    question = "who is the narrator?"
    answer, timestamps = ask_question(question)

    print("\nAnswer:")
    print(answer)

    print("\nTimestamps:")
    for t in timestamps:
        print(
            f"https://www.youtube.com/watch?v={t['video_id']}&t={int(t['start_time'])}s"
        )
