# Chat Streaming API Documentation

## Endpoint: `POST /api/chats/chat/stream`

Stream-based chat với RAG assistant sử dụng Server-Sent Events (SSE).

---

## Request

### Headers
```
Content-Type: application/json
Authorization: Bearer <token>
```

### Body
```json
{
  "chat_id": 123,              // null = create new chat
  "major": "Công Nghệ Thông Tin",  // optional
  "top_k": 15,                 // default: 15
  "enable_reranking": true,    // optional
  "search_mode": "vector",     // "vector" | "fulltext" | "hybrid"
  "role": "user",              // required: "user"
  "content": "Môn IS336 học gì?"
}
```

---

## Response: Server-Sent Events (SSE)

Format: `data: {json}\n\n`

### Event Order

```
1. chat_info     → Chat session info
2. metadata      → Retrieval metadata
3. sources       → Source documents
4. answer_chunk  → (Multiple) Text chunks
5. done          → Stream complete
```

---

## Event Types

### 1. `chat_info`
Sent first, contains chat session ID.

```json
{
  "type": "chat_info",
  "data": {
    "chat_id": 123
  }
}
```

### 2. `metadata`
Retrieval metadata from RAG pipeline.

```json
{
  "type": "metadata",
  "data": {
    "intent": "factual",
    "refined_query": "môn is336 học những nội dung gì",
    "search_mode": "vector",
    "major": null,
    "num_sections": 5,
    "retrieval_time_ms": 1234.56
  }
}
```

### 3. `sources`
List of source sections used for answer.

```json
{
  "type": "sources",
  "data": [
    {
      "section_id": "abc123",
      "title": "Mô tả môn học",
      "hierarchy_path": "IS336 > Mô tả môn học",
      "text_preview": "Môn học này giới thiệu về...",
      "score": 0.95
    }
  ]
}
```

### 4. `answer_chunk`
Text chunks streamed as they're generated. **Multiple events**.

```json
{
  "type": "answer_chunk",
  "data": "Môn IS336 "
}
```
```json
{
  "type": "answer_chunk",
  "data": "dạy về "
}
```
```json
{
  "type": "answer_chunk",
  "data": "Hệ quản trị..."
}
```

### 5. `done`
Final event, contains saved message ID.

```json
{
  "type": "done",
  "data": {
    "message_id": 456
  }
}
```

### 6. `error` (if failed)
```json
{
  "type": "error",
  "data": "Error message here"
}
```

---

## Frontend Implementation Example

### TypeScript/React

```typescript
const streamChat = async (content: string, chatId?: number) => {
  const response = await fetch('/api/chats/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      chat_id: chatId,
      content,
      role: 'user',
      search_mode: 'vector'
    })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  let answer = '';
  let sources = [];
  let newChatId = chatId;
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = decoder.decode(value);
    const lines = text.split('\n');
    
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      
      const json = JSON.parse(line.slice(6));
      
      switch (json.type) {
        case 'chat_info':
          newChatId = json.data.chat_id;
          break;
        case 'metadata':
          setMetadata(json.data);
          break;
        case 'sources':
          sources = json.data;
          setSources(sources);
          break;
        case 'answer_chunk':
          answer += json.data;
          setAnswer(answer);
          break;
        case 'done':
          setMessageId(json.data.message_id);
          break;
        case 'error':
          setError(json.data);
          break;
      }
    }
  }
  
  return { chatId: newChatId, answer, sources };
};
```

---

## Response Headers

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Chat-Id: 123
```
