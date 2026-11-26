from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..ai.agents.growth_agent import run_growth_agent
from ..ai.rag.ingestion import index_creator_content
from ..ai.rag.retriever import answer_rag_query
from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/ai", tags=["AI Copilot & RAG"])


class RagQueryRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query must not be empty")
        return v.strip()


class AgentChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message must not be empty")
        return v.strip()


@router.post("/index")
def index_content(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = index_creator_content(db, current_user.user_id)
    return {"status": "ok", "indexed_chunks": count}


@router.post("/rag-query")
def rag_query(body: RagQueryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return answer_rag_query(db, current_user.user_id, body.query)


@router.post("/agent-chat")
def agent_chat(body: AgentChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return run_growth_agent(db, current_user.user_id, body.message)
