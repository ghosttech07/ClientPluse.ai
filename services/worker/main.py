import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, update
from services.api.db import Session, Job, File, init_db, now
from services.worker.processors import process

def run_once():
    with Session() as db:
        # A stale lease is recovered after a crash; uploads remain durable in SQL.
        cutoff=(datetime.now(timezone.utc)-timedelta(minutes=15)).isoformat()
        db.execute(update(Job).where(Job.status=='Processing',Job.started_at<cutoff).values(status='Queued'))
        db.commit()
        j=db.scalar(select(Job).where(Job.status=='Queued').order_by(Job.created_at).limit(1))
        if not j: return False
        claim=db.execute(update(Job).where(Job.id==j.id,Job.status=='Queued').values(status='Processing',started_at=now(),attempts=Job.attempts+1))
        db.commit()
        if claim.rowcount: process(j.file_id)
    return True
if __name__=='__main__':
    init_db()
    print('Evidence worker ready. Waiting for durable processing jobs.')
    while True:
        if not run_once(): time.sleep(1)
