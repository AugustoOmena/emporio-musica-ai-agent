from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
import chromadb
from chromadb.utils import embedding_functions

from src.utils import find_file_by_pattern


class RAGEngine:
    def __init__(
        self,
        data_dir: str = "data",
        persist_dir: str = "data/chroma_db",
        collection_name: str = "store_policies"
    ):
        self.data_dir = Path(data_dir)
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.pdf_path = find_file_by_pattern(self.data_dir, "politica", "pdf")

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn
        )
        self._index_pdf_if_needed()

    def _split_into_chunks(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        words = text.split()
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                overlap_words: List[str] = []
                overlap_length = 0
                for w in reversed(current_chunk):
                    if overlap_length + len(w) + 1 > overlap:
                        break
                    overlap_words.insert(0, w)
                    overlap_length += len(w) + 1
                
                current_chunk = overlap_words
                current_length = overlap_length

            current_chunk.append(word)
            current_length += word_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _extract_chunks(self, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
        if not self.pdf_path or not self.pdf_path.exists():
            raise FileNotFoundError(f"Policy PDF not found in '{self.data_dir}'.")

        reader = PdfReader(str(self.pdf_path))
        extracted_chunks = []
        doc_counter = 0

        for page_num, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            clean_text = " ".join(raw_text.split())
            if not clean_text:
                continue

            page_chunks = self._split_into_chunks(clean_text, chunk_size, overlap)
            for chunk_content in page_chunks:
                extracted_chunks.append({
                    "id": f"policy_p{page_num}_c{doc_counter}",
                    "text": chunk_content,
                    "metadata": {"page": page_num}
                })
                doc_counter += 1

        return extracted_chunks

    def _index_pdf_if_needed(self) -> None:
        if self.collection.count() > 0:
            return

        chunks = self._extract_chunks()
        if not chunks:
            return

        self.collection.add(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks]
        )

    def search_policies(self, query: str, top_k: int = 3) -> str:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return "Nenhuma política encontrada para o termo consultado."

        formatted_excerpts = []
        for doc, meta in zip(documents, metadatas):
            page_info = f"[Página {meta['page']}]" if meta and "page" in meta else ""
            formatted_excerpts.append(f"{page_info} {doc}")

        return "\n\n---\n\n".join(formatted_excerpts)


_rag_engine_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance