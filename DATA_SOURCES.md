# 재무지표 추가 확보 결과 — v1.2.1
조사일: 2026-10-23 (한국시간). 숫자를 확인한 원자료만 반영했습니다.

| 지수 | 항목 | 포함 범위 | 원자료/한계 |
|---|---|---|---|
| 나스닥 종합 | PER | 1999년 말 152, 2013년 말 31 | NASDAQ Composite Whitepaper p.6 Table 11. 과거 2점만 있음 |
| 나스닥 종합 | EPS | 1999년 말 27, 2013년 말 133 | 같은 표의 Index Earnings: 구성기업 이익 합계 ÷ 지수 divisor. 정수 반올림 |
| 나스닥 종합 | 예상 PER / 예상 EPS | 미확보 | 연속 원자료를 검증하지 못함 |
| S&P 500 | PER / EPS | 1996–2026 각 1월 1일, 각 31점 | 기존 Multpl / OfficialData 자료 유지. TTM이며 달력연도 실적 아님 |
| S&P 500 | 예상 PER | 2026-10-16, 19.25 | WSJ / Birinyi. 향후 12개월 영업이익 추정 |
| S&P 500 | 예상 EPS | 미확보 | 공식 보고서 XLSX 경로가 현재 404. 다른 사이트의 OCR·역산치를 원자료로 혼용하지 않음 |
| 다우 산업평균 | PER | 2026-10-22, 21.14 | WSJ, TTM 보고이익 |
| 다우 산업평균 | 예상 PER | 표 기준일 2026-10-22, 19.78 | 예상치는 금요일 주간 갱신. 표 기준일과 추정 갱신일이 다를 수 있음 |
| 다우 산업평균 | EPS / 예상 EPS | 미확보 | 계산 정의가 일치하는 지수 EPS 원자료 미확보 |

## 확인한 출처
- NASDAQ Composite Whitepaper (2014-04-02), Bloomberg valuation table, p.6:
  https://www.wsj.com/public/resources/documents/nasdaqcompretrospective.pdf
- WSJ 공개 PER 표: https://www.wsj.com/market-data/stocks/peyields?eafs_enabled=false
- Barron's 동일 계열 표: https://www.barrons.com/market-data/stocks/us/pe-yields?eafs_enabled=false
  두 매체가 같은 제공자 자료를 사용하므로 독립적인 검증 자료로 계산하지 않음.
- S&P 500 PER: https://www.multpl.com/s-p-500-pe-ratio/table/by-year
- S&P 500 명목 EPS: https://www.officialdata.org/us-economy/s-p-500-earnings
- S&P DJI 공식 EPS 파일(이번 조사에서 HTTP 404): https://www.spglobal.com/spdji/en/documents/additional-material/sp-500-eps-est.xlsx
- Yardeni: https://yardeni.com/charts/us-stock-market/stock-market-valuation/stock-market-p-e-ratios
  장기 예상 PER/EPS 차트는 확인. 차트 이미지에서 숫자를 추정하여 시계열로 만들지 않음.
- GuruFocus 다우 PER: https://www.gurufocus.com/economic_indicators/6780/dow-30-pe-ratio
  과거 차트 제공, 데이터 다운로드는 Premium 표시. WSJ와 산식이 다른 수치를 연결하지 않음.
- Siblis 공개 API: https://siblisresearch.com/financial-data-api/
  실제 /api/v1/indices 응답 확인. 무료 목록에는 NDX(나스닥100)와 USA(자체 U.S. Large Cap)가 있지만 나스닥 종합/다우가 없음. S&P500으로도 임의 대체하지 않음.
- https://charts.allofthesewords.com/fwd_eps.html
  S&P500 예상 EPS를 PER와 가격으로 재구성하며 최근 값은 차트 OCR 사용을 명시. 직접 공표 EPS와 구분하여 미반영.

## 구현
- WSJ 표를 매번 수집하고 지수 이름과 각 표 기준일을 검증합니다. 나스닥100 행은 제외합니다.
- 신규 확보값을 관측일별로 누적합니다. 수집 실패 시 기존 숫자를 보존합니다.
- 과거 문헌 자료와 시점 자료는 점으로만 표시하며 사이를 보간하지 않습니다. 회귀선도 만들지 않습니다. 기존 다른 지표의 회귀/표준편차 설정은 유지합니다.
- 나스닥 2점은 기본 10Y 범위 밖입니다. MAX에서는 두 점, 20Y에서는 2013년 점을 확인할 수 있습니다.
- EPS를 지수÷PER로 임의 역산하지 않습니다. 제공자별 적자기업 처리·가중 방식·영업/보고이익 기준에 따라 동일 EPS가 아닐 수 있습니다.
- financial_observations.json은 포함된 관측값과 출처를 따로 확인하기 위한 자료입니다. 실행 데이터는 data.json입니다.

전체 항목을 채운 것으로 해석하면 안 됩니다. 12개 중 7개에 하나 이상의 관측값이 있고, 연속 연도별 자료는 2개뿐입니다.
