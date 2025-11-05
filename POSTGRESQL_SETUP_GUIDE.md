# 🐘 PostgreSQL + pgvector Setup Guide

Complete guide to integrate PostgreSQL with pgvector for EduScribe.

---

## 🎯 **What We're Building:**

```
PostgreSQL Database with pgvector
├── Store lecture data (metadata, status)
├── Store documents (PDFs, PPTs)
├── Store document chunks with embeddings (vector search!)
├── Store transcriptions (20s chunks)
├── Store structured notes (60s synthesis)
└── Store final comprehensive notes
```

**Benefits:**
- ✅ **Transactions**: ACID compliance, data integrity
- ✅ **Relationships**: Proper foreign keys, joins
- ✅ **Vector Search**: Fast similarity search with pgvector
- ✅ **Scalability**: Handle thousands of lectures
- ✅ **SQL Queries**: Powerful querying capabilities
- ✅ **Production-Ready**: Battle-tested database

---

## 📋 **Step-by-Step Setup:**

### **Step 1: Install PostgreSQL**

#### **Option A: Docker (Recommended - Easiest)**

```powershell
# Pull PostgreSQL with pgvector pre-installed
docker pull pgvector/pgvector:pg16

# Run container
docker run -d `
  --name eduscribe-db `
  -e POSTGRES_PASSWORD=your_secure_password `
  -e POSTGRES_DB=eduscribe `
  -p 5432:5432 `
  -v eduscribe-data:/var/lib/postgresql/data `
  pgvector/pgvector:pg16

# Verify it's running
docker ps

# Check logs
docker logs eduscribe-db
```

**Advantages:**
- ✅ pgvector pre-installed
- ✅ Easy to start/stop
- ✅ Isolated environment
- ✅ Easy to reset

---

#### **Option B: Local Installation (Windows)**

1. **Download PostgreSQL:**
   - Go to: https://www.postgresql.org/download/windows/
   - Download PostgreSQL 16 installer
   - Run installer

2. **Installation Settings:**
   - Port: `5432` (default)
   - Password: Choose strong password
   - Locale: Default
   - Components: PostgreSQL Server, pgAdmin 4, Command Line Tools

3. **Install pgvector:**
   ```powershell
   # Download from: https://github.com/pgvector/pgvector/releases
   # Or use pre-built binary for Windows
   ```

4. **Verify Installation:**
   ```powershell
   psql --version
   # Should show: psql (PostgreSQL) 16.x
   ```

---

### **Step 2: Create Database and Enable pgvector**

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql terminal:
CREATE DATABASE eduscribe;

# Connect to the database
\c eduscribe

# Enable pgvector extension
CREATE EXTENSION vector;

# Verify extension is installed
\dx
# Should show 'vector' in the list

# Exit
\q
```

---

### **Step 3: Run Database Schema**

```powershell
cd d:\store\notify\backend

# Run schema file
psql -U postgres -d eduscribe -f database/schema.sql

# Or from Python:
python -c "from database.connection import init_database; init_database()"
```

**What this creates:**
- ✅ 9 tables (users, subjects, lectures, documents, etc.)
- ✅ pgvector indexes for fast similarity search
- ✅ Helper functions for vector search
- ✅ Triggers for auto-updating timestamps

---

### **Step 4: Install Python Dependencies**

```powershell
cd d:\store\notify\backend

# Install PostgreSQL adapter and pgvector client
pip install psycopg2-binary pgvector

# Or install all requirements
pip install -r requirements.txt
```

---

### **Step 5: Configure Environment Variables**

Update `backend/.env`:

```env
# Database - PostgreSQL with pgvector
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/eduscribe

# For Docker:
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/eduscribe

# For Railway (production):
DATABASE_URL=postgresql://user:pass@host:port/dbname
# Railway provides this automatically

# Other settings
GROQ_API_KEY=gsk_your_key_here
WHISPER_MODEL_SIZE=small
```

---

### **Step 6: Test Connection**

Create `backend/test_db.py`:

```python
from database.connection import init_db_pool, get_db_cursor, init_database

# Initialize database
print("Initializing database...")
init_database()

# Test connection
print("Testing connection...")
with get_db_cursor() as cursor:
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ Connected to: {version['version']}")
    
    # Test pgvector
    cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
    pgvector = cursor.fetchone()
    if pgvector:
        print(f"✅ pgvector extension installed: version {pgvector['extversion']}")
    else:
        print("❌ pgvector not installed!")

print("✅ Database setup complete!")
```

Run test:
```powershell
python test_db.py
```

Expected output:
```
Initializing database...
✅ Database schema initialized
Testing connection...
✅ Connected to: PostgreSQL 16.x ...
✅ pgvector extension installed: version 0.5.1
✅ Database setup complete!
```

---

## 🔄 **How It Works:**

### **1. Document Upload & Embedding:**

```python
from database.connection import save_document, save_document_chunks
from sentence_transformers import SentenceTransformer

# User uploads PDF
document_id = save_document(
    lecture_id=1,
    filename="ml_lecture.pdf",
    file_type="pdf",
    file_path="/storage/uploads/ml_lecture.pdf",
    content="Machine learning is..."
)

# Extract text and create chunks
chunks = [
    "Machine learning is a subset of AI...",
    "Neural networks consist of layers...",
    # ... more chunks
]

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(chunks)

# Save to database with pgvector
chunk_data = [
    {
        'document_id': document_id,
        'lecture_id': 1,
        'text': chunk,
        'index': i,
        'embedding': embedding
    }
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
]

save_document_chunks(chunk_data)
# ✅ Chunks stored with vector embeddings!
```

---

### **2. RAG Query (Vector Similarity Search):**

```python
from database.connection import search_similar_chunks
from sentence_transformers import SentenceTransformer

# User's transcription
transcription = "What are neural networks?"

# Generate query embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = model.encode(transcription)

# Search similar chunks using pgvector
similar_chunks = search_similar_chunks(
    query_embedding=query_embedding,
    lecture_id=1,
    top_k=10
)

# Results:
# [
#   {
#     'chunk_id': 42,
#     'chunk_text': 'Neural networks consist of layers...',
#     'similarity': 0.87,
#     'document_filename': 'ml_lecture.pdf'
#   },
#   ...
# ]

# Use these chunks for RAG!
context = "\n\n".join([chunk['chunk_text'] for chunk in similar_chunks])
```

**How pgvector works:**
```sql
-- Behind the scenes, pgvector uses HNSW index for fast search
SELECT chunk_text, 
       1 - (embedding <=> query_embedding) AS similarity
FROM document_chunks
WHERE lecture_id = 1
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

---

### **3. Save Transcriptions & Notes:**

```python
from database.connection import (
    save_transcription,
    save_structured_notes,
    save_final_notes
)

# Save 20-second transcription
save_transcription(
    lecture_id=1,
    chunk_index=0,
    text="Today we'll discuss machine learning...",
    enhanced_notes="Machine learning fundamentals...",
    timestamp="00:00:20",
    importance=0.8
)

# Save 60-second structured notes
save_structured_notes(
    lecture_id=1,
    content="## Machine Learning\n- Subset of AI...",
    transcription_count=3
)

# Save final comprehensive notes
save_final_notes(
    lecture_id=1,
    title="Introduction to Machine Learning",
    markdown="# Machine Learning\n\n## Core Concepts...",
    sections=[
        {"title": "Core Concepts", "content": "..."},
        {"title": "Neural Networks", "content": "..."}
    ],
    glossary={"Machine Learning": "Subset of AI..."},
    key_takeaways=[
        "ML enables data-driven learning",
        "Three main types: supervised, unsupervised, reinforcement"
    ]
)
```

---

### **4. Query Lecture Data:**

```python
from database.connection import get_lecture_data

# Get complete lecture with all related data
lecture = get_lecture_data(lecture_id=1)

# Returns:
# {
#   'id': 1,
#   'title': 'ML Lecture 1',
#   'status': 'completed',
#   'transcriptions': [...],  # All transcriptions
#   'structured_notes': [...],  # All structured notes
#   'documents': [...],  # All uploaded documents
#   'final_notes': {...}  # Final comprehensive notes
# }
```

---

## 📊 **Database Schema Overview:**

```
users (id, email, username)
  ↓
subjects (id, user_id, name)
  ↓
lectures (id, subject_id, user_id, title, status)
  ↓
  ├── documents (id, lecture_id, filename, content)
  │     ↓
  │     └── document_chunks (id, document_id, chunk_text, embedding[384])
  │                          ↑ pgvector for similarity search!
  │
  ├── transcriptions (id, lecture_id, text, enhanced_notes)
  │
  ├── structured_notes (id, lecture_id, content)
  │
  └── final_notes (id, lecture_id, title, markdown, sections, glossary)
```

---

## 🚀 **Production Deployment (Railway):**

### **Step 1: Add PostgreSQL Plugin**

1. Go to Railway.app
2. Open your project
3. Click "New" → "Database" → "PostgreSQL"
4. Railway automatically:
   - Creates database
   - Sets `DATABASE_URL` environment variable
   - Provides connection details

### **Step 2: Enable pgvector**

```bash
# Connect to Railway database
railway connect

# In psql:
CREATE EXTENSION vector;
\q
```

### **Step 3: Run Migrations**

```bash
# Deploy backend with schema
railway up

# Or run schema manually
railway run python -c "from database.connection import init_database; init_database()"
```

---

## 🔧 **Useful Commands:**

### **Database Management:**

```powershell
# Connect to database
psql -U postgres -d eduscribe

# List all tables
\dt

# Describe table structure
\d document_chunks

# View pgvector indexes
\di

# Check database size
SELECT pg_size_pretty(pg_database_size('eduscribe'));

# Count records
SELECT 
    'lectures' as table, COUNT(*) FROM lectures
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'document_chunks', COUNT(*) FROM document_chunks;
```

### **Vector Search Testing:**

```sql
-- Test vector similarity search
SELECT 
    chunk_text,
    1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM document_chunks
WHERE lecture_id = 1
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

### **Backup & Restore:**

```powershell
# Backup database
pg_dump -U postgres eduscribe > backup.sql

# Restore database
psql -U postgres eduscribe < backup.sql
```

---

## 🐛 **Troubleshooting:**

### **Issue: "psycopg2 not found"**

```powershell
pip install psycopg2-binary
```

### **Issue: "pgvector extension not found"**

```sql
-- Check if pgvector is installed
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- If not available, reinstall PostgreSQL with pgvector
-- Or use Docker image: pgvector/pgvector:pg16
```

### **Issue: "Connection refused"**

```powershell
# Check if PostgreSQL is running
# Docker:
docker ps

# Windows service:
Get-Service postgresql*

# Test connection
psql -U postgres -h localhost -p 5432
```

### **Issue: "Permission denied"**

```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE eduscribe TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

---

## ✅ **Verification Checklist:**

- [ ] PostgreSQL installed and running
- [ ] pgvector extension enabled
- [ ] Database `eduscribe` created
- [ ] Schema tables created (9 tables)
- [ ] HNSW index on `document_chunks.embedding`
- [ ] Python can connect to database
- [ ] Can insert and query data
- [ ] Vector similarity search works
- [ ] Environment variables configured

---

## 📈 **Performance Tips:**

1. **Index Optimization:**
   ```sql
   -- Already created in schema.sql
   CREATE INDEX document_chunks_embedding_idx 
   ON document_chunks USING hnsw (embedding vector_cosine_ops);
   ```

2. **Connection Pooling:**
   - Already implemented in `connection.py`
   - Min 1, Max 10 connections

3. **Batch Inserts:**
   - Use `execute_many()` for bulk inserts
   - Already implemented for document chunks

4. **Query Optimization:**
   - Use indexes on foreign keys (already created)
   - Limit results with `LIMIT`
   - Use `EXPLAIN ANALYZE` to check query performance

---

## 🎉 **You're Done!**

Your EduScribe app now uses:
- ✅ PostgreSQL for robust data storage
- ✅ pgvector for fast similarity search
- ✅ Proper relationships and transactions
- ✅ Production-ready database architecture

**Next:** Integrate with your existing code to use PostgreSQL instead of FAISS files!
