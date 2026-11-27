-- Wallet reale di RadarSignal (pagina #wallet, radar/pages/wallet.html): posizioni eseguite davvero e loro movimenti.
-- Da eseguire una volta nel progetto Supabase: SQL Editor → New query → incolla questo file → Run (vedi supabase/LEGGIMI.md).
-- Sicurezza: la pagina usa solo la chiave pubblica "anon"; ogni riga appartiene a un utente (user_id = auth.uid()) e la
-- Row Level Security permette di leggere e scrivere soltanto le proprie righe. Lo script si può rieseguire senza perdere dati.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- posizioni
create table if not exists public.wallet_posizioni (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null default auth.uid() references auth.users (id) on delete cascade,
  asset         text not null check (char_length(asset) between 1 and 20),
  mercato       text not null default 'perp' check (mercato in ('spot', 'perp', 'opzione')),
  lato          text not null check (lato in ('long', 'short')),
  leva          numeric not null default 1 check (leva >= 1 and leva <= 200),
  exchange      text not null default 'Bitget' check (exchange in ('Bitget', 'OKX', 'altro')),
  stato         text not null default 'aperta' check (stato in ('aperta', 'chiusa')),
  strategia     text not null default 'fuori segnale' check (strategia in ('W3.2', 'scanner', 'fuori segnale')),
  segnale_data  date null,
  note          text null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------------------------------------------------------------- movimenti (ingressi, tranche DCA, riduzioni, chiusura)
create table if not exists public.wallet_movimenti (
  id            uuid primary key default gen_random_uuid(),
  posizione_id  uuid not null references public.wallet_posizioni (id) on delete cascade,
  user_id       uuid not null default auth.uid() references auth.users (id) on delete cascade,
  tipo          text not null check (tipo in ('ingresso', 'aggiunta', 'riduzione', 'chiusura')),
  data          timestamptz not null default now(),
  prezzo        numeric not null check (prezzo > 0),
  quantita      numeric not null check (quantita > 0),
  margine       numeric null check (margine is null or margine >= 0),
  commissioni   numeric not null default 0 check (commissioni >= 0),
  funding       numeric not null default 0,   -- pagato (+) o incassato (−), in dollari
  note          text null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ---------------------------------------------------------------- indici
create index if not exists wallet_posizioni_user_idx on public.wallet_posizioni (user_id, stato);
create index if not exists wallet_movimenti_user_idx on public.wallet_movimenti (user_id);
create index if not exists wallet_movimenti_pos_idx on public.wallet_movimenti (posizione_id, data);

-- ---------------------------------------------------------------- updated_at automatico
create or replace function public.wallet_set_updated_at() returns trigger
language plpgsql set search_path = public as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists wallet_posizioni_updated_at on public.wallet_posizioni;
create trigger wallet_posizioni_updated_at before update on public.wallet_posizioni
  for each row execute function public.wallet_set_updated_at();

drop trigger if exists wallet_movimenti_updated_at on public.wallet_movimenti;
create trigger wallet_movimenti_updated_at before update on public.wallet_movimenti
  for each row execute function public.wallet_set_updated_at();

-- un movimento può stare solo su una posizione dello stesso utente
create or replace function public.wallet_check_owner() returns trigger
language plpgsql set search_path = public as $$
begin
  if not exists (select 1 from public.wallet_posizioni p where p.id = new.posizione_id and p.user_id = new.user_id) then
    raise exception 'posizione non trovata';
  end if;
  return new;
end;
$$;

drop trigger if exists wallet_movimenti_owner on public.wallet_movimenti;
create trigger wallet_movimenti_owner before insert or update on public.wallet_movimenti
  for each row execute function public.wallet_check_owner();

-- ---------------------------------------------------------------- Row Level Security: ognuno vede e scrive solo le sue righe
alter table public.wallet_posizioni enable row level security;
alter table public.wallet_movimenti enable row level security;
alter table public.wallet_posizioni force row level security;
alter table public.wallet_movimenti force row level security;

drop policy if exists wallet_posizioni_select on public.wallet_posizioni;
drop policy if exists wallet_posizioni_insert on public.wallet_posizioni;
drop policy if exists wallet_posizioni_update on public.wallet_posizioni;
drop policy if exists wallet_posizioni_delete on public.wallet_posizioni;
create policy wallet_posizioni_select on public.wallet_posizioni for select to authenticated using (user_id = auth.uid());
create policy wallet_posizioni_insert on public.wallet_posizioni for insert to authenticated with check (user_id = auth.uid());
create policy wallet_posizioni_update on public.wallet_posizioni for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy wallet_posizioni_delete on public.wallet_posizioni for delete to authenticated using (user_id = auth.uid());

drop policy if exists wallet_movimenti_select on public.wallet_movimenti;
drop policy if exists wallet_movimenti_insert on public.wallet_movimenti;
drop policy if exists wallet_movimenti_update on public.wallet_movimenti;
drop policy if exists wallet_movimenti_delete on public.wallet_movimenti;
create policy wallet_movimenti_select on public.wallet_movimenti for select to authenticated using (user_id = auth.uid());
create policy wallet_movimenti_insert on public.wallet_movimenti for insert to authenticated with check (user_id = auth.uid());
create policy wallet_movimenti_update on public.wallet_movimenti for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy wallet_movimenti_delete on public.wallet_movimenti for delete to authenticated using (user_id = auth.uid());

-- nessun accesso per chi non ha fatto l'accesso
revoke all on public.wallet_posizioni from anon;
revoke all on public.wallet_movimenti from anon;
grant select, insert, update, delete on public.wallet_posizioni to authenticated;
grant select, insert, update, delete on public.wallet_movimenti to authenticated;
