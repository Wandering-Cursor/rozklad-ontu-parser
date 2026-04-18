def trim_text(text: str, max_length: int = 1000) -> str:
    """
    Trims the input text to a specified maximum length.

    Args:
        text (str): The input text to be trimmed.
        max_length (int): The maximum allowed length of the text. Default is 1000 characters.

    Returns:
        str: The trimmed text if it exceeds the maximum length, otherwise returns the original text.
    """
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
