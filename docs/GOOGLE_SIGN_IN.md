# Google sign-in setup

The website now has **Continue with Google** on both sign-in and registration. It uses Supabase OAuth with PKCE and returns to `/auth/callback`, verifies the user, then opens the dashboard. Google creates a Supabase account on first sign-in.

## Credentials and environment files

The browser already needs these public Supabase settings in `apps/web/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://niumtoxiouvslutaagpz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your existing Supabase public anon key>
```

These settings are already configured in this workspace. **No additional Google API key or Google client secret belongs in this frontend file.** Keep the Gemini key and Supabase service-role key exclusively on the backend.

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

Click **Continue with Google**, select your own account, and complete the Google consent screen. The app should return to `/auth/callback` and then `/dashboard`. Open Account settings to see the account email. If the provider is disabled, the website shows a clear message and retains email sign-in.

## Production

Add your production website origin to Google, and its exact `/auth/callback`, `/login`, and `/dashboard` URLs to Supabase. Change Supabase Site URL to the public HTTPS website. Disable shared `DEMO_MODE` before publishing.

Official references: [Supabase Google sign-in](https://supabase.com/docs/guides/auth/social-login/auth-google), [Supabase redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls).
