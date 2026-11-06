"""
update-google-ads.py
Busca o dia a dia das campanhas no Google Ads e grava google-ads-data.json.
Roda 3x por dia via GitHub Actions. Mesmo esquema do robô do Festival Interlagos:
as credenciais (token de desenvolvedor, OAuth, MCC da Lime) são as mesmas, só muda a conta.

Conta: Duas Rodas — 587-995-2911 (customer 5879952911), MCC 4736269396.
"""
import json, os
from datetime import datetime, date

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

DEVELOPER_TOKEN   = os.environ['GOOGLE_ADS_DEVELOPER_TOKEN']
CLIENT_ID         = os.environ['GOOGLE_ADS_CLIENT_ID']
CLIENT_SECRET     = os.environ['GOOGLE_ADS_CLIENT_SECRET']
REFRESH_TOKEN     = os.environ['GOOGLE_ADS_REFRESH_TOKEN']
CUSTOMER_ID       = os.environ.get('GOOGLE_ADS_CUSTOMER_ID', '5879952911').replace('-', '')
LOGIN_CUSTOMER_ID = os.environ.get('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '4736269396').replace('-', '')

SINCE             = os.environ.get('GOOGLE_ADS_SINCE', '2026-10-01')        # início das vendas da temporada
CAMPAIGN_CONTAINS = os.environ.get('GOOGLE_ADS_CAMPAIGN_CONTAINS', '').strip()  # ex.: "2RODAS"; vazio = conta inteira
OUT_FILE          = 'google-ads-data.json'


def get_client():
    return GoogleAdsClient.load_from_dict({
        'developer_token':   DEVELOPER_TOKEN,
        'client_id':         CLIENT_ID,
        'client_secret':     CLIENT_SECRET,
        'refresh_token':     REFRESH_TOKEN,
        'login_customer_id': LOGIN_CUSTOMER_ID,
        'use_proto_plus':    True,
    })


def fetch(client):
    svc = client.get_service('GoogleAdsService')
    until = date.today().strftime('%Y-%m-%d')
    filtro = f"AND campaign.name LIKE '%{CAMPAIGN_CONTAINS}%'" if CAMPAIGN_CONTAINS else ''
    query = f"""
        SELECT
            campaign.id, campaign.name, campaign.status, segments.date,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM campaign
        WHERE segments.date BETWEEN '{SINCE}' AND '{until}'
            AND campaign.status != 'REMOVED'
            {filtro}
        ORDER BY segments.date ASC
    """
    por_dia, campanhas = {}, {}
    for batch in svc.search_stream(customer_id=CUSTOMER_ID, query=query):
        for row in batch.results:
            iso   = row.segments.date
            custo = row.metrics.cost_micros / 1_000_000
            d = por_dia.setdefault(iso, {'dataISO': iso, 'data': f'{iso[8:10]}/{iso[5:7]}',
                                         'gasto': 0.0, 'impressoes': 0, 'cliques': 0, 'conversoes': 0.0, 'valorConv': 0.0})
            d['gasto']      += custo
            d['impressoes'] += row.metrics.impressions
            d['cliques']    += row.metrics.clicks
            d['conversoes'] += row.metrics.conversions
            d['valorConv']  += row.metrics.conversions_value

            c = campanhas.setdefault(str(row.campaign.id), {'id': str(row.campaign.id), 'nome': row.campaign.name,
                                                             'status': row.campaign.status.name, 'gasto': 0.0,
                                                             'impressoes': 0, 'cliques': 0, 'conversoes': 0.0})
            c['gasto'] += custo; c['impressoes'] += row.metrics.impressions
            c['cliques'] += row.metrics.clicks; c['conversoes'] += row.metrics.conversions

    dias = []
    for d in sorted(por_dia.values(), key=lambda x: x['dataISO']):
        d['gasto']      = round(d['gasto'], 2)
        d['conversoes'] = round(d['conversoes'], 2)
        d['valorConv']  = round(d['valorConv'], 2)
        d['ctr']        = round(d['cliques'] / d['impressoes'] * 100, 2) if d['impressoes'] else 0
        d['cpc']        = round(d['gasto'] / d['cliques'], 2) if d['cliques'] else None
        d['cpa']        = round(d['gasto'] / d['conversoes'], 2) if d['conversoes'] else None
        dias.append(d)
    for c in campanhas.values():
        c['gasto'] = round(c['gasto'], 2); c['conversoes'] = round(c['conversoes'], 2)

    return {
        'updated':   datetime.now().strftime('%d/%m/%Y %H:%M'),
        'account':   'Duas Rodas | ' + CUSTOMER_ID,
        'filtro':    CAMPAIGN_CONTAINS or 'conta inteira',
        'since':     SINCE,
        'campanhas': sorted(campanhas.values(), key=lambda c: -c['gasto']),
        'data':      dias,
    }


def main():
    try:
        out = fetch(get_client())
    except GoogleAdsException as e:
        for err in e.failure.errors:
            print('Google Ads API:', err.message)
        raise
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    tot = sum(d['gasto'] for d in out['data'])
    print(f"✓ {OUT_FILE}: {len(out['data'])} dias desde {SINCE}, R$ {tot:,.2f}, {len(out['campanhas'])} campanha(s) ({out['filtro']})")


if __name__ == '__main__':
    main()
