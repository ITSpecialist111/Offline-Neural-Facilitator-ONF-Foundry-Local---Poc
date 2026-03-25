import chromadb
import os
import uuid
from typing import List, Dict

from chromadb.utils import embedding_functions

class RagService:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Use a local embedding function to ensure no external model downloads are triggered
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="knowledge_vault",
            embedding_function=self.emb_fn
        )
        print(f"RAG Service Initialized. Documents in vault: {self.collection.count()}")

    def add_document(self, text: str, source: str = "manual"):
        """Adds a document to the vector store."""
        if not text or not text.strip():
            return
            
        self.collection.add(
            documents=[text],
            metadatas=[{"source": source}],
            ids=[str(uuid.uuid4())]
        )
        
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """Searches for relevant documents. Returns [{'text': str, 'metadata': dict}]"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            # Flatten results (list of lists)
            output = []
            if results['documents']:
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    meta = results['metadatas'][0][i] if results['metadatas'] else {}
                    output.append({"text": doc, "metadata": meta})
            return output
        except Exception as e:
            print(f"RAG Search Error: {e}")
            return []

    def count(self):
        return self.collection.count()
    
    def migrate_from_file(self, filepath="vault.txt"):
        """Migrates lines from a text file if the vault is empty."""
        if self.count() > 0:
            return
            
        if os.path.exists(filepath):
            print(f"Migrating {filepath} to Vector Store...")
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Split by paragraphs or lines? Let's do paragraphs
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                for p in paragraphs:
                    self.add_document(p, source=filepath)
            print("Migration complete.")
