import os
import re
import sys
import glob
import urllib3
import requests
from concurrent.futures import ThreadPoolExecutor

# We make insecure requests if a domain has SSL issues, disable warning for clean output
urllib3.disable_warnings()

AGENT = os.getenv("AGENT", "Mozilla/5.0 ()")
SKIPLIST = [
    "https://linkedin.com",
    "https://linux.die.net",
    "https://code.visualstudio.com",
    "https://dl.acm.org",
    "https://www.unrealengine.com",
    "https://www.fxguide.com",
    "https://www.kaggle.com",
    "https://helpx.adobe.com",
    "https://www.virtra.com",
    "medium.com/"
]


def get_status(link):
    # Skip certain hosts which don't play nicely
    for skip_link in SKIPLIST:
        if skip_link in link:
            return True, 0

    try:
        status = requests.head(link, timeout=60, headers={"User-Agent": AGENT}, allow_redirects=True).status_code
    except requests.exceptions.SSLError:  # In case of failed certificate verification try without
        status = requests.head(link, timeout=60, headers={"User-Agent": AGENT}, allow_redirects=True, verify=False).status_code
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):  # In case of timeout
        status = "timed out"
    except:
        print(f"Unhandled exception during request to: {link}")
        raise

    if status in [200]:
        return True, status

    return False, status


def main():
    html_files = glob.glob("**/*.html", recursive=True)

    links = []
    re_link = re.compile("http[s]?://[a-zA-Z0-9./~=?_%:#&@+-]*")

    for html_file in html_files:
        with open(html_file, encoding="utf-8") as f:
            contents = f.read()

        links += re_link.findall(contents)

    with ThreadPoolExecutor(max_workers=8) as executor:
        codes_generator = executor.map(get_status, links)

    codes_checks = list(codes_generator)

    all_good = True
    for i, (passed, code) in enumerate(codes_checks):
        if not passed:
            print(f"Fail: {links[i]} ({code})")
            all_good = False

    if not all_good:
        sys.exit(1)


if __name__ == "__main__":
    main()
