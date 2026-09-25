"""
Qualitative RAG Agent.

Connects to a Chroma vector database, embeds documents/queries with
Sentence Transformers (local, no API key/quota needed), retrieves the
most relevant chunks, and uses the LLM to generate a cited answer.
"""
import os
import glob
import logging
import chromadb
from chromadb.utils import embedding_functions

import config
from logging_config import Timer

logger = logging.getLogger("qualitative_agent")

DOCS_DIR = config.DOCS_DIR
VECTORDB_DIR = config.VECTORDB_DIR
RELEVANCE_THRESHOLD = config.RELEVANCE_THRESHOLD


class QualitativeAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL_NAME
        )
        self.chroma_client = chromadb.PersistentClient(path=VECTORDB_DIR)
        self.collection = self.chroma_client.get_or_create_collection(
            name="enterprise_docs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        if self.collection.count() == 0:
            self._index_documents()

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return [c.strip() for c in chunks if c.strip()]

    def _index_documents(self):
        logger.info("Indexing documents into Chroma...")
        doc_paths = glob.glob(os.path.join(DOCS_DIR, "*.md"))
        ids, texts, metadatas = [], [], []
        for path in doc_paths:
            doc_id = os.path.splitext(os.path.basename(path))[0]
            with open(path, "r") as f:
                content = f.read()
            chunks = self._chunk_text(content)
            for i, chunk in enumerate(chunks):
                ids.append(f"{doc_id}_chunk{i}")
                texts.append(chunk)
                metadatas.append({"source": doc_id, "chunk_index": i})
        if ids:
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Indexed {len(ids)} chunks from {len(doc_paths)} documents.")

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=k)
        retrieved = []
        for doc, meta, distance in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            similarity = 1 - distance  # Chroma default is cosine distance
            retrieved.append(
                {
                    "text": doc,
                    "source": meta["source"],
                    "chunk_index": meta["chunk_index"],
                    "similarity": round(similarity, 4),
                }
            )
        return retrieved

    def answer(self, query: str) -> dict:
        with Timer() as t:
            retrieved = self.retrieve(query)
            relevant = [r for r in retrieved if r["similarity"] >= RELEVANCE_THRESHOLD]

            if not relevant:
                logger.info(
                    "No relevant sources found",
                    extra={
                        "event": "qualitative_answer",
                        "query": query,
                        "sources": [],
                        "execution_time_sec": None,
                    },
                )
                return {
                    "answer": "I couldn't find anything in the knowledge base relevant to that question.",
                    "sources": [],
                    "agent": "qualitative",
                }

            context = "\n\n".join(f"[Source: {r['source']}]\n{r['text']}" for r in relevant)
            system_instruction = (
                "You are an enterprise documentation assistant. Answer the question using ONLY "
                "the provided context. Cite sources by name. If the context doesn't fully answer "
                "the question, say so explicitly rather than guessing."
            )
            prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            try:
                answer_text = self.llm.generate(prompt, system_instruction=system_instruction)
            except Exception as e:
                logger.error(
                    "LLM generation failed",
                    extra={"event": "qualitative_answer_error", "query": query, "error": str(e)},
                )
                raise

        source_list = [
            {"document": r["source"], "chunk": r["chunk_index"], "similarity": r["similarity"]}
            for r in relevant
        ]
        logger.info(
            "Qualitative query answered",
            extra={
                "event": "qualitative_answer",
                "query": query,
                "sources": source_list,
                "execution_time_sec": t.elapsed,
            },
        )

        return {
            "answer": answer_text,
            "sources": source_list,
            "agent": "qualitative",
        }

