# Buyback vs Dilution

Genera gráficos JPG de recompra neta o dilución de acciones (% interanual, por trimestre, últimos 5 años) usando `yfinance`.

## Requisitos

```bash
pip install yfinance matplotlib pandas pillow
```

Requiere pandas ≥ 2.2 (usa frecuencia `"QE"`).

## Uso

```bash
python buyback_dilution.py /ruta/absoluta/salida AMZN AAPL MRK
```

- Sin ruta: usa `OUT_DIR`.
- Sin tickers: usa `DEFAULT_TICKERS`.
- Salida: `TICKER_buyback_dilution.jpg` en la carpeta indicada (se crea si no existe).

## Configuración

Constantes al inicio del script: `OUT_DIR`, `DEFAULT_TICKERS`, `YEARS`, `REPORT_LAG_DAYS`, `BG` (fondo), `TICKER_COLOR`.

## Método

1. Acciones en circulación (`get_shares_full`), último dato de cada trimestre.
2. Detección de saltos >25% entre trimestres (splits o datos rotos) y reescalado de la serie previa.
3. Filtro de mediana móvil para eliminar datos de nivel anómalos.
4. Variación interanual (`pct_change(4)`), con signo invertido: **>0 = recompra neta, <0 = dilución**.
5. Se descartan trimestres con menos de 45 días desde el cierre (aún sin reportar).

## Limitaciones

- Mide cambio neto de acciones: incluye emisión por compensación en acciones, no solo recompras.
- yfinance puede traer huecos, series cortas o conteos erráticos. Revisar a mano:
  - ADRs y emisores extranjeros (YPF, PAM, VIST): poco confiables.
  - Clases duales (BRK-B) y acciones restringidas (TSLA).
  - IPOs recientes (NBIS, CRWV): historia insuficiente.
- Si aparece `Alerta: |cambio| > 25%`, esa imagen no es confiable.
- Los valores difieren unas décimas de sitios que usan acciones diluidas reportadas (p. ej. stockanalysis.com).
