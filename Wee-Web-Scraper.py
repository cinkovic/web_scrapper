import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
import string
import sys
import time


def create_directory(title: str) -> str:
    """
    Create a directory with a timestamp prefix and website title.

    Args:
        title: The title of the website.

    Returns:
        The name of the created directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    directory_name = timestamp + "_" + sanitize_filename(title[:20])
    os.makedirs(directory_name, exist_ok=True)
    return directory_name


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing special characters and non-ASCII characters.

    Args:
        filename: The filename to sanitize.

    Returns:
        The sanitized filename.
    """
    filename = filename.split('?', 1)[0]
    filename = filename.split('#', 1)[0]
    # Replace any characters not in ASCII letters, digits, periods, underscores, or hyphens with underscores
    filename = ''.join(char if char in string.ascii_letters + string.digits + "._-" else "_" for char in filename)
    return filename


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.

    Args:
        url: The URL to check.

    Returns:
        True if the URL is valid, False otherwise.
    """
    parsed_url = urlparse(url)
    return bool(parsed_url.netloc) and bool(parsed_url.scheme)


def download_file(url: str, filename: str, directory: str) -> str:
    """
    Download a file from a URL and save it to the specified directory.

    Args:
        url: The URL of the file to download.
        filename: The desired filename for the downloaded file.
        directory: The directory to save the file in.

    Returns:
        The absolute path of the downloaded file.
    """
    if not is_valid_url(url):
        print(f"Skipping invalid URL: {url}")
        return ""

    try:
        response = requests.get(url, timeout=4)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {filename}")
        print(f"Error: {e}")
        return ""

    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(directory, sanitized_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, "wb") as file:
            file.write(response.content)
    except IOError as e:
        print(f"Failed to save file: {file_path}")
        print(f"Error: {e}")
        return ""

    return os.path.abspath(file_path)


def modify_html_content(content: str, directory_name: str, base_url: str) -> None:
    """
    Modify the HTML content to use local files.

    Args:
        content: The HTML content to modify.
        directory_name: The directory name of the website.
        base_url: The base URL of the website.
    """
    soup = BeautifulSoup(content, "html.parser")

    # Update image sources
    for img in soup.find_all("img"):
        if img.has_attr("src"):
            img["src"] = os.path.join("images", sanitize_filename(img["src"]))

    # Update script sources
    for script in soup.find_all("script"):
        if script.has_attr("src"):
            script["src"] = os.path.join("js", sanitize_filename(script["src"]))

    # Update CSS sources
    for link in soup.find_all("link", rel="stylesheet"):
        if link.has_attr("href"):
            link["href"] = os.path.join("css", sanitize_filename(link["href"]))

    modified_content = soup.prettify(formatter="html5")
    with open(os.path.join(directory_name, "index.html"), "w", encoding="utf-8") as file:
        file.write(modified_content)


def parse_website(url: str, time_limit: int = 4) -> None:
    """
    Parse and download the website content.

    Args:
        url: The URL of the website to parse.
        time_limit: The maximum time limit for each download task in seconds (default: 4).
    """
    start_time = time.time()

    # Parse the URL and extract the base URL
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc

    # Send a GET request to the website URL
    try:
        response = requests.get(url, timeout=4)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to access website: {url}")
        print(f"Error: {e}")
        return

    # Create a directory based on the website title
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string.strip()
    directory_name = create_directory(title)

    # Define subdirectories for different types of content
    subdirectories = {
        "images": os.path.join(directory_name, "images"),
        "audio": os.path.join(directory_name, "audio"),
        "pdfs": os.path.join(directory_name, "pdfs"),
        "text": os.path.join(directory_name, "text"),
        "js": os.path.join(directory_name, "js"),
        "css": os.path.join(directory_name, "css"),
    }

    # Create subdirectories
    for subdir in subdirectories.values():
        os.makedirs(subdir, exist_ok=True)

    # Save the index.html file
    with open(os.path.join(directory_name, "index.html"), "wb") as file:
        file.write(response.content)

    # Download additional content (images, audio, PDFs, text, scripts)
    for tag, attribute, subdir in [
        ("img", "src", subdirectories["images"]),
        ("audio", "src", subdirectories["audio"]),
        ("a", "href", subdirectories["pdfs"]),
        ("a", "href", subdirectories["text"]),
        ("script", "src", subdirectories["js"]),
    ]:
        for element in soup.find_all(tag):
            if element.has_attr(attribute):
                content_url = element[attribute]
                if content_url.startswith(".."):
                    content_url = urljoin(base_url, content_url)

                filename = os.path.basename(content_url)
                download_file(content_url, filename, subdir)

                # Check if the elapsed time exceeds the time limit
                elapsed_time = time.time() - start_time
                if elapsed_time >= time_limit:
                    print(f"Time limit exceeded ({time_limit}s). Stopping further downloads.")
                    return

    # Modify HTML content to use local files
    modify_html_content(response.content, directory_name, base_url)

    print("Website parsing and download completed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the website address as an argument.")
    else:
        website_url = sys.argv[1]
        time_limit = int(sys.argv[2]) if len(sys.argv) >= 3 else 4
        parse_website(website_url, time_limit)
