def safe_divide(numerator, denominator, default_value=0.0):
    """
    Safely divides two floats, returning a default value if the denominator is zero.

    Args:
        numerator (float): The number to be divided.
        denominator (float): The number to divide by.
        default_value (float, optional): The value to return if the denominator is zero. Defaults to 0.

    Returns:
        float: The result of the division, or the default value if the denominator is zero.
    """
    try:
        return numerator / denominator
    except ZeroDivisionError:
        return default_value


def calculate_planned_production_qty(stock_level, safety_stock_target_qty, sales_average, safety_stock_target=4.0):
    """
    Calculate the planned production quantity based on the given parameters.

    Args:
        stock_level (float): The current stock level.
        safety_stock_target_qty (float): The target safety stock quantity.
        sales_average (float): The average sales.

    Returns:
        float: The planned production quantity.
    """
    if stock_level < safety_stock_target_qty:
        planned_production_qty = safety_stock_target * sales_average - stock_level
        return planned_production_qty if planned_production_qty > 0 else 0
    else:
        return 0.0


def round_up_to_nearest(value, multiplier):
    """
    Rounds up a value to the closest multiplier.

    Args:
        value (float): The value to be rounded up.
        multiplier (float): The multiplier to use for rounding up.

    Returns:
        float: The rounded up value.
    """
    return (value + multiplier - 1) // multiplier * multiplier