import os
import csv
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers

load_dotenv()

ES_URL = os.getenv("URL")
ES_API_KEY = os.getenv("API_KEY")

client = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
    request_timeout=60
)

INDEX_NAME = "msmarco-semantic"

# --- 5) Perform a semantic search ---
query_text = "What causes muscle soreness after running?"
print("\nSemantic search query:", query_text)

resp = client.search(
    index=INDEX_NAME,
    query={
        "semantic": {
            "field": "text",
            "query": query_text
        }
    },
    size=5
)

print("\nTop semantic results:")
for hit in resp["hits"]["hits"]:
    score = hit["_score"]
    source = hit["_source"]
    print(f"Score: {score:.3f} | Text: {source.get('text')[:150]}…")