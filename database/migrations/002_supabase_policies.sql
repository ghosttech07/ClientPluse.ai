-- Optional: apply only when initial tables are in your Supabase public schema.
-- Application authorization remains owner-only. Public clients have no write policies.
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
CREATE POLICY workspace_owner_read ON public.workspaces FOR SELECT TO authenticated
USING (owner_id = auth.uid()::text);

ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;
CREATE POLICY file_owner_read ON public.files FOR SELECT TO authenticated
USING (EXISTS (SELECT 1 FROM public.workspaces w WHERE w.id=workspace_id AND w.owner_id=auth.uid()::text));

ALTER TABLE public.evidence_segments ENABLE ROW LEVEL SECURITY;
CREATE POLICY evidence_owner_read ON public.evidence_segments FOR SELECT TO authenticated
USING (EXISTS (SELECT 1 FROM public.workspaces w WHERE w.id=workspace_id AND w.owner_id=auth.uid()::text));

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY messages_owner_read ON public.messages FOR SELECT TO authenticated
USING (EXISTS (SELECT 1 FROM public.workspaces w WHERE w.id=workspace_id AND w.owner_id=auth.uid()::text));

ALTER TABLE public.generated_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY report_owner_read ON public.generated_reports FOR SELECT TO authenticated
USING (EXISTS (SELECT 1 FROM public.workspaces w WHERE w.id=workspace_id AND w.owner_id=auth.uid()::text));

ALTER TABLE public.processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;
-- No client policies on jobs/audit: backend server role only.
-- Create a PRIVATE bucket named evidence in the dashboard. The backend service role
-- uploads objects; no public object access is granted by this migration.
CREATE POLICY evidence_storage_owner_read ON storage.objects FOR SELECT TO authenticated
USING (bucket_id='evidence' AND (storage.foldername(name))[1]=auth.uid()::text);
