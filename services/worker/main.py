import time, logging
from services.api.db import init_db
from services.worker.pulse import run_once
from services.api.db import Session
from services.api.pulse_models import Customer, Complaint
from services.worker.pulse import recalculate
from sqlalchemy import select

if __name__=='__main__':
    init_db()
    print('ClientPulse worker ready. Waiting for durable communications.')
    next_review=time.monotonic()+60
    while True:
        try:
            if not run_once():
                if time.monotonic()>=next_review:
                    with Session() as db:
                        customers=list(db.scalars(select(Customer).join(Complaint,Complaint.customer_id==Customer.id).where(Complaint.status=='Open').distinct()))
                        for customer in customers:recalculate(db,customer)
                        db.commit()
                    next_review=time.monotonic()+60
                time.sleep(1)
        except Exception as error:
            logging.getLogger(__name__).error('Worker iteration failed (%s); retrying',type(error).__name__)
            time.sleep(5)
