import unittest
import sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from financial_data import annual_series, collect_financials, empty_financials, PE_URL

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
  self.assertEqual(result['sp500_pe']['values'],old['sp500_pe']['values']);self.assertEqual(result['sp500_pe']['status'],'stale');self.assertEqual(result['nasdaq_pe']['values'],[])
 def test_native_snapshot_only_observed_year(self):
  def quote(symbol):return {'quoteType':'INDEX','symbol':symbol,'regularMarketTime':1704067200,'trailingPE':25,'epsTrailingTwelveMonths':100,'forwardPE':20,'epsForward':125}
  result=collect_financials(fetch_html=lambda url:PE if url==PE_URL else EPS,quote_loader=quote)
  self.assertEqual(result['dow_forward_eps']['dates'],['2024-01-01']);self.assertEqual(result['dow_forward_eps']['values'],[125]);self.assertGreater(len(result['sp500_pe']['dates']),1)
if __name__=='__main__':unittest.main()
