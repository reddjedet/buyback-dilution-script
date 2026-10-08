import os
import sys

import matplotlib

matplotlib.use("Agg")  # sin ventana, solo guarda archivos
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

OUT_DIR = "/ruta/outputs/"  # se puede pisar por argumento
DEFAULT_TICKERS = [
    "AAPL",
    "AMZN",
    "MRK",
    "MSFT",
    "GOOGL",
    "META",
    "TSLA",
    "NVDA",
    "JPM",
    "V",
    "MA",
    "JNJ",
    "BRK-B",
    "PG",
    "UNH",
    "HD",
    "DIS",
    "BAC",
    "VZ",
    "ADBE",
    "KO",
    "PFE",
    "PEP",
    "COST",
    "PM",
    "DE",
    "UNP",
    "NU",
    "AMD",
    "CAT",
    "FCX",
    "MCD",
    "WMT",
    "INTC",
    "NEM",
    "LLY",
    "BMY",
    "ABBV",
    "TMO",
    "ABT",
    "CRWV",
    "ANET",
    "NBIS",
    "CEG",
    "SNDK",
    "RGTI",
    "PLTR",
    "GLW",
    "VST",
    "AVGO",
    "QCOM",
    "NEE",
    "XOM",
    "CVX",
]
YEARS = 5
REPORT_LAG_DAYS = 45
BG = "#ccb794"
TICKER_COLOR = "#c52821"


def compute(symbol, now):
    t = yf.Ticker(symbol)
    start = (now - pd.DateOffset(years=YEARS + 1)).strftime("%Y-%m-%d")
    s = t.get_shares_full(start=start)
    if s is None or s.empty:
        raise ValueError("Sin datos de acciones")
    s.index = s.index.tz_localize(None)
    s = s[~s.index.duplicated()]
    print(s.loc["2022-04-01":"2022-08-01"])

    # Ajuste por split: acciones previas * ratio de splits posteriores
    # sp = t.splits
    # if not sp.empty:
    #     sp.index = sp.index.tz_localize(None)
    #     s = s * pd.Series([sp[sp.index > d].prod() for d in s.index], index=s.index)
    #
    # s = s.resample("QE").last().ffill(limit=1)
    # s = s[s.index <= now - pd.Timedelta(days=REPORT_LAG_DAYS)]
    # y = (-s.pct_change(4) * 100).dropna().loc[now - pd.DateOffset(years=YEARS) :]
    # if y.empty:
    #     raise ValueError("Serie vacía tras el filtrado")
    # if (y.abs() > 25).any():
    #     print(f"[{symbol}] Alerta: |cambio| > 25%, revisar splits/datos")
    # return y
    s = s.resample("QE").last().ffill(limit=1)
    r = s / s.shift()
    f = r.where((r < 0.75) | (r > 1.33), 1.0).fillna(
        1.0
    )  # salto >25% = split/dato roto
    s = s * f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    med = s.rolling(5, center=True, min_periods=3).median()
    s = s.where(
        (s / med - 1).abs() < 0.015, med
    )  # nivel >1.5% fuera de la mediana local = dato malo
    s = s[s.index <= now - pd.Timedelta(days=REPORT_LAG_DAYS)]
    y = (-s.pct_change(4) * 100).dropna().loc[now - pd.DateOffset(years=YEARS) :]
    if y.empty:
        raise ValueError("Serie vacía tras el filtrado")
    if (y.abs() > 25).any():
        print(f"[{symbol}] Alerta: |cambio| > 25%, revisar splits/datos")
    return y


def plot(symbol, y, path):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set(ylabel="Reducción neta de acciones (% interanual)")
    ax.plot(
        y.index,
        y,
        color="black",
        lw=1.2,
        marker="o",
        ms=3,
        label="Recompra o dilución (% interanual)",
    )
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.axhline(
        y.mean(), color="gray", ls=":", lw=1.8, label=f"Promedio: {y.mean():.2f}%"
    )
    kw = {"alpha": 0.3, "interpolate": True}
    ax.fill_between(y.index, y, 0, where=y > 0, color="green", label="Buyback", **kw)
    ax.fill_between(y.index, y, 0, where=y < 0, color="crimson", label="Dilution", **kw)
    for d, v, c in [
        (y.idxmax(), y.max(), "green" if y.max() > 0 else "crimson"),
        (y.idxmin(), y.min(), "crimson" if y.min() < 0 else "green"),
        (y.index[-1], y.iloc[-1], "black"),
    ]:
        ax.scatter(d, v, color=c, zorder=3)
        ax.annotate(
            f"{v:.2f}%\n{d:%Y-%m-%d}",
            (d, v),
            textcoords="offset points",
            xytext=(0, 10 if v >= 0 else -28),
            ha="center",
            fontsize=8,
        )
    ax.set_xticks(y.index)
    ax.set_xticklabels(
        [f"{d:%Y-%m-%d}" for d in y.index], rotation=45, ha="right", fontsize=8
    )
    lo, hi = min(y.min(), 0), max(y.max(), 0)
    m = max((hi - lo) * 0.2, 0.5)
    ax.set_ylim(lo - m, hi + m)
    ax.set(
        ylabel="Reducción neta de acciones (% interanual)",
    )
    ax.grid(True, ls=":", alpha=0.5)
    ax.legend(loc="best", fontsize=8, facecolor=BG, framealpha=0.35)
    fig.text(
        0.99,
        0.01,
        "Fuente: yfinance | >0 = recompra neta, <0 = dilución",
        ha="right",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout()
    fig.subplots_adjust(top=0.90)
    fs = 13
    t1 = ax.text(
        0,
        1.02,
        symbol,
        transform=ax.transAxes,
        color=TICKER_COLOR,
        fontweight="bold",
        fontsize=fs,
    )
    t2 = ax.text(
        0,
        1.02,
        "Buyback Yield / Dilution - Quarterly",
        transform=ax.transAxes,
        fontsize=fs,
    )
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    aw = ax.get_window_extent(r).width
    w1, w2 = t1.get_window_extent(r).width, t2.get_window_extent(r).width
    x0 = (aw - w1 - w2 - 6) / 2 / aw
    t1.set_x(x0)
    t2.set_x(x0 + (w1 + 6) / aw)
    fig.savefig(path, format="jpg", dpi=150, facecolor=BG)
    plt.close(fig)


def main():
    args = sys.argv[1:]
    out_dir = args[0] if args else OUT_DIR
    tickers = [a.upper() for a in args[1:]] or DEFAULT_TICKERS
    os.makedirs(out_dir, exist_ok=True)
    now = pd.Timestamp.today().normalize()
    for sym in tickers:
        try:
            y = compute(sym, now)
            path = os.path.join(out_dir, f"{sym}_buyback_dilution.jpg")
            plot(sym, y, path)
            print(f"[{sym}] guardado: {path}")
        except Exception as e:  # noqa: BLE001
            print(f"[{sym}] error: {e}")


if __name__ == "__main__":
    main()
