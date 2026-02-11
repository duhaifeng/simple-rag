# SimpleRAG

可配置的增强检索召回系统（RAG），支持多 Embedding、多向量库、BM25 稀疏检索、Hybrid 融合、Rerank 精排，并提供 Web 控制面用于可视化配置、数据查看与召回测试。

## 项目结构

```
simple-rag/
├── docs/                          # 架构设计文档 & draw.io 架构图
├── configs/
│   └── profiles.yaml              # Embedding / VectorStore / Retrieval / Rerank profiles
├── backend/
│   ├── pyproject.toml
│   └── simple_rag/
│       ├── main.py                # FastAPI 入口
│       ├── config/                # Settings & profiles 加载
│       ├── api/                   # Query API & Control Plane API
│       ├── embeddings/            # Embedder 接口 + local_hf / remote 实现
│       ├── vectorstores/          # VectorStore 接口 + pgvector 实现
│       ├── retrieval/             # Retriever 接口 + dense / sparse / hybrid
│       │   └── bm25/             # Okapi BM25 (tokenizer + inverted index + scorer)
│       ├── rerank/                # Reranker 接口 + local_cross_encoder / remote
│       ├── ingest/                # 文档解析 & chunking
│       ├── services/              # QueryService (检索编排)
│       ├── storage/               # 本地文件存储 (S3 接口预留)
│       ├── models/                # SQLAlchemy DB models
│       └── utils/                 # NFKC 归一化, content_hash 等
├── frontend/                      # Vue 3 + Vite + TypeScript
│   └── src/
│       ├── views/                 # 召回测试台 / Profiles / 文档 / Chunk / 实验
│       ├── api/                   # Axios API client
│       └── router/                # Vue Router
├── .env.example
└── README.md
```

## 快速开始

### 1. 后端

```bash
cd backend
pip install -e ".[dev]"

# 启动（开发模式）
uvicorn simple_rag.main:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 数据库

需要 PostgreSQL 16 + pgvector 扩展：

```sql
CREATE EXTENSION vector;
```

### 4. 配置

复制 `.env.example` 到 `.env`，按需修改。Profiles 配置在 `configs/profiles.yaml`。

## 技术选型

| 维度 | 选择 |
|---|---|
| 后端语言 | Python (FastAPI) |
| 前端 | Vue 3 + Vite + TypeScript |
| 数据库 | PostgreSQL 16 + pgvector |
| Embedding | 可插拔：本地 HF (bge-m3) / 远程 OpenAI 兼容 |
| 稀疏检索 | Okapi BM25 (自实现, jieba 中文分词) |
| 向量库 | 可插拔：pgvector (MVP) / Qdrant / Milvus |
| Hybrid 融合 | RRF (Reciprocal Rank Fusion) |
| Rerank | 可插拔：本地 cross-encoder / 远程服务 |

详细架构设计见 `docs/SimpleRAG架构设计.md`。
