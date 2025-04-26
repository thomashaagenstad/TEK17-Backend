from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os

# Last inn API-nøkkel fra .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Sett riktig sti til FAISS-indeksen
index_path = "C:/Assignment 3/Data/tek17_faiss_index"

# Initialiser embeddings
embeddings = OpenAIEmbeddings(openai_api_key=api_key)

# Last FAISS-indeksen
print("🔍 Laster FAISS-indeks...")
vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
print("✅ FAISS-indeks lastet inn!")

# Kjør et testspørsmål
query = "Hva er krav til brannmotstand for bærende konstruksjoner i brannklasse 3?"
docs = vectorstore.similarity_search(query, k=3)

# Skriv ut treff
print(f"\n📄 Topp {len(docs)} relevante treff for: \"{query}\"\n")
for i, doc in enumerate(docs, 1):
    print(f"{i}. {doc.page_content[:500]}\n{'-'*80}")
