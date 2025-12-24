# Calculus RAG - System Architecture

A comprehensive visual guide to the system architecture.

---

## 1. System Overview

```mermaid
flowchart TB
    subgraph External["☁️ External Services"]
        OLLAMA_CLOUD[("Ollama Cloud<br/>DeepSeek R1 671B")]
    end

    subgraph Local["💻 Local Machine"]
        subgraph Frontend["Frontend Layer"]
            STREAMLIT["🖥️ Streamlit<br/>app.py<br/>Port 8501"]
        end

        subgraph Application["Application Layer"]
            RAG["🧠 RAG Pipeline<br/>rag/pipeline.py"]
            ROUTER["🔀 Model Router<br/>llm/model_router.py"]
            PREREQ["📚 Prerequisites<br/>prerequisites/"]
        end

        subgraph AI["AI Layer (Ollama)"]
            EMBED["📊 mxbai-embed-large<br/>Embeddings (1024d)"]
            LLM_SMALL["⚡ qwen2-math:1.5b<br/>Simple Questions"]
            LLM_LARGE["🔄 qwen2-math:7b<br/>Moderate Questions"]
        end

        subgraph Data["Data Layer"]
            PGVECTOR[("🗄️ PostgreSQL 16<br/>+ pgvector<br/>Port 5432")]
            PDF["📁 PDF Files<br/>knowledge_content/"]
        end
    end

    STREAMLIT <--> RAG
    RAG <--> ROUTER
    RAG <--> PREREQ
    RAG <--> EMBED
    ROUTER <--> LLM_SMALL
    ROUTER <--> LLM_LARGE
    ROUTER <-.->|Complex queries| OLLAMA_CLOUD
    EMBED <--> PGVECTOR
    PDF -.->|Ingestion| PGVECTOR

    style OLLAMA_CLOUD fill:#e1f5fe
    style PGVECTOR fill:#fff3e0
    style RAG fill:#e8f5e9
```

---

## 2. Request Flow (Question → Answer)

```mermaid
sequenceDiagram
    autonumber

    actor User
    participant UI as 🖥️ Streamlit
    participant RAG as 🧠 RAG Pipeline
    participant Embed as 📊 Embedder
    participant DB as 🗄️ PostgreSQL
    participant Router as 🔀 Router
    participant LLM as 🤖 LLM

    User->>UI: "What is the derivative of sin(x)?"

    rect rgb(232, 245, 233)
        Note over UI,RAG: Query Processing
        UI->>RAG: process_query(question)
        RAG->>Embed: embed(question)
        Embed-->>RAG: vector[1024]
    end

    rect rgb(255, 243, 224)
        Note over RAG,DB: Context Retrieval
        RAG->>DB: similarity_search(vector, k=5)
        DB-->>RAG: relevant_chunks[]
    end

    rect rgb(227, 242, 253)
        Note over RAG,LLM: Answer Generation
        RAG->>Router: analyze_complexity(question)
        Router-->>RAG: SIMPLE | MODERATE | COMPLEX
        RAG->>Router: generate(context + question)

        alt SIMPLE
            Router->>LLM: qwen2-math:1.5b
        else MODERATE
            Router->>LLM: qwen2-math:7b
        else COMPLEX
            Router->>LLM: DeepSeek R1 (cloud)
        end

        LLM-->>Router: answer
        Router-->>RAG: answer + metadata
    end

    RAG-->>UI: RAGResponse(answer, sources)
    UI-->>User: Formatted answer with LaTeX
```

---

## 3. Model Routing Decision Tree

```mermaid
flowchart TD
    START([📝 Incoming Question]) --> ANALYZE{{"🔍 Complexity<br/>Analyzer"}}

    ANALYZE -->|Score < 3| SIMPLE
    ANALYZE -->|Score 3-5| MODERATE
    ANALYZE -->|Score > 5| COMPLEX

    subgraph Keywords["Keyword Detection"]
        SIMPLE_KW["✓ what is, define<br/>✓ basic, simple<br/>✓ calculate<br/>✓ power rule"]
        COMPLEX_KW["✓ prove, proof<br/>✓ derive, derivation<br/>✓ explain why<br/>✓ integration by parts<br/>✓ taylor series"]
    end

    SIMPLE["🟢 SIMPLE<br/>Basic definitions"]
    MODERATE["🟡 MODERATE<br/>Standard problems"]
    COMPLEX["🔴 COMPLEX<br/>Proofs & derivations"]

    SIMPLE --> MODEL1["⚡ qwen2-math:1.5b<br/>━━━━━━━━━━━━━<br/>• 1.5B parameters<br/>• ~1GB RAM<br/>• Response: <2s"]

    MODERATE --> MODEL2["🔄 qwen2-math:7b<br/>━━━━━━━━━━━━━<br/>• 7.6B parameters<br/>• ~4GB RAM<br/>• Response: 3-8s"]

    COMPLEX --> MODEL3["☁️ DeepSeek R1 671B<br/>━━━━━━━━━━━━━<br/>• 671B parameters<br/>• Cloud (Ollama)<br/>• Response: 5-15s"]

    MODEL1 --> RESPONSE([✅ Response])
    MODEL2 --> RESPONSE
    MODEL3 --> RESPONSE

    MODEL1 -.->|Error/Timeout| MODEL2
    MODEL2 -.->|Error/Timeout| MODEL3

    style SIMPLE fill:#c8e6c9
    style MODERATE fill:#fff9c4
    style COMPLEX fill:#ffcdd2
    style MODEL1 fill:#e8f5e9
    style MODEL2 fill:#fffde7
    style MODEL3 fill:#e3f2fd
```

---

## 4. Data Ingestion Pipeline

```mermaid
flowchart LR
    subgraph Input["📥 Input"]
        PDF[("📄 PDF File")]
        META["Metadata<br/>• filename<br/>• category<br/>• size"]
    end

    subgraph Extract["📖 Extraction"]
        PYMUPDF["PyMuPDF<br/>pymupdf4llm"]
        MD["Markdown<br/>Text"]
    end

    subgraph Process["⚙️ Processing"]
        CLEAN["🧹 Clean Text<br/>• Remove headers<br/>• Fix formatting"]
        CHUNK["✂️ Chunker<br/>• Size: 512 chars<br/>• Overlap: 50 chars"]
    end

    subgraph Embed["📊 Embedding"]
        OLLAMA["Ollama API<br/>localhost:11434"]
        MXBAI["mxbai-embed-large<br/>1024 dimensions"]
    end

    subgraph Store["💾 Storage"]
        PG[("PostgreSQL<br/>+ pgvector")]
        TABLE["calculus_knowledge<br/>━━━━━━━━━━━━━<br/>id: varchar<br/>embedding: vector(1024)<br/>content: text<br/>metadata: jsonb"]
    end

    PDF --> PYMUPDF
    META --> PYMUPDF
    PYMUPDF --> MD
    MD --> CLEAN
    CLEAN --> CHUNK
    CHUNK -->|"chunks[]"| OLLAMA
    OLLAMA --> MXBAI
    MXBAI -->|"vectors[]"| PG
    CHUNK -->|"text[]"| PG
    PG --> TABLE

    style PDF fill:#ffecb3
    style PG fill:#fff3e0
    style MXBAI fill:#e3f2fd
```

---

## 5. Backup & Restore

```mermaid
flowchart LR
    subgraph Backup["💾 Backup Process"]
        DB1[("PostgreSQL<br/>calculus_knowledge")]
        PGDUMP["pg_dump -Fc<br/>Custom Format"]
        DUMP["📦 starter.dump<br/>33.97 MB<br/>6,835 chunks"]
    end

    subgraph Restore["🔄 Restore Process"]
        DUMP2["📦 .dump file"]
        PGRESTORE["pg_restore -j N<br/>Parallel Restore"]
        DB2[("PostgreSQL<br/>calculus_knowledge")]
    end

    DB1 --> PGDUMP
    PGDUMP --> DUMP

    DUMP2 --> PGRESTORE
    PGRESTORE --> DB2

    subgraph Scripts["🔧 Scripts"]
        S1["backup_db.py"]
        S2["restore_db.py"]
    end

    S1 -.-> PGDUMP
    S2 -.-> PGRESTORE

    style DUMP fill:#c8e6c9
    style DUMP2 fill:#c8e6c9
    style DB1 fill:#fff3e0
    style DB2 fill:#fff3e0
```

**Quick Start Options:**
| Method | Command | Time |
|--------|---------|------|
| Restore pre-built | `python scripts/restore_db.py backups/starter.dump` | ~30 seconds |
| Full ingestion | `python scripts/ingest_pdfs.py` | 5-15 minutes |
| Add single PDF | `python scripts/add_pdf.py path/to/file.pdf` | 1-2 minutes |

---

## 6. Component Architecture

```mermaid
flowchart TB
    subgraph Config["⚙️ config.py"]
        SETTINGS["Settings<br/>━━━━━━━━━<br/>• Environment vars<br/>• .env file<br/>• Pydantic validation"]
    end

    subgraph Embeddings["📊 embeddings/"]
        EMB_BASE["BaseEmbedder<br/>(Abstract)"]
        EMB_OLLAMA["OllamaEmbedder<br/>mxbai-embed-large"]
        EMB_BGE["BGEEmbedder<br/>(Legacy)"]

        EMB_BASE --> EMB_OLLAMA
        EMB_BASE --> EMB_BGE
    end

    subgraph VectorStore["🗄️ vectorstore/"]
        VS_BASE["BaseVectorStore<br/>(Abstract)"]
        VS_PG["PgVectorStore<br/>PostgreSQL + pgvector"]

        VS_BASE --> VS_PG
    end

    subgraph LLM["🤖 llm/"]
        LLM_BASE["BaseLLM<br/>(Abstract)"]
        LLM_OLLAMA["OllamaLLM<br/>Local models"]
        LLM_CLOUD["CloudLLM<br/>Ollama Cloud"]
        LLM_ROUTER["ModelRouter<br/>Smart routing"]

        LLM_BASE --> LLM_OLLAMA
        LLM_BASE --> LLM_CLOUD
        LLM_ROUTER --> LLM_OLLAMA
        LLM_ROUTER --> LLM_CLOUD
    end

    subgraph Retrieval["🔍 retrieval/"]
        RET_BASE["Retriever"]
        RET_HYBRID["HybridRetriever<br/>Semantic + Keyword"]
        RET_PREREQ["PrerequisiteAwareRetriever"]

        RET_BASE --> RET_HYBRID
        RET_BASE --> RET_PREREQ
    end

    subgraph RAG["🧠 rag/"]
        PIPELINE["RAGPipeline<br/>━━━━━━━━━━━━━<br/>• Query processing<br/>• Context building<br/>• Response generation"]
    end

    SETTINGS -.-> EMB_OLLAMA
    SETTINGS -.-> VS_PG
    SETTINGS -.-> LLM_OLLAMA

    EMB_OLLAMA --> RET_BASE
    VS_PG --> RET_BASE
    RET_BASE --> PIPELINE
    LLM_ROUTER --> PIPELINE

    style SETTINGS fill:#f3e5f5
    style PIPELINE fill:#e8f5e9
    style LLM_ROUTER fill:#fff9c4
```

---

## 7. Prerequisite System

```mermaid
flowchart TD
    subgraph Topics["📚 Topic Registry"]
        CALC["Calculus Topics<br/>━━━━━━━━━━━━━<br/>limits.*<br/>derivatives.*<br/>integration.*"]
        PRECALC["Pre-Calculus Topics<br/>━━━━━━━━━━━━━<br/>algebra.*<br/>functions.*<br/>trig.*"]
    end

    subgraph Graph["🔗 Prerequisite Graph"]
        NODE1["derivatives.chain_rule"]
        NODE2["derivatives.basic"]
        NODE3["limits.introduction"]
        NODE4["algebra.functions"]

        NODE1 -->|requires| NODE2
        NODE2 -->|requires| NODE3
        NODE3 -->|requires| NODE4
    end

    subgraph Detector["🔍 Gap Detector"]
        QUERY["Student Query"]
        DETECT["Detect Required Topics"]
        MISSING["Identify Missing Prerequisites"]
        SUGGEST["Suggest Learning Path"]
    end

    CALC --> Graph
    PRECALC --> Graph

    QUERY --> DETECT
    DETECT --> Graph
    Graph --> MISSING
    MISSING --> SUGGEST

    style NODE1 fill:#ffcdd2
    style NODE2 fill:#fff9c4
    style NODE3 fill:#c8e6c9
    style NODE4 fill:#bbdefb
```

---

## 8. Database Schema

```mermaid
erDiagram
    CALCULUS_KNOWLEDGE {
        varchar id PK "chunk_id (e.g., Calculus_42)"
        vector_1024 embedding "mxbai-embed-large output"
        text content "Chunk text content"
        varchar document_id "Source PDF filename"
        integer chunk_index "Position in document"
        jsonb metadata "Extended properties"
    }

    METADATA_STRUCTURE {
        string source "PDF filename"
        string category "calculus/derivatives"
        integer chunk_index "0, 1, 2..."
        integer total_chunks "Total in document"
    }

    CALCULUS_KNOWLEDGE ||--|| METADATA_STRUCTURE : contains
```

---

## 9. Environment Configuration

```mermaid
flowchart LR
    subgraph ENV[".env File"]
        E1["EMBEDDING_TYPE=ollama"]
        E2["EMBEDDING_MODEL_NAME=mxbai-embed-large"]
        E3["VECTOR_DIMENSION=1024"]
        E4["OLLAMA_MODEL=qwen2-math:7b"]
        E5["CLOUD_LLM_ENABLED=true/false"]
        E6["CHUNK_SIZE=512"]
    end

    subgraph Config["config.py"]
        SETTINGS["Settings Class<br/>Pydantic BaseSettings"]
    end

    subgraph Components["Components"]
        C1["OllamaEmbedder"]
        C2["PgVectorStore"]
        C3["ModelRouter"]
        C4["PyMuPDFLoader"]
    end

    ENV --> SETTINGS
    SETTINGS --> C1
    SETTINGS --> C2
    SETTINGS --> C3
    SETTINGS --> C4

    style ENV fill:#fff3e0
    style SETTINGS fill:#f3e5f5
```

---

## 10. Directory Structure

```
📁 Calculus_RAG/
│
├── 📄 app.py                    # Streamlit entry point
├── 📄 .env                      # Configuration (from .env.example)
├── 📄 docker-compose.yml        # PostgreSQL setup
│
├── 📁 scripts/
│   ├── 📄 ingest_pdfs.py        # Full ingestion (clears DB)
│   ├── 📄 add_pdf.py            # Add single PDF (preserves DB)
│   ├── 📄 ingest_markdown.py    # Ingest markdown files
│   ├── 📄 backup_db.py          # Create database backup
│   ├── 📄 restore_db.py         # Restore from backup
│   ├── 📄 check_ingestion.py    # View DB status
│   └── 📄 interactive_rag.py    # Terminal chat
│
├── 📁 backups/
│   └── 📄 starter.dump          # Pre-built knowledge base (6,835 chunks)
│
├── 📁 src/calculus_rag/
│   ├── 📄 config.py             # Settings management
│   │
│   ├── 📁 embeddings/           # Text → Vector
│   │   ├── 📄 base.py           # Abstract interface
│   │   └── 📄 ollama_embedder.py
│   │
│   ├── 📁 vectorstore/          # Vector storage
│   │   ├── 📄 base.py           # Abstract interface
│   │   └── 📄 pgvector_store.py
│   │
│   ├── 📁 llm/                  # Language models
│   │   ├── 📄 base.py           # Abstract interface
│   │   ├── 📄 ollama_llm.py     # Local models
│   │   ├── 📄 cloud_llm.py      # Cloud models
│   │   └── 📄 model_router.py   # Smart routing
│   │
│   ├── 📁 loaders/              # PDF processing
│   │   └── 📄 pymupdf_loader.py
│   │
│   ├── 📁 retrieval/            # Search
│   │   ├── 📄 retriever.py
│   │   └── 📄 hybrid_retriever.py
│   │
│   ├── 📁 rag/                  # Orchestration
│   │   └── 📄 pipeline.py
│   │
│   └── 📁 prerequisites/        # Topic dependencies
│       ├── 📄 topics.py
│       ├── 📄 graph.py
│       └── 📄 detector.py
│
├── 📁 knowledge_content/        # Source content
│   ├── 📁 calculus/             # Calculus PDFs
│   ├── 📁 pre_calculus/         # Pre-calculus PDFs
│   ├── 📁 guides/               # Study guides
│   ├── 📁 reference/            # Reference materials
│   └── 📁 khan_academy/         # Khan Academy summaries (44 markdown files)
│
└── 📁 tests/                    # Test suite
```

---

## 11. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | Streamlit | 1.30+ | Web UI with LaTeX |
| **Backend** | Python | 3.10+ | Core application |
| **Database** | PostgreSQL | 16 | Document storage |
| **Vector Search** | pgvector | 0.5+ | Similarity search |
| **Local AI** | Ollama | 0.1+ | Model serving |
| **Embeddings** | mxbai-embed-large | 334M | Text → 1024d vectors |
| **Local LLM** | Qwen2-Math | 1.5B/7B | Math responses |
| **Cloud LLM** | DeepSeek R1 | 671B | Complex proofs |
| **PDF Processing** | pymupdf4llm | 1.0+ | Text extraction |
| **Config** | Pydantic | 2.0+ | Settings validation |
| **Package Manager** | uv | Latest | Fast installs |
