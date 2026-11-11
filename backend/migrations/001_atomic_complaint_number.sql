-- Apply manually to the Supabase project after review. This file is not run by the app.
create or replace function public.next_complaint_number(p_year integer)
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
    allocated_number integer;
begin
    if p_year < 2000 or p_year > 9999 then
        raise exception 'Invalid complaint number year';
    end if;

    insert into public.complaint_number_counter as counter (year, last_number)
    values (p_year, 1)
    on conflict (year)
    do update set last_number = counter.last_number + 1
    returning last_number into allocated_number;

    return allocated_number;
end;
$$;

revoke all on function public.next_complaint_number(integer) from public;
revoke all on function public.next_complaint_number(integer) from anon;
revoke all on function public.next_complaint_number(integer) from authenticated;
grant execute on function public.next_complaint_number(integer) to service_role;
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

    select status into old_status
    from public.complaints
    where id = p_complaint_id
    for update;

    if not found then
        raise exception 'Complaint not found';
    end if;

    update public.complaints
    set status = p_new_status,
        updated_at = transition_time,
        resolved_at = case when p_new_status in ('resolved', 'closed') then transition_time else null end
    where id = p_complaint_id
    returning * into updated_complaint;

    insert into public.status_history (complaint_id, old_status, new_status, changed_by, note)
    values (
        p_complaint_id,
        old_status,
        p_new_status,
        p_changed_by,
        coalesce(p_note, format('Status changed from %s to %s', old_status, p_new_status))
    );

    return next updated_complaint;
end;
$$;

revoke all on function public.transition_complaint_status(uuid, text, uuid, text) from public;
revoke all on function public.transition_complaint_status(uuid, text, uuid, text) from anon;
revoke all on function public.transition_complaint_status(uuid, text, uuid, text) from authenticated;
grant execute on function public.transition_complaint_status(uuid, text, uuid, text) to service_role;
