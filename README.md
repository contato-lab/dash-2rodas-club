# Dash 2 Rodas Club — Temporada 2026/27

Dashboard de vendas do camarote 2 Rodas Club (MotoGP Brasil, revista Duas Rodas). A Eventim não tem API, então a venda entra numa planilha preenchida à mão; o Meta Ads entra sozinho por um robô no GitHub Actions.

## Arquivos

- `dashboard-2rodas-club.html`: o dashboard. Feito a partir do molde do FanFest (`referencia-fanfest/`). Lê a planilha de vendas (CSV publicado) + `meta-data.json`. Tudo que muda de temporada fica no bloco `CONFIG` no começo do script: link do CSV, nome/preço/meta de cada produto (2Rodas Club R$ 7.280 e meta 1.250; Lounge Diogo Moreira R$ 8.900 e meta 250), marcos de campanha.
- `update-meta-ads.py` + `.github/workflows/update-meta.yml`: robô que puxa a conta Meta da Duas Rodas **act_2044706169171045** (conta informada pelo Eric em 05/11/2026; a temporada passada usava a act_1326431289216611) 3x por dia e grava `meta-data.json`. O JSON traz `dataISO` (data com ano) e o início da busca é `META_SINCE` (01/10/2026). `META_CAMPAIGN_CONTAINS` filtra por nome de campanha (ex.: `2RODAS`); vazio lê a conta inteira. Secret necessário no repo: `META_TOKEN`.
- `update-google-ads.py` + `.github/workflows/update-google-ads.yml`: robô de Google Ads, cópia adaptada do que roda no Festival Interlagos. Conta Duas Rodas **587-995-2911** (customer 5879952911) pela MCC da Lime (4736269396). Grava `google-ads-data.json` (dia a dia: gasto, impressões, cliques, conversões, valor de conversão, CTR, CPC, CPA, mais a lista de campanhas). `GOOGLE_ADS_SINCE` e `GOOGLE_ADS_CAMPAIGN_CONTAINS` funcionam igual ao Meta. Secrets necessários no repo (os mesmos nomes e valores do repo festival-interlagos-2026): `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`. Customer e MCC já estão no workflow.
- `meta-data.json`: o último arquivo gerado pelo robô da temporada passada (03/07/2026, conta antiga). Será substituído na primeira rodada do robô. `google-ads-data.json` ainda não existe; nasce na primeira rodada.
- `planilha-2rodas-club-2026-27-modelo.csv`: só o cabeçalho da planilha nova.
- `planilha-2rodas-club-2025-26-copia.csv`: cópia da planilha da temporada passada (152 linhas diárias de 02/10/2025 a 09/03/2026 + bloco por estado que soma 207). Original no Drive: https://drive.google.com/file/d/1ihE_t_8XPdOHpFEfZ2QaWGFE8_b5CHN2/view
- `referencia-fanfest/`: dashboard do FanFest MotoGP que serviu de molde (repo contato-lab/fanfest-dashboard).

## Planilha nova (Google Sheets)

Criada em 05/11/2026 na pasta "Dash 2 Rodas Club" do Drive:
https://docs.google.com/spreadsheets/d/1XERNYR4nJMb5FPOpRJj7IkDjOH_WnM4N0-hYYt3q8FQ/edit

Colunas (uma linha por venda ou por lote de vendas do dia):

| coluna | o que vai | obrigatório |
|---|---|---|
| data | dia da venda, sempre com ano: 10/11/2026 | sim |
| produto | `2Rodas Club` ou `Lounge` (qualquer texto com "lounge"/"diogo" vira Lounge; com "club"/"rodas"/"camarote" vira 2Rodas Club) | sim |
| quantidade | número de ingressos; em branco conta 1 | não |
| valor_unitario | em reais, ex.: 7280 ou 7.280,00; em branco usa o preço do CONFIG | não |
| estado | UF do comprador (SP, GO...); alimenta o gráfico por estado | não |
| observacao | texto livre; aparece na tabela e no tooltip do dia | não |

Linha com data vazia/inválida ou produto não reconhecido é ignorada e o dashboard avisa quantas foram.

## Pra colocar no ar

1. Na planilha: Arquivo → Compartilhar → Publicar na web → aba única → formato CSV → Publicar. Copiar o link.
2. No `dashboard-2rodas-club.html`, trocar `COLE_AQUI_O_LINK_DO_CSV_PUBLICADO` pelo link (em `CONFIG.vendasCsvUrl`).
3. No repo `contato-lab/dash-2rodas-club` (upload pelo site do GitHub, substituindo o arquivo inteiro): subir `dashboard-2rodas-club.html`, `update-meta-ads.py`, `update-google-ads.py`, `.github/workflows/update-meta.yml` e `.github/workflows/update-google-ads.yml`.
4. Settings → Secrets and variables → Actions: conferir `META_TOKEN` (último run em 03/07/2026) e criar os 4 secrets do Google Ads copiando do repo `festival-interlagos-2026` (secret não passa de um repo pro outro sozinho).
5. Settings → Pages → Deploy from branch `main` / root. O dashboard fica em `https://contato-lab.github.io/dash-2rodas-club/dashboard-2rodas-club.html`.
6. Actions → rodar à mão "Atualizar Meta Ads — 2 Rodas Club" e "Atualizar Google Ads — 2 Rodas Club" pra gerar os dois JSON da temporada.
7. Opcional: preencher `CONFIG.marcos` com datas de abertura de vendas e início de mídia, e `META_CAMPAIGN_CONTAINS` / `GOOGLE_ADS_CAMPAIGN_CONTAINS` com um pedaço do nome das campanhas do camarote, se as contas tiverem outras campanhas rodando junto.

Pra testar antes de publicar: abrir o HTML por um servidor local com `?csv=<link ou arquivo csv>` na URL (também aceita `?meta=` e `?google=`), que troca a fonte só naquela aba.
