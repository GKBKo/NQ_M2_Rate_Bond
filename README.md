# NASDAQ · M2 · 기준금리 · 글로벌 유동성 매크로 대시보드 (정적 웹 버전)

원본 Streamlit 앱을 **GitHub Pages에서 서버 없이** 동작하도록 이식한 버전입니다.
Macro Lens UI로 레이아웃과 차트 스타일을 개선했으며, 모바일 반응형 설정 패널을 지원합니다.

## 구성 파일
| 파일 | 설명 |
|---|---|
| `index.html` | 대시보드 본체 (data.json을 읽어 Plotly로 렌더) |
| `data.json` | 데이터 (GitHub Actions가 매일 자동 생성/갱신). 지금 든 것은 미리보기용 샘플 |
| `fetch_data.py` | Yahoo Finance + FRED에서 데이터를 받아 data.json 생성 |
| `requirements.txt` | fetch_data.py 실행에 필요한 패키지 |
| `.github/workflows/update.yml` | 매일 자동으로 data.json 갱신하는 워크플로 |

## 왜 이런 구조인가
GitHub Pages는 정적 호스팅이라 Streamlit(파이썬 서버)을 못 돌립니다.
브라우저에서 직접 Yahoo/FRED를 부르면 CORS로 차단됩니다(이전에 나스닥 로딩 실패 원인).
그래서 **GitHub Actions(서버)에서 파이썬으로 데이터를 받아 data.json으로 저장 → index.html이 같은 도메인의 data.json을 읽는** 방식으로 CORS 문제를 원천 제거했습니다.

## 배포 방법 (5단계)
1. GitHub에서 새 저장소 생성 (예: `nasdaq-macro-dashboard`)
2. 이 폴더의 파일 전부 업로드 (`.github` 폴더 포함해서 그대로)
3. 저장소 **Settings → Pages → Source: Deploy from a branch → main / (root)** 저장
4. 저장소 **Actions** 탭 → `Update dashboard data` → **Run workflow** 클릭 (첫 실데이터 생성)
5. 1~2분 뒤 `https://<사용자명>.github.io/<저장소명>/` 접속 → 완료

이후 매일 07:00(KST) 자동으로 최신 데이터로 갱신됩니다.

## 로컬에서 먼저 확인
- 동봉된 샘플 `data.json`이 있으므로, 로컬 웹서버로 `index.html`을 열면 바로 미리보기됩니다.
  (data.json은 fetch로 읽으므로 파일 더블클릭이 아니라 아래처럼 서버로 여세요)
```
cd 이_폴더
python -m http.server 8000
# 브라우저에서 http://localhost:8000 접속
```
- 실데이터 data.json을 직접 만들려면:
```
pip install -r requirements.txt
python fetch_data.py
```

## 재현된 원본 기능
- 분석기간(YTD/1·3·5·10·20·30Y/MAX + 직접 날짜)
- Y축 모드 4종(다중/동일/지수화/증감률), 다중축은 좌2·우5 개별 배정
- 나스닥 Line ↔ 봉차트, 로그 회귀채널 + 표준편차 배수 슬라이더
- 7개 지표 토글, 메트릭 카드, 좌상단 값박스 + 호버 추적
- 글로벌 유동성 프록시(Fed+ECB+BOJ USD환산 YoY, 시프트 없음)

## 표시 설정 변경
- 첫 실행 시 나스닥만 표시합니다. 다른 지표는 설정에서 선택할 수 있습니다.
- 회귀선과 표준편차 채널의 기본 설정은 유지합니다.
- 글로벌 유동성은 12개월 이동 없이 실제 관측 날짜에 표시하며, 선택한 시작일·종료일을 적용합니다.

## Macro Lens UI
- 차분한 청록색 차트와 은은한 회귀 채널 음영
- 나스닥 요약: 선택 기간 마지막 종가·기간 상승률·최고 및 최저 종가
- 차트 상단 기간 버튼과 차트를 가리지 않는 지표 값 표시
- 선택된 지표의 스타일 옵션만 노출, 축 설정은 접이식 패널로 정리
- 모바일 설정 패널, 기본 설정 복원 버튼
- 기존 나스닥 회귀·표준편차 계산 유지

## v1.1.0 — 2026-10-23
- 상단 소개 문구 및 나스닥 요약 영역 제거
- 브라우저 높이에 맞춰 차트 높이 자동 조절
- 날짜 입력을 라벨과 같은 줄에 배치하고 설정 패널 여백 축소
- 업데이트 날짜는 차트 하단에 표시
