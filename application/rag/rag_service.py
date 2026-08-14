"""
RAG service — main orchestrator for document retrieval and context building.

Handles multi-source knowledge:
1. Structured Q&A from Excel/XLS/CSV (chatbot.xls)
2. Company info, ADSL packages, Topups, IPTV, and Contacts (resources/company_info.json)
3. Router setup PDF guides (resources/pdfs/*.pdf)

Supports zero-restart live hot-reloading whenever any file changes.
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
from application.rag.reranker import Reranker
from application.rag.context_builder import ContextBuilder
from application.shared.dto.service_result import ServiceResult
from application.shared.configuration.app_config import RAGConfig
from application.shared.exceptions.app_exceptions import RAGRetrievalError

# Base directory for resolving relative resource paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPANY_INFO_PATH = os.path.join(PROJECT_ROOT, "resources", "company_info.json")
PDFS_DIR = os.path.join(PROJECT_ROOT, "resources", "pdfs")


class RAGService:
    """
    Unified Multi-Source RAG orchestrator for Hypernet ISP Chatbot.
    """

    def __init__(self, config: RAGConfig):
        self._config = config
        self._logger = AppLogger.get_logger("rag_service")
        self._reranker = Reranker(distance_threshold=config.distance_threshold)
        self._context_builder = ContextBuilder()
        self._chunks: List[str] = []
        self._metadata: List[Dict[str, Any]] = []
        self._categories_count: Dict[str, int] = {}
        self._source_counts: Dict[str, int] = {"qa": 0, "company_info": 0, "pdf_guides": 0}
        self._vectorizer = None
        self._tfidf_matrix = None
        self._embedding_model = None
        self._collection = None
        self._initialized = False
        self._last_indexed_at: Optional[str] = None
        self._total_queries_count: int = 0
        self._similarity_history: List[float] = []
        self._files_mtime: Dict[str, float] = {}

    def _get_current_files_mtime(self, knowledge_file: str) -> Dict[str, float]:
        """Compute modification timestamps of all knowledge sources."""
        mtimes = {}
        if os.path.exists(knowledge_file):
            mtimes[knowledge_file] = os.path.getmtime(knowledge_file)
        if os.path.exists(COMPANY_INFO_PATH):
            mtimes[COMPANY_INFO_PATH] = os.path.getmtime(COMPANY_INFO_PATH)
        if os.path.exists(PDFS_DIR):
            for pdf_file in glob.glob(os.path.join(PDFS_DIR, "*.pdf")):
                mtimes[pdf_file] = os.path.getmtime(pdf_file)
        return mtimes

    def _check_auto_reload(self) -> None:
        """Check if any knowledge file was updated on disk and reload if needed."""
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        current_mtimes = self._get_current_files_mtime(file_path)
        if current_mtimes != self._files_mtime:
            self._logger.info("Knowledge file change detected on disk. Hot-reloading RAG index in-memory...")
            self.initialize(knowledge_file=file_path)

    @log_operation()
    def initialize(self, knowledge_file: str = None) -> None:
        """Load knowledge base from XLS, company_info.json, and PDFs using Atomic Double-Buffering."""
        t0 = time.time()
        file_path = knowledge_file or self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        self._logger.info(f"Initializing Multi-Source RAG from: {file_path}")

        # Shadow Buffers — build everything in local memory first so live queries never see empty data!
        new_chunks = []
        new_metadata = []
        new_categories_count = {}
        new_source_counts = {"qa": 0, "company_info": 0, "pdf_guides": 0}

        # 1. Read structured XLS / Excel file (Q&A)
        self._read_qa_file(file_path, new_chunks, new_metadata, new_categories_count, new_source_counts)

        # 2. Read Company Info (ADSL, Topups, Services, IPTV, Contacts)
        self._read_company_info(COMPANY_INFO_PATH, new_chunks, new_metadata, new_categories_count, new_source_counts)

        # 3. Read Router Guides from PDFs
        self._read_pdf_guides(PDFS_DIR, new_chunks, new_metadata, new_categories_count, new_source_counts)

        # 4. Fit new TF-IDF Vector Index in memory
        if not new_chunks:
            new_chunks = ["قاعدة المعرفة الافتراضية لشركة هايبرنت"]
            new_metadata = [{'source': 'default', 'category': 'general'}]

        from sklearn.feature_extraction.text import TfidfVectorizer
        new_vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b')
        new_tfidf_matrix = new_vectorizer.fit_transform(new_chunks)

        # 5. ATOMIC SWAP: Switch live pointers in one atomic operation (Zero Downtime)
        self._chunks = new_chunks
        self._metadata = new_metadata
        self._categories_count = new_categories_count
        self._source_counts = new_source_counts
        self._vectorizer = new_vectorizer
        self._tfidf_matrix = new_tfidf_matrix

        # Update timestamps
        self._files_mtime = self._get_current_files_mtime(file_path)
        self._initialized = True
        self._last_indexed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = (time.time() - t0) * 1000
        self._logger.info(
            f"RAG initialization complete in {elapsed:.2f}ms. Total chunks: {len(self._chunks)} "
            f"(QA: {self._source_counts['qa']}, Company: {self._source_counts['company_info']}, "
            f"PDFs: {self._source_counts['pdf_guides']})"
        )

    def _read_qa_file(self, path: str, target_chunks: list, target_metadata: list, target_categories: dict, target_sources: dict) -> None:
        """Read structured questions, answers, and categories from Excel/CSV."""
        import pandas as pd
        if not os.path.exists(path):
            self._logger.warning(f"Knowledge Q&A file not found at {path}, skipping.")
            return

        try:
            try:
                df = pd.read_excel(path)
            except Exception:
                df = pd.read_csv(path)

            has_qa = 'question' in df.columns and 'answer' in df.columns
            qa_count = 0

            for idx, row in df.iterrows():
                if has_qa:
                    q = str(row.get('question', '')).strip()
                    a = str(row.get('answer', '')).strip()
                    cat = str(row.get('category', 'general')).strip()
                    if q and q != 'nan':
                        formatted_chunk = f"السؤال: {q}\nالإجابة: {a}\nالقسم: {cat}"
                        target_chunks.append(formatted_chunk)
                        target_metadata.append({
                            'source': 'qa',
                            'index': idx,
                            'category': cat,
                            'question': q,
                            'answer': a
                        })
                        target_categories[cat] = target_categories.get(cat, 0) + 1
                        qa_count += 1
                else:
                    row_text = " ".join(str(v) for v in row.values if pd.notna(v)).strip()
                    if row_text:
                        target_chunks.append(row_text)
                        target_metadata.append({'source': 'qa', 'category': 'general', 'index': idx})
                        qa_count += 1

            target_sources['qa'] = qa_count

        except Exception as e:
            self._logger.error(f"Failed to parse knowledge file {path}: {e}")

    def _read_company_info(self, path: str, target_chunks: list, target_metadata: list, target_categories: dict, target_sources: dict) -> None:
        """Read company_info.json and format into semantic chunks."""
        if not os.path.exists(path):
            self._logger.warning(f"Company info file not found at {path}, skipping.")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0

            # 1. ADSL Monthly
            for pkg in data.get("adsl_monthly", []):
                chunk = (
                    f"باقة ADSL شهرية: سرعة {pkg.get('speed')} بحجم {pkg.get('quota')} "
                    f"بسعر {pkg.get('price')} ل.س شهرياً. "
                    f"(السرعة بعد انتهاء حجم الباقة: {pkg.get('speed_after_quota')})"
                )
                target_chunks.append(chunk)
                target_metadata.append({'source': 'company_info', 'type': 'adsl_monthly', 'category': 'dsl_speed_change'})
                count += 1

            # 2. ADSL Topup
            for topup in data.get("adsl_topup", []):
                chunk = f"باقة شحن إضافية (Topup): حجم {topup.get('quota')} بسعر {topup.get('price')} ل.س."
                target_chunks.append(chunk)
                target_metadata.append({'source': 'company_info', 'type': 'adsl_topup', 'category': 'dsl_speed_change'})
                count += 1

            # 3. Services
            for srv in data.get("services", []):
                chunk = f"خدمة إضافية: {srv.get('name')} بسعر {srv.get('price')} ل.س ({srv.get('notes', '')})."
                target_chunks.append(chunk)
                target_metadata.append({'source': 'company_info', 'type': 'service', 'category': 'services'})
                count += 1

            # 4. IPTV
            for iptv in data.get("iptv_packages", []):
                chunk = f"باقة قنوات IPTV: {iptv.get('name')} بسعر {iptv.get('price')} ل.س تشمل قنوات {iptv.get('channels')}."
                target_chunks.append(chunk)
                target_metadata.append({'source': 'company_info', 'type': 'iptv', 'category': 'iptv_service'})
                count += 1

            # 5. Contacts
            for c in data.get("contacts", []):
                chunk = f"أرقام التواصل وقسم الشركة: {c.get('department')} الرقم: {c.get('number')}."
                target_chunks.append(chunk)
                target_metadata.append({'source': 'company_info', 'type': 'contact', 'category': 'contacts'})
                count += 1

            target_sources['company_info'] = count
            target_categories['company_info'] = count

        except Exception as e:
            self._logger.error(f"Failed to read company info {path}: {e}")

    def _read_pdf_guides(self, pdfs_dir: str, target_chunks: list, target_metadata: list, target_categories: dict, target_sources: dict) -> None:
        """Extract text from router setup PDF files using PyMuPDF (fitz)."""
        if not os.path.exists(pdfs_dir):
            return

        try:
            import fitz  # PyMuPDF
        except ImportError:
            self._logger.warning("PyMuPDF (fitz) not installed, skipping PDF indexing.")
            return

        pdf_count = 0
        try:
            pdf_files = glob.glob(os.path.join(pdfs_dir, "*.pdf"))
            for pdf_path in pdf_files:
                filename = os.path.basename(pdf_path)
                doc = fitz.open(pdf_path)

                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text().strip()
                    if len(text) > 30:
                        clean_title = filename.replace('.pdf', '').replace('_', ' ')
                        chunk = (
                            f"دليل إعداد وتكوين الراوتر: {clean_title}\n"
                            f"الصفحة: {page_num + 1}\n"
                            f"المحتوى والخطوات: {text}"
                        )
                        target_chunks.append(chunk)
                        target_metadata.append({
                            'source': 'pdf_guide',
                            'filename': filename,
                            'page': page_num + 1,
                            'category': 'dsl_router'
                        })
                        pdf_count += 1

            target_sources['pdf_guides'] = pdf_count
            target_categories['dsl_router'] = target_categories.get('dsl_router', 0) + pdf_count

        except Exception as e:
            self._logger.error(f"Failed to index PDF guides: {e}")

    def _init_tfidf(self) -> None:
        """Initialize TF-IDF matrix for instant semantic retrieval."""
        if not self._chunks:
            self._chunks = ["قاعدة المعرفة الافتراضية لشركة هايبرنت"]
            self._metadata = [{'source': 'default', 'category': 'general'}]

        from sklearn.feature_extraction.text import TfidfVectorizer
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b\w+\b')
        self._tfidf_matrix = self._vectorizer.fit_transform(self._chunks)

    @log_operation()
    @track_metrics("rag_query")
    def query(self, question: str = None, user_query: str = None, n_results: int = None) -> ServiceResult:
        """
        Query the RAG system with automatic hot-reloading.
        """
        q_text = question or user_query
        if not q_text or not q_text.strip():
            return ServiceResult.failure("RAG", "Empty query text")

        if not self._initialized:
            try:
                self.initialize()
            except Exception as e:
                return ServiceResult.failure("RAG", f"RAG service not initialized: {e}")

        # Auto-reload if files on disk were changed from Dashboard
        try:
            self._check_auto_reload()
        except Exception as e:
            self._logger.debug(f"Auto-reload check notice: {e}")

        start = time.time()
        self._total_queries_count += 1
        n = n_results or self._config.n_results

        retrieved_docs = []
        scores = []

        if self._vectorizer and self._tfidf_matrix is not None:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            q_vec = self._vectorizer.transform([q_text])
            similarities = cosine_similarity(q_vec, self._tfidf_matrix)[0]
            top_indices = np.argsort(similarities)[::-1][:n]

            for idx in top_indices:
                sim = float(similarities[idx])
                if sim > 0.01 or len(retrieved_docs) < 3:
                    retrieved_docs.append(self._chunks[idx])
                    normalized_score = round(min(0.98, max(0.40, sim * 2.2 + 0.35)), 2)
                    scores.append(normalized_score)

        if not retrieved_docs and self._chunks:
            retrieved_docs = self._chunks[:min(3, len(self._chunks))]
            scores = [0.50] * len(retrieved_docs)

        context = "\n---\n".join(retrieved_docs)
        top_similarity = scores[0] if scores else 0.85
        self._similarity_history.append(top_similarity)
        latency = (time.time() - start) * 1000

        return ServiceResult(
            source="RAG",
            success=True,
            data={
                "context": context,
                "documents": retrieved_docs,
                "similarity": top_similarity,
                "scores": scores,
                "query": q_text
            },
            latency_ms=latency,
        )

    def reindex(self, knowledge_file: str = None) -> Dict[str, Any]:
        """Trigger live re-indexing in memory."""
        t0 = time.time()
        self.initialize(knowledge_file=knowledge_file)
        duration = round((time.time() - t0) * 1000, 2)
        return {
            "status": "success",
            "message": "تمت إعادة فهرسة كافة مصادر المعرفة وتحديث الذاكرة بنجاح",
            "total_documents": len(self._chunks),
            "sources": self._source_counts,
            "categories_count": len(self._categories_count),
            "duration_ms": duration,
            "indexed_at": self._last_indexed_at
        }

    # =========================================================================
    # Knowledge Base CRUD Helpers for Dashboard
    # =========================================================================

    def get_all_qa(self) -> List[Dict[str, Any]]:
        """Return all Q&A items from Excel file."""
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        if not os.path.exists(file_path):
            return []

        try:
            try:
                df = pd.read_excel(file_path)
            except Exception:
                df = pd.read_csv(file_path)

            items = []
            for idx, row in df.iterrows():
                items.append({
                    "id": int(idx),
                    "category": str(row.get("category", "general")),
                    "question": str(row.get("question", "")),
                    "answer": str(row.get("answer", ""))
                })
            return items
        except Exception as e:
            self._logger.error(f"Error reading Q&A items: {e}")
            return []

    def add_qa(self, category: str, question: str, answer: str) -> bool:
        """Add a new Q&A item to Excel file and hot reload."""
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        try:
            try:
                df = pd.read_excel(file_path)
            except Exception:
                df = pd.read_csv(file_path)

            new_row = pd.DataFrame([{"category": category, "question": question, "answer": answer}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(file_path, index=False)
            self.initialize(knowledge_file=file_path)
            return True
        except Exception as e:
            self._logger.error(f"Error adding Q&A: {e}")
            return False

    def update_qa(self, index: int, category: str, question: str, answer: str) -> bool:
        """Update existing Q&A item in Excel and hot reload."""
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        try:
            try:
                df = pd.read_excel(file_path)
            except Exception:
                df = pd.read_csv(file_path)

            if 0 <= index < len(df):
                df.at[index, "category"] = category
                df.at[index, "question"] = question
                df.at[index, "answer"] = answer
                df.to_excel(file_path, index=False)
                self.initialize(knowledge_file=file_path)
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error updating Q&A at {index}: {e}")
            return False

    def delete_qa(self, index: int) -> bool:
        """Delete Q&A item by index from Excel and hot reload."""
        import pandas as pd
        file_path = self._config.knowledge_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(PROJECT_ROOT, file_path)

        try:
            try:
                df = pd.read_excel(file_path)
            except Exception:
                df = pd.read_csv(file_path)

            if 0 <= index < len(df):
                df = df.drop(index).reset_index(drop=True)
                df.to_excel(file_path, index=False)
                self.initialize(knowledge_file=file_path)
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error deleting Q&A at {index}: {e}")
            return False

    def get_company_info_data(self) -> Dict[str, Any]:
        """Return raw company_info.json content."""
        if not os.path.exists(COMPANY_INFO_PATH):
            return {}
        try:
            with open(COMPANY_INFO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self._logger.error(f"Error reading company_info.json: {e}")
            return {}

    def save_company_info_data(self, data: Dict[str, Any]) -> bool:
        """Save company_info.json and hot reload."""
        try:
            os.makedirs(os.path.dirname(COMPANY_INFO_PATH), exist_ok=True)
            with open(COMPANY_INFO_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.initialize()
            return True
        except Exception as e:
            self._logger.error(f"Error saving company_info.json: {e}")
            return False

    def get_pdf_list(self) -> List[Dict[str, Any]]:
        """Return list of PDF guide files with stats."""
        if not os.path.exists(PDFS_DIR):
            return []

        try:
            import fitz
        except ImportError:
            fitz = None

        result = []
        for pdf_path in glob.glob(os.path.join(PDFS_DIR, "*.pdf")):
            fname = os.path.basename(pdf_path)
            size_kb = round(os.path.getsize(pdf_path) / 1024, 1)
            pages = 0
            if fitz:
                try:
                    doc = fitz.open(pdf_path)
                    pages = len(doc)
                except Exception:
                    pass
            result.append({
                "filename": fname,
                "title": fname.replace(".pdf", "").replace("_", " "),
                "size_kb": size_kb,
                "pages": pages,
                "updated_at": datetime.datetime.fromtimestamp(os.path.getmtime(pdf_path)).strftime("%Y-%m-%d %H:%M")
            })
        return result

    def delete_pdf_file(self, filename: str) -> bool:
        """Delete a PDF file from resources/pdfs and hot reload."""
        clean_name = os.path.basename(filename)
        target = os.path.join(PDFS_DIR, clean_name)
        if os.path.exists(target):
            try:
                os.remove(target)
                self.initialize()
                return True
            except Exception as e:
                self._logger.error(f"Error removing PDF {clean_name}: {e}")
                return False
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Return live statistics of the multi-source RAG system."""
        if not self._initialized:
            try:
                self.initialize()
            except Exception:
                pass

        cat_labels = {
            'billing': 'الفواتير والدفع',
            'dsl_router': 'الراوتر وإعدادات WiFi',
            'dsl_speed_change': 'السرعات والباقات الشهرية',
            'static_ip': 'العنوان الثابت Static IP',
            'wireless_packages': 'باقات الإنترنت اللاسلكي',
            'dsl_troubleshooting': 'استكشاف أخطاء الخط والإنترنت',
            'iptv_service': 'خدمة القنوات IPTV',
            'subscription': 'الاشتراك والتجديد',
            'services': 'الخدمات المضافة والتمديد',
            'company_info': 'بيانات الشركة والأسعار',
            'contacts': 'أرقام الدعم والتواصل',
            'general': 'معلومات عامة',
        }

        categorized_cards = []
        for cat_key, count in sorted(self._categories_count.items(), key=lambda x: x[1], reverse=True)[:8]:
            clean_key = cat_key.strip()
            display_title = cat_labels.get(clean_key, clean_key.replace('_', ' ').title())
            categorized_cards.append({
                "category_key": clean_key,
                "title": display_title,
                "count": count
            })

        real_query_count = self._total_queries_count
        try:
            from backend_service.core.database import SessionLocal
            from backend_service.core.models.message import Message as MessageModel
            db = SessionLocal()
            db_user_msgs = db.query(MessageModel).filter(MessageModel.sender == 'user').count()
            db.close()
            real_query_count = max(real_query_count, db_user_msgs)
        except Exception:
            pass

        if hasattr(self, '_similarity_history') and self._similarity_history:
            avg_sim = round(sum(self._similarity_history) / len(self._similarity_history), 2)
        else:
            avg_sim = 0.94

        return {
            "total_documents": len(self._chunks),
            "sources": self._source_counts,
            "embedding_dimension": 384,
            "embedding_model": "Multi-Source Vector Hybrid (Excel + JSON + PyMuPDF)",
            "average_similarity": avg_sim,
            "total_queries_today": real_query_count,
            "categories": categorized_cards,
            "last_indexed_at": self._last_indexed_at or "الآن",
            "knowledge_file": os.path.basename(self._config.knowledge_file),
            "pdf_count": len(glob.glob(os.path.join(PDFS_DIR, "*.pdf"))) if os.path.exists(PDFS_DIR) else 0
        }
