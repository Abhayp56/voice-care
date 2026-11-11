-- Advisory AI outputs are stored separately and can never set evidence.verified.
create table if not exists public.ai_evidence_reviews (
    id uuid primary key default gen_random_uuid(),
    evidence_id uuid not null references public.evidence(id) on delete cascade,
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    requested_by uuid not null references auth.users(id),
    result jsonb not null check (jsonb_typeof(result) = 'object'),
    created_at timestamptz not null default now()
);

create index if not exists ai_evidence_reviews_complaint_created_idx
    on public.ai_evidence_reviews (complaint_id, created_at desc);

alter table public.ai_evidence_reviews enable row level security;
revoke all on public.ai_evidence_reviews from public, anon, authenticated;
grant all on public.ai_evidence_reviews to service_role;
