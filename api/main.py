from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
import re

# Last inn API-nøkkel og sti til FAISS-indeks
openai_api_key = os.getenv("OPENAI_API_KEY")
vectorstore_path = os.getenv("FAISS_INDEX_PATH", "C:/Assignment 3/Data/tek17_faiss_index")

# FastAPI-oppsett
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Forventet datastruktur
class ChatRequest(BaseModel):
    question: str

# Opprett prompttemplate
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Du er en ekspert på byggteknisk forskrift (TEK17), spesielt kapittel 11: Sikkerhet ved brann.

Svar kort og tydelig basert KUN på teksten under. Ikke anta eller gjett. Dersom svaret ikke fremgår, skriv: "Dette fremgår ikke eksplisitt av TEK17 kapittel 11."

Dersom du refererer til krav som er gitt i tabeller i regelverket (for eksempel brannmotstand, dørbredde, materialklasser o.l.), oppgi nøyaktige verdier og referer til riktig paragraf, f.eks. "jf. § 11-4 tabell 1".

Spørsmål:
{question}

TEK17 utdrag:
{context}

Svar:
"""
)

# Tabellbaserte ytelser fra § 11-4 med aliaser
brannkrav_tabell = {
    ("bærende hovedsystem", "1"): "R 30 [B 30]",
    ("bærende hovedsystem", "2"): "R 60 [B 60]",
    ("bærende hovedsystem", "3"): "R 90 A2-s1,d0 [A 90]",
    ("sekundære bygningsdeler", "2"): "R 60 [B 60]",
    ("sekundære bygningsdeler", "3"): "R 60 A2-s1,d0 [A 60]",
    ("trappeløp", "2"): "R 30 [B 30]",
    ("trappeløp", "3"): "R 30 A2-s1,d0 [A 30]",
    ("bærekonstruksjon under øverste kjeller", "2"): "R 90 A2-s1,d0 [A 90]",
    ("bærekonstruksjon under øverste kjeller", "3"): "R 120 A2-s1,d0 [A 120]",
}

# Alias for fleksibelt søk
deltype_alias = {
    "bærende konstruksjoner": "bærende hovedsystem",
    "bærende bygningsdel": "bærende hovedsystem",
    "bærende bygningsdeler": "bærende hovedsystem",
    "hovedbæresystem": "bærende hovedsystem",
    "sekundære bærekonstruksjoner": "sekundære bygningsdeler",
    "sekundære bærende konstruksjoner": "sekundære bygningsdeler",
    "trappeløp": "trappeløp",
    "konstruksjon under kjeller": "bærekonstruksjon under øverste kjeller",
    "bæresystem under kjeller": "bærekonstruksjon under øverste kjeller"
}

# Chat-endepunkt
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    question = data.get("question")
    question_clean = question.lower().replace(" ", "")

    # Prøv tabelloppslag med alias
    for alias, canonical in deltype_alias.items():
        if alias.replace(" ", "") in question_clean:
            for klasse in ["1", "2", "3"]:
                if f"brannklasse{klasse}" in question_clean:
                    krav = brannkrav_tabell.get((canonical, klasse))
                    if krav:
                        return {
                            "answer": {
                                "query": question,
                                "result": f"Kravet til brannmotstand for {alias} i brannklasse {klasse} er {krav} (jf. § 11-4 tabell 1).",
                                "source": "§ 11-4 tabell 1"
                            }
                        }

    # Hvis ikke funnet i tabellen, bruk embeddings og LLM
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)

    retriever = vectorstore.as_retriever(search_kwargs={"k": 6})
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=openai_api_key),
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt_template},
        return_source_documents=True,
    )

    result = qa({"query": question})
    answer_text = result["result"]
    documents = result.get("source_documents", [])

    paragraf = None
    if documents:
        content = documents[0].page_content
        match = re.search(r"§\s*11-\d+", content)
        if match:
            paragraf = match.group(0)

    return {
        "answer": {
            "query": question,
            "result": answer_text,
            "source": paragraf or "Ukjent paragraf"
        }
    }
