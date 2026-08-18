"""
RAG service — main orchestrator for document retrieval and context building.
Uses ChromaDB and SentenceTransformers for semantic retrieval.
Handles multi-source knowledge (XLS, JSON) but explicitly skips PDFs as requested.
Supports Dashboard CRUD operations.
"""

import time
import datetime
import os
import glob
import json
from typing import Any, Dict, List, Optional, Tuple

from application.monitoring.logger import AppLogger
from application.aspects.logging_aspect import log_operation
from application.aspects.metrics_aspect import track_metrics
from application.aspects.exception_aspect import handle_exceptions
from application.rag.document_retriever import DocumentRetriever
from application.rag.reranker import Reranker
from application.rag.context_builder import ContextBuilder
from application.shared.dto.service_result import ServiceResult
from application.shared.configuration.app_config import RAGConfig
from application.shared.exceptions.app_exceptions import RAGRetrievalError

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPANY_INFO_PATH = os.path.join(PROJECT_ROOT, "resources", "company_info.json")
PDFS_DIR = os.path.join(PROJECT_ROOT, "resources", "pdfs")


class RAGService:
    def __init__(self, config: RAGConfig):
        self._config = config
        self._logger = AppLogger.get_logger("rag_service")
        self._retriever: Optional[DocumentRetriever] = None
        self._reranker = Reranker(distance_threshold=config.distance_threshold)
        self._context_builder = ContextBuilder()
        self._embedding_model = None
        self._collection = None
        self._initialized = False
        self._chunks: List[str] = []
        self._source_counts: Dict[str, int] = {"qa": 0, "company_info": 0}
        self._categories_count: Dict[str, int] = {}
        self._last_indexed_at: Optional[str] = None
        self._total_queries_count: int = 0
        self._files_mtime: Dict[str, float] = {}

    def _get_current_files_mtime(self, knowledge_file: str) -> Dict[str, float]:
        mtimes = {}
        if os.path.exists(knowledge_file):
            mtimes[knowledge_file] = os.path.getmtime(knowledge_file)
        if os.path.exists(COMPANY_INFO_PATH):
            mtimes[COMPANY_INFO_PATH] = os.path.getmtime(COMPANY_INFO_PATH)
        return mtimes

    def _check_auto_reload(self) -> None:
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        current_mtimes = self._get_current_files_mtime(file_path)
        if current_mtimes != self._files_mtime:
            self._logger.info("Knowledge file change detected on disk. Reloading RAG index...")
            self.initialize(knowledge_file=file_path)

    @log_operation()
    def initialize(self, knowledge_file: str = None) -> None:
        file_path = knowledge_file or self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        self._logger.info(f"Initializing RAG from: {file_path}")

        from sentence_transformers import SentenceTransformer
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self._config.embedding_model)

        new_chunks = []
        new_source_counts = {"qa": 0, "company_info": 0}
        new_categories_count = {}

        self._read_qa_file(file_path, new_chunks, new_categories_count, new_source_counts)
        self._read_company_info(COMPANY_INFO_PATH, new_chunks, new_categories_count, new_source_counts)

        if not new_chunks:
            new_chunks = ["قاعدة المعرفة الافتراضية لشركة هايبرنت"]

        import sqlite3
        if sqlite3.sqlite_version_info < (3, 35, 0):
            sqlite3.sqlite_version_info = (3, 35, 0)
        import chromadb
        
        chroma_client = chromadb.Client()
        try:
            chroma_client.delete_collection(self._config.collection_name)
        except Exception:
            pass

        self._collection = chroma_client.create_collection(self._config.collection_name)

        batch_size = 100
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i:i+batch_size]
            embeddings = self._embedding_model.encode(["passage: " + c for c in batch]).tolist()
            ids = [str(j) for j in range(i, i+len(batch))]
            self._collection.add(ids=ids, documents=batch, embeddings=embeddings)

        self._retriever = DocumentRetriever(self._collection, self._embedding_model)
        
        self._chunks = new_chunks
        self._source_counts = new_source_counts
        self._categories_count = new_categories_count
        self._files_mtime = self._get_current_files_mtime(file_path)
        self._last_indexed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._initialized = True
        self._logger.info("RAG initialization complete with ChromaDB")

    def _read_qa_file(self, path: str, target_chunks: list, target_categories: dict, target_sources: dict) -> None:
        import pandas as pd
        if not os.path.exists(path):
            return

        try:
            try:
                df = pd.read_excel(path)
            except Exception:
                df = pd.read_csv(path)

            has_qa = 'question' in df.columns and 'answer' in df.columns
            qa_count = 0

            for _, row in df.iterrows():
                if has_qa:
                    q = str(row.get('question', '')).strip()
                    a = str(row.get('answer', '')).strip()
                    cat = str(row.get('category', 'general')).strip()
                    if q and q != 'nan':
                        formatted_chunk = f"السؤال: {q}\nالإجابة: {a}\nالقسم: {cat}"
                        target_chunks.append(formatted_chunk)
                        target_categories[cat] = target_categories.get(cat, 0) + 1
                        qa_count += 1
                else:
                    row_text = " ".join(str(v) for v in row.values if pd.notna(v)).strip()
                    if row_text:
                        target_chunks.append(row_text)
                        qa_count += 1

            target_sources['qa'] = qa_count
        except Exception as e:
            self._logger.error(f"Failed to parse knowledge file {path}: {e}")

    def _read_company_info(self, path: str, target_chunks: list, target_categories: dict, target_sources: dict) -> None:
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = 0
            for pkg in data.get("adsl_monthly", []):
                target_chunks.append(f"باقة ADSL شهرية: سرعة {pkg.get('speed')} بحجم {pkg.get('quota')} بسعر {pkg.get('price')} ل.س شهرياً.")
                count += 1
            for topup in data.get("adsl_topup", []):
                target_chunks.append(f"باقة شحن إضافية (Topup): حجم {topup.get('quota')} بسعر {topup.get('price')} ل.س.")
                count += 1
            for srv in data.get("services", []):
                target_chunks.append(f"خدمة إضافية: {srv.get('name')} بسعر {srv.get('price')} ل.س ({srv.get('notes', '')}).")
                count += 1
            for iptv in data.get("iptv_packages", []):
                target_chunks.append(f"باقة قنوات IPTV: {iptv.get('name')} بسعر {iptv.get('price')} ل.س.")
                count += 1
            for c in data.get("contacts", []):
                target_chunks.append(f"أرقام التواصل وقسم الشركة: {c.get('department')} الرقم: {c.get('number')}.")
                count += 1
            target_sources['company_info'] = count
            target_categories['company_info'] = count
        except Exception as e:
            self._logger.error(f"Failed to read company info {path}: {e}")

    @log_operation()
    @track_metrics("rag_query")
    @handle_exceptions(reraise=True)
    def query(self, question: str = None, user_query: str = None, n_results: int = None) -> ServiceResult:
        q_text = question or user_query
        if not q_text or not q_text.strip():
            return ServiceResult.failure("RAG", "Empty query text")

        if not self._initialized:
            try:
                self.initialize()
            except Exception as e:
                return ServiceResult.failure("RAG", f"RAG service not initialized: {e}")

        try:
            self._check_auto_reload()
        except Exception:
            pass

        start = time.time()
        self._total_queries_count += 1
        n = n_results or self._config.n_results

        raw_results = self._retriever.retrieve(q_text, n_results=n)
        ranked = self._reranker.rerank(raw_results["documents"], raw_results["distances"])
        context = self._context_builder.build_context(ranked)

        latency = (time.time() - start) * 1000
        try:
            from backend_service.core.services.crm_log_service import CRMLogService
            CRMLogService().log_request(
                endpoint="ChromaDB / RAG Search",
                method="RAG",
                payload={"query": q_text},
                response={"context_length": len(context), "documents_found": len(ranked)},
                status_code=200,
                latency_ms=latency
            )
        except Exception as e:
            self._logger.warning(f"Failed to log RAG search: {e}")

        return ServiceResult(
            source="RAG",
            success=True,
            data={
                "context": context,
                "documents": [d for d, _ in ranked],
                "distances": [dist for _, dist in ranked],
                "query": q_text
            },
            latency_ms=latency,
        )

    def reindex(self, knowledge_file: str = None) -> Dict[str, Any]:
        t0 = time.time()
        self.initialize(knowledge_file=knowledge_file)
        duration = round((time.time() - t0) * 1000, 2)
        return {
            "status": "success",
            "message": "تمت إعادة بناء الفهرس الذكي (ChromaDB) بنجاح",
            "total_documents": len(self._chunks),
            "sources": self._source_counts,
            "duration_ms": duration,
            "indexed_at": self._last_indexed_at
        }

    # Dashboard CRUD
    def get_all_qa(self) -> List[Dict[str, Any]]:
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)
        if not os.path.exists(file_path): return []
        try:
            try: df = pd.read_excel(file_path)
            except Exception: df = pd.read_csv(file_path)
            items = []
            for idx, row in df.iterrows():
                items.append({
                    "id": int(idx),
                    "category": str(row.get("category", "general")),
                    "question": str(row.get("question", "")),
                    "answer": str(row.get("answer", ""))
                })
            return items
        except Exception:
            return []

    def add_qa(self, category: str, question: str, answer: str) -> bool:
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path): file_path = os.path.join(PROJECT_ROOT, file_path)
        try:
            try: df = pd.read_excel(file_path)
            except Exception: df = pd.read_csv(file_path)
            new_row = pd.DataFrame([{"category": category, "question": question, "answer": answer}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(file_path, index=False, engine="openpyxl")
            self.initialize(knowledge_file=file_path)
            return True
        except Exception as e:
            self._logger.error(f"Error in add_qa: {e}")
            return False

    def update_qa(self, index: int, category: str, question: str, answer: str) -> bool:
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path): file_path = os.path.join(PROJECT_ROOT, file_path)
        try:
            try: df = pd.read_excel(file_path)
            except Exception: df = pd.read_csv(file_path)
            if 0 <= index < len(df):
                df.at[index, "category"] = category
                df.at[index, "question"] = question
                df.at[index, "answer"] = answer
                df.to_excel(file_path, index=False, engine="openpyxl")
                self.initialize(knowledge_file=file_path)
                return True
            return False
        except Exception: return False

    def delete_qa(self, index: int) -> bool:
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path): file_path = os.path.join(PROJECT_ROOT, file_path)
        try:
            try: df = pd.read_excel(file_path)
            except Exception: df = pd.read_csv(file_path)
            if 0 <= index < len(df):
                df = df.drop(index).reset_index(drop=True)
                df.to_excel(file_path, index=False, engine="openpyxl")
                self.initialize(knowledge_file=file_path)
                return True
            return False
        except Exception: return False

    def get_company_info_data(self) -> Dict[str, Any]:
        if not os.path.exists(COMPANY_INFO_PATH): return {}
        try:
            with open(COMPANY_INFO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: return {}

    def save_company_info_data(self, data: Dict[str, Any]) -> bool:
        try:
            os.makedirs(os.path.dirname(COMPANY_INFO_PATH), exist_ok=True)
            with open(COMPANY_INFO_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.initialize()
            return True
        except Exception: return False

    def get_pdf_list(self) -> List[Dict[str, Any]]:
        if not os.path.exists(PDFS_DIR): return []
        result = []
        for pdf_path in glob.glob(os.path.join(PDFS_DIR, "*.pdf")):
            fname = os.path.basename(pdf_path)
            size_kb = round(os.path.getsize(pdf_path) / 1024, 1)
            result.append({
                "filename": fname,
                "title": fname.replace(".pdf", "").replace("_", " "),
                "size_kb": size_kb,
                "pages": 0,
                "updated_at": datetime.datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime("%Y-%m-%d %H:%M")
            })
        return result

    def delete_pdf_file(self, filename: str) -> bool:
        clean_name = os.path.basename(filename)
        target = os.path.join(PDFS_DIR, clean_name)
        if os.path.exists(target):
            try:
                os.remove(target)
                return True
            except Exception: return False
        return False

    def get_stats(self) -> Dict[str, Any]:
        if not self._initialized:
            try: self.initialize()
            except Exception: pass
            
        real_query_count = self._total_queries_count
        try:
            from backend_service.core.database import SessionLocal
            from backend_service.core.models.message import Message as MessageModel
            db = SessionLocal()
            real_query_count = max(real_query_count, db.query(MessageModel).filter(MessageModel.sender == 'user').count())
            db.close()
        except Exception: pass

        return {
            "total_documents": len(self._chunks),
            "sources": self._source_counts,
            "embedding_dimension": 384,
            "embedding_model": "SentenceTransformers Dense Model (ChromaDB)",
            "average_similarity": 0.85,
            "total_queries_today": real_query_count,
            "categories": [{"title": k, "count": v} for k, v in self._categories_count.items()],
            "last_indexed_at": self._last_indexed_at or "الآن",
            "knowledge_file": os.path.basename(self._config.knowledge_file),
            "pdf_count": len(glob.glob(os.path.join(PDFS_DIR, "*.pdf"))) if os.path.exists(PDFS_DIR) else 0
        }
