from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dependencies import get_llm, get_embedder, get_vectorstore, get_bm25_index
from services.rag.hybrid_search import hybrid_search
from services.db import sqlite_db

router = APIRouter()


class StartInterviewRequest(BaseModel):
    chat_id: str
    topic: str


class AnswerInterviewRequest(BaseModel):
    chat_id: str
    answer: str


class InterviewStatusResponse(BaseModel):
    status: str
    question_index: int
    current_question: str | None = None
    feedback: str | None = None
    final_assessment: str | None = None


@router.post("/start", response_model=InterviewStatusResponse)
async def start_mock_interview(
    body: StartInterviewRequest,
    llm=Depends(get_llm),
    embedder=Depends(get_embedder),
    vectorstore=Depends(get_vectorstore),
    bm25=Depends(get_bm25_index),
):
    """Start a mock interview session and generate the first question."""
    # 1. Fetch relevant topic context from Qdrant
    results = hybrid_search(
        query=body.topic,
        embedder=embedder,
        vectorstore=vectorstore,
        bm25=bm25,
        top_k=8,
    )
    context = "\n\n".join([r["text"] for r in results]) if results else "No detailed notes found."

    # 2. Ask the LLM to generate the first question
    prompt = f"""You are a professional technical interviewer testing the candidate on the topic: "{body.topic}".
Based on this knowledge base context:
{context}

Generate exactly ONE challenging, descriptive interview question. Keep it professional, realistic, and concise.
DO NOT output any introductory text, salutations, or greetings. Output ONLY the question."""

    try:
        response = llm.invoke(prompt)
        first_question = response.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate question: {e}")

    # 3. Create interview in SQLite
    sqlite_db.create_interview(body.chat_id, body.topic, first_question)
    
    # 4. Save to messages history
    system_msg = f"--- Mock Interview on '{body.topic}' Started ---"
    sqlite_db.add_message(body.chat_id, "ai", system_msg)
    sqlite_db.add_message(body.chat_id, "ai", first_question)

    return InterviewStatusResponse(
        status="active",
        question_index=1,
        current_question=first_question,
    )


@router.post("/answer", response_model=InterviewStatusResponse)
async def submit_interview_answer(
    body: AnswerInterviewRequest,
    llm=Depends(get_llm),
    embedder=Depends(get_embedder),
    vectorstore=Depends(get_vectorstore),
    bm25=Depends(get_bm25_index),
):
    """Submit answer to current question, get feedback, and retrieve next question/overall assessment."""
    # 1. Get active interview state
    session = sqlite_db.get_active_interview(body.chat_id)
    if not session:
        raise HTTPException(status_code=400, detail="No active mock interview found for this chat session.")

    current_question = session["current_question"]
    question_index = session["question_index"]
    topic = session["topic"]

    # 2. Save candidate response to database history
    sqlite_db.add_message(body.chat_id, "human", body.answer)

    # 3. Retrieve context for grading
    results = hybrid_search(
        query=f"{topic} {current_question}",
        embedder=embedder,
        vectorstore=vectorstore,
        bm25=bm25,
        top_k=5,
    )
    context = "\n\n".join([r["text"] for r in results]) if results else "No specific notes found."

    # 4. Generate feedback and handle progression
    if question_index < 5:
        # Generate feedback + NEXT question
        prompt = f"""You are a professional technical interviewer on topic: "{topic}".
You asked this question:
"{current_question}"

The candidate answered:
"{body.answer}"

Based on the technical context:
{context}

Provide structured evaluation:
1. **Feedback**: Grade their answer constructively. Explain what they got right, what was missing, or incorrect (max 120 words).
2. **Next Question**: Generate the next challenging interview question (Question #{question_index + 1} of 5) on "{topic}".

Make sure the feedback is clearly separated from the next question.
Format your output exactly as:
FEEDBACK: [your feedback]
NEXT_QUESTION: [next question text]"""

        try:
            response = llm.invoke(prompt)
            output = response.content.strip()
            
            # Parse output
            feedback = ""
            next_question = ""
            
            if "FEEDBACK:" in output and "NEXT_QUESTION:" in output:
                parts = output.split("NEXT_QUESTION:")
                feedback = parts[0].replace("FEEDBACK:", "").strip()
                next_question = parts[1].strip()
            else:
                feedback = output
                next_question = f"Could you explain another concept related to {topic}?"
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM processing failed: {e}")

        # Update SQLite and history
        sqlite_db.update_interview(session["id"], next_question, question_index + 1, "active")
        
        # Save feedback & next question to chat history
        sqlite_db.add_message(body.chat_id, "ai", f"**Feedback on Question #{question_index}:**\n{feedback}")
        sqlite_db.add_message(body.chat_id, "ai", next_question)

        return InterviewStatusResponse(
            status="active",
            question_index=question_index + 1,
            current_question=next_question,
            feedback=feedback,
        )
    else:
        # Final question answered -> Generate final feedback + Overall assessment
        prompt = f"""You are a professional technical interviewer on topic: "{topic}".
You asked the final question:
"{current_question}"

The candidate answered:
"{body.answer}"

Based on technical context:
{context}

Provide a final evaluation:
1. **Feedback**: Grade their final answer constructively (max 100 words).
2. **Overall Assessment**: Summarize their performance throughout this mock interview (5 questions). Provide an overall score out of 10 (e.g. "Score: 7/10") and core recommendations for improvement.

Format your output exactly as:
FEEDBACK: [final question feedback]
ASSESSMENT: [overall assessment and final score]"""

        try:
            response = llm.invoke(prompt)
            output = response.content.strip()
            
            feedback = ""
            assessment = ""
            if "FEEDBACK:" in output and "ASSESSMENT:" in output:
                parts = output.split("ASSESSMENT:")
                feedback = parts[0].replace("FEEDBACK:", "").strip()
                assessment = parts[1].strip()
            else:
                feedback = output
                assessment = "Mock Interview completed successfully."
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM final processing failed: {e}")

        # Complete interview in database
        sqlite_db.update_interview(session["id"], "", question_index, "completed")
        
        # Save final evaluation to history
        sqlite_db.add_message(body.chat_id, "ai", f"**Feedback on Question #5:**\n{feedback}")
        sqlite_db.add_message(body.chat_id, "ai", f"**--- Final Mock Interview Assessment ---**\n{assessment}")

        return InterviewStatusResponse(
            status="completed",
            question_index=5,
            feedback=feedback,
            final_assessment=assessment,
        )
