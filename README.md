# RAG Backend — Hệ thống Tư vấn Chương trình Đào tạo CNTT

Hệ thống **Retrieval-Augmented Generation (RAG)** backend phục vụ tư vấn chương trình đào tạo CNTT tại trường đại học. Hệ thống hỗ trợ phân biệt ngành (CNTT, KTMT, TTMT, TTNT…), phát hiện ý định truy vấn (intent detection), và cung cấp câu trả lời chính xác dựa trên tài liệu thực tế.

## Tính năng chính

- **Major-aware Retrieval**: Tự động phân biệt ngành học dựa trên H1 heading của tài liệu
- **3 Pipeline RAG**:
  - **Naive Pipeline** — Tìm kiếm chunk đơn giản (baseline)
  - **Standard Pipeline (Chunk-Based Extent)** — Tìm kiếm chunk → Mở rộng sang section + Reranking
  - **Intent-Based Pipeline (IA-ARF)** — Phát hiện ý định → Chiến lược truy xuất thông minh + Prompt tối ưu
- **5 Retrieval Intent**: `OVERVIEW`, `STRUCTURE`, `ROADMAP`, `FACTUAL`, `COMPARE`
- **3 Search Mode**: Vector (kNN), Fulltext (BM25), Hybrid (RRF)
- **Đa nhà cung cấp LLM**: Hỗ trợ cả Ollama (Gemma3:4b) và OpenAI (GPT-4o-mini)
- **Cohere Reranking**: Tùy chọn rerank bằng `rerank-multilingual-v3.0`
- **Chat với lịch sử hội thoại**: Tự động contextualize câu hỏi dựa trên lịch sử chat
- **Xác thực người dùng**: Email OTP + Google OAuth
- **Quản lý tài liệu**: CRUD tài liệu có phân quyền (admin/manager)

## Kiến trúc hệ thống

```
  Tài liệu Markdown
        ↓
  Ingestion Pipeline (MarkdownStructureChunker + BGE-M3 Embeddings)
        ↓
  Elasticsearch 8.15 (sections index + chunks index)
        ↓
  ┌──────────────────────────────────────────────────────────────┐
  │                      Query Pipelines                        │
  ├────────────────┬─────────────────────┬──────────────────────┤
  │ Naive Pipeline │ Standard Pipeline   │ IA-ARF Pipeline      │
  │                │ (Chunk-Based Extent)│ (Intent-Based)       │
  │ Chunk Search   │ Chunk → Section     │ Intent Detection     │
  │ → Simple Prompt│ → Query Expansion   │ → Smart Retrieval    │
  │ → LLM Answer  │ → Reranking         │ → Optimized Prompt   │
  │                │ → LLM Answer        │ → LLM Answer         │
  └────────────────┴─────────────────────┴──────────────────────┘
        ↓
  Gemma3:4b / GPT-4o-mini (Answer Generation)
```

### Chi tiết 3 Pipeline

#### 1. Naive Pipeline (`app/query/naive_pipeline.py`)

Pipeline đơn giản nhất, dùng làm **baseline đánh giá**:

```
Query → Embedding → Chunk Search → Simple Prompt → LLM Answer
```

- Không query expansion, không reranking, không section expansion
- Hỗ trợ 3 search mode: `vector`, `fulltext`, `hybrid`

#### 2. Standard Pipeline — Chunk-Based Extent (`app/query/pipeline.py`)

Pipeline tiêu chuẩn với kiến trúc **3 engine**:

```
Query → Retrieval Engine → Prompt Engine → Generation Engine
```

- **Retrieval Engine** (`retrieval_engine.py`): Query expansion → Chunk search → Section expansion → Cohere reranking
- **Prompt Engine** (`prompt_engine.py`): Xây dựng prompt từ sections với hierarchy context
- **Generation Engine** (`generation_engine.py`): Sinh câu trả lời qua LLM

#### 3. IA-ARF Pipeline — Intent-Based (`app/query/intent_based_rag_pipeline.py`)

Pipeline nâng cao với **phát hiện ý định** và **chiến lược truy xuất thông minh**:

```
Query → Intent Detection → Query Refinement → Smart Retrieval → Optimized Prompt → LLM Answer
```

| Intent      | Chiến lược truy xuất                                  |
|-------------|-------------------------------------------------------|
| `OVERVIEW`  | LLM decompose thành sub-queries theo target (ngành/môn)|
| `STRUCTURE` | Section-level search + expansion                      |
| `ROADMAP`   | Seed & Expand (tìm section → mở rộng placeholder)    |
| `FACTUAL`   | Chunk exact match + reranking                         |
| `COMPARE`   | Split entity → Retrieve riêng → Merge interleaved    |

## Yêu cầu hệ thống

- **Python** 3.9+
- **Docker & Docker Compose**
- **Ollama** với models:
  - `bge-m3` — embedding (1024 dims)
  - `gemma3:4b` — generation
- **(Tùy chọn)** API keys:
  - `OPENAI_API_KEY` — nếu dùng GPT-4o-mini
  - `COHERE_API_KEY` — nếu dùng Cohere reranking

## Cài đặt & Chạy

### 1. Clone & cài đặt dependencies

```bash
git clone <repository-url>
cd backend-support
pip install -r requirements.txt
```

### 2. Cài đặt Ollama models

```bash
ollama pull bge-m3
ollama pull gemma3:4b
```

### 3. Khởi động hạ tầng (Elasticsearch + PostgreSQL)

```bash
docker-compose up -d
```

Kiểm tra trạng thái:

```bash
# Elasticsearch
curl http://localhost:9200

# PostgreSQL
docker exec rag-postgres pg_isready -U rag_user -d rag_auth_db
```

### 4. Cấu hình environment

```bash
cp .env.example .env
# Chỉnh sửa .env theo nhu cầu (mặc định hoạt động cho local)
```

### 5. Khởi tạo database

```bash
alembic upgrade head
```

### 6. Khởi động server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Truy cập API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Nhóm | Method | Endpoint | Mô tả |
|------|--------|----------|--------|
| **Auth** | POST | `/api/auth/email/request-otp` | Yêu cầu OTP qua email |
| | POST | `/api/auth/email/verify-otp` | Xác thực OTP |
| | POST | `/api/auth/google` | Đăng nhập Google OAuth |
| | GET | `/api/auth/me` | Thông tin user hiện tại |
| **Docs** | GET/POST/PUT/DELETE | `/api/docs` | CRUD tài liệu |
| **Chats** | GET/POST | `/api/chats` | Quản lý phiên chat |
| | POST | `/api/chats/chat` | Chat RAG (normal) |
| | POST | `/api/chats/chat/stream` | Chat RAG (streaming) |
| **Ingestion** | POST | `/api/ingest` | Ingest tài liệu markdown |
| | GET | `/api/ingest/status` | Thống kê indices |
| | DELETE | `/api/ingest/clear` | Xóa & tạo lại indices |
| **Query** | POST | `/api/query` | RAG query endpoint |
| | GET | `/api/query/majors` | Danh sách ngành |
| **Parse** | POST | `/api/parse` | Parse tài liệu DOCX/PDF |
| **System** | GET | `/health` | Health check |

## Evaluation — Đánh giá Pipeline

Hệ thống cung cấp 3 script đánh giá tương ứng với 3 pipeline, sử dụng bộ test queries từ `tests/query.json` (với ground truth):

### 1. Naive Pipeline Evaluation

```bash
# Chạy tất cả queries (mặc định: vector search)
python tests/run_naive_evaluation.py

# Lọc theo intent
python tests/run_naive_evaluation.py --overview
python tests/run_naive_evaluation.py --factual

# Chọn search mode
python tests/run_naive_evaluation.py --search-mode hybrid
python tests/run_naive_evaluation.py --roadmap --search-mode fulltext
```

### 2. Standard Pipeline Evaluation (Chunk-Based Extent)

```bash
# Chạy tất cả queries (có query expansion + reranking)
python tests/run_pipeline_evaluation.py

# Lọc theo intent
python tests/run_pipeline_evaluation.py --structure
python tests/run_pipeline_evaluation.py --compare
```

> **Lưu ý**: Standard pipeline chưa hỗ trợ tùy chọn `--search-mode`.

### 3. IA-ARF Pipeline Evaluation (Intent-Based)

```bash
# Chạy tất cả queries (mặc định: hybrid mode)
python tests/run_ragas_evaluation.py

# Lọc theo intent
python tests/run_ragas_evaluation.py --overview
python tests/run_ragas_evaluation.py --roadmap

# Chọn search mode
python tests/run_ragas_evaluation.py --search-mode vector
python tests/run_ragas_evaluation.py --factual --search-mode hybrid
```

### Kết quả đánh giá

Kết quả được lưu dưới dạng JSON trong `tests/output/` với format chuẩn RAGAS:

```
tests/output/
├── naive_evaluation_<intent>_<mode>_<timestamp>.json
├── pipeline_evaluation_<intent>_<timestamp>.json
└── ragas_evaluation_<intent>_<mode>_<timestamp>.json
```

Mỗi file chứa:
- `question` — Câu hỏi gốc
- `answer` — Câu trả lời từ pipeline
- `contexts` — Danh sách context được truy xuất
- `ground_truth` — Đáp án kỳ vọng
- `metadata` — Thông tin bổ sung (intent, search mode, thời gian, số source…)
- `sources` — Chi tiết các nguồn tài liệu

## Cấu trúc thư mục

```
backend-support/
├── app/
│   ├── main.py                      # FastAPI entry point
│   ├── core/
│   │   └── config.py                # Pydantic Settings cấu hình
│   ├── clients/
│   │   ├── elasticsearch.py         # ES client (vector/fulltext/hybrid)
│   │   ├── ollama.py                # Ollama client (embedding + LLM)
│   │   ├── openai_client.py         # OpenAI client
│   │   └── cohere_reranker.py       # Cohere reranker
│   ├── ingestion/                   # Document ingestion pipeline
│   ├── query/
│   │   ├── naive_pipeline.py        # Naive RAG (baseline)
│   │   ├── pipeline.py              # Standard RAG (Chunk-Based Extent)
│   │   ├── intent_based_rag_pipeline.py  # IA-ARF Pipeline
│   │   ├── intent_based_retrieval_engine.py  # Smart retrieval
│   │   ├── intent_based_prompt_engine.py     # Optimized prompts
│   │   ├── retrieval_engine.py      # Standard retrieval
│   │   ├── prompt_engine.py         # Standard prompt builder
│   │   ├── generation_engine.py     # LLM answer generation
│   │   └── query_expander.py        # Query expansion
│   ├── retrieval_engine/
│   │   ├── intent_detection.py      # Intent classifier
│   │   └── refine_query.py          # Query refinement
│   ├── routers/                     # API endpoints
│   ├── models/                      # SQLAlchemy + Pydantic models
│   ├── schemas/                     # Request/Response schemas
│   ├── repositories/                # Database access layer
│   ├── services/                    # Business logic
│   │   ├── document_ingestion_service.py
│   │   ├── document_parser_service.py
│   │   ├── history_contextualizer.py
│   │   ├── auth_service.py
│   │   └── email_service.py
│   └── utils/
│       └── chunker.py               # MarkdownStructureChunker
├── data/
│   └── raw/                         # Tài liệu markdown thô
├── tests/
│   ├── query.json                   # Test queries + ground truth
│   ├── run_naive_evaluation.py      # Đánh giá Naive Pipeline
│   ├── run_pipeline_evaluation.py   # Đánh giá Standard Pipeline
│   ├── run_ragas_evaluation.py      # Đánh giá IA-ARF Pipeline
│   ├── output/                      # Kết quả đánh giá (JSON)
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── e2e/                         # End-to-end tests
├── scripts/                         # Utility scripts
├── alembic/                         # Database migrations
├── docker-compose.yml               # ES + PostgreSQL
├── requirements.txt                 # Python dependencies
└── .env.example                     # Config template
```

## Troubleshooting

### Elasticsearch không kết nối được

```bash
docker ps                              # Kiểm tra container
docker-compose logs elasticsearch      # Xem logs
docker-compose restart elasticsearch   # Khởi động lại
```

### Ollama model không tìm thấy

```bash
ollama list                            # Liệt kê models
ollama pull bge-m3                     # Pull embedding model
ollama pull gemma3:4b                  # Pull LLM model
```

### Lỗi PostgreSQL

```bash
docker-compose logs postgres           # Xem logs
docker-compose restart postgres        # Khởi động lại
alembic upgrade head                   # Chạy lại migration
```

### Query chậm

- Giảm `top_k` parameter
- Sử dụng major filter để thu hẹp phạm vi
- Kiểm tra tải Ollama server (`ollama ps`)
- Cân nhắc chuyển sang OpenAI (`USE_OPENAI=true`)

## Development

```bash
# Run tests
pytest tests/ -v

# Format code
black app/

# Type checking
mypy app/
```

## License

MIT
