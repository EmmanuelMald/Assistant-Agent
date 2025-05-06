import re


def find_image_urls(text: str) -> list[str]:
    """
    Finds image URLs within a given text string.

    Specifically targets URLs pointing to Google Cloud Storage (GCS)
    and ending with common image file extensions.

    Args:
        text: str -> The text string to search within.

    Returns:
        A list of found image URLs (strings). Returns an empty list if none are found.
    """
    regex = r"(https://storage\.googleapis\.com/.+\.(?:png|jpg|jpeg|gif|webp|svg))"
    urls = re.findall(regex, text)
    return urls
