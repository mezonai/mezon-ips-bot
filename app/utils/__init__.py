"""Utility for converting numbers to Vietnamese text."""


def number_to_vietnamese_text(number: float) -> str:
    """Convert a number to Vietnamese text representation.

    Example:
        9000000 -> "Chín triệu đồng chẵn"
        1500000 -> "Một triệu năm trăm nghìn đồng chẵn"
    """
    if number == 0:
        return "Không đồng"

    # Handle negative numbers
    if number < 0:
        return "Âm " + number_to_vietnamese_text(-number)

    # Split into integer and decimal parts
    integer_part = int(number)

    # Units
    ones = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def read_group(n: int, needs_zero_hundred: bool = False) -> str:
        """Read a 3-digit group.

        Args:
            n: The 3-digit number (0-999).
            needs_zero_hundred: If True and hundred=0, prefix with "không trăm"
                               to separate from a higher group.
        """
        if n == 0:
            return ""

        hundred = n // 100
        ten = (n % 100) // 10
        one = n % 10

        result = []

        # Hundreds
        if hundred > 0:
            result.append(ones[hundred])
            result.append("trăm")
        elif needs_zero_hundred:
            result.append("không trăm")

        # Tens
        if ten > 1:
            result.append(ones[ten])
            result.append("mươi")
        elif ten == 1:
            result.append("mười")
        elif (hundred > 0 or needs_zero_hundred) and one > 0:
            result.append("lẻ")

        # Ones
        if one > 0:
            if ten > 1 and one == 1:
                result.append("mốt")
            elif ten > 0 and one == 5:
                result.append("lăm")
            else:
                result.append(ones[one])

        return " ".join(result)

    # Break number into groups of 3 digits
    groups = []
    temp = integer_part
    while temp > 0:
        groups.append(temp % 1000)
        temp //= 1000

    # Scale names
    scales = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]

    # Build result
    result_parts = []
    seen_higher_group = False
    for i in range(len(groups) - 1, -1, -1):
        if groups[i] > 0:
            needs_zero_hundred = seen_higher_group
            group_text = read_group(groups[i], needs_zero_hundred)
            if group_text:
                result_parts.append(group_text)
                if i > 0 and i < len(scales):
                    result_parts.append(scales[i])
            seen_higher_group = True

    result = " ".join(result_parts)

    # Capitalize first letter
    if result:
        result = result[0].upper() + result[1:]

    return result + " đồng chẵn"
