"""Knowledge vault (RAG) service.

Uses ChromaDB with its built-in on-device embedding model when available (no
external downloads, fully offline). If ChromaDB is not installed the service
degrades to a lightweight in-memory keyword store so knowledge upload/search
endpoints keep functioning instead of 500-ing.
"""

from __future__ import annotations

import os
import uuid
from typing import Dict, List


class _MemoryStore:
    """Tiny offline fallback: keyword-overlap ranking, no embeddings."""

    def __init__(self) -> None:
        self._docs: List[Dict] = []

    def add(self, text: str, source: str) -> None:
        self._docs.append({"text": text, "metadata": {"source": source}})

    def search(self, query: str, n_results: int) -> List[Dict]:
        terms = {t for t in query.lower().split() if len(t) > 2}
        if not terms:
            return self._docs[:n_results]
        scored = []
        for d in self._docs:
            words = set(d["text"].lower().split())
            score = len(terms & words)
            if score:
                scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _s, d in scored[:n_results]]

    def count(self) -> int:
        return len(self._docs)


class RagService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.backend = "memory"
        self.collection = None
        self._memory = _MemoryStore()

        try:
            import chromadb
            from chromadb.utils import embedding_functions

            self.client = chromadb.PersistentClient(path=persist_directory)
            emb_fn = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self.client.get_or_create_collection(
                name="knowledge_vault", embedding_function=emb_fn
            )
            self.backend = "chromadb"
            print(f"[RagService] ChromaDB ready. Documents in vault: {self.collection.count()}")
        except Exception as exc:
            print(f"[RagService] ChromaDB unavailable ({exc}). Using in-memory fallback.")

    @property
    def available(self) -> bool:
        return True  # always functional (chromadb or memory)

    def add_document(self, text: str, source: str = "manual") -> None:
        if not text or not text.strip():
            return
        if self.backend == "chromadb":
            try:
                self.collection.add(
                    documents=[text],
                    metadatas=[{"source": source}],
                    ids=[str(uuid.uuid4())],
                )
                return
            except Exception as exc:
                print(f"[RagService] add failed ({exc}); falling back to memory.")
        self._memory.add(text, source)

    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        if self.backend == "chromadb":
            try:
                results = self.collection.query(query_texts=[query], n_results=n_results)
                output: List[Dict] = []
                if results.get("documents"):
                    docs = results["documents"][0]
                    metas = results.get("metadatas") or [[]]
                    for i in range(len(docs)):
                        meta = metas[0][i] if metas and metas[0] else {}
                        output.append({"text": docs[i], "metadata": meta})
                return output
            except Exception as exc:
                print(f"[RagService] search failed ({exc}); using memory fallback.")
        return self._memory.search(query, n_results)

    def count(self) -> int:
        if self.backend == "chromadb":
            try:
                return self.collection.count()
            except Exception:
                pass
        return self._memory.count()

    def migrate_from_file(self, filepath: str = "vault.txt") -> None:
        if self.count() > 0:
            return
        if os.path.exists(filepath):
            print(f"[RagService] Migrating {filepath} into vault...")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for paragraph in (p.strip() for p in content.split("\n\n")):
                if paragraph:
                    self.add_document(paragraph, source=filepath)
            print("[RagService] Migration complete.")
