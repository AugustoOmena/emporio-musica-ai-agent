<h1 style="display: flex; align-items: center; gap: 8px;">
  <img src="docs/assets/logo.jpeg" width="68" />
  Empório da Música - Intelligent Customer Support Agent
</h1>

A solution developed for **Artefact's AI Engineer technical challenge**, featuring an autonomous conversational agent prototype for the fictional music store _Empório da Música_, based in Campo Grande, Mato Grosso do Sul, Brazil.

The agent assists customers efficiently, understands conversational context, enforces scope guardrails, and intelligently determines when to query **operational relational data** (products, orders, promotions) versus **unstructured business rules** (return policies, shipping, and warranties).

---

## Solution Architecture

The project implements a hybrid architecture with a strict separation between structured tabular data and semantic knowledge retrieval:

```text
┌────────────────────────────────────────────────────────┐
│                   Streamlit UI (app.py)                │
└──────────────────────────┬─────────────────────────────┘
                           │ (Prompt + Conversation History)
                           ▼
┌────────────────────────────────────────────────────────┐
│                  StoreAgent (LiteLLM)                  │
│       Gemini 3.5 Flash Lite / OpenAI / Anthropic / MCP │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       [Tool: Dynamic SQL]       [Tool: Semantic RAG]
                ▼                        ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│     DuckDB In-Memory    │    │   ChromaDB Persistent   │
│   (data/*.csv Tables)   │    │ (politicas_da_loja.pdf) │
└─────────────────────────┘    └─────────────────────────┘
```

## Core Components

### `src/database.py` — Relational Data Layer with DuckDB

- Dynamically loads operational CSV files (`products`, `orders`, `customers`, `promotions`, `categories`).
- Normalizes table names and exposes typed schemas, allowing the model to generate analytical SQL queries at runtime while ensuring complete protection against data mutations (_read-only_).

### `src/rag_engine.py` — Vector RAG Layer with ChromaDB

- Ingests `politicas_da_loja.pdf` using word-boundary sliding-window chunking (500 characters with 100-character overlap).
- Indexes chunks using local vector embeddings and persists vectors locally (`data/chroma_db`) via `PersistentClient`, with lazy-loading initialization.

### `src/tools.py` — Function Calling

- Registers formal tool definitions using JSON Schema, ensuring seamless tool-calling execution via LiteLLM.

### `src/agent.py` and `src/prompts.py` — Orchestration and Agent Persona

- Manages the conversational ReAct / Tool Calling loop with execution depth limits to prevent recursive stalls.
- Enforces guardrails to gracefully decline requests outside the musical instrument domain.

---

## Technical Design Decisions

| Decision            | Technology                | Technical Rationale                                                                                                                                  |
| ------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM Orchestration   | LiteLLM                   | Universal multi-provider abstraction, allowing seamless switching between Google Gemini, OpenAI, Claude, and MCP without changing application logic. |
| Primary Model       | `gemini-3.5-flash-lite`   | Ultra-low latency, reliable native tool-calling accuracy, cost efficiency, and an extensive context window.                                          |
| Relational Database | DuckDB                    | Embedded in-memory analytical SQL engine, eliminating external database infrastructure, network overhead, and credential management.                 |
| Vector Database     | ChromaDB (Persistent)     | Embedded local vector database running with `PersistentClient`, preventing re-indexing overhead on each application interaction.                     |
| Embedding Model     | `all-MiniLM-L6-v2` (ONNX) | Lightweight local embedding model (\~80 MB), ensuring zero token costs and fast offline vector search without heavy framework dependencies.          |
| User Interface      | Streamlit                 | Rapid interactive prototyping with persistent session state management and model selection directly in the UI.                                       |

---

## Running Locally

### 1\. Prerequisites

- Python 3.10 or higher.
- A Google AI Studio API key (or credentials from your preferred provider).

### 2\. Environment Setup

Clone the repository and configure the virtual environment:

bash

```bash
git clone https://github.com/AugustoOmena/<repository-name>.git
cd <repository-name>

python3.10 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 3\. Environment Variables

Copy the example environment file:

bash

```bash
cp .env.example .env
```

Edit `.env` and provide your API credentials:

env

```env
GEMINI_API_KEY=your_api_key_here
DEFAULT_MODEL=gemini/gemini-3.5-flash-lite
```

### 4\. Running the Application

You can interact with the agent through two different interfaces:

#### Option A: Web Interface (Streamlit)

Ideal for experiencing the complete conversational interface:

bash

```bash
streamlit run app.py
```

The application will open in your default browser at:

[http://localhost:8501](http://localhost:8501)

#### Option B: Terminal Interface (CLI)

For quick tests directly from the terminal:

bash

```bash
python cli.py
```

Enter your question when prompted, or type `sair` to end the session.

---

## Conversation Examples

Validated real-world scenarios documented in the `examples/` directory:

| File                       | Description                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------- |
| `01_catalogo_e_filtros.md` | Guitar catalog search with budget filtering under R$ 1,000.                           |
| `02_informacoes_gerais.md` | Store physical address and general location inquiries.                                |
| `03_consulta_preco.md`     | Specific product price and technical specifications lookup (Takamine GD20).           |
| `04_politica_devolucao.md` | Remote purchase withdrawal and refund rules according to store policy.                |
| `05_fora_de_escopo.md`     | Guardrail activation for politely handling non-musical requests (e.g., cake recipes). |

---

## AI Coding Assistants and Development Workflow

Throughout the development of this project, I used AI assistants as technical pair-programming partners to:

- Accelerate the creation of boilerplate code for Tool Calling schemas.
- Assist with debugging and validating regular expressions for DuckDB table name sanitization (`src/utils.py`).
- Structure synthetic test scenarios and project documentation.

---

## Known Limitations and Future Improvements (Production)

With additional development time and a focus on enterprise production readiness, the following AI Engineering improvements would be prioritized:

### 1. LLM Observability, Tracing, and Telemetry

Integrate dedicated LLM tracing frameworks (such as **Langfuse**, **LangSmith**, or **Arize Phoenix** via OpenTelemetry) to monitor runtime performance in real time. This would provide end-to-end visibility into:

- Step-by-step Tool Calling latency and execution errors.
- Token consumption and cost attribution per user session.
- Real-time hallucination tracking and negative user feedback loops.

### 2. Hybrid Search (RAG) and Cross-Encoder Re-ranking

Upgrade the retrieval pipeline to a **Hybrid Retrieval** architecture:

- Combine dense vector embeddings with sparse lexical indexing (**BM25**) using Reciprocal Rank Fusion (RRF) to ensure accurate keyword matching for legal acronyms (e.g., "CDC") and technical instrument codes.
- Replace the lightweight local embedding model with a high-capacity multilingual model (e.g., Google `text-embedding-004` or `multilingual-e5`).
- Introduce a cross-encoder re-ranker (e.g., Cohere Re-ranker) to score and filter retrieved chunks before injecting them into the system prompt.

### 3. Automated LLM Evaluation Pipeline (CI/CD Evals)

Establish a continuous evaluation framework using tools like **Ragas** or **DeepEval**:

- **Tool-Selection Accuracy:** Measure precision and recall of SQL generation and policy lookup triggers across synthetic gold-standard test suites.
- **Faithfulness & Groundedness:** Automatically penalize and flag responses containing facts not explicitly supported by the database query or policy chunks.
- **Guardrail Robustness:** Continuous red-teaming against prompt injection and scope-escape attempts.

### 4. Semantic Caching and Context Compression

- Implement a semantic cache (e.g., **Redis Vector Engine** or **GPTCache**) to return instant cached responses for repetitive high-frequency questions (such as physical store location, business hours, and payment terms) without triggering model inference.
- Introduce dynamic context summarization to prune older messages in long WhatsApp sessions, keeping token utilization predictable while preserving conversation intent.
