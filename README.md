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

#### Operational Relational Dataset (`data/*.csv`)

The structured data layer automatically parses, sanitizes, and registers six operational CSV tables into DuckDB:

| Table Name    | Source File Pattern | Business Purpose                                                     | Key Fields                                                                                 |
| :------------ | :------------------ | :------------------------------------------------------------------- | :----------------------------------------------------------------------------------------- |
| `products`    | `*products*.csv`    | Master catalog of musical instruments offered by the store[cite: 2]. | `product_id`, `name`, `category_id`, `price_brl`, `stock_quantity`, `description`, `specs` |
| `categories`  | `*categories*.csv`  | Instrument classification hierarchy[cite: 2].                        | `category_id`, `name`, `description`                                                       |
| `customers`   | `*customers*.csv`   | Customer identification for authenticated order lookups.             | `customer_id`, `full_name`, `cpf`, `email`, `phone`, `city`, `state`                       |
| `orders`      | `*orders*.csv`      | Customer purchases, delivery timelines, tracking IDs, and statuses.  | `order_id`, `customer_id`, `order_date`, `status`, `tracking_code`, `total_brl`            |
| `order_items` | `*order_items*.csv` | Line-item breakdown per order.                                       | `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price_brl`                    |
| `promotions`  | `*promotions*.csv`  | Seasonal sales campaigns and discount percentages[cite: 6].          | `promotion_id`, `name`, `discount_percent`, `start_date`, `end_date`, `is_active`          |

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

### Prompt Engineering Strategy

The system prompt in `src/prompts.py` was engineered to maximize tool execution reliability and enforce strict factual grounding:

1. **Dynamic Schema Grounding (Zero Hallucination):**
   Rather than hardcoding table descriptions, the prompt introspects the DuckDB instance at startup and injects the live relational schema (`{schema}`) directly into the prompt context. This ensures the model constructs syntactically valid SQL queries with precise column names and types.

2. **Relational Disambiguation & Join Guidance:**
   In retail databases, product names typically store manufacturer models (e.g., `Yamaha C40`) rather than generic category nouns (e.g., `Violão`). The prompt explicitly instructs the LLM on catalog semantics, mandating `JOIN` operations between `products` and `categories` and multi-field matching (`ILIKE` across `name`, `description`, and `categories.name`). This prevents empty queries and multi-turn retry loops.

3. **Deterministic Tool Routing Heuristics:**
   The prompt enforces a clear dichotomy between transactional operations (delegated exclusively to `consultar_banco_dados`) and institutional policies (delegated exclusively to `consultar_politicas_loja`), eliminating ambiguous or redundant tool calls.

4. **Domain Guardrails & Persona Calibration:**
   The prompt anchors the assistant to the _Empório da Música_ persona (warm, professional, music-oriented). Negative constraints prevent answering out-of-scope requests (e.g., programming, medical, or culinary queries) and strictly forbid guessing prices, stock levels, or order numbers without prior tool validation.

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

## AI Coding Assistants & Engineering Workflow

In full alignment with the challenge guidelines regarding transparency, Generative AI models and coding assistants were integrated throughout the development lifecycle as technical pair-programming partners.

### 1. Tooling Selected

- **Primary Pair-Programming Assistant:** Google Gemini (via interactive technical reasoning sessions).
- **Execution Environment:** macOS development environment, testing code iteratively across terminal CLI and Streamlit.

### 2. Workflow Breakdown & Critical Validation

Rather than relying on one-shot code generation, the assistant was utilized in a disciplined, human-in-the-loop engineering workflow:

- **Architecture & Contract Scaffolding:** Accelerated the generation of initial boilerplate code, specifically strict JSON Schema definitions for LiteLLM Tool Calling declarations and DuckDB metadata introspection helpers.
- **Troubleshooting Relational Queries (Join Disambiguation):** During runtime testing of product inquiries (e.g., searching for acoustic guitars under R$ 1,000), queries initially resulted in empty sets due to DuckDB filtering solely on `products.name` (which contained model codes like `Yamaha C40` rather than the category noun `Violão`). Through active debugging sessions, we identified the multi-turn tool-calling loop, redesigned the system prompt heuristics, and mandated explicit relational `JOIN` operations with `categories` and `description` fallback filtering.
- **RAG Vector Pipeline Refinement:** Evaluated ChromaDB lifecycle design trade-offs. We explicitly audited and replaced an initial in-memory ephemeral client with `PersistentClient` in `data/chroma_db/`, implemented word-boundary sliding-window chunking to prevent mid-word string truncations, and introduced lazy initialization (`get_rag_engine()`) to eliminate import-time side effects during testing.
- **Documentation & Evaluation Scenarios:** Assisted in drafting structured, bilingual technical documentation (English README and executive reporting; Portuguese conversational test cases) and formatting benchmark interaction logs across the 5 required evaluation scenarios.

### 3. Engineering Autonomy

All business logic, database constraints, defensive exception handling, UI refinements, and architectural decisions were reviewed, debugged, executed locally, and validated against actual dataset tables before Git commits.

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
