import contextvars
import json

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from services.rag.hybrid_search import hybrid_search

active_sources = contextvars.ContextVar("active_sources", default=None)


def _record_sources(results: list[dict]) -> None:
    sources_list = active_sources.get()
    if sources_list is not None:
        for r in results:
            meta = r.get("metadata", {})
            source = {
                "filename": meta.get("filename", "unknown"),
                "source_type": meta.get("source_type", "unknown"),
                "text": r.get("text", ""),
                "score": r.get("score", 0.0) or r.get("combined_score", 0.0),
            }
            if not any(s["filename"] == source["filename"] and s["text"] == source["text"] for s in sources_list):
                sources_list.append(source)


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(description="The search query string to look up in the knowledge base.")


class CompareResumeJDInput(BaseModel):
    jd_text: str = Field(description="The full text content of the job description.")
    resume_text: str | None = Field(default=None, description="The full text content of the candidate's resume. Leave empty or None if the resume is already uploaded to the knowledge base.")


class ExplainCodeInput(BaseModel):
    query: str = Field(description="The function name, class name, or code concept to search and explain.")


class GenerateQuizInput(BaseModel):
    topic: str = Field(description="The topic or technology (e.g. React, Python) to generate a quiz on.")


class ToolFactory:
    """Factory that creates LangChain tools with access to RAG dependencies."""

    def __init__(self, embedder, vectorstore, bm25, llm):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.bm25 = bm25
        self.llm = llm

    def _search_knowledge_base(self, query: str) -> str:
        """Search the knowledge base using hybrid search."""
        results = hybrid_search(
            query=query,
            embedder=self.embedder,
            vectorstore=self.vectorstore,
            bm25=self.bm25,
            top_k=6,
        )
        _record_sources(results)

        if not results:
            return "No relevant documents found in the knowledge base."

        output_parts = []
        for r in results:
            meta = r.get("metadata", {})
            filename = meta.get("filename", "unknown")
            source_type = meta.get("source_type", "unknown")
            text = r.get("text", "")
            output_parts.append(f"SOURCE: {filename} ({source_type})\n{text}\n---")

        return "\n\n".join(output_parts)

    def _compare_resume_jd(self, jd_text: str, resume_text: str = None) -> str:
        """Compare resume against a job description."""
        if not resume_text or not resume_text.strip():
            # Search for resume documents in the knowledge base
            resume_results = hybrid_search(
                query="resume cv education experience profile projects skills",
                embedder=self.embedder,
                vectorstore=self.vectorstore,
                bm25=self.bm25,
                top_k=15,
                source_type_filter=["pdf", "text", "markdown"],
            )
            
            # Find chunks belonging to PDF files
            pdf_chunks = [r for r in resume_results if r.get("metadata", {}).get("source_type") == "pdf"]
            if pdf_chunks:
                # Group by the first PDF filename found to reconstruct the full text
                filename = pdf_chunks[0]["metadata"]["filename"]
                resume_chunks = [r for r in pdf_chunks if r["metadata"]["filename"] == filename]
                resume_text = "\n\n".join([r["text"] for r in resume_chunks])
            else:
                if resume_results:
                    resume_text = "\n\n".join([r["text"] for r in resume_results[:8]])
                else:
                    return "Error: No resume was provided, and no uploaded resume/profile document could be found in your knowledge base. Please upload your resume PDF first."

        # Search for context about JD requirements
        context_results = hybrid_search(
            query=jd_text[:500],
            embedder=self.embedder,
            vectorstore=self.vectorstore,
            bm25=self.bm25,
            top_k=6,
        )
        _record_sources(context_results)

        context = "\n".join([r["text"] for r in context_results])

        prompt = f"""Analyze the fit between this resume and job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

ADDITIONAL CONTEXT FROM KNOWLEDGE BASE:
{context}

Provide a structured analysis:
1. **Matching Skills** — What skills from the JD does the candidate already have?
2. **Missing Skills / Gaps** — What's missing?
3. **Suggested Talking Points** — Key achievements to highlight in an interview
4. **Overall Fit Percentage** — Estimate with brief justification

Be specific and actionable."""

        response = self.llm.invoke(prompt)
        return response.content

    def _explain_code(self, query: str) -> str:
        """Explain code found in the knowledge base."""
        results = hybrid_search(
            query=query,
            embedder=self.embedder,
            vectorstore=self.vectorstore,
            bm25=self.bm25,
            top_k=4,
            source_type_filter=["code"],
        )
        _record_sources(results)

        if not results:
            return "No relevant code found in the knowledge base."

        code_chunks = "\n\n---\n\n".join([r["text"] for r in results])

        prompt = f"""Explain this code as if you're describing it in a technical interview.

CODE:
{code_chunks}

Cover:
1. **What it does** — Clear functional description
2. **Why it's designed this way** — Design decisions and patterns used
3. **Time/Space Complexity** — If applicable
4. **Potential Improvements** — What could be done better

Be concise but thorough, as if preparing for a placement interview."""

        response = self.llm.invoke(prompt)
        return response.content

    def _generate_quiz(self, topic: str) -> str:
        """Generate quiz questions from knowledge base content."""
        results = hybrid_search(
            query=topic,
            embedder=self.embedder,
            vectorstore=self.vectorstore,
            bm25=self.bm25,
            top_k=8,
        )
        _record_sources(results)

        if not results:
            return f"No content found about '{topic}' in the knowledge base."

        content = "\n\n".join([r["text"] for r in results])

        prompt = f"""Generate 5 multiple choice questions from this content about "{topic}".

CONTENT:
{content}

Format each question exactly as:
Q1: [question]
A) [option]
B) [option]
C) [option]
D) [option]
Answer: [letter]
Explanation: [brief explanation why]

Make questions challenging but fair — suitable for campus placement preparation."""

        response = self.llm.invoke(prompt)
        return response.content

    def get_tools(self) -> list[StructuredTool]:
        """Return all 4 Structured LangChain tools."""
        return [
            StructuredTool.from_function(
                name="search_knowledge_base",
                func=self._search_knowledge_base,
                description=(
                    "Search the user's personal knowledge base for relevant information. "
                    "Returns relevant documents from PDFs, code, notes, and other ingested sources."
                ),
                args_schema=SearchKnowledgeBaseInput,
            ),
            StructuredTool.from_function(
                name="compare_resume_jd",
                func=self._compare_resume_jd,
                description=(
                    "Compare a resume against a job description. "
                    "Returns analysis of matching skills, gaps, and talking points."
                ),
                args_schema=CompareResumeJDInput,
            ),
            StructuredTool.from_function(
                name="explain_code",
                func=self._explain_code,
                description=(
                    "Explain code from the knowledge base as if in a technical interview. "
                    "Returns explanation covering functionality, design, complexity, and improvements."
                ),
                args_schema=ExplainCodeInput,
            ),
            StructuredTool.from_function(
                name="generate_quiz",
                func=self._generate_quiz,
                description=(
                    "Generate multiple choice quiz questions on a topic from the knowledge base. "
                    "Returns 5 MCQ questions with answers and explanations."
                ),
                args_schema=GenerateQuizInput,
            ),
        ]
