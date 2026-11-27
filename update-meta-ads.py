"""
update-meta-ads.py
Chama a API do Meta Ads e salva meta-data.json
Roda diariamente via GitHub Actions
Conta: Duas Rodas — act_2044706169171045 (informada pelo Eric em 05/11/2026)
"""
import json, os, urllib.request, urllib.parse
from datetime import datetime, date

TOKEN    = os.environ['META_TOKEN']
ACCT     = os.environ.get('META_ACCT', 'act_2044706169171045')
OUT_FILE = 'meta-data.json'
FIELDS   = 'date_start,spend,impressions,reach,clicks,actions,action_values,cost_per_action_type'

def get_action_count(actions, action_type):
    if not actions: return 0
    for a in actions:
        if a.get('action_type') == action_type:
            return int(float(a.get('value', 0)))
    return 0

def get_action_amount(action_values, action_type):
    if not action_values: return 0.0
    for a in action_values:
        if a.get('action_type') == action_type:
            return round(float(a.get('value', 0)), 2)
    return 0.0

def get_cpp(cpa, action_type):
    if not cpa: return None
    for a in cpa:
        if a.get('action_type') == action_type:
            return round(float(a.get('value', 0)), 2)
    return None

since = os.environ.get('META_SINCE', '2026-10-01')   # início das vendas da temporada
until = date.today().strftime('%Y-%m-%d')

# Opcional: só campanhas cujo nome contenha este texto (ex.: "2RODAS").
# Vazio = conta inteira, igual ao FanFest.
CAMPAIGN_CONTAINS = os.environ.get('META_CAMPAIGN_CONTAINS', '').strip()

query = {
    'fields':         FIELDS,
    'time_increment': '1',
    'time_range':     json.dumps({'since': since, 'until': until}),
    'level':          'account',
    'limit':          '90',
    'access_token':   TOKEN,
}
if CAMPAIGN_CONTAINS:
    query['filtering'] = json.dumps([{'field': 'campaign.name', 'operator': 'CONTAIN', 'value': CAMPAIGN_CONTAINS}])
params = urllib.parse.urlencode(query)

url = f'https://graph.facebook.com/v20.0/{ACCT}/insights?{params}'
all_data = []

while url:
    with urllib.request.urlopen(url) as resp:
        result = json.loads(resp.read())
    all_data.extend(result.get('data', []))
    url = result.get('paging', {}).get('next')

parsed = []
for day in all_data:
    p = day['date_start'].split('-')   # YYYY-MM-DD → DD/MM
    parsed.append({
        'data':       f"{p[2]}/{p[1]}",
        'dataISO':    day['date_start'],   # YYYY-MM-DD, pra temporada que cruza o ano
        'leads':      get_action_count(day.get('actions'),         'lead'),
        'compras':    get_action_count(day.get('actions'),         'purchase'),
        'gasto':      round(float(day.get('spend', 0)), 2),
        'cpl':        get_cpp(day.get('cost_per_action_type'),     'lead'),
        'cpp':        get_cpp(day.get('cost_per_action_type'),     'purchase'),
        'valorConv':  get_action_amount(day.get('action_values'),  'purchase'),
        'impressoes': int(day.get('impressions', 0)),
        'alcance':    int(day.get('reach', 0)),
        'cliques':    int(day.get('clicks', 0)),
        'atc':        get_action_count(day.get('actions'),         'add_to_cart'),
        'lpViews':    get_action_count(day.get('actions'),         'landing_page_view'),
        'checkout':   get_action_count(day.get('actions'),         'initiate_checkout'),
    })

# ── Funil do site inteiro, pelo pixel [DR] REVISTA DUAS RODAS (não só quem veio de anúncio) ──
# Conta os eventos que o GTM do 2rodasclub.com dispara: ViewContent (página de compra),
# AddToCart, InitiateCheckout e Purchase. PageView não entra porque o pixel também está no site da revista.
PIXEL_ID    = os.environ.get('META_PIXEL', '584624378945680')
PIXEL_SINCE = os.environ.get('META_PIXEL_SINCE', '2026-11-26')   # GTM com o pixel novo publicado em 26/11/2026
EVENTOS     = {'ViewContent': 'viewContent', 'AddToCart': 'addToCart', 'InitiateCheckout': 'initiateCheckout', 'Purchase': 'purchase'}
pixel_dias, pixel_erro = {}, None
try:
    from datetime import timezone, timedelta
    brt = timezone(timedelta(hours=-3))
    ini = int(datetime.strptime(PIXEL_SINCE, '%Y-%m-%d').replace(tzinfo=brt).timestamp())
    fim = int(datetime.now(tz=brt).timestamp())
    passo = 7 * 86400   # a API devolve no máximo alguns dias de cada vez
    t = ini
    while t < fim:
        q = urllib.parse.urlencode({'aggregation': 'event', 'start_time': t, 'end_time': min(fim, t + passo), 'access_token': TOKEN})
        u = f'https://graph.facebook.com/v20.0/{PIXEL_ID}/stats?{q}'
        while u:
            with urllib.request.urlopen(u) as resp:
                res = json.loads(resp.read())
            for bloco in res.get('data', []):
                st = bloco.get('start_time', '')
                try:
                    hora = datetime.strptime(st[:19], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc).astimezone(brt)
                except ValueError:
                    continue
                dia = hora.strftime('%Y-%m-%d')
                for item in bloco.get('data', []):
                    chave = EVENTOS.get(item.get('value'))
                    if chave:
                        d = pixel_dias.setdefault(dia, {'dataISO': dia, 'viewContent': 0, 'addToCart': 0, 'initiateCheckout': 0, 'purchase': 0})
                        d[chave] += int(item.get('count', 0))
            u = res.get('paging', {}).get('next')
        t += passo
except Exception as e:   # sem permissão no pixel ou API fora do ar: o resto do dashboard segue funcionando
    pixel_erro = str(e)[:300]

output = {
    'updated': datetime.now().strftime('%d/%m/%Y %H:%M'),
    'account': 'Duas Rodas | ' + ACCT,
    'filtro':  CAMPAIGN_CONTAINS or 'conta inteira',
    'data':    parsed,
    'pixel':   sorted(pixel_dias.values(), key=lambda d: d['dataISO']),
    'pixelErro': pixel_erro,
}

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✓ {len(parsed)} dias salvos | Último: {parsed[-1]['data'] if parsed else 'N/A'}")
