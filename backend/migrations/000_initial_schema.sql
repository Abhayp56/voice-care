-- Initial schema for a fresh 4BIT VoiceCare Supabase project.
-- Apply this before 001_atomic_complaint_number.sql and later migrations.
-- Backend operations use the service-role key; no public client table access is granted.

create extension if not exists pgcrypto;

create table if not exists public.departments (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    description text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.complaint_categories (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    default_priority text not null default 'medium'
        check (default_priority in ('low', 'medium', 'high', 'critical')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.department_mapping (
    id uuid primary key default gen_random_uuid(),
    category_id uuid not null references public.complaint_categories(id) on delete cascade,
    department_id uuid not null references public.departments(id) on delete restrict,
    created_at timestamptz not null default now(),
    unique (category_id)
);

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text not null,
    role text not null default 'department_staff'
        check (role in ('department_staff', 'department_head', 'hospital_admin', 'higher_authority')),
    department_id uuid references public.departments(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.complaints (
    id uuid primary key default gen_random_uuid(),
    complaint_number text not null unique,
    patient_name text,
    patient_phone text,
    description text not null,
    language text not null default 'en',
    category_id uuid not null references public.complaint_categories(id) on delete restrict,
    department_id uuid not null references public.departments(id) on delete restrict,
    priority text not null default 'medium'
        check (priority in ('low', 'medium', 'high', 'critical')),
    status text not null default 'received'
        check (status in ('received', 'assigned', 'in_progress', 'needs_review', 'resolved', 'escalated', 'closed')),
    assigned_to uuid references public.profiles(id) on delete set null,
    resolved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create table if not exists public.complaint_number_counter (
    year integer primary key check (year between 2000 and 9999),
    last_number integer not null check (last_number >= 0)
);
create index if not exists complaints_department_status_created_idx
    on public.complaints (department_id, status, created_at desc);
create index if not exists complaints_category_idx on public.complaints (category_id);

create table if not exists public.status_history (
    id uuid primary key default gen_random_uuid(),
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    old_status text,
    new_status text not null,
    changed_by uuid references public.profiles(id) on delete set null,
    note text,
    created_at timestamptz not null default now()
);
create index if not exists status_history_complaint_created_idx
    on public.status_history (complaint_id, created_at);

create table if not exists public.evidence (
    id uuid primary key default gen_random_uuid(),
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    file_path text not null,
    file_type text not null default 'image' check (file_type in ('image', 'document', 'note')),
    notes text,
    submitted_by uuid references public.profiles(id) on delete set null,
    verified_by uuid references public.profiles(id) on delete set null,
    verified_at timestamptz,
    created_at timestamptz not null default now()
);
create index if not exists evidence_complaint_created_idx on public.evidence (complaint_id, created_at desc);

create table if not exists public.escalations (
    id uuid primary key default gen_random_uuid(),
    complaint_id uuid not null references public.complaints(id) on delete cascade,
    department_id uuid not null references public.departments(id) on delete restrict,
    deadline timestamptz not null,
    escalated_at timestamptz not null default now(),
    reason text,
    resolved_at timestamptz
);

create table if not exists public.audit_logs (
    id uuid primary key default gen_random_uuid(),
    actor_id uuid references public.profiles(id) on delete set null,
    action text not null,
    table_name text not null,
    record_id uuid,
    details jsonb,
    created_at timestamptz not null default now()
);

-- Starter routing data. Review and adjust these departments/categories to match the hospital.
insert into public.departments (name, description) values
    ('Maintenance', 'Facilities, water, electricity, and equipment'),
    ('Sanitation', 'Cleanliness and waste management'),
    ('Pharmacy', 'Medicines and pharmacy services'),
    ('Administration', 'Beds, staffing, and general hospital services')
on conflict (name) do nothing;

insert into public.complaint_categories (name, default_priority) values
    ('Drinking Water', 'high'),
    ('Washroom Cleanliness', 'high'),
    ('Medicine Availability', 'high'),
    ('Bed Availability', 'medium'),
    ('Electricity Problem', 'high'),
    ('Staff Availability', 'medium')
on conflict (name) do nothing;

insert into public.department_mapping (category_id, department_id)
select c.id, d.id
from (values
    ('Drinking Water', 'Maintenance'),
    ('Washroom Cleanliness', 'Sanitation'),
    ('Medicine Availability', 'Pharmacy'),
    ('Bed Availability', 'Administration'),
    ('Electricity Problem', 'Maintenance'),
    ('Staff Availability', 'Administration')
) as routes(category_name, department_name)
join public.complaint_categories c on c.name = routes.category_name
join public.departments d on d.name = routes.department_name
on conflict (category_id) do nothing;

create or replace view public.public_complaints_view as
select c.complaint_number, d.name as department_name, k.name as category_name,
       c.status, c.created_at::date as submission_date
from public.complaints c
join public.departments d on d.id = c.department_id
join public.complaint_categories k on k.id = c.category_id;

create or replace view public.public_department_statistics as
select d.name as department_name,
       count(c.id)::bigint as total_complaints,
       count(c.id) filter (where c.status in ('resolved', 'closed'))::bigint as resolved_count,
       count(c.id) filter (where c.status not in ('resolved', 'closed'))::bigint as open_count
from public.departments d
left join public.complaints c on c.department_id = d.id
group by d.id, d.name;

-- Lock operational data behind the trusted backend. Service-role access bypasses RLS.
do $$
declare table_name text;
begin
    foreach table_name in array array[
        'departments', 'complaint_categories', 'department_mapping', 'profiles',
        'complaints', 'complaint_number_counter', 'status_history', 'evidence', 'escalations', 'audit_logs'
    ] loop
        execute format('alter table public.%I enable row level security', table_name);
        execute format('revoke all on public.%I from anon, authenticated', table_name);
        execute format('grant all on public.%I to service_role', table_name);
    end loop;
end $$;

revoke all on public.public_complaints_view, public.public_department_statistics from anon, authenticated;
grant select on public.public_complaints_view, public.public_department_statistics to service_role;

-- Create/refresh the private bucket expected by the backend. Storage writes use service_role.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('evidence', 'evidence', false, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set
    public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

notify pgrst, 'reload schema';
