"""Public index fundamentals; never substitute ETF/company figures for an index."""
from datetime import date, datetime, timezone
from copy import deepcopy
import math
import re
import urllib.request
from bs4 import BeautifulSoup

INDEXES = {'nasdaq': ('나스닥 종합', '^IXIC'), 'sp500': ('S&P 500', '^GSPC'), 'dow': ('다우 산업평균', '^DJI')}
METRICS = ('pe', 'eps', 'forward_pe', 'forward_eps')
PE_URL = 'https://www.multpl.com/s-p-500-pe-ratio/table/by-year'
EPS_URL = 'https://www.officialdata.org/us-economy/s-p-500-earnings'

def number(value, positive=False):
    try:
        v = float(str(value).replace(',', '').replace('$', '').strip())
        return v if math.isfinite(v) and (not positive or v > 0) else None
    except (TypeError, ValueError):
        return None

def empty_series(index, metric):
    return {'dates': [], 'values': [], 'source': '', 'source_url': '', 'retrieved_at': None,
            'basis': '', 'status': 'unavailable', 'reason': '검증된 공개 지수 자료가 아직 없습니다. ETF·개별기업 값으로 대체하지 않습니다.'}

def empty_financials():
    return {f'{index}_{metric}': empty_series(index, metric) for index in INDEXES for metric in METRICS}

def get_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (MacroLens public data reader)'})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode('utf-8')

def annual_series(html, metric, today=None):
    today = today or date.today()
    soup = BeautifulSoup(html, 'html.parser')
    if metric == 'pe':
        table = soup.find('table', id='datatable')
    else:
        table = next((t for t in soup.find_all('table') if 'S&P 500 EPS' in t.get_text(' ', strip=True) and 'Month' not in t.find('tr').get_text(' ', strip=True)), None)
    if table is None:
        raise ValueError('Expected annual table not found')
    rows = {}
    for row in table.find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in row.find_all('td')]
        if len(cells) < 2:
            continue
        if metric == 'pe':
            match = re.fullmatch(r'Jan 1, (\d{4})', cells[0])
        else:
            match = re.fullmatch(r'(\d{4})', cells[0])
        if not match:
            continue
        year = int(match.group(1)); dt = f'{year:04d}-01-01'
        val = number(cells[1], positive=(metric == 'pe'))
        if 1996 <= year and dt <= today.isoformat() and val is not None:
            rows[dt] = val
    if len(rows) < 5:
        raise ValueError('Annual data is incomplete')
    dates = sorted(rows)
    return {'dates': dates, 'values': [rows[d] for d in dates],
            'source': 'Multpl (S&P / Shiller)' if metric == 'pe' else 'OfficialData (S&P / Shiller 재게시)',
            'source_url': PE_URL if metric == 'pe' else EPS_URL,
            'basis': '매년 1월 1일 관측값 · 직전 12개월(TTM) 기준. 달력연도 결산 실적 또는 연평균이 아닙니다. EPS는 명목값입니다. 과거 공개 시점별 빈티지 자료가 아니므로 백테스트 신호로 사용하지 마세요.',
            'retrieved_at': datetime.now(timezone.utc).isoformat(), 'status': 'ok', 'reason': ''}

def collect_financials(previous=None, fetch_html=get_html, quote_loader=None):
    out = empty_financials()
    for key, old in (previous or {}).items():
        if key in out and isinstance(old, dict):
            out[key] = deepcopy(old)
    for metric, url in [('pe', PE_URL), ('eps', EPS_URL)]:
        key = 'sp500_' + metric
        try:
            out[key] = annual_series(fetch_html(url), metric)
        except Exception as error:
            out[key]['status'] = 'stale' if out[key].get('dates') else 'unavailable'
            out[key]['reason'] = '수집 실패 · 기존 관측값 유지' if out[key].get('dates') else '공개 연도별 자료 수집 실패'
            print('Financial annual:', key, type(error).__name__)
    if quote_loader is None:
        import yfinance as yf
        quote_loader = lambda symbol: yf.Ticker(symbol).get_info()
    fields = {'pe': ('trailingPE',), 'eps': ('epsTrailingTwelveMonths', 'trailingEps'),
              'forward_pe': ('forwardPE',), 'forward_eps': ('epsForward', 'forwardEps')}
    for index, (_, symbol) in INDEXES.items():
        try:
            info = quote_loader(symbol)
            if info.get('quoteType') != 'INDEX' or info.get('symbol') != symbol:
                raise ValueError('Not a verified index quote')
            stamp = info.get('regularMarketTime')
            dt = datetime.fromtimestamp(float(stamp), timezone.utc).date().isoformat()
            if dt > date.today().isoformat():
                raise ValueError('Future observation')
            for metric in METRICS:
                if index == 'sp500' and metric in ('pe', 'eps'):
                    continue  # preserve the consistent historical January series
                key = index + '_' + metric
                value = next((number(info.get(f), positive=metric.endswith('pe')) for f in fields[metric] if number(info.get(f), positive=metric.endswith('pe')) is not None), None)
                if value is None:
                    out[key]['status'] = 'stale' if out[key].get('dates') else 'unavailable'
                    out[key]['reason'] = '제공자가 이 지수의 해당 재무 값을 반환하지 않았습니다.'
                    continue
                old = out[key]; rows = dict(zip(old.get('dates', []), old.get('values', [])))
                rows[dt] = value
                annual = {}
                for d in sorted(rows):
                    annual[d[:4]] = (d, rows[d])
                pairs = sorted(annual.values())
                out[key] = {'dates': [p[0] for p in pairs], 'values': [p[1] for p in pairs],
                    'source': f'Yahoo Finance ({symbol}, INDEX)', 'source_url': f'https://finance.yahoo.com/quote/{symbol}/',
                    'retrieved_at': datetime.now(timezone.utc).isoformat(), 'status': 'ok', 'reason': '',
                    'basis': '수집 개시 이후 연도별 마지막 확보 관측값. 과거 연도는 소급 생성하지 않습니다. 실제 EPS·PER는 제공자의 TTM 값이며 예상치는 제공자의 Forward 값입니다. Forward 대상 기간은 제공자가 명시하지 않을 수 있습니다.'}
        except Exception as error:
            print('Financial quote:', symbol, type(error).__name__)
            for metric in METRICS:
                if index == 'sp500' and metric in ('pe', 'eps'):
                    continue
                key = index + '_' + metric
                out[key]['status'] = 'stale' if out[key].get('dates') else 'unavailable'
                out[key]['reason'] = '지수 재무정보 수집 실패 · 기존값 유지' if out[key].get('dates') else '검증된 무료 지수 재무정보를 확보하지 못했습니다.'
    return supplement_public(out, fetch_html)


WSJ_URL = 'https://www.wsj.com/market-data/stocks/peyields?eafs_enabled=false'

def parse_public_pe(html, today=None):
    """Read each table's own date; never map NASDAQ 100 to Composite."""
    today = today or date.today()
    result = {}
    for table in BeautifulSoup(html, 'html.parser').find_all('table'):
        match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{2})\b', table.get_text(' ', strip=True))
        if not match:
            continue
        dt = datetime.strptime(match[1], '%m/%d/%y').date()
        if dt > today:
            continue
        for tr in table.find_all('tr'):
            cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
            if len(cells) < 4:
                continue
            index = {'Dow Jones Industrial Average': 'dow', 'S&P 500 Index': 'sp500'}.get(cells[0])
            if not index:
                continue
            for metric, col in [('pe', 1), ('forward_pe', 3)]:
                if index == 'sp500' and metric == 'pe':
                    continue
                val = number(cells[col], positive=True)
                if val is not None:
                    result[index + '_' + metric] = (dt.isoformat(), val)
    if not result:
        raise ValueError('No dated index valuation rows')
    return result

def supplement_public(out, fetch_html=get_html):
    # Archival observations are dated year-end, not invented annual histories.
    for metric, values in [('pe', [152.0, 31.0]), ('eps', [27.0, 133.0])]:
        key = 'nasdaq_' + metric
        if not out[key].get('dates') or out[key].get('status') == 'archival' or 'Whitepaper' in out[key].get('source', ''):
            out[key] = dict(dates=['1999-12-31', '2013-12-31'], values=values,
                source='NASDAQ Composite Whitepaper (2014-04-02), p.6 Table 11 / Bloomberg',
                source_url='https://www.wsj.com/public/resources/documents/nasdaqcompretrospective.pdf',
                retrieved_at=datetime.now(timezone.utc).isoformat(), status='archival', reason='',
                sparse=True, badge='과거 2점',
                basis='1999년 말·2013년 말의 두 관측값만 있습니다. 연속 시계열이나 최신값이 아닙니다. MAX 또는 20Y/30Y 기간에서 점으로 표시합니다. EPS 항목은 원문의 Index Earnings(구성기업 이익 합계 ÷ 지수 divisor)이며 정수 반올림 값입니다. 결측 연도를 보간하지 않습니다.')
    keys = ['dow_pe', 'dow_forward_pe', 'sp500_forward_pe']
    try:
        rows = parse_public_pe(fetch_html(WSJ_URL))
        for key in keys:
            if key not in rows:
                raise ValueError('Missing expected public row: ' + key)
        for key, (dt, value) in rows.items():
            old = out[key]
            # Do not splice data from another provider with a different methodology.
            history = dict(zip(old['dates'], old['values'])) if old.get('source_url') == WSJ_URL else {}
            history[dt] = value
            dates = sorted(history)
            out[key] = dict(dates=dates, values=[history[d] for d in dates],
                source='WSJ / Birinyi Associates / Dow Jones Market Data', source_url=WSJ_URL,
                retrieved_at=datetime.now(timezone.utc).isoformat(), status='ok', reason='',
                sparse=True, badge='시점 자료',
                basis='공개 표의 기준일에 확보한 관측값입니다. 연간 결산값/연평균/완전한 과거 시계열이 아닙니다. 실제 PER는 TTM 보고이익 기준, 예상 PER는 향후 12개월 영업이익 추정 기준(금요일 주간 갱신)입니다. 예상값의 x축은 표 기준일이며 추정치 수정일과 다를 수 있습니다. 출처별 산식 차이가 있어 PER로 EPS를 역산하지 않습니다.')
    except Exception as error:
        print('Financial public table:', type(error).__name__)
        for key in keys:
            if out[key].get('source_url') == WSJ_URL:
                out[key]['status'] = 'stale'
                out[key]['reason'] = '공개 표 갱신 실패 · 이전 관측값 유지'
    return out
