# -*- coding: utf-8 -*-
"""
fetch_data.py
GitHub Actions에서 실행되어 원본 Streamlit 앱과 동일한 소스(Yahoo Finance + FRED)로
데이터를 받아 data.json 으로 저장한다. (브라우저 CORS 문제 없이 정적 사이트에서 로드)
"""
import json, time, sys
from datetime import date
import numpy as np
import pandas as pd

START = "1996-01-01"

# ── 나스닥 (Yahoo Finance → 실패 시 Stooq) ────────────────────────────────
def load_nasdaq():
    df = pd.DataFrame()
    try:
        import yfinance as yf
        for attempt in range(3):
            try:
                d = yf.download("^IXIC", start=START, progress=False, auto_adjust=False)
                if d is not None and not d.empty:
                    if isinstance(d.columns, pd.MultiIndex):
                        d.columns = d.columns.droplevel(1)
                    df = d
                    break
            except Exception as e:
                print("yfinance retry:", e)
            time.sleep(4 * (attempt + 1))
    except Exception as e:
        print("yfinance import/err:", e)

    if df is None or df.empty:
        try:
            import pandas_datareader.data as web
            d = web.DataReader("^IXIC", "stooq").sort_index()
            df = d
        except Exception as e:
            print("stooq err:", e)

    if df is None or df.empty:
        raise RuntimeError("나스닥 데이터를 불러오지 못했습니다.")

    for c in ["Open", "High", "Low", "Close"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Close"])
    df = df[df["Close"] > 100]
    return df

# ── FRED ──────────────────────────────────────────────────────────────────
def fred(series, start=START):
    import pandas_datareader.data as web
    return web.DataReader(series, "fred", start)

def load_fred():
    out = {}
    try: out["m2"] = fred("M2SL")["M2SL"]
    except Exception as e: print("M2:", e); out["m2"] = None
    try: out["fed"] = fred("FEDFUNDS")["FEDFUNDS"]
    except Exception as e: print("FEDFUNDS:", e); out["fed"] = None
    try: out["dgs10"] = pd.to_numeric(fred("DGS10")["DGS10"], errors="coerce").dropna()
    except Exception as e: print("DGS10:", e); out["dgs10"] = None
    try: out["dgs30"] = pd.to_numeric(fred("DGS30")["DGS30"], errors="coerce").dropna()
    except Exception as e: print("DGS30:", e); out["dgs30"] = None
    return out

def monthly_last(s):
    s = s.dropna()
    s.index = pd.to_datetime(s.index)
    g = s.groupby(s.index.to_period("M")).last()
    g.index = g.index.to_timestamp()
    return g

def load_global_liquidity():
    total = None
    try:
        walcl = fred("WALCL")["WALCL"]
        total = monthly_last(walcl) / 1000.0
    except Exception as e:
        print("WALCL:", e)
    try:
        ecb = monthly_last(fred("ECBASSETSW")["ECBASSETSW"])
        eurusd = monthly_last(fred("DEXUSEU")["DEXUSEU"])
        ecb_usd = (ecb * eurusd) / 1000.0
        total = ecb_usd if total is None else total.add(ecb_usd, fill_value=0)
    except Exception as e:
        print("ECB:", e)
    try:
        boj = monthly_last(fred("JPNASSETS")["JPNASSETS"]) * 100_000_000
        usdjpy = monthly_last(fred("DEXJPUS")["DEXJPUS"])
        boj_usd = (boj / usdjpy) / 1e9
        total = boj_usd if total is None else total.add(boj_usd, fill_value=0)
    except Exception as e:
        print("BOJ:", e)

    if total is None or total.dropna().empty:
        return None
    total = total.dropna().sort_index()
    yoy = (total.pct_change(12) * 100).dropna()
    return yoy

def ser(idx, vals):
    return {
        "dates": [pd.Timestamp(t).strftime("%Y-%m-%d") for t in idx],
        "values": [None if pd.isna(v) else float(v) for v in vals],
    }

def main():
    nd = load_nasdaq()
    fr = load_fred()
    liq_actual = load_global_liquidity()

    data = {"updated": date.today().strftime("%Y-%m-%d")}

    data["nasdaq"] = {
        "dates": [pd.Timestamp(t).strftime("%Y-%m-%d") for t in nd.index],
        "open":  [None if pd.isna(v) else float(v) for v in nd["Open"]]  if "Open"  in nd else [],
        "high":  [None if pd.isna(v) else float(v) for v in nd["High"]]  if "High"  in nd else [],
        "low":   [None if pd.isna(v) else float(v) for v in nd["Low"]]   if "Low"   in nd else [],
        "close": [None if pd.isna(v) else float(v) for v in nd["Close"]],
    }
    data["m2"]    = ser(fr["m2"].index,    fr["m2"].values)    if fr["m2"]    is not None else None
    data["fed"]   = ser(fr["fed"].index,   fr["fed"].values)   if fr["fed"]   is not None else None
    data["dgs10"] = ser(fr["dgs10"].index, fr["dgs10"].values) if fr["dgs10"] is not None else None
    data["dgs30"] = ser(fr["dgs30"].index, fr["dgs30"].values) if fr["dgs30"] is not None else None
    data["liquidity_actual"]  = ser(liq_actual.index,  liq_actual.values)  if liq_actual  is not None else None

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("data.json 저장 완료:", data["updated"],
          "| 나스닥", len(data["nasdaq"]["dates"]), "행")

if __name__ == "__main__":
    main()
