-- Store the browser's location snapshot alongside private resolution evidence.
-- This is an upload-time coordinate, not proof of photo authenticity or a ward geofence.
alter table public.evidence
  add column if not exists gps_latitude double precision check (gps_latitude between -90 and 90),
  add column if not exists gps_longitude double precision check (gps_longitude between -180 and 180),
  add column if not exists gps_accuracy_m double precision check (gps_accuracy_m > 0 and gps_accuracy_m <= 5000);

-- Public tracking only includes complaints submitted as resolved/closed.
create or replace view public.public_complaints_view as
select c.complaint_number, d.name as department_name, k.name as category_name,
       c.status, coalesce(c.resolved_at, c.updated_at)::date as submission_date
from public.complaints c
join public.departments d on d.id = c.department_id
join public.complaint_categories k on k.id = c.category_id
where c.status in ('resolved', 'closed');

revoke all on public.public_complaints_view from anon, authenticated;
grant select on public.public_complaints_view to service_role;

-- Aggregate public counts also exclude unresolved, unpublished complaints.
create or replace view public.public_department_statistics as
select d.name as department_name,
       count(c.id)::bigint as total_complaints,
       count(c.id)::bigint as resolved_count,
       0::bigint as open_count
from public.departments d
left join public.complaints c
  on c.department_id = d.id and c.status in ('resolved', 'closed')
group by d.id, d.name;
revoke all on public.public_department_statistics from anon, authenticated;
grant select on public.public_department_statistics to service_role;
notify pgrst, 'reload schema';
