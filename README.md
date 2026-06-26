# AI ISP Chatbot Architecture

This project is a robust, multi-tier chatbot application built for an ISP. It follows a modular architecture consisting of 13 main modules designed to separate concerns, facilitate message-bus communication, integrate with CRM systems, and provide observability through Aspect-Oriented Programming (AOP).

## Root Files

- **`main.py`**: The main entry point to start the chatbot application. Initializes components, configures AOP, and sets up the server.
- **`mock_crm_server.py`**: A mock server for simulating Model Context Protocol (MCP) interactions with a CRM backend.
- **`database_setup.sql`**: SQL script for setting up the MySQL persistence layer for sessions and chat history.
- **`requirements.txt`**: Python dependencies for the project.
- **`chatbot.xls`**: Documentation or spreadsheet related to chatbot intents/flows.

## Application Architecture (`application/`)

- **`app.py`**: Application bootstrap, configuring and wiring the underlying services and dependencies.

### 1. Agent (`application/agent/`)
Handles the decision-making process to route user queries efficiently.
- `agent_service.py`: Main service coordinating the agent logic.
- `intent_classifier.py`: Analyzes incoming messages to classify the user intent.
- `task_planner.py`: Breaks down complex queries into executable tasks.
- `workflow_selector.py`: Selects the appropriate workflow based on intent and task.

### 2. Analytics (`application/analytics/`)
Collects and manages usage and analytics data.
- `analytics_service.py`: Service to handle analytics logic.
- `usage_metrics.py`: Tracks token usage, interactions, and other important metrics.

### 3. Aspects (`application/aspects/`)
Aspect-Oriented Programming (AOP) decorators for handling cross-cutting concerns cleanly.
- `exception_aspect.py`: Global exception handling and reporting.
- `logging_aspect.py`: Centralized logging decorators for functions.
- `metrics_aspect.py`: Decorators for tracking execution times and usage stats.
- `tracing_aspect.py`: Distributed tracing decorators for observability.

### 4. CRM Integration (`application/crm_integration/`)
Integration with external CRM systems via MCP.
- `crm_connector.py`: Low-level connection handling.
- `crm_service.py`: Business logic for retrieving customer data and performing CRM actions.
- `mcp_client.py`: Client for interacting with the Model Context Protocol server.

### 5. Facade (`application/facade/`)
Acts as the central orchestrator and entry point for the business logic.
- `chatbot_facade.py`: High-level interface to the chatbot system.
- `service_dispatcher.py`: Dispatches tasks to appropriate underlying modules.
- `workflow_coordinator.py`: Manages the end-to-end execution of a user query.

### 6. LLM (`application/llm/`)
Manages interactions with Large Language Models.
- `inference_engine.py`: Core execution logic for running prompts against models.
- `llm_service.py`: Higher-level service wrapping the LLM functionality.
- `ollama_provider.py`: Integration specifically for Ollama as an LLM provider.
- `output_parser.py`: Parses the raw responses from LLMs into structured data.
- `prompt_builder.py`: Constructs complex prompts dynamically based on context.

### 7. Message Bus (`application/message_bus/`)
Handles internal asynchronous communication between modules.
- `broker.py`: The core message broker.
- **`commands/`**: Command definitions (e.g., `analyze_intent.py`, `execute_crm.py`, `execute_rag.py`, `generate_response.py`).
- **`events/`**: Event definitions triggered upon completion (e.g., `crm_completed.py`, `intent_analyzed.py`, `rag_completed.py`, `response_ready.py`).

### 8. Monitoring (`application/monitoring/`)
Infrastructure for logging, metrics, and tracing storage.
- `logger.py`: Centralized logger configuration and output formatting.
- `metrics_collector.py`: Collects and formats application metrics.
- `trace_manager.py`: Manages and exports distributed traces.

### 9. Presentation (`application/presentation/`)
The user interface layer.
- `telegram_bot.py`: Connects the application logic to a Telegram bot interface.

### 10. RAG (`application/rag/`)
Retrieval-Augmented Generation module to provide context-aware answers.
- `context_builder.py`: Assembles retrieved documents into a context window for the LLM.
- `document_retriever.py`: Retrieves relevant documents from the knowledge base.
- `rag_service.py`: Central service for executing RAG logic.
- `reranker.py`: Reranks retrieved documents for better relevance.

### 11. Response Generation (`application/response_generation/`)
Finalizes the output before sending it to the user.
- `formatter.py`: Formats text (e.g., markdown, HTML) for the specific presentation layer.
- `response_builder.py`: Constructs the final `ChatResponse` object.
- `response_service.py`: Service orchestrating response generation.

### 12. Session Management (`application/session_management/`)
Manages user context across multiple messages.
- `conversation_context.py`: Represents the context and history of an ongoing chat.
- `session_service.py`: Manages loading, updating, and saving sessions to MySQL.

### 13. Shared (`application/shared/`)
Common data transfer objects, configurations, and exceptions.
- **`configuration/`**: `app_config.py` - Manages application settings.
- **`dto/`**: Data Transfer Objects (`agent_decision.py`, `chat_message.py`, `chat_response.py`, `service_result.py`).
- **`exceptions/`**: `app_exceptions.py` - Custom application exceptions.
