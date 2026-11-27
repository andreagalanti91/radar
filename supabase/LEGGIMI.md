# Wallet reale · configurazione di Supabase

La pagina **Wallet** della dashboard (`#wallet`, file `radar/pages/wallet.html`) registra le posizioni eseguite davvero.
I dati stanno nel progetto Supabase `https://shahrgciutsoxxaukwbp.supabase.co`: accesso con email e password, ogni account
vede solo i propri dati (Row Level Security). La pagina non permette di registrarsi: gli account si creano dal pannello.

Il collegamento è già nel repository: `radar/wallet_config.json` contiene l'URL del progetto e la chiave **publishable**
(`sb_publishable_…`), pubblica per design: la sicurezza la dà la RLS. La chiave segreta (`sb_secret_…` / `service_role`)
non va mai copiata nel repository, nella pagina o nei segreti di GitHub.

## Passi da fare una volta (pannello Supabase)

### 1. Tabelle e regole di accesso

**SQL Editor → New query** → incolla **tutto** il file `supabase/schema.sql` → **Run**.

Crea `wallet_posizioni` e `wallet_movimenti`, indici, aggiornamento automatico di `updated_at`, RLS attiva su entrambe con le
regole "solo le righe con `user_id = auth.uid()`" per lettura, inserimento, modifica ed eliminazione. Lo script è unico e
idempotente: si può rieseguire senza perdere dati (tabelle `if not exists`, policy cancellate e ricreate).

Controllo: **Table Editor** → entrambe le tabelle senza l'avviso "RLS disabled".

### 2. Niente registrazioni pubbliche

**Authentication → Sign In / Providers → Email**:
- **Allow new users to sign up**: **disattivato** (nessuno può creare un account dalla pagina o con la chiave pubblica).
- Provider Email attivo: serve per l'accesso con password.
- **Confirm email**: può restare com'è; gli utenti creati a mano con "Auto Confirm User" non devono confermare nulla.

### 3. Utenti

**Authentication → Users → Add user → Create new user**: email e password, spunta **Auto Confirm User** → **Create user**.
Un account per persona: ognuno vede solo le sue posizioni. La password si cambia o si reimposta dallo stesso pannello.

## Uso

Aprire la dashboard → **Wallet** → email e password. Il pulsante **Esci** chiude la sessione su quel dispositivo.

## Cambiare progetto (facoltativo)

Si modifica `radar/wallet_config.json`, oppure si impostano in GitHub (**Settings → Secrets and variables → Actions**) i segreti
`RADAR_SUPABASE_URL` e `RADAR_SUPABASE_ANON`: se presenti entrambi sostituiscono il file (il giro orario `.github/workflows/daily.yml`
li passa a `radar/dashboard.py`). Senza URL e chiave la pagina mostra "Wallet non ancora configurato".

Anteprima senza Supabase (solo in locale): pagina generata aperta da `localhost` o da file con `?demo=1#wallet`: dati finti in memoria.

## Cosa salva la pagina

- `wallet_posizioni`: moneta, mercato (spot, perp, opzione), lato, leva, exchange, stato, strategia (W3.2, scanner, fuori segnale),
  data del segnale, note.
- `wallet_movimenti`: ingresso, aggiunta (tranche DCA), riduzione, chiusura, con data, prezzo, quantità, margine, commissioni,
  funding (pagato positivo, incassato negativo).
- Il capitale di partenza (valore del conto e calo massimo) sta nei metadati del proprio utente (`user_metadata.capitale`).
