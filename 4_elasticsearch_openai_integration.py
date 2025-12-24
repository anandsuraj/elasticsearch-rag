# Install the required packages
# pip install -qU elasticsearch openai
import os
import csv
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from openai import OpenAI


load_dotenv()

'''--- 1) Setup Elasticsearch and OpenAI clients ---'''

es_client = Elasticsearch(
    os.getenv("URL"),
    api_key=os.getenv("API_KEY")
)
INDEX_NAME = "msmarco-semantic"

openai_client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
)
index_source_fields = {
    "msmarco-semantic": [
        "text"
    ]
}

'''--- 2) Define functions to get results and generate completions ---'''


def get_elasticsearch_results(query):
    # Define the Elasticsearch query to retrieve results based on semantic search
    es_query = {
        "retriever": {
            "standard": {
                "query": {
                    "semantic": {
                        "field": "text",  # Specify the field to perform semantic search on
                        "query": query  # The user-provided query for semantic search
                    }
                }
            }
        },
        "highlight": {
            "fields": {
                "text": {
                    "type": "semantic",  # Highlight matches based on semantic relevance
                    "number_of_fragments": 2,  # Return up to 2 fragments of highlighted text
                    "order": "score"  # Order the fragments by their relevance score
                }
            }
        },
        "size": 10  # Limit the number of results to 10
    }
    result = es_client.search(index=INDEX_NAME, body=es_query)
    return result["hits"]["hits"]


'''--- 3) Create OpenAI prompt from Elasticsearch results ---'''


def create_openai_prompt(results):
    context = ""
    for hit in results:
        # For semantic_text matches, we need to extract the text from the highlighted field
        if "highlight" in hit:
            highlighted_texts = []
            for values in hit["highlight"].values():
                highlighted_texts.extend(values)
            context += "\n --- \n".join(highlighted_texts)
        else:
            context_fields = index_source_fields.get(hit["_index"])
            for source_field in context_fields:
                hit_context = hit["_source"][source_field]
                if hit_context:
                    context += f"{source_field}: {hit_context}\n"
    prompt = f"""
  Instructions:
  
  - You are an assistant for question-answering tasks.
  - Answer questions truthfully and factually using only the context presented.
  - If you don't know the answer, just say that you don't know, don't make up an answer.
  - You must always cite the document where the answer was extracted using inline academic citation style [], using the position.
  - Use markdown format for code examples.
  - You are correct, factual, precise, and reliable.
  
  Context:
  {context}
  
  """
    return prompt


'''--- 4) Generate OpenAI completion based on prompt and question ---'''


def generate_openai_completion(user_prompt, question):
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": user_prompt},
            {"role": "user", "content": question},
        ]
    )
    return response.choices[0].message.content


'''--- 5) Main execution ---'''
if __name__ == "__main__":
    # you can replace with input("Enter your question: ")
    question = "can you tell me about Loco Moco"
    elasticsearch_results = get_elasticsearch_results(question)
    context_prompt = create_openai_prompt(elasticsearch_results)
    openai_completion = generate_openai_completion(context_prompt, question)
    print(openai_completion)
