-- Durable lifecycle timestamps and notification outbox. No SLA values are
-- assumed: a hospital must add approved rows to complaint_sla_policies.
create table if not exists public.complaint_sla_policies (
    category_id uuid not null references public.complaint_categories(id) on delete cascade,
    priority text not null check (priority in ('low', 'medium', 'high', 'critical')),
    resolution_minutes integer not null check (resolution_minutes > 0),
    enabled boolean not null default true,
    updated_at timestamptz not null default now(),
    primary key (category_id, priority)
);

create table if not exists public.complaint_lifecycle_records (
    complaint_id uuid primary key references public.complaints(id) on delete cascade,
    received_at timestamptz not null default now(),
    assigned_at timestamptz,
    acknowledged_at timestamptz,
    work_started_at timestamptz,
    resolution_due_at timestamptz,
    resolution_submitted_at timestamptz,
    resolved_at timestamptz,
    escalated_at timestamptz,
    closed_at timestamptz,
    updated_at timestamptz not null default now()
);

create table if not exists public.complaint_lifecycle_events (
    id uuid primary key default gen_random_uuid(),
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    old_status text,
    new_status text not null,
    actor_id uuid references auth.users(id) on delete set null,
    note text,
    occurred_at timestamptz not null default now()
);
create index if not exists complaint_lifecycle_events_complaint_time_idx
    on public.complaint_lifecycle_events (complaint_id, occurred_at desc);

create table if not exists public.notification_outbox (
    id uuid primary key default gen_random_uuid(),
    event_key text not null unique,
    event_type text not null,
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    department_id uuid,
    payload jsonb not null default '{}'::jsonb check (jsonb_typeof(payload) = 'object'),
    delivery_state text not null default 'queued' check (delivery_state in ('queued', 'sent', 'failed')),
    attempts integer not null default 0 check (attempts >= 0),
    created_at timestamptz not null default now(),
    delivered_at timestamptz
);
create index if not exists notification_outbox_pending_idx
    on public.notification_outbox (created_at) where delivery_state = 'queued';

create or replace function public.voicecare_record_complaint_lifecycle()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    due_minutes integer;
begin
    if tg_op = 'INSERT' then
        select policy.resolution_minutes into due_minutes
        from public.complaint_sla_policies as policy
        where policy.category_id = new.category_id
          and policy.priority = new.priority
          and policy.enabled = true;

        insert into public.complaint_lifecycle_records (
            complaint_id, received_at, assigned_at, resolution_due_at, updated_at
        ) values (
            new.id,
            coalesce(new.created_at, now()),
            case when new.department_id is not null then coalesce(new.created_at, now()) end,
            case when due_minutes is not null then coalesce(new.created_at, now()) + make_interval(mins => due_minutes) end,
            now()
        ) on conflict (complaint_id) do nothing;

        insert into public.complaint_lifecycle_events (complaint_id, old_status, new_status, note)
        values (new.id, null, new.status, 'Complaint received');

        insert into public.notification_outbox (event_key, event_type, complaint_id, department_id)
        values ('complaint:' || new.id::text || ':received', 'complaint_received', new.id, new.department_id)
        on conflict (event_key) do nothing;
        return new;
    end if;

    if old.status is distinct from new.status then
        update public.complaint_lifecycle_records
        set assigned_at = case when new.status = 'assigned' and assigned_at is null then now() else assigned_at end,
            acknowledged_at = case when new.status = 'acknowledged' then now() else acknowledged_at end,
            work_started_at = case when new.status = 'in_progress' and work_started_at is null then now() else work_started_at end,
            resolution_submitted_at = case when new.status = 'needs_review' then now() else resolution_submitted_at end,
            resolved_at = case when new.status = 'resolved' then now() when new.status in ('in_progress', 'needs_review') then null else resolved_at end,
            escalated_at = case when new.status = 'escalated' then now() else escalated_at end,
            closed_at = case when new.status = 'closed' then now() else closed_at end,
            updated_at = now()
        where complaint_id = new.id;

        insert into public.complaint_lifecycle_events (complaint_id, old_status, new_status, actor_id, note)
        values (
            new.id, old.status, new.status,
            nullif(current_setting('voicecare.actor_id', true), '')::uuid,
            'Complaint status changed'
        );

        insert into public.notification_outbox (event_key, event_type, complaint_id, department_id, payload)
        values (
            'complaint:' || new.id::text || ':status:' || new.updated_at::text,
            'complaint_status_changed', new.id, new.department_id,
            jsonb_build_object('status', new.status)
        ) on conflict (event_key) do nothing;
    end if;
    return new;
end;
$$;

drop trigger if exists complaints_lifecycle_after_write on public.complaints;
create trigger complaints_lifecycle_after_write
after insert or update of status on public.complaints
for each row execute function public.voicecare_record_complaint_lifecycle();

-- Preserve the authenticated actor inside the same transaction so the lifecycle
-- audit trigger can record it without trusting a client-supplied identity.
create or replace function public.transition_complaint_status(
    p_complaint_id uuid,
    p_new_status text,
    p_changed_by uuid,
    p_note text default null
)
returns setof public.complaints
language plpgsql
security definer
set search_path = public
as $$
declare
    old_status text;
    updated_complaint public.complaints%rowtype;
    transition_time timestamptz := now();
begin
    if p_new_status not in ('received', 'assigned', 'in_progress', 'needs_review', 'resolved', 'escalated', 'closed') then
        raise exception 'Invalid complaint status';
    end if;
    perform set_config('voicecare.actor_id', coalesce(p_changed_by::text, ''), true);
    select status into old_status from public.complaints where id = p_complaint_id for update;
    if not found then raise exception 'Complaint not found'; end if;
    update public.complaints
    set status = p_new_status,
        updated_at = transition_time,
        resolved_at = case when p_new_status in ('resolved', 'closed') then transition_time else null end
    where id = p_complaint_id
    returning * into updated_complaint;
    insert into public.status_history (complaint_id, old_status, new_status, changed_by, note)
    values (p_complaint_id, old_status, p_new_status, p_changed_by,
        coalesce(p_note, format('Status changed from %s to %s', old_status, p_new_status)));
    return next updated_complaint;
end;
$$;

alter table public.complaint_sla_policies enable row level security;
alter table public.complaint_lifecycle_records enable row level security;
alter table public.complaint_lifecycle_events enable row level security;
alter table public.notification_outbox enable row level security;
revoke all on public.complaint_sla_policies, public.complaint_lifecycle_records,
    public.complaint_lifecycle_events, public.notification_outbox from public, anon, authenticated;
grant all on public.complaint_sla_policies, public.complaint_lifecycle_records,
    public.complaint_lifecycle_events, public.notification_outbox to service_role;
