# University Knowledge Agent

## Goal
A deployed RAG + Agent + Eval system that answers questions about Singapore
universities (NUS/NTU public course info, admissions, policies), built as a
2-week portfolio project for AI Product Engineer / AI Applied Engineer job
applications.

## Tech stack
- Backend: Python, FastAPI, Pydantic (structured output), SSE streaming
- RAG orchestration: LlamaIndex or LangChain
- Embeddings: Gemini text-embedding-004 (free tier) or open-source BGE (local)
- Vector store: Supabase (pgvector, free tier)
- LLM inference: Groq (Llama 3.1/3.3, primary), Gemini Flash as fallback on
  rate limits / long-context needs
- Agent orchestration: LangGraph (tool calling, routing, state)
- Eval: RAGAS (faithfulness, answer relevancy, context precision/recall)
- Frontend: minimal Next.js or Streamlit chat UI — no animation polish,
  function over form
- Deployment: Docker, Render/Railway (backend), Vercel (frontend if Next.js)
- Observability: LangSmith free tier or structured logging
- Tests: pytest, optional GitHub Actions CI

## Architecture
User query -> FastAPI gateway (SSE) -> Agent router (LangGraph): in scope?
  -> yes: RAG retrieval (pgvector) -> LLM generation (Groq, Gemini fallback)
     -> structured answer + citations
  -> no: tool call (web search fallback / module comparison / CAP calculator)
     -> LLM generation -> structured answer + citations
Eval runs offline against a fixed test set via RAGAS; scores feed back into
chunk size / top-k / prompt tuning.

## Constraints
- Zero infrastructure cost — stay within free tiers throughout
- Ship something deployed early; UI polish must never delay deployment
- Every RAG-based answer must return sources; no answer presented as fact
  without a citation or an explicit "outside knowledge base" flag

## Timeline (14 days, 2 phases)
- Days 1-7: data ingestion, RAG pipeline, first working end-to-end query
  (gate: RAG baseline usable)
- Days 8-14: agent/tool layer, RAGAS eval harness with before/after
  comparison, deployment, README + demo video (gate: deployed + eval report)