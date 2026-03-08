"""
Strategy selector for gradual migration from old signal.py to new strategy_engine.
Provides routing logic and feature flag control for the analyze endpoint.
"""
from typing import Dict, Optional
from .strategy_engine import StrategyEngine

# NOTE: This is a NEW RISK_CONFIG schema for the new strategy engine.
# The legacy RISK_CONFIG (with single_trade_pct, stop_loss_pct, etc.) exists in
# backend/routers/analysis.py lines 34-57 and is used by calculate_position_recommendation().
# This NEW schema maps legacy risk preferences to the new Kelly-based parameters.
NEW_RISK_CONFIG = {
    "conservative": {
        "kelly_fraction": 0.15,      # More conservative Kelly
        "max_position_pct": 0.20,    # Lower max position
        "min_position_pct": 0.05,
        "atr_multiplier": 1.5,       # Tighter stop loss
        "rsi_oversold": 25.0,       # More selective entry
        "rsi_overbought": 75.0,
        "fixed_pct": 0.03            # Lower fixed stop
    },
    "neutral": {
        "kelly_fraction": 0.25,      # Quarter-Kelly (default)
        "max_position_pct": 0.30,
        "min_position_pct": 0.05,
        "atr_multiplier": 2.0,
        "rsi_oversold": 30.0,
        "rsi_overbought": 70.0,
        "fixed_pct": 0.05
    },
    "aggressive": {
        "kelly_fraction": 0.40,      # Higher Kelly fraction
        "max_position_pct": 0.50,    # Higher max position
        "min_position_pct": 0.05,
        "atr_multiplier": 2.5,      # Wider stops for trend following
        "rsi_oversold": 35.0,       # Earlier entry
        "rsi_overbought": 65.0,
        "fixed_pct": 0.07
    }
}


class StrategySelector:
    """Selects between old and new strategy engines based on feature flags"""

    def __init__(self, use_new_engine: bool = False):
        """
        Initialize strategy selector.

        Args:
            use_new_engine: Feature flag to use new strategy engine
        """
        self.use_new_engine = use_new_engine

    def map_risk_to_params(self, risk_preference: str) -> Dict:
        """
        Map risk_preference to StrategyParams format.

        This enables backward compatibility by converting legacy
        risk_preference values to new structured parameters.

        Args:
            risk_preference: One of 'conservative', 'neutral', 'aggressive'

        Returns:
            Dictionary with structure matching StrategyParams
        """
        risk_config = NEW_RISK_CONFIG.get(risk_preference, NEW_RISK_CONFIG["neutral"])

        return {
            "trend": {
                "ma_short_period": 5,
                "ma_long_period": 20,
                "rsi_oversold": risk_config["rsi_oversold"],
                "rsi_overbought": risk_config["rsi_overbought"],
                "volume_surge_threshold": 1.5
            },
            "bottom": {
                "bollinger_period": 20,
                "bollinger_std": 2.0,
                "rsi_bottom_threshold": risk_config["rsi_oversold"],
                "support_lookback": 20,
                "volume_shrink_threshold": 0.7
            },
            "kelly": {
                "win_rate_estimate": 0.55,
                "avg_win_avg_loss_ratio": 1.5,
                "max_position_pct": risk_config["max_position_pct"],
                "min_position_pct": risk_config["min_position_pct"],
                "kelly_fraction": risk_config["kelly_fraction"]
            },
            "stop_loss": {
                "fixed_pct": risk_config["fixed_pct"],
                "atr_multiplier": risk_config["atr_multiplier"],
                "atr_period": 14,
                "support_pct": 0.02,
                "trailing_activation_pct": 0.02
            }
        }

    def get_strategy_engine(self, risk_preference: Optional[str] = None,
                          strategy_params: Optional[Dict] = None) -> Dict:
        """
        Get appropriate strategy engine and parameters.

        Priority:
        1. If strategy_params provided: use new engine with custom params
        2. If use_new_engine and risk_preference: use new engine with mapped params
        3. Otherwise: indicate old engine should be used

        Args:
            risk_preference: Legacy risk preference value
            strategy_params: New structured strategy parameters

        Returns:
            Dict with:
                - use_new_engine: bool
                - params: strategy parameters dict
                - engine: StrategyEngine instance if use_new_engine=True
        """
        if strategy_params:
            # Explicit new engine request
            engine = StrategyEngine(strategy_params)
            return {
                "use_new_engine": True,
                "params": strategy_params,
                "engine": engine
            }

        if self.use_new_engine and risk_preference:
            # Convert risk preference to new params
            params = self.map_risk_to_params(risk_preference)
            engine = StrategyEngine(params)
            return {
                "use_new_engine": True,
                "params": params,
                "engine": engine
            }

        # Fall back to old engine
        # NOTE: This returns legacy RISK_CONFIG from backend/routers/analysis.py lines 34-57
        # with keys: single_trade_pct, stop_loss_pct, take_profit_pct, max_risk_per_trade, signal_threshold
        return {
            "use_new_engine": False,
            "params": {"fallback": "legacy_risk_config_in_analysis_py_lines_34_57"},
            "engine": None
        }

    def get_migration_status(self) -> Dict:
        """
        Get current migration status.

        Returns:
            Dict with migration information
        """
        return {
            "use_new_engine": self.use_new_engine,
            "migration_phase": "phase_1" if not self.use_new_engine else "phase_2",
            "supported_risk_levels": ["conservative", "neutral", "aggressive"],
            "deprecated": "risk_preference" if self.use_new_engine else None
        }
