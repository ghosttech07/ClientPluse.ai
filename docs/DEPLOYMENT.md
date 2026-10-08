# Deployment preparation

The website is prepared for local use and cloud deployment, but no hosting account or production credentials are assumed and no live deployment is claimed.

## Frontend

Import the project into Vercel with root directory `apps/web`. Set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` and server `API_URL=https://your-api.example`. Build using `npm run build`. The Next.js rewrite proxies authenticated `/api` requests to FastAPI. Configure proxy/upload limits and timeouts for your plan; 25 MB uploads may require direct signed upload support if your frontend host rejects large bodies. That two-stage flow is not implemented.

## Backend and worker


Use one worker for this MVP. Lease expiry is 15 minutes; heartbeat extension/multi-worker concurrency and a Redis adapter are future work. Reports use private local volume storage. Use TLS and production monitoring.

## Supabase

Enable email/password Auth, configure redirects for signup and password recovery, and create a private `evidence` bucket if using optional storage. For account work, the server needs the public/anon key to validate `/auth/v1/user`. The service-role key is only needed for the optional private mirror; never expose it publicly. Apply database/storage policies after the initial schema when database tables are in Supabase public schema.

## Acceptance before publication

