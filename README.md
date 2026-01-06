# RAG Backend - Educational Program Information System

Backend RAG system cho hệ thống tư vấn chương trình đào tạo CNTT với khả năng phân biệt các ngành.

## Tính năng

- **Major-aware retrieval**: Phân biệt giữa các ngành (CNTT, KTMT, TTNT) dựa trên H1 heading
- **2-tier retrieval**: Search chunks → Expand to sections để có ngữ nghĩa đầy đủ
- **Vector search**: Elasticsearch 8.15.0 với BGE-M3 embeddings (1024 dims)
- **LLM generation**: Gemma3:4b qua Ollama Langchain
- **Doc ID strategy**: Idempotent indexing với section_id/chunk_id

## Kiến trúc

```
Data (simple-output.json)
    ↓
Ingestion Pipeline (H1 major extraction + BGE-M3 embeddings)
    ↓
Elasticsearch (sections + chunks indices)
    ↓
Query Pipeline (vector search + section expansion)
    ↓
Gemma3:4b (answer generation)
```

## Yêu cầu

- Python 3.9+
- Docker & Docker Compose
- Ollama với models:
  - `bge-m3` (embeddings)
  - `gemma3:4b` (generation)

## Setup

### 1. Cài đặt Ollama models

```bash
ollama pull bge-m3
ollama pull gemma3:4b
```

### 2. Start Elasticsearch

```bash
docker-compose up -d
```

Kiểm tra Elasticsearch đã chạy:
```bash
curl http://localhost:9200
```

### 3. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local setup)
```

### 5. Start FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Sử dụng

### 1. Ingest dữ liệu

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "simple-output.json"}'
```

Response:
```json
{
  "status": "success",
  "major": "Ngành Công Nghệ Thông Tin",
  "sections_indexed": 150,
  "chunks_indexed": 450,
  "sections_failed": 0,
  "chunks_failed": 0
}
```

### 2. Query without major filter

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Môn Hệ điều hành có bao nhiêu tín chỉ?",
    "include_sources": true
  }'
```

### 3. Query với major filter

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Môn Hệ điều hành có bao nhiêu tín chỉ?",
    "major": "Ngành Công Nghệ Thông Tin",
    "include_sources": true
  }'
```

Response:
```json
{
  "answer": "Môn Hệ điều hành có 4 tín chỉ, gồm 3 tín chỉ lý thuyết và 1 tín chỉ thực hành.",
  "sources": [...],
  "metadata": {
    "major_used": "Ngành Công Nghệ Thông Tin",
    "chunks_retrieved": 10,
    "sections_retrieved": 3,
    "total_time_ms": 2450.5
  }
}
```

### 4. Health check

```bash
curl http://localhost:8000/health
```

### 5. API Documentation

Truy cập: http://localhost:8000/docs

## API Endpoints

### Ingestion

- **POST** `/api/ingest` - Ingest data từ simple-output.json
- **GET** `/api/ingest/status` - Lấy thống kê indices
- **DELETE** `/api/ingest/clear` - Xóa và tạo lại indices

### Query

- **POST** `/api/query` - RAG query endpoint
- **GET** `/api/query/majors` - Lấy danh sách majors

### System

- **GET** `/` - Root endpoint
- **GET** `/health` - Health check

## Cấu trúc thư mục

```
backend-support/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── elasticsearch/       # ES client & schemas
│   ├── ollama/             # Ollama Langchain client
│   ├── ingestion/          # Data ingestion pipeline
│   ├── query/              # Query pipeline
│   └── routers/            # API endpoints
├── data/
│   └── raw/                # Markdown files
├── simple-output.json      # Chunked data
├── chunker.py             # Chunking script
├── docker-compose.yml     # Elasticsearch setup
├── requirements.txt       # Python deps
└── .env.example          # Config template
```

## Troubleshooting

### Elasticsearch connection failed
```bash
# Check if ES is running
docker ps
docker-compose logs elasticsearch

# Restart ES
docker-compose restart elasticsearch
```

### Ollama model not found
```bash
# List models
ollama list

# Pull missing model
ollama pull bge-m3
ollama pull gemma3:4b
```

### Slow query performance
- Reduce `top_k` parameter
- Use major filter to narrow search
- Check Ollama server load

## Development

### Run tests
```bash
pytest tests/ -v
```

### Format code
```bash
black app/
```

### Type checking
```bash
mypy app/
```

## License

MIT
