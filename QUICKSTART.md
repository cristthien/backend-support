# Quick Start Guide

## Đã hoàn thành

✅ .venv và dependencies  
✅ Output files cho 3 ngành (CNTT, KTMT, TTNT)  
✅ Elasticsearch indices  
✅ Test scripts sẵn sàng  

## Cần làm ngay

### 1. Pull Ollama models

```bash
ollama pull bge-m3
ollama pull gemma3:4b
```

### 2. Chạy ingestion

```bash
cd /Users/admin/Documents/School/backend-support
export OLLAMA_HOST=http://localhost:11434
.venv/bin/python test_ingestion.py
```

### 3. Test query

```bash
.venv/bin/python test_query.py
```

## Files đã tạo

- `test_ingestion.py` - Ingest 3 ngành vào ES
- `test_query.py` - Test câu hỏi về TTNT
- `ktmt-output.json` - KTMT data (27 sections)  
- `ttnt-output.json` - TTNT data (24 sections)
