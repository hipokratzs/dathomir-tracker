"""Atualiza o ROTE R8 Tracker (Dathomir, Lothal...) lendo os dados direto do jogo, pelo swgoh-comlink.

O swgoh.gg bloqueia acesso automatico (Cloudflare, erro 403), por isso o robo usa o
swgoh-comlink (github.com/swgoh-utils/swgoh-comlink), um servico que conversa com os
servidores do jogo. No GitHub Actions ele sobe sozinho como contêiner (ver update.yml).

Uso:
  python update.py              le o jogo, grava data.json, registra as mudancas em log.json e atualiza index.html
  python update.py --dry-run    le o jogo e mostra as mudancas, sem gravar nada
  python update.py --seed-only  so copia config.json, data.json e log.json para dentro do index.html

Variavel de ambiente: COMLINK_URL (padrao http://localhost:3000)
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
COMLINK = os.environ.get("COMLINK_URL", "http://localhost:3000").rstrip("/")
MIN_RELIC = 6  # guarda jogadores a partir de R6
MIN_STARS = 6  # naves: guarda a partir de 6 estrelas (7 = pronta para o platoon)
PAUSE = 0.3    # segundos entre jogadores
LOG_MAX = 500  # quantas rodadas com mudanca o historico guarda


def path(name):
    return os.path.join(HERE, name)


def load(name):
    with open(path(name), encoding="utf-8") as f:
        return json.load(f)


def save(name, obj):
    with open(path(name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def post(endpoint, payload, tries=3):
    body = json.dumps({"payload": payload, "enums": False}).encode()
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(f"{COMLINK}/{endpoint}", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if attempt == tries:
                raise RuntimeError(f"Falha em /{endpoint} {payload}: {e}") from e
            time.sleep(3 * attempt)


def wait_comlink(limit=180):
    """O comlink leva alguns segundos para subir; espera ate ele responder."""
    t0 = time.time()
    while True:
        try:
            post("metadata", {}, tries=1)
            return
        except Exception as e:
            if time.time() - t0 > limit:
                raise RuntimeError(f"swgoh-comlink nao respondeu em {COMLINK}: {e}")
            time.sleep(5)


def relic_level(unit):
    # No jogo, relic.currentTier 2 = R0, 3 = R1 ... (currentTier - 2).
    tier = (unit.get("relic") or {}).get("currentTier") or 0
    return max(0, tier - 2)


def fetch(cfg):
    wait_comlink()
    wanted = {u["id"] for u in cfg["units"]}
    ships = {u["id"] for u in cfg["units"] if u.get("ship")}
    out = {uid: [] for uid in wanted}
    seen = set()
    guild = post("guild", {"guildId": cfg["guild_id"], "includeRecentGuildActivityInfo": False})
    members = (guild.get("guild") or {}).get("member") or []
    if len(members) < 10:
        raise RuntimeError(f"A guilda voltou com {len(members)} membros; abortando para nao gravar dado ruim.")
    for m in members:
        p = post("player", {"playerId": m["playerId"]})
        name = p.get("name") or m.get("playerName") or m["playerId"]
        for unit in p.get("rosterUnit", []):
            uid = unit.get("definitionId", "").split(":")[0]
            if uid not in wanted:
                continue
            seen.add(uid)
            if uid in ships:
                stars = unit.get("currentRarity") or 0
                if stars >= MIN_STARS:
                    out[uid].append({"name": name, "stars": stars})
                continue
            if unit.get("currentTier") != 13 or unit.get("currentRarity") != 7:
                continue
            relic = relic_level(unit)
            if relic >= MIN_RELIC:
                out[uid].append({"name": name, "relic": relic})
        time.sleep(PAUSE)
    if not any(out.values()):
        raise RuntimeError("Nenhum personagem da lista encontrado em nenhum jogador; abortando.")
    for uid in sorted(wanted - seen):
        print(f"Aviso: ninguem da guilda tem {uid}. Confira se o ID no config.json esta certo.")
    for uid in out:
        out[uid].sort(key=lambda x: (-level(x), x["name"].lower()))
    return {
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "jogo (swgoh-comlink)",
        "members": len(members),
        "units": out,
    }


def level(entry):
    """Relic para personagens, estrelas para naves."""
    return entry["stars"] if "stars" in entry else entry["relic"]


def ready(u, entry):
    return entry.get("stars", 0) >= 7 if u.get("ship") else entry.get("relic", 0) >= 8


def missing(cfg, data):
    res = {}
    for u in cfg["units"]:
        ps = data["units"].get(u["id"], [])
        r8 = {p["name"] for p in ps if ready(u, p)}
        reported = [n for n in u.get("reported", []) if n not in r8]
        res[u["id"]] = max(0, u["target"] - len(r8) - len(reported))
    return res


def diff(cfg, old, new):
    lines, changes = [], []
    for u in cfg["units"]:
        uid, label, ship = u["id"], u["name"], bool(u.get("ship"))
        if uid not in old["units"]:
            continue  # personagem recem-adicionado: a primeira leitura nao conta como mudanca
        before = {p["name"]: level(p) for p in old["units"].get(uid, [])}
        after = {p["name"]: level(p) for p in new["units"].get(uid, [])}
        goal = 7 if ship else 8
        fmt = (lambda v: f"{v} estrelas" if v is not None else "abaixo de 6 estrelas") if ship else \
              (lambda v: f"R{v}" if v is not None else "abaixo de R6")
        for player in sorted(set(before) | set(after), key=str.lower):
            a, b = before.get(player), after.get(player)
            if a != b:
                star = f"  <<< chegou a {fmt(goal)}" if (b or 0) >= goal > (a or 0) else ""
                lines.append(f"{label}: {player} {fmt(a)} -> {fmt(b)}{star}")
                ch = {"unit": uid, "player": player, "from": a, "to": b}
                if ship:
                    ch["kind"] = "stars"
                changes.append(ch)
    m_old, m_new = missing(cfg, old), missing(cfg, new)
    known = [uid for uid in m_old if uid in old["units"]]  # ignora personagens recem-adicionados
    total_old, total_new = sum(m_old[k] for k in known), sum(m_new[k] for k in known)
    if total_old != total_new:
        lines.append(f"Total de upgrades pendentes: {total_old} -> {total_new}")
    return lines, changes


def embed_seeds(cfg, data, log):
    html_path = path("index.html")
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    def put(html, tag_id, obj):
        payload = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
        pattern = re.compile(r'(<script type="application/json" id="%s">)(.*?)(</script>)' % tag_id, re.S)
        if not pattern.search(html):
            raise RuntimeError(f"Bloco {tag_id} nao encontrado no index.html")
        return pattern.sub(lambda m: m.group(1) + payload + m.group(3), html, count=1)

    html = put(html, "seed-config", cfg)
    html = put(html, "seed-data", data)
    html = put(html, "seed-log", log)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def load_log():
    return load("log.json") if os.path.exists(path("log.json")) else []


def main():
    cfg = load("config.json")
    if "--seed-only" in sys.argv:
        embed_seeds(cfg, load("data.json"), load_log())
        print("index.html atualizado com config.json, data.json e log.json.")
        return
    old = load("data.json") if os.path.exists(path("data.json")) else None
    new = fetch(cfg)
    lines, changes = diff(cfg, old, new) if old else (["Primeira leitura."], [])
    print("\n".join(lines) if lines else "Nenhuma mudanca.")
    if "--dry-run" in sys.argv:
        return
    log = load_log()
    if changes:
        log.insert(0, {"time": new["updated"], "changes": changes})
        del log[LOG_MAX:]
        save("log.json", log)
    save("data.json", new)
    embed_seeds(cfg, new, log)


if __name__ == "__main__":
    main()
