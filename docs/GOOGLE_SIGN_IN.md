# Google sign-in setup

The website now has **Continue with Google** on both sign-in and registration. It uses Supabase OAuth with PKCE and returns to `/auth/callback`, verifies the user, then opens onboarding or the workspace for existing users. Google creates a Supabase account on first sign-in.

## Credentials and environment files

The browser already needs these public Supabase settings in `apps/web/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://niumtoxiouvslutaagpz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your existing Supabase public anon key>
```

On a new desktop, create this file using your project's public Supabase settings. Environment files are ignored by Git and do not transfer with the repository. **No additional Google API key or Google client secret belongs in this frontend file.** Keep the Gemini key and Supabase service-role key exclusively on the backend.

Create a **Google OAuth Client ID and Client Secret** and enter them in the hosted Supabase Dashboard's Google provider settings. Adding them to the app `.env` alone does not enable Google login.

## 1. Google Auth Platform

Open [Google Cloud Console](https://console.cloud.google.com/) and choose/create a project. Configure Google Auth Platform branding and audience for your app. If the consent screen is in testing, add your Google email under test users.

Create an OAuth client with application type **Web application**.

Authorized JavaScript origins for local development:

```
http://127.0.0.1:3000
http://localhost:3000
```

Authorized redirect URI (copy exactly; this is the Supabase callback, not your local app):

```
https://niumtoxiouvslutaagpz.supabase.co/auth/v1/callback
```

Copy the generated Client ID and Client Secret privately.

## 2. Enable the provider in Supabase

In your Supabase project, go to **Authentication → Sign In / Providers → Google**. Enable Google, enter the Client ID and Client Secret, and save. Dashboard labels may vary; choose the Google sign-in provider.

## 3. Configure app redirects in Supabase

Go to **Authentication → URL Configuration**. For this local setup, set Site URL to:

```
http://127.0.0.1:3000
```

Add these Redirect URLs:

```
http://127.0.0.1:3000/auth/callback
http://localhost:3000/auth/callback
http://127.0.0.1:3000/login
http://localhost:3000/login
http://127.0.0.1:3000/dashboard
http://localhost:3000/dashboard
```

Stay on the same hostname throughout sign-in so the PKCE verifier saved in your browser can be found on return. Start from the current app at `http://127.0.0.1:3000/login`.

## 4. Test

Click **Continue with Google**, select your own account, and complete the Google consent screen. The app should return to `/auth/callback` and then `/onboarding`, where existing users continue to their workspace. Open Account settings to see the account email. If the provider is disabled, the website shows a clear message and retains email sign-in.

## Production

For the deployed ClientPulse website, configure these exact values:

| Setting | Value |
| --- | --- |
| Google OAuth client: Authorized JavaScript origins | `https://client-pluse-ai.vercel.app` |
| Google OAuth client: Authorized redirect URIs | `https://niumtoxiouvslutaagpz.supabase.co/auth/v1/callback` |
| Supabase Authentication: Site URL | `https://client-pluse-ai.vercel.app` |
| Supabase Authentication: Redirect URLs | `https://client-pluse-ai.vercel.app/auth/callback` |

Clear the existing Site URL field before entering the production URL, then save changes. Site URL accepts one complete URL; add local development URLs as separate Redirect URL entries. Use the port actually used by your local app (for example, `http://127.0.0.1:3001/auth/callback`).

These are settings in Google Cloud and Supabase, not settings applied by a GitHub push. After saving them, start a fresh login attempt at `https://client-pluse-ai.vercel.app/login`.

## Troubleshooting

- **Google `redirect_uri_mismatch`:** Add the exact Supabase `/auth/v1/callback` URL above to the same Google OAuth client whose Client ID is saved in Supabase. The app's `/auth/callback` URL goes in Supabase's redirect allowlist.
- **Supabase `500 unexpected_failure` with `invalid port ":3000https:" after host`:** The Site URL contains joined URLs such as `http://localhost:3000https://client-pluse-ai.vercel.app`. Replace the entire Site URL with the production URL above and remove malformed redirect entries. Save and begin a new login attempt.
- **Other authentication 500 errors:** Open Supabase Logs, select the Auth source, and inspect the failed `/callback` event's `error` field. API Gateway events with `log_type: edge` show the HTTP status but may omit the underlying Auth error. Do not share secrets or tokens from logs.

Official references: [Supabase Google sign-in](https://supabase.com/docs/guides/auth/social-login/auth-google), [Supabase redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls).
