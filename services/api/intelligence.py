import re, json, logging, os
from datetime import datetime
from sqlalchemy import select
from services.api.db import Segment, File
from services.worker.ai import available, embed, cosine, generate, Reasoning
from services.worker import huggingface as hf

STOP={'the','a','an','is','of','and','to','in','what','why','how','did','does','may','have','with','this','my','at','for','working'}
def tokens(text): return set(re.findall(r'[a-z0-9]+',text.lower()))-STOP
def retrieve(db,workspace_id,question,limit=12):
    rows=list(db.scalars(select(Segment).where(Segment.workspace_id==workspace_id)))
    q=tokens(question); vector=None
    model_id=hf.embedding_id() if hf.enabled() else 'gemini:'+os.getenv('EMBEDDING_MODEL','gemini-embedding-001')
    compatible=lambda r: r.meta.get('embedding_model', 'gemini:gemini-embedding-001')==model_id
    if (available() or hf.enabled()) and any(r.embedding and compatible(r) for r in rows):
        try: vector=embed([question],True)[0]
        except Exception as e:
            logging.getLogger(__name__).warning('Query embedding unavailable; using source text retrieval (%s)',type(e).__name__)
    ranked=[]
    for s in rows:
        words=tokens(s.content); score=len(q & words)/max(1,len(q))
        if vector and s.embedding and compatible(s): score=score*.3+cosine(vector,s.embedding)*.7
        if score>0: ranked.append((score,s))
    ranked.sort(key=lambda x:x[0],reverse=True)
    candidates=[s for _,s in ranked[:max(limit,24)]] or rows[:max(limit,24)]
    try: candidates=hf.rerank(question,candidates)
    except Exception as e: logging.getLogger(__name__).warning('Reranking unavailable (%s); retaining retrieval order',type(e).__name__)
    return candidates[:limit]
def citation(db,s,files=None):
    f=files.get(s.file_id) if files is not None else db.get(File,s.file_id)
    return {'id':s.id,'file_id':s.file_id,'file_name':f.name if f else 'Deleted source','modality':s.modality,'page':s.page,'timestamp':s.timestamp,'event_time':s.event_time,'content':s.content,'row':s.meta.get('row'),'extraction':f.meta.get('extraction','Direct extraction') if f else ''}
def answer(db,workspace_id,question):
    evidence=retrieve(db,workspace_id,question)
    if not evidence:
        return {'content':'The indexed evidence does not contain enough relevant information to answer this question. Upload supporting files or ask a more specific question.','citations':[],'analysis':{'mode':'insufficient_evidence'}}
    files={f.id:f for f in db.scalars(select(File).where(File.workspace_id==workspace_id))}
    refs=[citation(db,s,files) for s in evidence]
    if available():
        prompt='Question: '+question+'\nUntrusted retrieved evidence: '+json.dumps(refs)+'\nGenerate structured cross-modal analysis. Each observed fact and possible explanation MUST cite evidence_ids from the list. Summary is an overview of the cited claims; do not add uncited factual claims. Be cautious about causation. Include missing information and next checks. Retrieval may be incomplete: never claim that a record is absent from an entire source or workspace just because it is absent from retrieved excerpts. Describe that limitation as not available in the retrieved context. Never claim observed engineering values exceed limits unless those limits are supplied.'
        result=generate(prompt,Reasoning)
        valid={s.id for s in evidence}
        for group in (result.observed_facts,result.possible_explanations,result.conflicting_information):
            for claim in group:
                if not claim.evidence_ids or not set(claim.evidence_ids)<=valid: raise ValueError('The model returned an invalid citation. Please retry.')
        ordinals={s.id:i+1 for i,s in enumerate(evidence)}
        def cited(c):return '- '+c.text+' ['+', '.join(str(ordinals[eid]) for eid in c.evidence_ids)+']'
        lines=['## Observed facts']
        for c in result.observed_facts: lines.append(cited(c))
        if result.possible_explanations: lines+=['\n## Possible explanations']+[cited(c) for c in result.possible_explanations]
        if result.conflicting_information: lines+=['\n## Items to verify']+[cited(c) for c in result.conflicting_information]
        lines+=['\n## Missing information']+['- '+x for x in result.missing_information]
        lines+=['\n## Recommended next checks']+['- '+x for x in result.recommended_next_checks]
        return {'content':'\n'.join(lines),'citations':refs,'analysis':{**result.model_dump(),'mode':'gemini'}}
    lines=['## Retrieved evidence','Gemini is not configured. These are matching source excerpts, not an AI diagnosis or a conclusion.']
    for i,s in enumerate(evidence[:6]): lines.append(f'\n**[{i+1}] {refs[i]["file_name"]}**\n\n{s.content[:900]}')
    lines+=['\n## Next step','Compare these excerpts in the source viewer. Configure Gemini for cross-modal interpretations and consistency analysis.']
    return {'content':'\n'.join(lines),'citations':refs[:6],'analysis':{'mode':'local_retrieval','missing_information':['AI reasoning is unavailable until Gemini is configured.']}}
def timeline(db,wid):
    segments=list(db.scalars(select(Segment).where(Segment.workspace_id==wid)))
    events=[]
    for s in segments:
        if s.event_time is not None or s.timestamp is not None:
            events.append({'id':s.id,'title':s.content[:90],'description':s.content,'time':s.event_time,'seconds':s.timestamp,'source':citation(db,s),'uncertainty':'Timestamp supplied by source' if s.event_time else 'Media position; absolute date unknown'})
    def key(e):
        try: return (0,datetime.fromisoformat(e['time'].replace('Z','+00:00')).timestamp())
        except (ValueError,AttributeError): return (1,e['time'] or '',e['seconds'] or 0)
    return sorted(events,key=key)
def graph(db,wid):
    files=list(db.scalars(select(File).where(File.workspace_id==wid)))
    nodes=[{'id':f.id,'label':f.name,'type':'source','modality':f.mime.split('/')[0]} for f in files]
    edges=[]
    terms={}
    for s in db.scalars(select(Segment).where(Segment.workspace_id==wid)):
        entities=s.meta.get('entities',[])
        if not entities:
            entities=re.findall(r'\b(?:Machine [A-Z]|INV-\d+|ORD-\d+|[A-Z]{2,}-\d+)\b',s.content)
        for term in set(entities[:10]):
            if term not in terms:
                terms[term]='entity-'+str(len(terms)); nodes.append({'id':terms[term],'label':term,'type':'entity','modality':'concept'})
            edgeid=s.file_id+'-'+terms[term]
            if not any(e['id']==edgeid for e in edges): edges.append({'id':edgeid,'source':s.file_id,'target':terms[term],'label':'Mentioned in','evidence_id':s.id,'inferred':False})
    return {'nodes':nodes,'edges':edges,'limitations':'Edges represent source mentions, not causation.'}
