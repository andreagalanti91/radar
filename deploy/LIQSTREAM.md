# Liquidazioni reali di Binance e Bybit: raccoglitore su una VM gratuita in Europa

**Perché serve.** Il radar gira su runner GitHub negli USA: da lì Binance futures e Bybit sono bloccati, e le loro liquidazioni
esistono solo come flussi WebSocket (nessun archivio REST pubblico). `radar/liqstream.py` resta collegato 24 ore su 24 a
Binance (`forceOrder`), Bybit (`allLiquidation.BTCUSDT`) e OKX (`liquidation-orders`) da una VM in Europa, salva ogni evento in
`data/liq_stream/AAAA-MM-GG/HH.csv` (stesse colonne di `data/liq_events`) e ogni ora fa commit e push sul repo. Il giro orario del
radar li legge da solo (`radar/liqsources.summary`, exchange `binance` e `bybit`); se la VM si ferma il radar continua con le
fonti REST e segnala "raccoglitore fermo".

Limite noto: Binance invia al massimo una liquidazione per simbolo al secondo (snapshot), quindi nelle cascate il totale Binance
è sottostimato; Bybit e OKX inviano tutto.

Costo: 0 € (Oracle Cloud Always Free). Tempo: circa 30–40 minuti la prima volta.

---

## 1. Creare la VM (Oracle Cloud Always Free)
1. Registrarsi su <https://www.oracle.com/cloud/free/> (serve una carta per la verifica, non viene addebitato nulla con le
   risorse "Always Free"). **Home region: Italy Northwest (Milan) o Germany Central (Frankfurt).** La home region non si cambia
   dopo e le risorse gratuite esistono solo lì.
2. Menu → Compute → Instances → **Create instance**.
   - Image: **Canonical Ubuntu 24.04**.
   - Shape: **VM.Standard.E2.1.Micro** (Always Free, 1 GB RAM: basta) oppure Ampere **VM.Standard.A1.Flex** 1 OCPU / 6 GB
     (se dice "out of capacity", riprovare più tardi o usare la E2.1.Micro).
   - Networking: lasciare la VCN proposta con **IP pubblico**.
   - SSH keys: "Upload public key" con la propria chiave pubblica del PC (`~/.ssh/id_ed25519.pub`; se non c'è:
     `ssh-keygen -t ed25519`).
3. Annotare l'IP pubblico e collegarsi: `ssh ubuntu@IP_DELLA_VM`. Non serve aprire porte in ingresso oltre a SSH.

## 2. Preparare il sistema
```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install git python3-venv
sudo timedatectl set-timezone UTC
# verifica che Binance e Bybit rispondano da qui (atteso 200; 451/403 = regione bloccata)
curl -s -o /dev/null -w "binance %{http_code}\n" https://fapi.binance.com/fapi/v1/ping
curl -s -o /dev/null -w "bybit %{http_code}\n" "https://api.bybit.com/v5/market/time"
```

## 3. Chiave di deploy (accesso in scrittura al SOLO repo radar)
Sulla VM:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/radar_deploy -N "" -C "liqstream-vm"
cat ~/.ssh/radar_deploy.pub
```
Su GitHub: repo **radar** → **Settings** → **Deploy keys** → **Add deploy key**:
- Title: `liqstream VM`
- Key: incollare la riga stampata da `cat` (inizia con `ssh-ed25519`)
- Spuntare **Allow write access** → **Add key**.

La chiave privata resta solo sulla VM (`~/.ssh/radar_deploy`); non va mai copiata nel repo né nei Secrets.
Per revocarla: stessa pagina → Delete.

## 4. Clonare il repo e installare
```bash
cd ~
GIT_SSH_COMMAND='ssh -i ~/.ssh/radar_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new' \
  git clone git@github.com:andreagalanti91/radar.git
cd ~/radar
git config core.sshCommand "ssh -i ~/.ssh/radar_deploy -o IdentitiesOnly=yes"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt websockets
```

## 5. Variabili d'ambiente (fuori dal repo)
```bash
sudo tee /etc/liqstream.env >/dev/null <<'EOF'
LIQSTREAM_SSH_KEY=/home/ubuntu/.ssh/radar_deploy
LIQSTREAM_BRANCH=claude/vibrant-brahmagupta-fvv2gh
EOF
sudo chmod 600 /etc/liqstream.env
```
Alternativa alla chiave di deploy: un token GitHub **fine-grained** limitato al repo radar con permesso *Contents: Read and
write* e scadenza, scritto come `LIQSTREAM_GIT_TOKEN=...` in `/etc/liqstream.env` al posto di `LIQSTREAM_SSH_KEY` (clonare
allora con `https://github.com/andreagalanti91/radar.git`). Il programma lo passa a git solo come header via variabili
d'ambiente: non compare nei log né nella riga di comando.

## 6. Prova a mano (2–3 minuti, senza push)
```bash
cd ~/radar
.venv/bin/python -m radar.liqstream --no-push
```
Atteso nel log: `binance: connesso`, `bybit: connesso`, `okx: connesso`. Gli eventi arrivano solo quando qualcuno viene
liquidato (con mercato calmo possono passare minuti). Fermare con Ctrl+C: viene scritto `data/liq_stream/.../HH.csv` dell'ora
in corso e `data/liq_stream/status.json`. Poi cancellare la prova: `rm -rf data/liq_stream`.

Se OKX si disconnette di continuo sulla porta 8443, aggiungere in `/etc/liqstream.env`
`LIQSTREAM_OKX_URL=wss://ws.okx.com/ws/v5/public`. Se Binance cambia indirizzo dei flussi, `LIQSTREAM_BINANCE_URL=...`.

## 7. Servizio permanente (systemd)
```bash
sudo cp ~/radar/deploy/liqstream.service /etc/systemd/system/liqstream.service
# se l'utente non è "ubuntu" o il repo è altrove, correggere User, WorkingDirectory ed ExecStart nel file
sudo systemctl daemon-reload
sudo systemctl enable --now liqstream
systemctl status liqstream
journalctl -u liqstream -f          # log dal vivo (Ctrl+C per uscire)
```
Il servizio si riavvia da solo se cade e al riavvio della VM; le connessioni si riaprono da sole (attesa 1 s → 60 s).
Ogni ora, ~20 secondi dopo hh:00: scrive i file delle ore chiuse, `git pull --rebase` e `git push` (solo `data/liq_stream`).

## 8. Verifica
- Dopo la prima ora intera: su GitHub compare `data/liq_stream/AAAA-MM-GG/HH.csv` con commit `liqstream: ...`.
- Al giro successivo del radar la sezione liquidazioni multi-exchange mostra anche `binance` e `bybit`.
- `data/liq_stream/status.json`: per exchange eventi, riconnessioni, ultimo messaggio.

## Manutenzione
- Aggiornare il codice: il `git pull` orario porta anche il codice nuovo ma il processo gira con quello vecchio:
  dopo modifiche a `radar/liqstream.py` eseguire `sudo systemctl restart liqstream`.
- Oracle può recuperare le istanze Always Free **inattive** per 7 giorni (CPU, rete e memoria molto basse): controllare una
  volta al mese che la VM sia accesa (`journalctl -u liqstream --since "1 hour ago"`). Se viene recuperata, rifare i passi 1–7
  (la chiave di deploy vecchia va cancellata su GitHub).
- Spazio: pochi KB l'ora; nessuna pulizia necessaria.
- Sicurezza: aggiornamenti automatici `sudo apt -y install unattended-upgrades`; nessuna porta aperta oltre a SSH.
