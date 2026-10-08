# Customer email sending

Add RESEND_API_KEY and RESEND_FROM_EMAIL to the backend environment. The From address must belong to a domain verified in Resend. Reply-To is taken from the confirmed Supabase user email, never from browser input; RESEND_REPLY_TO is not used for this user-directed flow.

Reports > Follow-up email > review/edit > Save draft > Approve > enter recipient > confirm review > Send email. Non-email reports cannot be sent. No email is sent on drafting or approval alone.

POST /api/v1/drafts/{id}/send accepts recipient and the reviewed content snapshot. It verifies tenant ownership, confirmed identity, approval, exact content, and sender configuration. One send record is stored per draft. Retries reuse its immutable payload and Resend idempotency key. Accepted drafts cannot be sent to another recipient or edited. Pending attempts older than 23 hours require checking Resend rather than automatically risking a duplicate.

Accepted means Resend accepted the request, not that the recipient received it. Delivery/bounce webhooks are not implemented. No real email was sent during development tests. Apply migration version 4 on backend restart; the new delivery table is protected by RLS and browser roles have no access.
