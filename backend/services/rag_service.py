"""Persistent, network-free knowledge retrieval."""

from __future__ import annotations

import hashlib
import math
import os
import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


class LocalHashEmbedding:
    """Deterministic feature hashing with no model download or telemetry."""

    DIMENSIONS = 384

    @staticmethod
    def name() -> str:
        return "onf-local-hash-v1"

    def get_config(self) -> dict:
        return {"dimensions": self.DIMENSIONS}

    @staticmethod
    def build_from_config(config: dict) -> "LocalHashEmbedding":
        return LocalHashEmbedding()

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def _embed(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z0-9][a-z0-9_-]+", text.lower())
        counts = Counter(tokens)
        vector = [0.0] * self.DIMENSIONS
        for token, frequency in counts.items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.DIMENSIONS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign * (1.0 + math.log(frequency))
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class RagService:
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "before", "but", "by", "can", "do", "for",
        "from", "has", "have", "how", "i", "if", "in", "is", "it", "of", "on", "or", "our", "should",
        "that", "the", "their", "this", "to", "we", "what", "when", "where", "which", "who", "with",
    }

    def __init__(self, persist_directory: str = "./chroma_db") -> None:
        self.seeded_chunks = 0
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self.embedding_function = LocalHashEmbedding()
        self.collection = self.client.get_or_create_collection(
            name="knowledge_vault_local_v2",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def status(self) -> dict:
        return {
            "status": "ready",
            "documents": self.count(),
            "curated_chunks": self.seeded_chunks,
            "embedding": self.embedding_function.name(),
        }

    def add_document(self, text: str, source: str = "manual", metadata: dict | None = None) -> int:
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        metadatas = []
        for index, _ in enumerate(chunks, start=1):
            item: dict[str, Any] = {"source": source, "chunk": index}
            item.update(metadata or {})
            metadatas.append(item)

        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=[str(uuid.uuid4()) for _ in chunks],
        )
        return len(chunks)

    def seed_directory(self, directory: str = "knowledge") -> int:
        """Idempotently loads curated Markdown evidence with section-level citations."""
        root = Path(directory)
        if not root.exists():
            return 0

        seeded = 0
        for path in sorted(root.rglob("*.md")):
            content = path.read_text(encoding="utf-8")
            source, sections = self._markdown_sections(content, fallback_title=path.stem.replace("-", " ").title())
            seed_key = path.relative_to(root).as_posix()
            self.collection.delete(where={"seed_key": seed_key})

            documents: list[str] = []
            metadatas: list[dict[str, Any]] = []
            ids: list[str] = []
            for section_index, (section, body) in enumerate(sections, start=1):
                for chunk_index, chunk in enumerate(self._chunk_text(body), start=1):
                    documents.append(chunk)
                    metadatas.append(
                        {
                            "source": source,
                            "section": section,
                            "seed_key": seed_key,
                            "curated": "true",
                            "chunk": chunk_index,
                        }
                    )
                    ids.append(str(uuid.uuid5(uuid.NAMESPACE_URL, f"onf://knowledge/{seed_key}/{section_index}/{chunk_index}")))

            if documents:
                self.collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
                seeded += len(documents)
        self.seeded_chunks = seeded
        return seeded

    def search(self, query: str, n_results: int = 3) -> list[dict]:
        if not query.strip() or self.count() == 0:
            return []
        limit = min(max(n_results * 8, 24), self.count())
        results = self.collection.query(query_texts=[query], n_results=limit)
        output = []
        query_terms = self._search_terms(query)
        query_bigrams = set(zip(query_terms, query_terms[1:]))
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        for index, document in enumerate(documents):
            distance = distances[index] if index < len(distances) else None
            metadata = metadatas[index] if index < len(metadatas) else {}
            semantic = max(0.0, 1.0 - distance) if distance is not None else 0.0
            document_terms = self._search_terms(document)
            document_term_set = set(document_terms)
            lexical = (
                sum(1 for term in set(query_terms) if term in document_term_set) / max(1, len(set(query_terms)))
            )
            document_bigrams = set(zip(document_terms, document_terms[1:]))
            phrase = len(query_bigrams & document_bigrams) / max(1, len(query_bigrams))
            curated_boost = 0.08 if metadata.get("curated") == "true" and lexical >= 0.12 else 0.0
            relevance = min(1.0, (semantic * 0.52) + (lexical * 0.34) + (phrase * 0.14) + curated_boost)
            output.append(
                {
                    "text": document,
                    "metadata": metadata,
                    "relevance": round(relevance, 3),
                }
            )
        return sorted(output, key=lambda item: item["relevance"], reverse=True)[:max(n_results, 1)]

    def count(self) -> int:
        return self.collection.count()

    def migrate_from_file(self, filepath: str = "vault.txt") -> int:
        if self.count() > 0 or not os.path.exists(filepath):
            return 0
        with open(filepath, "r", encoding="utf-8") as source:
            return self.add_document(source.read(), source=os.path.basename(filepath))

    @classmethod
    def _search_terms(cls, text: str) -> list[str]:
        return [
            token for token in re.findall(r"[a-z0-9][a-z0-9_-]+", (text or "").lower())
            if token not in cls.STOPWORDS and len(token) > 1
        ]

    @staticmethod
    def _markdown_sections(content: str, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
        source = fallback_title
        current_section = "Overview"
        buffer: list[str] = []
        sections: list[tuple[str, str]] = []

        def flush() -> None:
            body = "\n".join(buffer).strip()
            if body:
                sections.append((current_section, body))
            buffer.clear()

        for line in re.sub(r"\r\n?", "\n", content or "").split("\n"):
            if line.startswith("# "):
                source = line[2:].strip() or source
                continue
            if re.match(r"^#{2,3}\s+", line):
                flush()
                current_section = re.sub(r"^#{2,3}\s+", "", line).strip() or "Overview"
                continue
            buffer.append(line)
        flush()
        return source, sections

    @staticmethod
    def _chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
        clean = re.sub(r"\r\n?", "\n", text or "").strip()
        if not clean:
            return []
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", clean) if paragraph.strip()]
        chunks: list[str] = []
        for paragraph in paragraphs:
            cursor = 0
            while cursor < len(paragraph):
                end = min(len(paragraph), cursor + size)
                if end < len(paragraph):
                    boundary = paragraph.rfind(" ", cursor, end)
                    end = boundary if boundary > cursor + size // 2 else end
                chunks.append(paragraph[cursor:end].strip())
                if end >= len(paragraph):
                    break
                cursor = max(cursor + 1, end - overlap)
        return [chunk for chunk in chunks if chunk]