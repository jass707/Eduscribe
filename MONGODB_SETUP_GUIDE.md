# 🍃 MongoDB Atlas Setup Guide - MUCH EASIER!

**Why MongoDB is Better for EduScribe:**
- ✅ **No installation** - Cloud-hosted (MongoDB Atlas)
- ✅ **Built-in vector search** - No extensions needed
- ✅ **Free tier** - 512MB free forever
- ✅ **Flexible schema** - Perfect for evolving note structures
- ✅ **Easy deployment** - Works everywhere
- ✅ **No PostgreSQL errors** - Simple Python driver

---

## 🚀 **Quick Setup (5 Minutes):**

### **Step 1: Create Free MongoDB Atlas Account**

1. **Go to:** https://www.mongodb.com/cloud/atlas/register
2. **Sign up** with email or Google
3. **Create Organization** → Skip (use default)
4. **Create Project** → Name it "EduScribe"

---

### **Step 2: Create Free Cluster**

1. Click **"Build a Database"**
2. Choose **"M0 FREE"** tier:
   - ✅ 512MB storage
   - ✅ Shared RAM
   - ✅ No credit card required
3. **Cloud Provider:** AWS (or any)
4. **Region:** Choose closest to you
5. **Cluster Name:** `eduscribe-cluster`
6. Click **"Create"** (takes 1-3 minutes)

---

### **Step 3: Create Database User**

1. **Security → Database Access**
2. Click **"Add New Database User"**
3. **Authentication Method:** Password
4. **Username:** `eduscribe_user`
5. **Password:** Click "Autogenerate Secure Password" (copy it!)
6. **Database User Privileges:** Read and write to any database
7. Click **"Add User"**

---

### **Step 4: Whitelist IP Address**

1. **Security → Network Access**
2. Click **"Add IP Address"**
3. Choose **"Allow Access from Anywhere"** (for development)
   - IP: `0.0.0.0/0`
4. Click **"Confirm"**

*(For production, add specific IPs)*

---

### **Step 5: Get Connection String**

1. Go to **"Database"** tab
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. **Driver:** Python, Version: 3.12 or later
5. **Copy connection string:**
   ```
   mongodb+srv://eduscribe_user:<password>@eduscribe-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. **Replace `<password>`** with your actual password

---

### **Step 6: Install Python Dependencies**

```powershell
cd d:\store\notify\backend

# Install MongoDB drivers
pip install pymongo motor dnspython

# Or install all at once
pip install -r requirements_mongodb.txt
```

---

### **Step 7: Configure Environment**

Update `backend/.env`:

```env
# MongoDB Atlas Connection
MONGODB_URL=mongodb+srv://eduscribe_user:YOUR_PASSWORD@eduscribe-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority

# Replace:
# - YOUR_PASSWORD with your actual password
# - xxxxx with your cluster ID

# Other settings
GROQ_API_KEY=gsk_your_key_here
WHISPER_MODEL_SIZE=small
```

---

### **Step 8: Test Connection**

Create `backend/test_mongodb.py`:

```python
import asyncio
from database.mongodb_connection import init_mongodb, setup_indexes, get_db

async def test():
    # Initialize connection
    db = init_mongodb()
    print(f"✅ Connected to MongoDB!")
    
    # Create indexes
    await setup_indexes()
    print(f"✅ Indexes created!")
    
    # Test insert
    result = await db.test_collection.insert_one({"test": "data"})
    print(f"✅ Test insert successful: {result.inserted_id}")
    
    # Clean up
    await db.test_collection.delete_many({})
    print(f"✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test())
```

Run test:
```powershell
python test_mongodb.py
```

Expected output:
```
✅ MongoDB Atlas connected successfully!
✅ MongoDB indexes created successfully!
✅ Test insert successful: 507f1f77bcf86cd799439011
✅ All tests passed!
```

---

## 🔍 **Step 9: Create Vector Search Index (for RAG)**

### **Via Atlas Dashboard:**

1. **Go to:** MongoDB Atlas Dashboard
2. **Click:** Your cluster → **"Search"** tab
3. **Click:** "Create Search Index"
4. **Choose:** "JSON Editor"
5. **Index Name:** `vector_search`
6. **Database:** `eduscribe`
7. **Collection:** `document_embeddings`
8. **Paste this configuration:**

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "type": "knnVector",
        "dimensions": 384,
        "similarity": "cosine"
      },
      "lecture_id": {
        "type": "string"
      },
      "document_id": {
        "type": "string"
      }
    }
  }
}
```

9. **Click:** "Create Search Index"
10. **Wait:** 1-2 minutes for index to build

---

## 📊 **How It Works:**

### **1. Store Documents with Embeddings:**

```python
from database.mongodb_connection import save_document, save_document_embeddings
from sentence_transformers import SentenceTransformer

# Save document
doc_id = await save_document(
    lecture_id="lecture_123",
    filename="ml_lecture.pdf",
    file_type="pdf",
    file_path="/storage/uploads/ml_lecture.pdf",
    content="Full PDF text content..."
)

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
chunks = ["Machine learning is...", "Neural networks consist of..."]
embeddings = model.encode(chunks)

# Save embeddings
embedding_data = [
    {
        'lecture_id': "lecture_123",
        'document_id': doc_id,
        'chunk_text': chunk,
        'chunk_index': i,
        'embedding': embedding
    }
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
]

await save_document_embeddings(embedding_data)
# ✅ Stored in MongoDB with vector embeddings!
```

---

### **2. Vector Search (RAG Query):**

```python
from database.mongodb_connection import vector_search
from sentence_transformers import SentenceTransformer

# User's transcription
transcription = "What are neural networks?"

# Generate query embedding
model = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = model.encode(transcription)

# Search similar chunks
results = await vector_search(
    query_embedding=query_embedding,
    lecture_id="lecture_123",
    top_k=10
)

# Results:
# [
#   {
#     'chunk_text': 'Neural networks consist of layers...',
#     'similarity': 0.87,
#     'document_id': '...'
#   },
#   ...
# ]

# Use for RAG
context = "\n\n".join([r['chunk_text'] for r in results])
```

---

### **3. Save Lecture Data:**

```python
from database.mongodb_connection import (
    create_lecture,
    save_transcription,
    save_structured_notes,
    save_final_notes
)

# Create lecture
lecture_id = await create_lecture(
    user_id="user_123",
    subject_id="subject_456",
    title="Introduction to Machine Learning"
)

# Save transcriptions (20-second chunks)
await save_transcription(
    lecture_id=lecture_id,
    chunk_index=0,
    text="Today we'll discuss ML...",
    enhanced_notes="Machine learning fundamentals...",
    timestamp="00:00:20",
    importance=0.8
)

# Save structured notes (60-second synthesis)
await save_structured_notes(
    lecture_id=lecture_id,
    content="## Machine Learning\n- Subset of AI...",
    transcription_count=3
)

# Save final notes
await save_final_notes(
    lecture_id=lecture_id,
    title="Introduction to Machine Learning",
    markdown="# ML\n\n## Core Concepts...",
    sections=[{"title": "Core Concepts", "content": "..."}],
    glossary={"ML": "Machine Learning..."},
    key_takeaways=["ML enables data-driven learning"]
)
```

---

## 🗂️ **MongoDB Collections:**

```
eduscribe (database)
│
├── users
│   └── { _id, email, username, created_at }
│
├── subjects
│   └── { _id, user_id, name, description }
│
├── lectures
│   └── { _id, subject_id, user_id, title, status, duration, metadata }
│
├── documents
│   └── { _id, lecture_id, filename, content, file_type, upload_date }
│
├── document_embeddings (Vector Search Index!)
│   └── { _id, lecture_id, document_id, chunk_text, embedding[384], metadata }
│
├── transcriptions
│   └── { _id, lecture_id, chunk_index, text, enhanced_notes, timestamp }
│
├── structured_notes
│   └── { _id, lecture_id, content, transcription_count, created_at }
│
└── final_notes
    └── { _id, lecture_id, title, markdown, sections[], glossary{}, key_takeaways[] }
```

---

## 🎯 **Advantages Over PostgreSQL:**

| Feature | MongoDB Atlas | PostgreSQL + pgvector |
|---------|---------------|----------------------|
| **Setup Time** | ✅ 5 minutes | ❌ 30+ minutes |
| **Installation** | ✅ None (cloud) | ❌ Local install + extension |
| **Errors** | ✅ Minimal | ❌ Many (pgvector, permissions, etc.) |
| **Free Tier** | ✅ 512MB free | ❌ Self-hosted only |
| **Vector Search** | ✅ Built-in | ⚠️ Requires pgvector extension |
| **Schema Changes** | ✅ Flexible | ❌ Migrations required |
| **Deployment** | ✅ Works everywhere | ⚠️ Manual setup |
| **Learning Curve** | ✅ Easy (JSON) | ❌ SQL + extensions |

---

## 🚀 **Production Deployment:**

### **Railway:**
```env
# Railway automatically provides MongoDB via addon
# Or use your Atlas connection string
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/eduscribe
```

### **Vercel:**
```env
# Add to Vercel environment variables
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/eduscribe
```

### **Any Platform:**
- Just set `MONGODB_URL` environment variable
- MongoDB Atlas works from anywhere!

---

## 🔧 **Useful MongoDB Commands:**

### **View Data (MongoDB Compass - GUI):**

1. Download: https://www.mongodb.com/products/compass
2. Connect with your connection string
3. Browse collections visually
4. Run queries easily

### **Python Shell:**

```python
import asyncio
from database.mongodb_connection import get_db

async def explore():
    db = get_db()
    
    # Count documents
    count = await db.lectures.count_documents({})
    print(f"Lectures: {count}")
    
    # Find all lectures
    async for lecture in db.lectures.find():
        print(lecture)
    
    # Find by ID
    lecture = await db.lectures.find_one({"_id": "lecture_123"})
    print(lecture)

asyncio.run(explore())
```

---

## 🐛 **Troubleshooting:**

### **Issue: "Connection timeout"**

**Solution:**
- Check IP whitelist (0.0.0.0/0 for development)
- Verify connection string has correct password
- Check internet connection

### **Issue: "Authentication failed"**

**Solution:**
- Verify username/password in connection string
- Check user has "Read and write" permissions
- Try regenerating password

### **Issue: "Vector search not working"**

**Solution:**
- Verify Atlas Search index is created
- Index name must be `vector_search`
- Collection must be `document_embeddings`
- Wait 1-2 minutes for index to build

### **Issue: "dnspython not found"**

**Solution:**
```powershell
pip install dnspython
```

---

## ✅ **Verification Checklist:**

- [ ] MongoDB Atlas account created
- [ ] Free M0 cluster created
- [ ] Database user created
- [ ] IP address whitelisted (0.0.0.0/0)
- [ ] Connection string copied
- [ ] Python packages installed (pymongo, motor, dnspython)
- [ ] `.env` file updated with MONGODB_URL
- [ ] Test connection successful
- [ ] Indexes created
- [ ] Vector Search index created (for RAG)

---

## 🎉 **You're Done!**

**MongoDB Atlas is now ready for EduScribe!**

**Benefits:**
- ✅ No PostgreSQL installation errors
- ✅ No pgvector extension issues
- ✅ Cloud-hosted, always accessible
- ✅ Free tier (512MB)
- ✅ Built-in vector search
- ✅ Flexible schema for notes
- ✅ Easy deployment anywhere

**Next:** Replace FAISS file storage with MongoDB vector search!

---

## 📚 **Additional Resources:**

- **MongoDB Atlas Docs:** https://docs.atlas.mongodb.com/
- **Vector Search Guide:** https://www.mongodb.com/docs/atlas/atlas-vector-search/
- **Python Driver:** https://pymongo.readthedocs.io/
- **Motor (Async):** https://motor.readthedocs.io/

---

**MongoDB is MUCH easier than PostgreSQL for this project!** 🚀
