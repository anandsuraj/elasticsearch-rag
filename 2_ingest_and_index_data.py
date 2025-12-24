# this script will take almost 5 minutes to run due to downloading and indexing data

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

# --- 1) Create index with semantic_text mapping ---
if not client.indices.exists(index=INDEX_NAME):
    resp = client.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "text": {"type": "semantic_text"}
            }
        },
    )
    print("Index created:", resp)
else:
    print("Index already exists")

# --- 2) Download the TSV dataset ---
tsv_url = (
    "https://raw.githubusercontent.com/"
    "elastic/stack-docs/refs/heads/main/docs/en/stack/ml/nlp/data/"
    "msmarco-passagetest2019-unique.tsv"
)

print("Downloading dataset...")
r = requests.get(tsv_url, stream=True)
r.raise_for_status()

# Write to local that will be parsed
local_file = "msmarco-passagetest2019-unique.tsv"
with open(local_file, "wb") as f:
    for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)

print("Download complete")

# --- 3) Bulk load into Elasticsearch ---
print("Indexing documents in bulk...")

actions = []
with open(local_file, newline="", encoding="utf-8") as tsvfile:
    reader = csv.reader(tsvfile, delimiter="\t")
    for i, row in enumerate(reader):
        # Assumes first is id, second is text
        if len(row) < 2:
            continue
        doc_id = row[0]
        text = row[1].strip()

        actions.append({
            "_index": INDEX_NAME,
            "_id": doc_id,
            "_source": {"text": text}
        })

        # Flush every few docs
        if len(actions) >= 1000:
            helpers.bulk(client, actions)
            actions = []

    if actions:
        helpers.bulk(client, actions)

print("Indexing complete")