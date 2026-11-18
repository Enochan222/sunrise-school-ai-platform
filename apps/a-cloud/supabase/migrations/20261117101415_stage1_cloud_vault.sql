-- A-only Cloud variant. Apply only to the dedicated empty IDEA trial project.
begin;
create schema if not exists vault_private;
revoke all on schema vault_private from public, anon, authenticated;

create table vault_private.admins (
  user_id uuid primary key references auth.users(id),
  singleton boolean not null default true unique check(singleton),
  schools text[] not null check(cardinality(schools) between 1 and 2)
);
create table vault_private.sessions (
  session_id uuid primary key,
  actor_id uuid not null references vault_private.admins(user_id),
  school_id text not null,
  csrf text not null,
  updated_at timestamptz not null default now()
);
create table vault_private.shells (
  shell_id uuid primary key default gen_random_uuid(),
  school_id text not null,
  actor_id uuid not null references vault_private.admins(user_id),
  op_key text not null check(op_key ~ '^[A-Za-z0-9_-]{1,80}$'),
  payload jsonb not null,
  notebook_id text not null unique default ('notebook:'||gen_random_uuid()::text),
  archived boolean not null default false,
  created_at timestamptz not null default now(),
  unique(actor_id,school_id,op_key),
  unique(shell_id,school_id,notebook_id)
);
create table vault_private.sources (
  source_id text primary key default ('source:'||gen_random_uuid()::text),
  shell_id uuid not null,
  school_id text not null,
  notebook_id text not null,
  actor_id uuid not null references vault_private.admins(user_id),
  op_key text not null check(op_key ~ '^[A-Za-z0-9_-]{1,80}$'),
  metadata jsonb not null,
  sha256 text not null check(sha256 ~ '^[0-9a-f]{64}$'),
  original_path text not null unique,
  cipher_sha256 text check(cipher_sha256 ~ '^[0-9a-f]{64}$'),
  full_text text check(octet_length(full_text)<=1048576),
  state text not null default 'PENDING' check(state in ('PENDING','READY')),
  version integer not null default 1 check(version=1),
  created_at timestamptz not null default now(),
  unique(actor_id,school_id,op_key),
  foreign key(shell_id,school_id,notebook_id)
    references vault_private.shells(shell_id,school_id,notebook_id),
  check(state<>'READY' or (full_text is not null and length(btrim(full_text))>0 and cipher_sha256 is not null))
);
create index sources_scope on vault_private.sources(school_id,shell_id,state);
alter table vault_private.admins enable row level security;
alter table vault_private.sessions enable row level security;
alter table vault_private.shells enable row level security;
alter table vault_private.sources enable row level security;
revoke all on all tables in schema vault_private from public,anon,authenticated;

-- These helpers require the A service credential and a live Auth session.
-- The A server separately verifies the end-user JWT/signature/AAL and identity;
-- neither user-editable metadata nor a stale role claim authorizes data access.
create function vault_private.identity(p_actor uuid,p_session uuid,p_school text) returns uuid
language plpgsql security definer set search_path='' as $$
begin
  if coalesce(auth.role(),'')<>'service_role' or p_actor is null or p_session is null then
    raise sqlstate 'PT403' using message='Private A server credential required';
  end if;
  if not exists(select 1 from auth.sessions s where s.id=p_session and s.user_id=p_actor and s.aal='aal2'
        and (s.not_after is null or s.not_after>now()))
     or not exists(select 1 from vault_private.admins a where a.user_id=p_actor and p_school=any(a.schools)) then
    raise sqlstate 'PT403' using message='Admin MFA session or school denied';
  end if;
  return p_session;
end $$;
create function vault_private.guard(p_actor uuid,p_session uuid,p_school text,p_csrf text) returns uuid
language plpgsql security definer set search_path='' as $$
declare sid uuid:=vault_private.identity(p_actor,p_session,p_school);
begin
  if not exists(select 1 from vault_private.sessions s where s.session_id=sid
    and s.actor_id=p_actor and s.school_id=p_school and s.csrf=p_csrf) then
    raise sqlstate 'PT403' using message='Session scope changed or CSRF invalid';
  end if;
  return sid;
end $$;
create function vault_private.shell_view(s vault_private.shells) returns jsonb
language sql immutable set search_path='' as $$
 select s.payload||jsonb_build_object('shell_id',s.shell_id,'school_id',s.school_id,
   'notebook_id',s.notebook_id,'archived',s.archived)
$$;
create function vault_private.source_view(s vault_private.sources) returns jsonb
language sql immutable set search_path='' as $$
 select s.metadata||jsonb_build_object('source_id',s.source_id,'shell_id',s.shell_id,
  'school_id',s.school_id,'notebook_id',s.notebook_id,'state',s.state,
  'sha256',s.sha256,'version',s.version,'original_path',s.original_path,'cipher_sha256',s.cipher_sha256,
  'initial_version_id',encode(extensions.digest(convert_to(replace(jsonb_build_array(s.source_id,s.sha256)::text,', ',','),'UTF8'),'sha256'),'hex'),
  'rights_owner_actor_id',s.actor_id,'created_by_actor_id',s.actor_id,
  'original_mime_type','application/pdf','native_locator',s.source_id,
  'approved_sharing',false,'ai_usage_allowed',false,'ai_usage',false,'created_at',s.created_at)
$$;
create function public.vault_auth_session(p_actor uuid,p_session uuid) returns boolean
language plpgsql security definer set search_path='' as $$
begin
 if coalesce(auth.role(),'')<>'service_role'
 or not exists(select 1 from vault_private.admins a where a.user_id=p_actor)
 or not exists(select 1 from auth.sessions s where s.id=p_session and s.user_id=p_actor
  and (s.not_after is null or s.not_after>now())) then
  raise sqlstate 'PT401' using message='Live administrator session required';end if;
 return true;
end $$;
create function public.vault_open_session(p_actor uuid,p_session uuid,p_school text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare sid uuid:=vault_private.identity(p_actor,p_session,p_school); c text:=encode(extensions.gen_random_bytes(32),'hex');
begin
 insert into vault_private.sessions(session_id,actor_id,school_id,csrf) values(sid,p_actor,p_school,c)
 on conflict(session_id) do update set school_id=excluded.school_id,csrf=excluded.csrf,updated_at=now();
 return jsonb_build_object('school_id',p_school,'csrf_token',c,'actor_id',p_actor);
end $$;
create function public.vault_session(p_actor uuid,p_session uuid,p_school text,p_csrf text) returns jsonb
language plpgsql security definer set search_path='' as $$
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 return jsonb_build_object('school_id',p_school,'actor_id',p_actor,'csrf_token',p_csrf,
  'available_schools',(select to_jsonb(a.schools) from vault_private.admins a where a.user_id=p_actor));
end $$;
create function public.vault_switch_school(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_new_school text) returns jsonb
language plpgsql security definer set search_path='' as $$
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 return public.vault_open_session(p_actor,p_session,p_new_school);
end $$;
create function public.vault_list_shells(p_actor uuid,p_session uuid,p_school text,p_csrf text) returns jsonb
language plpgsql security definer set search_path='' as $$
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 return jsonb_build_object('shells',coalesce((select jsonb_agg(vault_private.shell_view(s)
 order by s.payload->>'academic_year',s.payload->>'grade',s.payload->>'subject',s.payload->>'curriculum_stream')
 from vault_private.shells s where s.school_id=p_school),'[]'::jsonb));
end $$;
create function public.vault_get_shell(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare s vault_private.shells;
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 select * into s from vault_private.shells where shell_id=p_shell and school_id=p_school;
 if not found then raise sqlstate 'PT404' using message='Shell not found'; end if;
 return vault_private.shell_view(s);
end $$;
create function public.vault_create_shell(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_key text,p_payload jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare s vault_private.shells; fresh boolean:=false; k text;
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 if p_key is null or p_key!~'^[A-Za-z0-9_-]{1,80}$' or jsonb_typeof(p_payload) is distinct from 'object'
 or (select count(*) from jsonb_object_keys(p_payload))<>4 then
  raise sqlstate 'PT422' using message='Invalid request'; end if;
 foreach k in array array['academic_year','grade','subject','curriculum_stream'] loop
  if jsonb_typeof(p_payload->k) is distinct from 'string' or length(btrim(p_payload->>k)) not between 1 and 48
    or (p_payload->>k)~'[[:cntrl:]]' then raise sqlstate 'PT422' using message='Invalid classification'; end if;
 end loop;
 if (p_payload->>'academic_year')!~'^[A-Za-z0-9._ -]{1,32}$'
 or length(p_payload->>'grade')>32 then raise sqlstate 'PT422' using message='Invalid classification';end if;
 insert into vault_private.shells(school_id,actor_id,op_key,payload)
 values(p_school,p_actor,p_key,p_payload) on conflict(actor_id,school_id,op_key) do nothing
 returning * into s;
 fresh:=found;
 if not fresh then select * into s from vault_private.shells where actor_id=p_actor and school_id=p_school and op_key=p_key;end if;
 if s.payload<>p_payload then raise sqlstate 'PT409' using message='Idempotency conflict';end if;
 return vault_private.shell_view(s)||jsonb_build_object('created',fresh);
end $$;
create function public.vault_archive_shell(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare s vault_private.shells;
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 update vault_private.shells set archived=true where shell_id=p_shell and school_id=p_school returning * into s;
 if not found then raise sqlstate 'PT404' using message='Shell not found';end if;
 return vault_private.shell_view(s);
end $$;
create function public.vault_reserve_source(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid,p_key text,p_metadata jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare sh vault_private.shells;s vault_private.sources; fresh boolean; id text:='source:'||gen_random_uuid()::text;k text;
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 select * into sh from vault_private.shells where shell_id=p_shell and school_id=p_school for update;
 if not found then raise sqlstate 'PT404' using message='Shell not found';end if;
 if sh.archived then raise sqlstate 'PT409' using message='Archived shell';end if;
 if p_key is null or p_key!~'^[A-Za-z0-9_-]{1,80}$' or jsonb_typeof(p_metadata) is distinct from 'object'
 or (select count(*) from jsonb_object_keys(p_metadata))<>5 then raise sqlstate 'PT422' using message='Invalid request';end if;
 foreach k in array array['title','license','retention','original_name','sha256'] loop
  if jsonb_typeof(p_metadata->k) is distinct from 'string' or length(btrim(p_metadata->>k)) not between 1 and 200
   or (p_metadata->>k)~'[[:cntrl:]]' then raise sqlstate 'PT422' using message='Invalid metadata';end if;
 end loop;
 if (p_metadata->>'sha256')!~'^[0-9a-f]{64}$' or length(p_metadata->>'license')>120
 or length(p_metadata->>'retention')>100 or length(p_metadata->>'original_name')>180
 or (p_metadata->>'original_name')~'[/\\]' or (p_metadata->>'original_name')!~*'\.pdf$' then
 raise sqlstate 'PT422' using message='Invalid original metadata';end if;
 insert into vault_private.sources(source_id,shell_id,school_id,notebook_id,actor_id,op_key,metadata,sha256,original_path)
 values(id,p_shell,p_school,sh.notebook_id,p_actor,p_key,p_metadata,p_metadata->>'sha256',
 p_school||'/'||p_shell::text||'/'||substring(id from 8)||'.bin')
 on conflict(actor_id,school_id,op_key) do nothing returning * into s;
 fresh:=found;
 if not fresh then select * into s from vault_private.sources where actor_id=p_actor and school_id=p_school and op_key=p_key;end if;
 if s.shell_id<>p_shell or s.metadata<>p_metadata then raise sqlstate 'PT409' using message='Idempotency conflict';end if;
 return vault_private.source_view(s)||jsonb_build_object('created',fresh);
end $$;
create function public.vault_finish_source(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid,p_source text,p_text text,p_cipher_sha text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare s vault_private.sources;sh vault_private.shells;
begin
 perform vault_private.guard(p_actor,p_session,p_school,p_csrf);
 select * into sh from vault_private.shells where shell_id=p_shell and school_id=p_school for update;
 if not found then raise sqlstate 'PT404' using message='Shell not found';end if;
 if sh.archived then raise sqlstate 'PT409' using message='Archived shell';end if;
 select * into s from vault_private.sources where source_id=p_source and shell_id=p_shell and school_id=p_school for update;
 if not found then raise sqlstate 'PT404' using message='Source not found';end if;
 if s.notebook_id<>sh.notebook_id then raise sqlstate 'PT403' using message='Source ownership mismatch';end if;
 if p_text is null or length(btrim(p_text))=0 or octet_length(p_text)>1048576
 or p_cipher_sha is null or p_cipher_sha!~'^[0-9a-f]{64}$' then raise sqlstate 'PT422' using message='Invalid extraction';end if;
 if s.state='READY' and (s.full_text<>p_text or s.cipher_sha256<>p_cipher_sha) then
 raise sqlstate 'PT409' using message='Original and index are immutable';end if;
 if not exists(select 1 from storage.objects o where o.bucket_id='sunrise-a-originals' and o.name=s.original_path) then
 raise sqlstate 'PT409' using message='Original storage receipt missing';end if;
 update vault_private.sources set full_text=p_text,cipher_sha256=p_cipher_sha,state='READY' where source_id=p_source returning * into s;
 return vault_private.source_view(s);
end $$;
create function public.vault_materials(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
begin
 perform public.vault_get_shell(p_actor,p_session,p_school,p_csrf,p_shell);
 return jsonb_build_object('materials',coalesce((select jsonb_agg(vault_private.source_view(s) order by s.created_at)
 from vault_private.sources s where s.school_id=p_school and s.shell_id=p_shell),'[]'::jsonb));
end $$;
create function public.vault_source(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid,p_source text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare s vault_private.sources;sh jsonb;
begin
 sh:=public.vault_get_shell(p_actor,p_session,p_school,p_csrf,p_shell);
 select * into s from vault_private.sources where source_id=p_source and school_id=p_school and shell_id=p_shell;
 if not found then raise sqlstate 'PT404' using message='Source not found';end if;
 if s.notebook_id<>sh->>'notebook_id' then raise sqlstate 'PT403' using message='Source ownership mismatch';end if;
 return vault_private.source_view(s);
end $$;
create function public.vault_search(p_actor uuid,p_session uuid,p_school text,p_csrf text,p_shell uuid,p_query text,p_limit integer default 20) returns jsonb
language plpgsql security definer set search_path='' as $$
declare sh jsonb;hits jsonb;
begin
 sh:=public.vault_get_shell(p_actor,p_session,p_school,p_csrf,p_shell);
 if p_query is null or length(btrim(p_query)) not between 1 and 300 or p_query~'[[:cntrl:]]'
 or p_limit is null or p_limit not between 1 and 50 then raise sqlstate 'PT422' using message='Nonempty scoped query required';end if;
 select coalesce(jsonb_agg(h),'[]'::jsonb) into hits from (
  select s.source_id,s.metadata->>'title' as title,1 as relevance
  from vault_private.sources s where s.school_id=p_school and s.shell_id=p_shell
   and s.notebook_id=sh->>'notebook_id' and s.state='READY'
   and strpos(lower(s.full_text),lower(btrim(p_query)))>0
  order by s.created_at limit p_limit) h;
 return jsonb_build_object('results',hits,'total_count',jsonb_array_length(hits),'search_type','text');
end $$;

-- Storage has no public or authenticated policies. Only this A project's
-- server-side service credential can fetch/write encrypted original bytes.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 values('sunrise-a-originals','sunrise-a-originals',false,4259840,array['application/octet-stream']);
revoke all on all functions in schema vault_private from public,anon,authenticated;

-- Explicitly revoke every newly created RPC from PUBLIC/anon/authenticated.
revoke all on function public.vault_auth_session(uuid,uuid) from public,anon,authenticated;
grant execute on function public.vault_auth_session(uuid,uuid) to service_role;
revoke all on function public.vault_open_session(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.vault_open_session(uuid,uuid,text) to service_role;
revoke all on function public.vault_session(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.vault_session(uuid,uuid,text,text) to service_role;
revoke all on function public.vault_switch_school(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.vault_switch_school(uuid,uuid,text,text,text) to service_role;
revoke all on function public.vault_list_shells(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.vault_list_shells(uuid,uuid,text,text) to service_role;
revoke all on function public.vault_get_shell(uuid,uuid,text,text,uuid) from public,anon,authenticated;
grant execute on function public.vault_get_shell(uuid,uuid,text,text,uuid) to service_role;
revoke all on function public.vault_create_shell(uuid,uuid,text,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.vault_create_shell(uuid,uuid,text,text,text,jsonb) to service_role;
revoke all on function public.vault_archive_shell(uuid,uuid,text,text,uuid) from public,anon,authenticated;
grant execute on function public.vault_archive_shell(uuid,uuid,text,text,uuid) to service_role;
revoke all on function public.vault_reserve_source(uuid,uuid,text,text,uuid,text,jsonb) from public,anon,authenticated;
grant execute on function public.vault_reserve_source(uuid,uuid,text,text,uuid,text,jsonb) to service_role;
revoke all on function public.vault_finish_source(uuid,uuid,text,text,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.vault_finish_source(uuid,uuid,text,text,uuid,text,text,text) to service_role;
revoke all on function public.vault_materials(uuid,uuid,text,text,uuid) from public,anon,authenticated;
grant execute on function public.vault_materials(uuid,uuid,text,text,uuid) to service_role;
revoke all on function public.vault_source(uuid,uuid,text,text,uuid,text) from public,anon,authenticated;
grant execute on function public.vault_source(uuid,uuid,text,text,uuid,text) to service_role;
revoke all on function public.vault_search(uuid,uuid,text,text,uuid,text,integer) from public,anon,authenticated;
grant execute on function public.vault_search(uuid,uuid,text,text,uuid,text,integer) to service_role;
notify pgrst,'reload schema';
commit;
