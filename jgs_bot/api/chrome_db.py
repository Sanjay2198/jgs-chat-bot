import os
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Simple loader script to push the lines from jgs_doc.txt into a Chroma collection.
# Uses Chroma Cloud by default; configure via env vars.

# Load .env if present so CHROMA_* values are picked up when running locally.
load_dotenv()

CLOUD_HOST = os.getenv("CHROMA_HOST", "https://api.trychroma.com")
if not CLOUD_HOST.startswith("http"):
    CLOUD_HOST = f"https://{CLOUD_HOST}"
if CLOUD_HOST.startswith("https://"):
    ssl = True
    host_only = CLOUD_HOST.removeprefix("https://")
    port = int(os.getenv("CHROMA_PORT", "443"))
elif CLOUD_HOST.startswith("http://"):
    ssl = False
    host_only = CLOUD_HOST.removeprefix("http://")
    port = int(os.getenv("CHROMA_PORT", "80"))
else:
    ssl = True
    host_only = CLOUD_HOST
    port = int(os.getenv("CHROMA_PORT", "443"))

CLOUD_API_KEY = os.getenv("CHROMA_API_KEY") or os.getenv("CHROMADB_API_KEY")
CLOUD_TENANT = os.getenv("CHROMA_TENANT") or os.getenv("CHROMADB_TENANT")
CLOUD_DATABASE = os.getenv("CHROMA_DATABASE") or os.getenv("CHROMADB_DATABASE") or "jgs_db"

if not (CLOUD_API_KEY and CLOUD_TENANT):
    raise RuntimeError("Set CHROMA_API_KEY and CHROMA_TENANT (and optional CHROMA_DATABASE) before loading data.")

auth_headers = {"X-Chroma-Token": CLOUD_API_KEY, "Authorization": f"Bearer {CLOUD_API_KEY}"}

client_settings = Settings(
    chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
    chroma_client_auth_credentials=CLOUD_API_KEY,
    chroma_auth_token_transport_header="X-Chroma-Token",
)

chroma_client = chromadb.HttpClient(
    host=host_only,
    port=port,
    ssl=ssl,
    headers=auth_headers,
    tenant=CLOUD_TENANT,
    database=CLOUD_DATABASE,
    settings=client_settings,
)

collection = chroma_client.get_or_create_collection(name=CLOUD_DATABASE)

doc_path = Path(__file__).resolve().parent / "jgs_doc.txt"
with open(doc_path, "r", encoding="utf-8") as f:
    jgs_db: list[str] = f.read().splitlines()

collection.add(
    ids=[str(uuid.uuid4()) for _ in jgs_db],
    documents=jgs_db,
    metadatas=[{"line": idx} for idx in range(len(jgs_db))],
)

print(collection.peek())

# results = collection.query(
#     query_texts=[
#         "what is jgs?",
#         "can i return customized items",
#     ],
#     n_results=1,
# )
# for i, query_results in enumerate(results["documents"]):
#     print(f"\nquery {i}")
#     print("\n".join(query_results))
