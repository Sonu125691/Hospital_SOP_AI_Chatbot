# 🏥 Hospital SOP AI Chatbot

A **Hospital SOP AI chatbot** designed to answer queries related to Hospital Standard Operating Procedures (SOPs) using a hybrid **Rule-Based + RAG (Retrieval-Augmented Generation)** architecture.

---

## Features

**Rule-Based Retrieval (Primary)**

  * Extracts precise information from structured SOP JSON data
  * Handles department + section level queries accurately

**RAG-Based Retrieval (Secondary)**

  * Uses FAISS vector database for semantic search
  * Handles indirect queries like SOP codes or vague questions

**Intelligent Query Routing**

  * Detects:

    * Department
    * Section
    * Multi-intent queries
    * Broad queries
  * Dynamically decides retrieval strategy

**Multi-Intent Handling**

  * Supports queries like:

    * *"Blood bank and fire safety overview"*
    * *"BB-SOP-001 and fire safety procedure"*

* 🛑 **Strict Hallucination Control**

  * LLM is forced to answer only from context
  * Returns fallback if information is unavailable

* 🧾 **Structured SOP Knowledge**

  * Covers:

    * Purpose
    * Scope
    * Procedure
    * Responsibilities
    * Documents
    * Approval Authority
    * Overview

---

## Architecture Overview

```text
User Query
   ↓
Query Analyzer (Intent Detection)
   ↓
-------------------------------------
| Rule-Based System (Primary)       |
| - JSON structured data           |
-------------------------------------
   ↓
-------------------------------------
| RAG System (Secondary)           |
| - FAISS vector search            |
-------------------------------------
   ↓
LLM (Strict Prompt Controlled)
   ↓
Final Answer
```

---

## Tech Stack

* **Frontend**: Streamlit
* **Backend**: Python
* **LLM**: (Groq / llama-3.3-70b-versatile)
* **Embeddings**: HuggingFace (`all-MiniLM-L6-v2`)
* **Vector DB**: FAISS
* **Framework**: LangChain

---

## ⚙️ How It Works

### 1. Query Analysis

* Detects:

  * Department (e.g., Blood Bank)
  * Section (e.g., Procedure)
  * Multi-intent queries

---

### 2. Rule-Based Retrieval

* Extracts exact data from JSON
* Primary source of truth

---

### 3. RAG Retrieval

* Used when rule-based fails
* Semantic search over SOP documents

---

### 4. LLM Processing

* Strict prompt:

  * No hallucination
  * No assumptions
  * Only context-based answers

---

## 💡 Example Queries

```text
✔ What is the procedure in blood bank operations?
✔ Responsibilities in ICU admission?
✔ Blood bank and fire safety overview
✔ BB-SOP-001 is which department?
✔ Procedure of fire safety and SOP code of blood bank
```

---

## 🛡️ Key Design Decisions

* **Rule-Based First Approach**

  * Ensures accuracy and structured output

* **Minimal Prompt Strategy**

  * Avoids LLM confusion

* **Context-Driven Design**

  * System controls logic, not the LLM

* **Multi-Intent Support**

  * Handles complex real-world queries
