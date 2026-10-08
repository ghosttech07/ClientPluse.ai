# Gmail API sending on Render Free

Render Free blocks outbound SMTP. Use Gmail API over HTTPS instead.

1. Create or select a Google Cloud project and enable Gmail API.
2. Configure Google Auth Platform branding and audience. For an external testing app, add your Gmail account as a test user.
3. Create a Web application OAuth client. Add `https://developers.google.com/oauthplayground` as an authorized redirect URI.
4. Open OAuth Playground, open its settings, enable Use your own OAuth credentials, and enter the client ID and secret.
5. Request only `https://www.googleapis.com/auth/gmail.send`, authorize the Gmail account used as the sender, and exchange the code for tokens. Complete Google consent yourself.
6. Save the refresh token, client ID and secret only in the Render backend environment:

```env
EMAIL_PROVIDER=gmail_api
GMAIL_EMAIL=your-address@gmail.com
GMAIL_CLIENT_ID=your-oauth-client-id
GMAIL_CLIENT_SECRET=your-oauth-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token
```

Redeploy the backend. Generate a fresh draft and review before sending. No domain purchase is required. Gmail account sending limits apply. Testing-mode refresh tokens for Gmail scopes expire after seven days; durable use requires a suitable production OAuth setup. Google may require app verification depending on its audience and use.

Keep credentials out of Git, the frontend and screenshots. An app password cannot replace OAuth credentials. API access is limited to sending; the app does not request inbox-reading access. Failed or uncertain Gmail attempts are not automatically retried; check Gmail Sent before creating a new draft.

Local SMTP remains available with `EMAIL_PROVIDER=gmail`, `GMAIL_EMAIL`, and `GMAIL_APP_PASSWORD`.
