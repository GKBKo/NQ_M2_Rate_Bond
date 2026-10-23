import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('stock_server',Path(__file__).resolve().parents[1]/'server.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class StockTests(unittest.TestCase):
 def fixture(self):
  return {'chart':{'result':[{'meta':{'symbol':'AAPL','instrumentType':'EQUITY','currency':'USD','exchangeName':'NMS','gmtoffset':-18000},'timestamp':[1704205800,1704292200,1704378600],'indicators':{'quote':[{'open':[100,None,102],'high':[103,None,105],'low':[99,None,101],'close':[102,None,104]}]}}]}}
 def test_only_complete_daily_bars(self):
  data=module.parse_history(self.fixture(),'AAPL');self.assertEqual(data['values'],[102,104]);self.assertEqual(len(data['dates']),2)
 def test_reject_foreign_fund_and_wrong_symbol(self):
  for key,val in [('currency','JPY'),('exchangeName','JPX'),('instrumentType','ETF'),('symbol','MSFT')]:
   raw=self.fixture();raw['chart']['result'][0]['meta'][key]=val
   with self.assertRaises(ValueError):module.parse_history(raw,'AAPL')
 def test_symbol_validation(self):
  for symbol in ['AAPL','BRK-B','AISP']:self.assertTrue(module.valid_symbol(symbol))
  for symbol in ['../file','AAPL?x=1','^IXIC','005930.KS<script>','']:self.assertFalse(module.valid_symbol(symbol))
 def test_search_filters(self):
  original=module.upstream
  module.upstream=lambda *_:{'quotes':[{'symbol':'AAPL','quoteType':'EQUITY','exchange':'NMS','longname':'Apple'},{'symbol':'SPY','quoteType':'ETF','exchange':'PCX'},{'symbol':'7203.T','quoteType':'EQUITY','exchange':'JPX'}]}
  try:self.assertEqual([r['symbol'] for r in module.search('Apple')],['AAPL'])
  finally:module.upstream=original
if __name__=='__main__':unittest.main()
