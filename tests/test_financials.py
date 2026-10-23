import unittest
import sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from financial_data import annual_series, collect_financials, empty_financials, PE_URL, parse_public_pe, supplement_public, WSJ_URL

PE='<table id="datatable"><tr><th>Date</th><th>Value</th></tr>'+''.join(f'<tr><td>Jan 1, {y}</td><td>{y-2000}</td></tr>' for y in range(2020,2027))+'<tr><td>Oct 22, 2026</td><td>99</td></tr></table>'
EPS='<table><tr><th>Year</th><th>S&amp;P 500 EPS ($)</th></tr>'+''.join(f'<tr><td>{y}</td><td>{y-1800}</td></tr>' for y in range(2020,2027))+'</table>'
class FinancialTests(unittest.TestCase):
 def test_annual_observation(self):
  pe=annual_series(PE,'pe',date(2026,10,23));eps=annual_series(EPS,'eps',date(2026,10,23))
  self.assertEqual(pe['dates'][-1],'2026-01-01');self.assertNotIn(99,pe['values']);self.assertEqual(eps['values'][-1],226)
 def test_bad_table_fails(self):
  with self.assertRaises(ValueError):annual_series('<html>blocked</html>','pe')
 def test_stale_preserved_and_proxy_rejected(self):
  old=empty_financials();old['sp500_pe']=annual_series(PE,'pe',date(2026,10,23))
  def fail(url):raise OSError('offline')
  result=collect_financials(old,fail,lambda symbol:{'quoteType':'ETF','symbol':symbol,'trailingPE':30})
  self.assertEqual(result['sp500_pe']['values'],old['sp500_pe']['values']);self.assertEqual(result['sp500_pe']['status'],'stale');self.assertEqual(result['nasdaq_pe']['values'],[152,31]);self.assertEqual(result['nasdaq_pe']['status'],'archival')
 def test_native_snapshot_only_observed_year(self):
  def quote(symbol):return {'quoteType':'INDEX','symbol':symbol,'regularMarketTime':1704067200,'trailingPE':25,'epsTrailingTwelveMonths':100,'forwardPE':20,'epsForward':125}
  result=collect_financials(fetch_html=lambda url:PE if url==PE_URL else EPS,quote_loader=quote)
  self.assertEqual(result['dow_forward_eps']['dates'],['2024-01-01']);self.assertEqual(result['dow_forward_eps']['values'],[125]);self.assertGreater(len(result['sp500_pe']['dates']),1)
class PublicTableTests(unittest.TestCase):
 def test_table_dates_and_index_identity(self):
  html='<table><tr><th>10/22/26†</th></tr><tr><td>Dow Jones Industrial Average</td><td>21.14</td><td>24.74</td><td>19.78</td></tr></table><table><tr><th>10/16/26†</th></tr><tr><td>NASDAQ 100 Index</td><td>30.27</td><td>33.15</td><td>21.45</td></tr><tr><td>S&amp;P 500 Index</td><td>23.51</td><td>25.47</td><td>19.25</td></tr></table>'
  rows=parse_public_pe(html,date(2026,10,23))
  self.assertEqual(rows['dow_pe'],('2026-10-22',21.14))
  self.assertEqual(rows['sp500_forward_pe'],('2026-10-16',19.25))
  self.assertFalse(any('nasdaq' in k for k in rows))
  first=supplement_public(empty_financials(),lambda _:html)
  second=supplement_public(first,lambda _:html.replace('10/22/26','10/23/26'))
  self.assertEqual(len(second['dow_pe']['dates']),2)
  third=supplement_public(second,lambda _:'blocked')
  self.assertEqual(third['dow_pe']['dates'],second['dow_pe']['dates'])
  self.assertEqual(third['dow_pe']['status'],'stale')
  with self.assertRaises(ValueError):parse_public_pe(html,date(2020,1,1))
if __name__=='__main__':unittest.main()

