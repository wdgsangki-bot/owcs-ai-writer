import requests
from bs4 import BeautifulSoup
import re

URL = "https://liquipedia.net/overwatch/Overwatch_Champions_Series/2026/Asia/Stage_1/Korea"

headers = {
    "User-Agent": "Mozilla/5.0"
}

html = requests.get(URL, headers=headers).text
soup = BeautifulSoup(html, "html.parser")

text = soup.get_text(" ", strip=True)

pattern = re.compile(
    r"([A-Za-z]{2,6})\s+(\d+)\s*:\s*(\d+)\s+\(Bo\d+\)\s+([A-Za-z]{2,6})"
)

matches = pattern.findall(text)

print("매치 수:", len(matches))
print()

for m in matches:
    print(m)