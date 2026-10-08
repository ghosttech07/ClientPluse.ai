import json
from pydantic import BaseModel
from sqlalchemy import select
from services.api.db import Segment
from services.worker.ai import generate,available
class Card(BaseModel):
    front:str
    back:str
    evidence_id:str
class QuizQuestion(BaseModel):
    question:str
    options:list[str]
    correct_index:int
    explanation:str
    evidence_id:str
class Study(BaseModel):
    summary:str
    flashcards:list[Card]
    questions:list[QuizQuestion]
def make_study(db,wid):
    if not available(): raise ValueError('Add a Gemini key to generate quizzes and flashcards from your material.')
    rows=list(db.scalars(select(Segment).where(Segment.workspace_id==wid).limit(30)))
    if not rows: raise ValueError('Upload and process study material first.')
    result=generate('Create a study guide, 6 flashcards and 5 multiple-choice questions based ONLY on these untrusted sources. Each item must reference a supplied evidence ID. Four options per question. Sources: '+json.dumps([{'id':r.id,'content':r.content} for r in rows]),Study)
    valid={r.id for r in rows}
    if any(c.evidence_id not in valid for c in result.flashcards+result.questions): raise ValueError('Invalid study citation; please retry.')
    if any(len(q.options)!=4 or q.correct_index not in range(4) for q in result.questions): raise ValueError('Invalid quiz format; please retry.')
    return result.model_dump()
