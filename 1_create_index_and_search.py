import os
import random
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
import json

load_dotenv()

ES_URL = os.getenv("URL")
ES_API_KEY = os.getenv("API_KEY")

client = Elasticsearch(
    ES_URL,
    api_key=ES_API_KEY,
    request_timeout=60
)

INDEX_NAME = "restaurants"

# --- 1) Create index with semantic + normal fields ---
if client.indices.exists(index=INDEX_NAME):
    client.indices.delete(index=INDEX_NAME)

client.indices.create(
    index=INDEX_NAME,
    mappings={
        "properties": {
            "name": {"type": "text"},
            "cuisine": {"type": "keyword"},
            "location": {"type": "keyword"},
            # semantic field to embed description for semantic search
            "text_semantic": {"type": "semantic_text"},
            "description": {"type": "text"}
        }
    }
)

print("Created index:", INDEX_NAME)

# --- 2) Generate and bulk load 100 restaurant docs ---
cuisines = ["Italian", "Indian", "Japanese", "Mexican", "Mediterranean"]
locations = ["Kolkata", "Delhi", "Mumbai", "Bengaluru", "Chennai"]

def random_description(name, cuisine):
    return (
        f"{name} serves amazing {cuisine} food with a great ambience, "
        "friendly staff and perfect for dinner or weekend brunch."
    )

actions = []
for i in range(1, 101):
    name = f"Restaurant {i}"
    cuisine = random.choice(cuisines)
    location = random.choice(locations)
    description = random_description(name, cuisine)

    actions.append({
        "_index": INDEX_NAME,
        "_id": i,
        "_source": {
            "name": name,
            "cuisine": cuisine,
            "location": location,
            "description": description,
            "text_semantic": description
        }
    })

helpers.bulk(client, actions)
print("Indexed 100 restaurant docs")

# Refresh so reads see the data
client.indices.refresh(index=INDEX_NAME)

# --- 3) Perform semantic search ---
semantic_query = "best place for authentic Indian dinner"
print("\nSemantic search for:", semantic_query)

semantic_resp = client.search(
    index=INDEX_NAME,
    query={
        "semantic": {
            "field": "text_semantic",
            "query": semantic_query
        }
    },
    size=5
)

print("Top semantic results:")
for hit in semantic_resp["hits"]["hits"]:
    src = hit["_source"]
    print(f"- ({hit['_score']:.3f}) {src['name']} [{src['cuisine']}, {src['location']}]")

# --- 4) Perform fuzzy search ---
fuzzy_query = "Italien restarant"
print("\nFuzzy search for:", fuzzy_query)

# Perform a fuzzy search to find documents that approximately match the query.
# The "multi_match" query searches across multiple fields (name, description, cuisine).
# The "fuzziness" parameter allows for minor typos or variations in the search term.
# The name^3 in the fields parameter of the multi_match query is a boost factor. It increases the importance of the name field in the search results.

fuzzy_resp = client.search(
    index=INDEX_NAME,
    query={
        "multi_match": {
            "query": fuzzy_query,
            "fields": ["name^3", "description", "cuisine"],
            "fuzziness": "AUTO"
        }
    },
    size=5
)

print("Top fuzzy results:")
for hit in fuzzy_resp["hits"]["hits"]:
    src = hit["_source"]
    print(f"- ({hit['_score']:.3f}) {src['name']} [{src['cuisine']}, {src['location']}]")

# --- 5) Print a few docs (optional) ---
print("\nSample docs:")
sample_resp = client.search(index=INDEX_NAME, query={"match_all": {}}, size=3)
print(json.dumps([h["_source"] for h in sample_resp["hits"]["hits"]], indent=2, ensure_ascii=False))
