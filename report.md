# Project Architecture Report

## 1. Architecture Used
The project utilizes a robust, multi-tier, modular architecture based on Domain-Driven Design (DDD) principles and Event-Driven Architecture (EDA). It employs a Message Bus for asynchronous communication between loosely coupled components (modules). It also leverages Aspect-Oriented Programming (AOP) for cross-cutting concerns like logging, metrics, exception handling, and tracing, ensuring the core business logic remains clean and maintainable.

## 2. File Responsibilities

### Root Files
- `main.py`: Entry point for the application. Initializes the server and components.

- `database_setup.sql`: Database schema definition for MySQL persistence layer.
- `requirements.txt`: Python package dependencies.

### Application Modules (`application/`)

**Agent (`application/agent/`)**
**Agent (`application/agent/`)**
- `agent_service.py`: The main orchestrator for the agent layer. It acts as the primary entry point when a user message needs to be analyzed, delegating heavy lifting to the `IntentClassifier` and extracting necessary parameters to create an `AgentDecision` object. It also determines the appropriate response tone.
- `intent_classifier.py`: The analytical core that maps raw text to a specific domain intent and decides which backend services must be called. It attempts to use an LLM for classification and falls back to keyword matching (`INTENT_KEYWORDS`) if necessary. It relies on the `INTENT_SERVICE_MAP` to determine required services.
- `intents.py`: A configuration file defining the vocabulary of the chatbot by listing all `ALLOWED_INTENTS`. This restricts the LLM to categorizing user queries into known buckets.
- `task_planner.py`: Takes the decision and turns it into an action plan. The `TaskPlanner.plan()` method creates a list of `TaskStep` objects dictating the order of operations (e.g., run RAG, then CRM, then LLM) and maps general intents to specific CRM function names.
- `workflow_selector.py`: A lightweight wrapper class providing a clean interface for selecting workflows based on intent, primarily delegating to the `INTENT_SERVICE_MAP` imported from the `intent_classifier`.

**Analytics (`application/analytics/`)**
- `analytics_service.py`: Core logic for managing analytics data.
- `usage_metrics.py`: Tracks LLM token usage and interaction statistics.

**Aspects (`application/aspects/`)**
- `exception_aspect.py`: Global exception handling decorator.
- `logging_aspect.py`: Centralized logging decorator.
- `metrics_aspect.py`: Performance and execution time tracking decorator.
- `tracing_aspect.py`: Distributed tracing decorator.

**CRM Integration (`backend_service/crm/`)**
- `crm_client.py`: Handles direct HTTP REST connections to the live Hypernet CRM.

**Facade (`application/facade/`)**
- `chatbot_facade.py`: High-level entry point for interacting with the chatbot.
- `service_dispatcher.py`: Routes tasks to the correct internal modules.
- `workflow_coordinator.py`: Manages the lifecycle of a user's query execution.

**LLM (`application/llm/`)**
- `inference_engine.py`: Executes prompts against the language models.
- `llm_service.py`: High-level wrapper for LLM interactions.
- `ollama_provider.py`: Specific integration logic for Ollama.
- `output_parser.py`: Extracts structured data from raw LLM text.
- `prompt_builder.py`: Dynamically creates context-aware prompts.

**Message Bus (`application/message_bus/`)**
- `broker.py`: The central event broker for publish/subscribe routing.
- `commands/*.py`: Definitions of actions (e.g., `analyze_intent`, `execute_crm`).
- `events/*.py`: Definitions of completed events (e.g., `crm_completed`, `response_ready`).

**Monitoring (`application/monitoring/`)**
- `logger.py`: Central logger configuration.
- `metrics_collector.py`: Collects and aggregates telemetry.
- `trace_manager.py`: Manages distributed tracing.

**Presentation (`application/presentation/`)**
- `telegram_bot.py`: Interface connecting the application to Telegram.

**RAG (`application/rag/`)**
- `context_builder.py`: Prepares retrieved docs for the LLM context.
- `document_retriever.py`: Fetches relevant documents from the knowledge base.
- `rag_service.py`: Core RAG execution logic.
- `reranker.py`: Orders retrieved documents by relevance.

**Response Generation (`application/response_generation/`)**
- `formatter.py`: Formats text output (markdown/HTML).
- `response_builder.py`: Constructs the final response object.
- `response_service.py`: Orchestrates the response generation phase.

**Session Management (`application/session_management/`)**
- `conversation_context.py`: Represents the chat history and state.
- `session_service.py`: Manages MySQL persistence for user sessions.

**Shared (`application/shared/`)**
- `configuration/app_config.py`: Application settings management.
- `dto/*.py`: Data Transfer Objects for cross-module data passing.
- `exceptions/app_exceptions.py`: Custom error definitions.

## 3. Unused / Miscellaneous Files
- `chatbot.xls`: A spreadsheet likely used for planning or documentation rather than runtime execution.
- `chatbot_knowledge_base.md`: The raw knowledge base data, utilized by the RAG system but not executable code.
- `explanation.txt`: A generic text file that appears to hold notes or explanations, not actively used by the application code.
- `report.txt`: The very file this report is written into.

## 4. Frameworks & Technologies Used

The project relies on a carefully selected stack of modern tools, predominantly favoring "Pure Python" and Clean Architecture for maximum control and performance over bloated monolithic frameworks (like LangChain or LlamaIndex).

### Core Application
- **Python (Pure Python)**: The foundation of the system. Custom implementations are used for core logic (Intent Classification, Task Planning, Context Building) to ensure 100% control over the conversational AI workflow and zero reliance on fragile high-level AI frameworks.
- **FastAPI**: A high-performance web framework used for the main API layer. It provides REST endpoints (e.g., `/api/chat`) and automated Swagger UI documentation, allowing the chatbot to be easily integrated into mobile or web applications.
- **Uvicorn**: An ASGI web server implementation for Python, used to run the FastAPI application.

### Artificial Intelligence & Machine Learning
- **Google Generative AI (Gemini)**: The primary LLM (Large Language Model) provider used for generating conversational responses and intelligent troubleshooting.
- **Sentence-Transformers**: Used to generate dense vector embeddings (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) for Arabic semantic search and knowledge retrieval.
- **ChromaDB**: An open-source vector database used as the memory backend for the RAG (Retrieval-Augmented Generation) system, storing and retrieving ISP technical support documents.

### Integrations & Presentation
- **python-telegram-bot**: A pure Python interface for the Telegram Bot API. It runs seamlessly as a background thread within the FastAPI process to service Telegram users directly.
- **Requests / HTTP**: Used for communicating with the actual Hypernet CRM API to fetch live customer data (e.g., line status, SNR values) or execute remote actions (e.g., reset port).

### Data Persistence
- **SQLAlchemy**: The Python SQL toolkit and Object Relational Mapper (ORM), providing an efficient way to interact with the relational database.
- **MySQL / PyMySQL**: Used for persistent storage of user sessions, chat history, and conversational state across API restarts.

### Dashboard (Analytics)
- **Flask**: A lightweight WSGI web framework used specifically to serve the internal analytics dashboard (`dashboard.py`), presenting live usage metrics and chat histories to administrators.
