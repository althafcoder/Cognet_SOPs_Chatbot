# Company RAG Chatbot

An enterprise-grade Retrieval-Augmented Generation (RAG) chatbot designed to ingest Standard Operating Procedures (SOPs) from Microsoft OneDrive, index them using Qdrant vector database, and provide an interactive AI chat interface using OpenAI's models.

## 🚀 Features

- **OneDrive Integration**: Automatically connects to Microsoft Graph API to fetch documents (PDF, DOCX) from specific client folders in OneDrive.
- **Intelligent Ingestion**: Detects file changes (via hashing) to prevent redundant indexing.
- **Context-Aware Chat**: Uses `gpt-4o` to generate accurate answers strictly based on ingested company knowledge.
- **Smart Suggestions**: Automatically generates follow-up questions based on the retrieved context using `gpt-4o-mini`.
- **Knowledge Base Manager**: A built-in sidebar in the UI to select clients and sync their files on demand.
- **Source Citations**: Returns exact sources and page numbers for the generated answers.

## 🛠️ Technology Stack

- **Backend Framework**: FastAPI, Uvicorn
- **Vector Database**: Qdrant (local/memory)
- **Relational Database**: SQLite (managed via SQLAlchemy) for tracking document metadata and scope hierarchy.
- **AI / LLM**: OpenAI API (Embeddings & Chat Completions)
- **Document Processing**: `PyMuPDF` (PDFs), `python-docx` (Word Documents)
- **Authentication**: MSAL (Microsoft Authentication Library) for Graph API

## 🧠 Architecture & Process Flow

The chatbot operates in two main phases: **Ingestion** and **Retrieval/Chat**.

### 1. Document Ingestion Phase
1. **Discovery**: The Knowledge Base Manager (UI) requests a list of clients from the OneDrive `SOPs` folder.
2. **Sync**: When a user clicks "Sync All Files", the backend triggers a background task.
3. **Download & Hash**: Documents are downloaded temporarily. A file hash is calculated to check if it's already indexed (skipping unchanged files).
4. **Extraction**: Text is extracted from PDFs and Word documents.
5. **Chunking & Metadata**: Text is split into chunks. The hierarchy (Client > Team > Benefit > Process) is registered in the SQLite database (`rag_scope.db`).
6. **Embedding**: Text chunks are converted into dense embeddings via OpenAI.
7. **Storage**: Embeddings and metadata are upserted into the Qdrant collection.

### 2. Retrieval & Chat Phase
1. **Query**: The user asks a question in the chat interface. (The scope can be filtered by specific clients using commands like `/client <Name>`).
2. **Retrieval**: The query is embedded and searched against the Qdrant vector database to find the most relevant chunks.
3. **Generation**: The `gpt-4o` model is prompted with the user query and the retrieved context chunks to generate a factual answer.
4. **Suggestions**: Simultaneously, `gpt-4o-mini` reads the retrieved context and suggests 1-3 follow-up questions.
5. **Response**: The UI displays the answer, sources (document & page number), and clickable follow-up suggestions.

## ⚙️ Setup & Installation

1. **Clone the repository** (or navigate to the directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
PROJECT_NAME="Company RAG Chatbot"
QDRANT_URL="memory"

# OpenAI Configuration
OPENAI_API_KEY="your_openai_api_key"

# Microsoft Graph API Configuration
MICROSOFT_CLIENT_ID="your_client_id"
MICROSOFT_CLIENT_SECRET="your_client_secret"
MICROSOFT_TENANT_ID="your_tenant_id"
MICROSOFT_USER_EMAIL="user@yourcompany.com"
```

## 🏃‍♂️ Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn rag.main:app --reload
```

- The API will be available at: `http://localhost:8000`
- The Chat UI is accessible at: `http://localhost:8000/`

## 💬 Usage

1. Open `http://localhost:8000/` in your browser.
2. In the **Knowledge Base Manager** sidebar, select a Client from the dropdown.
3. Click **Sync All Files** to ingest that client's SOPs from OneDrive into the vector database.
4. Once the sync is complete, type your question in the chat box.
5. The chatbot will answer based *only* on the synced documents and provide source citations.
