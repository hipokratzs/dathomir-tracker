# Dathomir R8 Tracker: como funciona

**Site:** https://hipokratzs.github.io/dathomir-tracker/
**Repositório:** https://github.com/hipokratzs/dathomir-tracker (conta pessoal hipokratzs)

## O que tem nesta pasta

| Arquivo | Para que serve |
|---|---|
| `index.html` | A página. Também abre direto no navegador (dois cliques), porque os dados ficam embutidos nela. |
| `config.json` | O que **você** edita à mão: metas, quem já entregou e as observações do Discord. |
| `data.json` | O que o **robô** grava: quem tem cada personagem em G13, 7★ e R6 ou mais. Não edite à mão. |
| `log.json` | O histórico que o **robô** grava: data, hora e quem subiu (ou desceu) de relíquia. Não edite à mão. |
| `update.py` | O robô. Lê os dados direto do jogo, grava `data.json` e `log.json` e atualiza a página. |
| `.github/workflows/update.yml` | O agendamento no GitHub, que roda o `update.py` a cada 15 minutos. |
| `_original/` | Cópia da primeira versão (a que lia do swgoh.gg). Fica só no seu PC, não vai para o GitHub. |

## O que a página mostra

1. **Resumo no topo:** quantos upgrades R8 faltam, quantos personagens estão abertos, quantos jogadores R7 estão a um passo.
2. **Um cartão por personagem:** quem já está em R8+, quem está em R7 (os primeiros a quem pedir) e R6.
3. **Discord summary:** a mensagem pronta no formato do canal #rote-platoon-needs (✅ 🟡 🔴 ❓, "Still needed", x/y), com botão **Copy**. Logo abaixo, o **R7 call-out** com os nomes de quem está a uma relíquia de cada personagem aberto.
4. **Change log:** cada vez que alguém sobe ou desce de relíquia num personagem da lista, aparece aqui com data e hora (no fuso de quem está vendo). Quem chega a R8 ganha ⭐.

Não há mais e-mail: o histórico na página substitui o aviso.

## De onde vêm os dados

O robô usa o **swgoh-comlink** (github.com/swgoh-utils/swgoh-comlink), que lê direto dos servidores do jogo. O swgoh.gg bloqueia robôs (Cloudflare, erro 403), então não serve. No GitHub, o comlink sobe sozinho a cada rodada como contêiner temporário; você não precisa de servidor. O dado é o do jogo na hora: subiu de relíquia, aparece na próxima rodada.

## Como a conta é feita

Para cada personagem, no `config.json`:

- `target`: quantos jogadores a guilda precisa ter em **R8 ou mais** no total.
- `needed`: quantos upgrades o Trash Panda pediu. É o "y" do "x/y" no resumo do Discord.
- `done`: quem já entregou antes do histórico automático começar (Maul e Snowtrooper). Quem subir daqui pra frente entra sozinho, pelo histórico.

O "x" do resumo é calculado: jogadores em R8+ hoje (mais os `reported`), menos os que já existiam antes do pedido (`target − needed`).

Metas atuais (`target` / `needed`): Maul 6/3, Savage 2/1, Jango Scion 8/3, Starkiller 12/1, NS Spirit 3/2, Dengar 4/2, NS Zombie 2/1, BT-1 2/1, Snowtrooper 3/1.

### Editando o `config.json`

Dá para editar direto no GitHub: abra o arquivo no repositório → ícone do lápis → *Commit changes*. A página reflete na próxima rodada (até 15 minutos) ou na hora, se você rodar o workflow (aba **Actions → Atualizar tracker → Run workflow**).

- Alguém avisou no Discord que chegou a R8 e o jogo ainda não mostra: coloque o nome em `"reported"`. Quando o dado chegar, o nome sai sozinho.
- Alguém se comprometeu a upar: `"pledged": ["Nome"]` (aparece como "committed" no Discord).
- Observação em aberto: `"check": "texto"` (o personagem fica com ❓ no resumo).
- Trash Panda aumentou um pedido (ex.: Jango de 3 para 4): some 1 em `target` **e** em `needed`.
- Personagem novo: `{"id": "BASE_ID", "name": "Nome", "short": "Nome curto", "target": N, "needed": N}`. O `BASE_ID` é o que aparece no fim da URL da busca do swgoh.gg (`#unit=BT1`).

## Rodar no seu computador (opcional)

Precisa do **Docker Desktop**, porque o comlink roda como contêiner:

1. `docker run -d --name comlink --restart unless-stopped -e APP_NAME=mythosaur-rote-tracker -p 3000:3000 ghcr.io/swgoh-utils/swgoh-comlink:latest`
2. Nesta pasta: `python update.py --dry-run` mostra o que mudou, sem gravar.

O GitHub já faz isso sozinho; esta parte é só para testes.

## Observações

- O GitHub costuma atrasar rodadas agendadas alguns minutos e, em horário de pico, pular uma ou outra.
- Cada rodada consulta a guilda e cada membro uma vez (cerca de 50 consultas), leva cerca de 1 minuto e não custa nada em repositório público.
- O GitHub pausa o agendamento se o repositório passar 60 dias sem alteração. Como o robô salva a cada mudança, só acontece se a guilda parar de upar. Se pausar, aparece um botão para reativar na aba Actions.
- Segurança: nenhum segredo fica no código. O gitleaks foi rodado em 14/11/2026 no histórico local, na pasta e no repositório público, sem achados.

## Planetas (abas)

O site tem uma aba por planeta, cada uma com link direto:
- `https://hipokratzs.github.io/dathomir-tracker/#dathomir`
- `https://hipokratzs.github.io/dathomir-tracker/#lothal`

No `config.json`, a lista `planets` define as abas e cada personagem tem `"planet": "dathomir"` ou `"lothal"`. Naves levam `"ship": true` e contam por estrelas (7★ = pronta, 6★ = "a um passo"), não por relíquia.

A lista de Lothal saiu do quadro de platoons do swgoh.gg (Rise of the Empire, Fase 4): 6 platoons, 90 vagas. Ali o `target` é o número de vagas de cada unidade.

Para um planeta novo: acrescente-o em `planets` e os personagens com `"planet": "<id>"`. Na primeira leitura, o robô não registra personagens novos no histórico, então não aparecem dezenas de "mudanças" falsas.

Se o robô mostrar "Aviso: ninguem da guilda tem XYZ", confira o ID no `config.json`.
