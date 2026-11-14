# Dathomir R8 Tracker: como funciona e como publicar

## O que tem nesta pasta

| Arquivo | Para que serve |
|---|---|
| `index.html` | A página. Abre direto no navegador (dois cliques) e já mostra os dados mais recentes, porque eles ficam embutidos nela. |
| `config.json` | O que **você** edita à mão: a meta de R8 de cada personagem e as observações do Discord. |
| `data.json` | O que o **robô** grava: quem tem cada personagem em G13, 7★ e R6 ou mais. Não edite à mão. |
| `update.py` | O robô. Lê os dados direto do jogo, grava `data.json`, atualiza a página e manda e-mail quando algo muda. |
| `.github/workflows/update.yml` | O agendamento no GitHub, que roda o `update.py` a cada 15 minutos. |
| `_original/` | Cópia da primeira versão (a que lia do swgoh.gg). Pode apagar depois que tudo estiver funcionando. |

## De onde vêm os dados (mudou em 14/11/2026)

A primeira versão lia do swgoh.gg, mas o teste real mostrou que o site **bloqueia qualquer robô** (Cloudflare, erro 403), até rodando do seu PC. Por isso o robô agora usa o **swgoh-comlink** (github.com/swgoh-utils/swgoh-comlink), um serviço da comunidade que lê os dados direto dos servidores do jogo. É o que a maioria das ferramentas de guilda usa hoje.

Vantagens:
- não depende do swgoh.gg nem do humor da proteção dele;
- o dado é o do jogo **na hora**: subiu de relíquia, aparece na próxima rodada (por isso 15 minutos agora faz sentido);
- no GitHub, o comlink sobe sozinho a cada rodada, como um contêiner temporário. Você não precisa de servidor.

## Como a conta é feita

Para cada personagem, `config.json` diz quantos jogadores a guilda precisa ter em **R8 ou mais** (`target`). A página conta quantos já estão em R8+, soma quem avisou no Discord (`reported`) e mostra quantos ainda faltam.

Metas atuais: Maul 6, Savage 2, Jango Scion 8, Starkiller 12, NS Spirit 3, Dengar 4, NS Zombie 2, BT-1 2, Snowtrooper 3. Elas saíram da lista do Trash Panda somada a quem já estava em R8 no dia 7/11. Se ele mudar uma necessidade (como fez com o Jango, de 2 para 3), aumente o `target` na mesma quantidade.

### Editando o `config.json`

- Alguém avisou no Discord que chegou a R8 e o tracker ainda não mostra: coloque o nome em `"reported"`. Quando o dado chegar, o nome sai sozinho dessa lista na página.
- Alguém se comprometeu a upar: `"pledged": ["Nome"]`.
- Observação em aberto: `"check": "texto"`.
- Para um personagem novo (Lothal, por exemplo), acrescente `{"id": "BASE_ID", "name": "Nome", "target": N}`. O `BASE_ID` é o que aparece no fim da URL da busca do swgoh.gg (`#unit=BT1`).

No GitHub, dá para editar o `config.json` direto no site (abre o arquivo → ícone do lápis → *Commit changes*). A página reflete a mudança na próxima rodada do robô; para ver na hora, rode o workflow manualmente (passo 6).

## Publicar no GitHub Pages (grátis), atualizando sozinho

1. Crie uma conta pessoal no GitHub, com um e-mail pessoal (não o do hospital).
2. Crie um repositório **público** (o Pages gratuito exige isso; os dados de guilda já são públicos no jogo). Envie todos os arquivos desta pasta **incluindo a pasta `.github`**. Atenção: o Windows esconde pastas que começam com ponto, e o upload pelo navegador às vezes ignora. Confira se, no GitHub, aparece `.github/workflows/update.yml`. Se não aparecer, no repositório clique em **Add file → Create new file**, digite o nome `.github/workflows/update.yml` (as barras criam as pastas) e cole o conteúdo do arquivo.
3. **Settings → Pages:** em *Source*, escolha *Deploy from a branch*, depois a branch `main` e a pasta `/ (root)`. Em um ou dois minutos o site fica em `https://SEU-USUARIO.github.io/NOME-DO-REPO/`.
4. **Settings → Actions → General → Workflow permissions:** marque *Read and write permissions*. Sem isso, o robô não consegue salvar os dados novos.
5. **Settings → Secrets and variables → Actions:**
   - *Secrets*: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_TO` (veja a seção de e-mail).
   - *Variables*: `SITE_URL` com o link do site, para ele aparecer no e-mail.
6. **Aba Actions → Atualizar tracker → Run workflow** roda uma vez na hora. Abra o log do passo *Ler o jogo e atualizar dados* e confira os pontos da seção "Primeira execução" abaixo.

Depois disso ele roda sozinho a cada 15 minutos, salva quando algo muda e o site se atualiza.

## Primeira execução: o que conferir

- **Vai chegar um e-mail logo na primeira rodada.** O `data.json` atual foi montado à mão a partir do swgoh.gg em 14/11, que estava atrasado em relação ao jogo. A primeira leitura do jogo vai achar diferenças e avisar. É esperado; da segunda em diante só chega e-mail quando alguém mudar de relíquia.
- **Confira três ou quatro jogadores** contra o jogo ou o swgoh.gg. Se as relíquias vierem todas 2 níveis acima ou abaixo, ajuste a função `relic_level` no `update.py`.
- **Se der erro** "swgoh-comlink nao respondeu" ou "A guilda voltou com 0 membros", copie o log e me mande. O robô nunca grava dado ruim: se algo falhar no meio, ele aborta sem salvar e sem mandar e-mail.

## E-mail quando algo mudar

O robô manda e-mail só quando um jogador sobe ou desce de relíquia num personagem da lista, ou quando o total pendente muda. O e-mail diz quem mudou, quem chegou a R8 e o que ainda falta.

Com Gmail:
1. Ative a verificação em duas etapas na conta Google.
2. Crie uma **senha de app** em myaccount.google.com → Segurança → Senhas de app.
3. Preencha os secrets assim: `SMTP_HOST` = `smtp.gmail.com`, `SMTP_PORT` = `465`, `SMTP_USER` = seu Gmail, `SMTP_PASS` = a senha de app (nunca a senha normal), `EMAIL_TO` = para onde o aviso vai (pode ser mais de um, separados por vírgula).

Use um e-mail pessoal, não o do hospital. A senha de app fica só nos *Secrets* do GitHub, que ninguém consegue ler depois de salvo, nem você.

## Alternativa: rodar no seu computador

Só vale se você não quiser usar o GitHub. Precisa do **Docker Desktop** instalado, porque o comlink roda como contêiner:

1. `docker run -d --name comlink --restart unless-stopped -e APP_NAME=mythosaur-rote-tracker -p 3000:3000 ghcr.io/swgoh-utils/swgoh-comlink:latest`
2. Nesta pasta: `python update.py --dry-run` mostra o que mudou, sem gravar.
3. Agende `python update.py` no **Agendador de Tarefas** do Windows (iniciar em esta pasta, repetir a cada 15 minutos). Para e-mail, crie as variáveis `SMTP_HOST` etc. como variáveis de ambiente do usuário.

O caminho pelo GitHub é mais simples e não depende do PC ligado.

## Observações

- O GitHub costuma atrasar rodadas agendadas alguns minutos e, em horário de pico, pular uma ou outra. Para o tracker isso não faz diferença.
- Cada rodada consulta a guilda e cada membro uma vez (cerca de 50 consultas), leva uns 2 minutos e não custa nada em repositório público.
- O GitHub pausa o agendamento se o repositório passar 60 dias sem nenhuma alteração. Como o robô salva dados a cada mudança, isso só acontece se a guilda parar de upar. Se pausar, aparece um botão para reativar na aba Actions.
