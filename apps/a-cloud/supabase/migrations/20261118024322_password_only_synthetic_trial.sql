-- Owner-approved 2026-11-18: PASSWORD ONLY, synthetic Cloud trial only.
-- Target: IDEA / sunrise-stage1-trial / bnepekozzgymbvbjtltb.
-- Preserves originals, records, credentials and the historical Mac runtime.
begin;
alter table vault_private.admins add column if not exists password_only_trial boolean not null default false;

create or replace function vault_private.identity(p_actor uuid,p_session uuid,p_school text) returns uuid
language plpgsql security definer set search_path='' as $$
begin
  if coalesce(auth.role(),'')<>'service_role' or p_actor is null or p_session is null then
    raise sqlstate 'PT403' using message='Private A server credential required';
  end if;
  if not exists(
    select 1 from auth.sessions s join vault_private.admins a on a.user_id=s.user_id
    where s.id=p_session and s.user_id=p_actor and p_school=any(a.schools)
      and (s.not_after is null or s.not_after>now())
      and (s.aal='aal2' or (s.aal='aal1' and a.password_only_trial
        and a.schools=array['synthetic-cloud-stage1','synthetic-cloud-negative']::text[]))
  ) then
    raise sqlstate 'PT403' using message='Approved trial or MFA session and school required';
  end if;
  return p_session;
end $$;

-- Fail closed on the wrong project/data: exactly one already-approved,
-- synthetic-only Admin with a synthetic .invalid email must exist.
do $$
declare n integer;
begin
  if (select count(*) from vault_private.admins)<>1 then
    raise exception 'Expected exactly one synthetic trial Admin';
  end if;
  update vault_private.admins a set password_only_trial=true
    where a.schools=array['synthetic-cloud-stage1','synthetic-cloud-negative']::text[]
      and exists(select 1 from auth.users u where u.id=a.user_id and u.email like '%.invalid');
  get diagnostics n=row_count;
  if n<>1 then raise exception 'Synthetic trial identity/scope not verified';end if;
end $$;
notify pgrst,'reload schema';
commit;

select 'PASSWORD_ONLY_SYNTHETIC_TRIAL_ENABLED' as result;
