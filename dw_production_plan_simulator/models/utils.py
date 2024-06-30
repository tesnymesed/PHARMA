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