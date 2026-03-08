"""Signal adapter for converting discrete signals to probability space.
This bridges the gap between existing signal.py (5-point discrete)
and the new strategy engine (continuous probability).
"""
from typing import Literal

# Discrete signal types from existing system
DiscreteSignal = Literal["strong_buy", "buy", "hold", "sell", "strong_sell"]


class SignalAdapter:
    """Adapter for signal type conversion"""

    # Mapping from discrete signals to probability space
    # Format: {signal: (probability_range, kelly_edge)}
    SIGNAL_MAPPING = {
        "strong_buy": (0.80, 0.35),   # 80% win prob, 35% edge
        "buy": (0.65, 0.20),          # 65% win prob, 20% edge
        "hold": (0.50, 0.00),          # 50% win prob, no edge
        "sell": (0.35, -0.20),         # 35% win prob, -20% edge
        "strong_sell": (0.20, -0.35)   # 20% win prob, -35% edge
    }

    @classmethod
    def discrete_to_probability(cls, signal: DiscreteSignal) -> tuple:
        """
        Convert discrete signal to probability and edge.

        Args:
            signal: Discrete signal from signal.py

        Returns:
            Tuple of (win_probability, edge)
        """
        return cls.SIGNAL_MAPPING.get(signal, (0.50, 0.00))

    @classmethod
    def discrete_to_strength(cls, signal: DiscreteSignal) -> float:
        """
        Convert discrete signal to strength score (-1 to 1).

        Args:
            signal: Discrete signal

        Returns:
            Strength score
        """
        strength_map = {
            "strong_buy": 1.0,
            "buy": 0.5,
            "hold": 0.0,
            "sell": -0.5,
            "strong_sell": -1.0
        }
        return strength_map.get(signal, 0.0)

    @classmethod
    def probability_to_discrete(cls, probability: float) -> DiscreteSignal:
        """
        Convert probability back to discrete signal (reverse mapping).

        Args:
            probability: Win probability (0 to 1)

        Returns:
            Discrete signal
        """
        if probability >= 0.75:
            return "strong_buy"
        elif probability >= 0.60:
            return "buy"
        elif probability >= 0.40:
            return "hold"
        elif probability >= 0.25:
            return "sell"
        else:
            return "strong_sell"
