# Elasticsearch Semantic Search & RAG Application

A complete implementation of semantic search using Elasticsearch and a RAG (Retrieval-Augmented Generation) application powered by OpenAI.

## Prerequisites

- Python 3.8+
- Elasticsearch Cloud account or local instance
- OpenAI API key

## Quick Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   
   Copy `.env_sample` to `.env` and add your credentials:
   ```env
   URL=<Your_Elasticsearch_URL>
   API_KEY=<Your_Elasticsearch_API_Key>
   OPENAI_API_KEY=<Your_OpenAI_API_Key>
   ```

## Usage

### Step 1: Create Index
```bash
python 1_create_index_and_search.py
```
Creates an Elasticsearch index with semantic search capabilities.

### Step 2: Ingest Data
```bash
python 2_ingest_and_index_data.py
```
Ingests the MS MARCO dataset and indexes it for semantic search.

### Step 3: Test Semantic Search
```bash
python 3_semantic_search_example.py
```
Performs semantic search queries on indexed data.

### Step 4: Elasticsearch + OpenAI Integration
```bash
python 4_elasticsearch_openai_integration.py
```
Demonstrates semantic search with OpenAI completions.

### Step 5: Run RAG Web Application
```bash
uvicorn fastapi_rag_app:app --reload
```
Launches a professional web UI at `http://127.0.0.1:8000` with:
- Real-time question answering using RAG
- Semantic search via Elasticsearch
- AI-powered responses via OpenAI
- Question history (last 20 queries)
- Modern gradient UI with loading indicators

## Project Structure

- `1_create_index_and_search.py` - Index creation and basic search
- `2_ingest_and_index_data.py` - Data ingestion pipeline
- `3_semantic_search_example.py` - Semantic search examples
- `4_elasticsearch_openai_integration.py` - ES + OpenAI integration
- `fastapi_rag_app.py` - Full-stack RAG web application
- `templates/index.html` - Web UI template
- `static/styles.css` - Professional styling
- `question_history.txt` - Query history storage

## Dataset

Uses MS MARCO passage test dataset (`msmarco-passagetest2019-unique.tsv`) for semantic search demonstrations.

## Features

- **Semantic Search**: Context-aware search using Elasticsearch embeddings
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate answers
- **Web Interface**: Professional UI with real-time feedback
- **History Tracking**: Maintains last 20 questions
- **Error Handling**: Robust error management for ES and OpenAI APIs

## License

MIT License
