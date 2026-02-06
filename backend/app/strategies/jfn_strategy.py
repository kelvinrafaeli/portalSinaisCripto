"""
Portal Sinais - Estrategia JFN
EMA rapida/lenta com filtro de assertividade baseado em simulacao de trades.
"""
from typing import Optional, List, Tuple
import pandas as pd

from app.strategies.base import BaseStrategy, SignalResult


class JFNStrategy(BaseStrategy):
    """
    Estrategia JFN baseada em:
    - Cruzamento de EMA rapida e EMA lenta
    - Filtro de assertividade (TP/SL simulado, sem exibir SL/TP no alerta)

    LONG: EMA rapida cruza acima da EMA lenta
    SHORT: EMA rapida cruza abaixo da EMA lenta
    """

    def __init__(self, **params):
        super().__init__(**params)
        self.fast_length = params.get("fast_length", 20)
        self.slow_length = params.get("slow_length", 50)
        self.take_pct = params.get("take_pct", 1.6)
        self.stop_pct = params.get("stop_pct", 0.8)
        self.max_hold_bars = params.get("max_hold_bars", 120)
        self.count_timeout_as_loss = params.get("count_timeout_as_loss", True)
        self.trades_window = params.get("trades_window", 50)
        self.assert_min = params.get("assert_min", 40.0)
        self.name = "JFN"

    def _resolve_exit(self, direction: int, entry: float, high: float, low: float) -> int:
        is_long = direction == 1
        tp = entry * (1 + self.take_pct / 100.0) if is_long else entry * (1 - self.take_pct / 100.0)
        sl = entry * (1 - self.stop_pct / 100.0) if is_long else entry * (1 + self.stop_pct / 100.0)
        hit_tp = high >= tp if is_long else low <= tp
        hit_sl = low <= sl if is_long else high >= sl

        if hit_tp and hit_sl:
            return -1
        if hit_sl:
            return -1
        if hit_tp:
            return 1
        return 0

    def _simulate_results(self, df: pd.DataFrame, fast_ma: pd.Series, slow_ma: pd.Series) -> List[int]:
        results: List[int] = []
        in_trade = False
        direction = 0
        entry_price = 0.0
        bars_held = 0
        entry_index = -1

        closes = df["close"]
        highs = df["high"]
        lows = df["low"]

        for i in range(1, len(df)):
            if pd.isna(fast_ma.iloc[i]) or pd.isna(slow_ma.iloc[i]):
                continue

            cross_up = fast_ma.iloc[i - 1] <= slow_ma.iloc[i - 1] and fast_ma.iloc[i] > slow_ma.iloc[i]
            cross_down = fast_ma.iloc[i - 1] >= slow_ma.iloc[i - 1] and fast_ma.iloc[i] < slow_ma.iloc[i]

            if not in_trade and (cross_up or cross_down):
                in_trade = True
                direction = 1 if cross_up else -1
                entry_price = float(closes.iloc[i])
                bars_held = 0
                entry_index = i
                continue

            if in_trade and i > entry_index:
                bars_held += 1
                outcome = self._resolve_exit(direction, entry_price, float(highs.iloc[i]), float(lows.iloc[i]))
                exit_now = outcome != 0 or bars_held >= self.max_hold_bars

                if exit_now:
                    is_timeout = outcome == 0 and bars_held >= self.max_hold_bars
                    is_win = outcome == 1
                    is_loss = outcome == -1 or (is_timeout and self.count_timeout_as_loss)

                    if is_win:
                        results.append(1)
                    elif is_loss:
                        results.append(0)

                    in_trade = False
                    direction = 0
                    entry_price = 0.0
                    bars_held = 0
                    entry_index = -1

        return results

    def _calculate_assertiveness(self, results: List[int]) -> Tuple[Optional[float], int, int, int]:
        if not results:
            return None, 0, 0, 0

        wins = sum(1 for r in results if r == 1)
        losses = sum(1 for r in results if r == 0)

        window = results[-self.trades_window:] if self.trades_window > 0 else results
        wins_window = sum(1 for r in window if r == 1)
        total_window = len(window)

        if total_window > 0:
            hit_rate = 100.0 * wins_window / total_window
            trades_shown = total_window
        else:
            total_all = max(wins + losses, 1)
            hit_rate = 100.0 * wins / total_all
            trades_shown = wins + losses

        return hit_rate, wins, losses, trades_shown

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[SignalResult]:
        min_rows = max(self.slow_length + 5, self.max_hold_bars + 2)
        if not self.validate_dataframe(df, min_rows=min_rows):
            return None

        closes = df["close"]
        fast_ma = self.ema(closes, self.fast_length)
        slow_ma = self.ema(closes, self.slow_length)

        if pd.isna(fast_ma.iloc[-1]) or pd.isna(slow_ma.iloc[-1]):
            return None

        cross_up = fast_ma.iloc[-2] <= slow_ma.iloc[-2] and fast_ma.iloc[-1] > slow_ma.iloc[-1]
        cross_down = fast_ma.iloc[-2] >= slow_ma.iloc[-2] and fast_ma.iloc[-1] < slow_ma.iloc[-1]

        if not cross_up and not cross_down:
            return None

        direction = "LONG" if cross_up else "SHORT"
        side_word = "COMPRA" if cross_up else "VENDA"
        price = float(closes.iloc[-1])

        message = f"Sinal {side_word}"

        return SignalResult(
            symbol=symbol,
            timeframe=timeframe,
            strategy=self.name,
            direction=direction,
            price=price,
            message=message
        )
