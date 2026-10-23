# Macro Lens v1.2.0

나스닥과 매크로·재무지표를 비교하는 GitHub Pages용 정적 대시보드입니다.

## v1.2.0 변경

- 차트 좌우/상하 축 가장자리의 드래그 핸들 비활성화.
- 커서 이동 시 마커를 다시 그리던 로직 제거. 값 표시줄 높이 고정 및 중복 크기 조절 방지.
- 지표 → 재무지표 아래 나스닥 종합 / S&P 500 / 다우 산업평균, 각 PER·EPS·예상 PER·예상 EPS 항목 추가.
- 설명을 원 안의 i 버튼으로 제공. 키보드/터치로도 열고 닫을 수 있습니다.
- 설정 자동 저장, 지금 저장, JSON 내보내기/불러오기, 기본값 복원.
- 기간·색상·굵기·선 종류·지표·축·차트 형태·회귀 설정·확대 범위 저장.
- 증감률을 시작 대비 변화율로 계산하고 지수화/수익률 모드에서 봉차트 단위 일치. 0 기준값은 결측 처리하고 0/음수 값은 선형 회귀 사용.

## 설정 사용법

왼쪽 **설정 저장** 메뉴에서 JSON 파일을 내보내거나 불러올 수 있습니다. 파일 경로를 저장하지 않으므로 폴더·PC·브라우저를 옮겨도 파일 선택으로 설정을 복원합니다. 파일에는 설정만 포함되며 시세·재무 데이터는 포함되지 않습니다.

조작할 때마다 같은 사이트의 브라우저 저장소(localStorage)에 자동 저장합니다. 창을 닫았다 열면 마지막 설정이 복원됩니다. 1Y/10Y 등의 기간 버튼은 최신 관측일 기준으로 기간을 유지하며, 날짜를 직접 입력하면 고정된 날짜를 유지합니다. 브라우저 데이터 삭제·시크릿 모드 종료 등으로 로컬 설정이 사라질 수 있으므로 파일 내보내기를 사용할 수 있습니다. 처음 사용하거나 기본값 복원 시 나스닥과 로그 회귀 ±1σ만 표시합니다. 유동성은 시프트하지 않습니다.

## 재무 자료의 범위

| 항목 | 포함/수집 방식 |
|---|---|
| S&P 500 PER | Multpl의 매년 1월 1일 TTM PER, 1996년 이후 |
| S&P 500 EPS | OfficialData의 S&P/Shiller 재게시 명목 EPS, 매년 1월 1일 TTM 관측값 |
| 나스닥 종합·다우 및 예상치 | Yahoo Finance에서 해당 INDEX 심볼과 필드를 실제로 반환하는 경우만 수집. 현재 패키지에서 확보하지 못한 항목은 미제공 표시 |

연도별 관측값은 해당 연도의 결산 EPS나 연평균 PER가 아닙니다. 과거 공개일별 빈티지 자료가 아니므로 당시 알려진 정보만 사용하는 백테스트에 바로 쓰지 마세요. 나스닥 종합은 ^IXIC이고, 다우는 ^DJI입니다. Nasdaq-100, QQQ/DIA ETF, NDAQ/DOW 개별기업 값으로 대체하지 않습니다. 예상 PER·EPS는 과거로 소급 생성하지 않으며 제공자의 Forward 기간 정의를 따릅니다.

출처:
- https://www.multpl.com/s-p-500-pe-ratio/table/by-year
- https://www.officialdata.org/us-economy/s-p-500-earnings
- https://finance.yahoo.com/
- https://fred.stlouisfed.org/

재무 데이터 갱신 실패 시 기존 관측값을 유지하고 상태/수집 시각을 각 ⓘ에서 확인할 수 있습니다. 외부 제공자가 필드를 제공하지 않거나 페이지 구조가 바뀌면 해당 항목은 미제공 또는 이전 자료 상태로 남습니다.

## 실행

압축을 풀고 폴더 안에서:

```bash
python -m http.server 8000
```

브라우저에서 http://localhost:8000 을 엽니다. HTML 파일 더블클릭은 data.json 로딩이 제한될 수 있습니다. Plotly는 CDN에서 로드하므로 인터넷이 필요합니다.

데이터를 갱신하려면:

```bash
pip install -r requirements.txt
python fetch_data.py
```

## GitHub Pages

폴더 내부 파일과 `.github` 폴더를 저장소 루트에 업로드합니다. 기존 설치에도 `settings.js`, `financial_data.py`, `requirements.txt`, `data.json`을 포함한 전체 변경 파일을 반영해야 합니다. Pages를 main / root로 설정하고 Actions의 Update dashboard data를 실행하면 됩니다. 워크플로는 한국시간 매일 오전 7시에 데이터 갱신을 예약합니다.

## 검증

```bash
node tests/settings.test.cjs
python -m unittest discover -s tests -p "test_*.py"
```

설정 왕복 변환·유효성 검사·저장 복원·커서 이벤트·재무 관측일 파싱·실패 시 기존 자료 유지 등을 확인합니다.
