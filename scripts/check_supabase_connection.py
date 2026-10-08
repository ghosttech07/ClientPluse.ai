"""Check/normalize a backend URI without printing credentials."""
from urllib.parse import unquote, quote
from dotenv import dotenv_values, set_key
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main():
    values=dotenv_values('.env');raw=values.get('DATABASE_URL','')
    if not raw.startswith(('postgresql://','postgresql+psycopg://')):
        print('DATABASE_URL is not a PostgreSQL connection.');return
    # The last @ separates the host even if the password contains unescaped @.
    scheme,rest=raw.split('://',1)
    credentials,host=rest.rsplit('@',1)
    username,password=credentials.split(':',1)
    password=unquote(password)
    candidates=[password]
    if password.startswith('[') and password.endswith(']'):candidates.append(password[1:-1])
    for candidate in candidates:
        uri='postgresql+psycopg://'+username+':'+quote(candidate,safe='')+'@'+host
        try:
            url=make_url(uri)
            if not url.host or not url.host.endswith(('.supabase.com','.supabase.co')):
                print('Connection host is not Supabase.');return
            engine=create_engine(url,connect_args={'connect_timeout':10,'sslmode':'require'})
            with engine.connect() as connection:
                assert connection.scalar(text('select current_database()'))=='postgres'
            if 'sslmode=' not in uri:uri+=('&' if '?' in uri else '?')+'sslmode=require'
            set_key('.env','DATABASE_URL',uri)
            print('Supabase PostgreSQL connection: PASS. URI safely normalized and TLS required.');return
        except Exception as error:
            original=getattr(error,'orig',None)
            code=getattr(original,'sqlstate',None)
            kind='authentication' if code=='28P01' else 'connection'
            message=str(original or error).lower()
            if 'password authentication failed' in message:kind='password authentication'
            elif 'tenant or user not found' in message:kind='project username/region (tenant or user not found)'
            elif 'resolve host' in message:kind='DNS resolution'
            elif 'timeout' in message:kind='network timeout'
            elif 'certificate' in message:kind='TLS certificate'
    print('Supabase '+kind+' check failed. No credential values printed. Verify the saved database password and connection details.')


if __name__=='__main__':main()
