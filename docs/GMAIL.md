# Gmail sending

Enable Google 2-Step Verification and create an app password for ClientPulse. Configure the backend root `.env`:

```env
EMAIL_PROVIDER=gmail
GMAIL_EMAIL=your-address@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

Restart the API. Review the recipient and draft before clicking Approve and send email. The sender is the configured Gmail address. Gmail sending limits apply. Keep the app password out of Git and the frontend.

Use a new draft after switching providers. SMTP does not provide provider-side idempotency, so uncertain attempts must be checked in Gmail Sent before generating another draft.
