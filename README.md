
# Wee Web Scraper

## Quick Start
Download and rewire a website for offline use. This Python script fetches the content from a specified URL into a local directory, tweaking the HTML to make use of static content downloaded to work offline.

## Features
- Downloads images, audio, PDFs, and more.
- Rewires HTML for offline browsing.
- Time-limited to avoid hang-ups.
- Command-line simplicity.

## Setup
- Needs: Python 3.x, `requests`, `beautifulsoup4`.
- Install dependencies: `pip install requests beautifulsoup4`.

## Usage
Run it with a URL, and optionally, a time limit in seconds (default: 4 seconds).
```
python web_scrapper.py <website_url> [time_limit]
```
Example: `python web_scrapper.py http://example.com 10`

## Note
- It's a single-threaded script.
- Large sites might take time. Tweak the time limit as required.

## License
This mini project is under the MIT License.
