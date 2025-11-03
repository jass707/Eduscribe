"""
Agentic Note Synthesizer for EduScribe
Combines multiple transcription chunks into structured, coherent notes
"""
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

# Initialize Groq client
groq_client = None
if GROQ_AVAILABLE and settings.GROQ_API_KEY:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)


async def synthesize_structured_notes(
    transcriptions: List[Dict[str, Any]],
    rag_context: List[str],
    lecture_id: str,
    previous_structured_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesize multiple transcription chunks into structured, coherent notes.
    
    Args:
        transcriptions: List of transcription dicts with 'text', 'timestamp', etc.
        rag_context: Relevant document chunks from FAISS
        lecture_id: Current lecture ID
        previous_structured_notes: Previously generated structured notes
    
    Returns:
        Dict with structured notes and metadata
    """
    # Combine all transcriptions
    full_transcription = "\n".join([t.get("text", "") for t in transcriptions])
    
    if not full_transcription.strip():
        return {
            "success": False,
            "error": "No transcription content to synthesize"
        }
    
    # Run synthesis in executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _synthesize_sync,
        full_transcription,
        rag_context,
        previous_structured_notes
    )
    
    return {
        "success": True,
        "structured_notes": result,
        "transcription_count": len(transcriptions),
        "lecture_id": lecture_id
    }


def _synthesize_sync(
    full_transcription: str,
    rag_context: List[str],
    previous_notes: Optional[str]
) -> str:
    """Synchronous synthesis function."""
    
    if not groq_client:
        print("⚠️  WARNING: GROQ client not available! Using fallback (will copy transcription errors)")
        print("⚠️  Please set GROQ_API_KEY in .env file!")
        return _fallback_synthesis(full_transcription)
    
    # Build context
    context_text = "\n\n".join(rag_context[:5]) if rag_context else "No additional context available."
    previous_text = previous_notes if previous_notes else "This is the first set of notes for this lecture."
    
    # System prompt for agentic synthesis with deep knowledge integration
    system_prompt = """You are an expert educational note-taker who MUST fix transcription errors and create accurate, educational notes.

CRITICAL RULES:
1. The transcription is FULL OF ERRORS from speech recognition (wrong words, grammar mistakes, nonsense phrases)
2. Your job is to UNDERSTAND what the speaker ACTUALLY meant and write CORRECT notes
3. DO NOT copy the transcription errors - FIX THEM!
4. Use the document context to understand correct terminology and concepts
5. Write clear, accurate, educational notes that make sense

EXAMPLE OF WHAT YOU MUST DO:
❌ BAD (copying errors): "humans have been devolving and learning from the past experience"
✅ GOOD (fixed): "Humans have been evolving and learning from past experiences"

❌ BAD: "machine learning is the code of many famous injectors built in Spanish"
✅ GOOD: "Machine learning is a core technology used in many famous applications"

❌ BAD: "machines are devolving by a living need to be programmed"
✅ GOOD: "Machines are evolving beyond the need to be explicitly programmed"

Your task:
1. READ the messy transcription and UNDERSTAND the actual topic
2. IDENTIFY what concepts the speaker is trying to explain
3. USE the document context to get correct information
4. WRITE clear, accurate notes using proper terminology
5. ORGANIZE information logically with headers and bullets
6. EXPLAIN concepts properly - don't just list broken sentences

Output format:
- Use ## for main topics (e.g., ## Introduction to Machine Learning)
- Use ### for subtopics (e.g., ### Types of Learning)
- Use bullet points for key information
- Use **bold** for important technical terms
- Write in complete, correct sentences
- Make it educational and easy to understand"""

    # User prompt with enhanced instructions
    user_prompt = f"""The transcription below is FULL OF ERRORS. Your job is to understand what was actually meant and create accurate notes.

MESSY TRANSCRIPTION (fix all errors!):
\"\"\"
{full_transcription}
\"\"\"

COURSE DOCUMENTS (use these to understand correct concepts):
\"\"\"
{context_text}
\"\"\"

PREVIOUS NOTES (for context, don't repeat):
\"\"\"
{previous_text}
\"\"\"

STEP-BY-STEP INSTRUCTIONS:
1. READ the transcription carefully - it has many errors
2. FIGURE OUT what topic the speaker is actually discussing (AI? Machine Learning? Neural Networks?)
3. LOOK at the course documents to understand the correct concepts
4. WRITE accurate, clear notes that explain what was MEANT (not what was said)
5. FIX all grammar errors, wrong words, and nonsense phrases
6. USE proper technical terminology from the documents
7. ORGANIZE with clear headers (##, ###) and bullet points

CRITICAL: Do NOT copy the transcription errors! Understand the meaning and write correct notes.

Example transformation:
Messy: "humans have been devolving and learning from the past experience since many years"
Fixed: "Humans have been evolving and learning from past experiences over many years"

Messy: "machine learning is the code of many famous injectors built in Spanish"  
Fixed: "Machine learning is a core technology used in many famous applications"

Now create accurate, educational notes:"""

    try:
        print(f"🤖 Calling GROQ API for synthesis...")
        response = groq_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Higher for better understanding/correction
            max_tokens=1500,  # More tokens for comprehensive notes
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ GROQ API synthesis successful! Generated {len(result)} characters")
        return result
        
    except Exception as e:
        print(f"❌ Error in agentic synthesis: {e}")
        print(f"⚠️  Falling back to simple synthesis (will have errors!)")
        return _fallback_synthesis(full_transcription)


def _fallback_synthesis(transcription: str) -> str:
    """Simple fallback if Groq is unavailable."""
    # Basic structure extraction
    sentences = transcription.split('.')
    
    notes = "## Lecture Notes\n\n"
    notes += "### Key Points\n\n"
    
    for i, sentence in enumerate(sentences[:10], 1):
        sentence = sentence.strip()
        if sentence:
            notes += f"- {sentence}\n"
    
    return notes


async def detect_topic_shift(
    current_transcription: str,
    previous_transcriptions: List[str]
) -> bool:
    """
    Detect if there's a significant topic shift in the lecture.
    This can trigger early synthesis even before 60 seconds.
    
    Args:
        current_transcription: Latest transcription text
        previous_transcriptions: Previous transcription texts
    
    Returns:
        True if topic shift detected, False otherwise
    """
    # Simple keyword-based detection for now
    # Can be enhanced with embeddings similarity
    
    if not previous_transcriptions:
        return False
    
    # Keywords that indicate topic transitions
    transition_keywords = [
        "now let's move on",
        "next topic",
        "moving on to",
        "let's discuss",
        "now we'll talk about",
        "switching to",
        "another important topic"
    ]
    
    current_lower = current_transcription.lower()
    
    for keyword in transition_keywords:
        if keyword in current_lower:
            return True
    
    return False
