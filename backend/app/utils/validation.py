"""
Data validation utilities
"""

from typing import Optional


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Default value if division by zero
    
    Returns:
        Result of division or default value
    """
    return numerator / denominator if denominator != 0 else default


def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate percentage with safe division
    
    Args:
        part: Part value
        whole: Whole value
    
    Returns:
        Percentage (0-100)
    """
    return safe_divide(part * 100, whole, 0.0)