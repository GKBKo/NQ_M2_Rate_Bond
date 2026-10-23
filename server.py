"""Local Macro Lens server: same-origin US equity search and daily prices."""
import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import re
import threading
import time
from urllib.parse import parse_qs, urlencode, urlparse, quote
from urllib.request import Request, urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent
EXCHANGES = {'NYQ', 'NMS', 'NGM', 'NCM', 'ASE', 'PCX', 'BTS', 'NYSE', 'NASDAQ', 'NYSEArca', 'NYSE American'}
ALIASES = {'애플':'AAPL','테슬라':'TSLA','엔비디아':'NVDA','마이크로소프트':'MSFT','아마존':'AMZN','구글':'GOOGL','알파벳':'GOOGL','메타':'META','브로드컴':'AVGO','팔란티어':'PLTR','블룸에너지':'BE','오라클':'ORCL','코히런트':'COHR','루멘텀':'LITE','비코':'VICR','오스터':'OUST','테라울프':'WULF','네비우스':'NBIS','코어위브':'CRWV','처브':'CB'}
CACHE = {}
LOCK = threading.Lock()

def upstream(path, params):
    url = 'https://query1.finance.yahoo.com/' + path + '?' + urlencode(params)
    req = Request(url, headers={'User-Agent':'Mozilla/5.0', 'Accept':'application/json'})
    with urlopen(req, timeout=20) as response:
        return json.load(response)

def valid_symbol(symbol):
    return isinstance(symbol, str) and bool(re.fullmatch(r'[A-Z][A-Z0-9.-]{0,14}', symbol))

def search(query):
    query = ALIASES.get(query.replace(' ', ''), query)
    raw = upstream('v1/finance/search', {'q':query, 'quotesCount':20, 'newsCount':0})
    results = []
    for row in raw.get('quotes', []):
        symbol = row.get('symbol', '')
        if row.get('quoteType') == 'EQUITY' and row.get('exchange') in EXCHANGES and valid_symbol(symbol):
            results.append({'symbol':symbol, 'name':row.get('longname') or row.get('shortname') or symbol, 'exchange':row.get('exchDisp') or row['exchange']})
    return results[:12]

def parse_history(raw, symbol):
    result = raw.get('chart', {}).get('result')
    if not result:
        raise ValueError('주가 자료가 없습니다.')
    result = result[0]; meta = result['meta']
    if meta.get('instrumentType') != 'EQUITY' or meta.get('currency') != 'USD' or meta.get('exchangeName') not in EXCHANGES or meta.get('symbol') != symbol:
        raise ValueError('미국 거래소에 상장된 USD 주식만 추가할 수 있습니다.')
    bars = result['indicators']['quote'][0]
    out = {k:[] for k in ['dates','values','open','high','low','close']}
    for i, stamp in enumerate(result.get('timestamp', [])):
        vals = [bars.get(k, [])[i] if i < len(bars.get(k, [])) else None for k in ['open','high','low','close']]
        if not all(isinstance(v, (int,float)) and math.isfinite(v) and v > 0 for v in vals):
            continue
        # Exchange-local calendar date; offset is sufficient for US regular-session daily bars.
        dt = datetime.fromtimestamp(stamp + meta.get('gmtoffset', -18000), timezone.utc).date().isoformat()
        out['dates'].append(dt); out['values'].append(vals[3])
        for k,v in zip(['open','high','low','close'], vals):out[k].append(v)
    if not out['dates']:raise ValueError('사용 가능한 일별 시세가 없습니다.')
    out.update(symbol=symbol, name=meta.get('longName') or meta.get('shortName') or symbol, source='Yahoo Finance', basis='일별 OHLC / Close. 배당 재투자 총수익이 아닙니다.', fetchedAt=datetime.now(timezone.utc).isoformat())
    return out

def history(symbol):
    if not valid_symbol(symbol):raise ValueError('티커 형식이 올바르지 않습니다.')
    key = ('history', symbol)
    with LOCK:old = CACHE.get(key)
    if old and time.time()-old[0] < 900:return old[1]
    data = parse_history(upstream('v8/finance/chart/'+quote(symbol, safe=''), {'period1':820454400,'period2':int(time.time())+86400,'interval':'1d','events':'history'}), symbol)
    with LOCK:CACHE[key] = (time.time(),data)
    return data

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, max-age=0')
        super().end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path not in ['/api/search','/api/history']:
            return super().do_GET()
        try:
            args = parse_qs(url.query)
            if url.path == '/api/search':
                q = args.get('q',[''])[0].strip()
                if not q or len(q)>100:raise ValueError('티커 또는 회사명을 입력하세요.')
                data = {'quotes':search(q)}
            else:data = history(args.get('symbol',[''])[0].upper())
            self.reply(200,data)
        except ValueError as error:self.reply(400,{'error':str(error)})
        except Exception:self.reply(502,{'error':'시세 제공자 연결 실패입니다. 잠시 후 다시 시도해 주세요.'})
    def reply(self,status,data):
        body = json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8793);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    for port in range(args.port,args.port+20):
        try:server=ThreadingHTTPServer(('127.0.0.1',port),partial(Handler,directory=str(ROOT)));break
        except OSError:continue
    else:raise SystemExit('사용 가능한 포트가 없습니다.')
    url=f'http://127.0.0.1:{port}/';print('Macro Lens v1.3.1:',url,flush=True)
    if not args.no_browser:threading.Timer(.5,lambda:webbrowser.open(url)).start()
    server.serve_forever()
