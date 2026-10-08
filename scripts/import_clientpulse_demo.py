"""Explicit opt-in importer. Requires an existing Supabase auth user's UUID."""
import argparse
import json
from pathlib import Path
from sqlalchemy import select
from services.api.db import Session, init_db
from services.api.pulse_models import Organization, Member, Customer
from services.api.pulse import queue, aliases, CustomerBody


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--user-id',required=True);parser.add_argument('--all-files',action='store_true');args=parser.parse_args()
    init_db();root=Path(__file__).resolve().parents[1]/'fixtures'/'clientpulse';manifest=json.loads((root/'manifest.json').read_text())
    with Session() as db:
        organization=db.scalar(select(Organization).where(Organization.owner_id==args.user_id))
        if not organization:
            organization=Organization(owner_id=args.user_id,name='Synthetic ClientPulse demonstration');db.add(organization);db.flush();db.add(Member(organization_id=organization.id,auth_id=args.user_id))
        if db.scalar(select(Customer).where(Customer.organization_id==organization.id,Customer.synthetic==True)):
            raise SystemExit('Synthetic customers already imported. Delete them explicitly before importing again.')
        clients={}
        for spec in manifest['customers']:
            customer=Customer(organization_id=organization.id,**spec);db.add(customer);db.flush();clients[customer.name]=customer
            aliases(db,customer,CustomerBody(**{k:v for k,v in spec.items() if k!='synthetic'}))
        from services.api.pulse import file_validation
        selected=manifest['files'] if args.all_files else [f for f in manifest['files'] if f['name'] in ('call-01.wav','email-01.eml','chat-01.png')]
        for spec in selected:
            data=(root/spec['name']).read_bytes();queue(db,organization.id,data,spec['name'],file_validation(data,spec['name']),clients[spec['customer']].id,spec['communication_at'],spec['channel'])
        db.commit();print('Created 12 labelled synthetic customers and queued',len(selected),'communications. Worker performs actual analysis; no findings were seeded.')


if __name__=='__main__':main()
