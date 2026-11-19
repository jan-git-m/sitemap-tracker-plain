import json
import os
import xml.etree.ElementTree as ET
import requests

SITEMAPS_FILE = "sitemaps.txt"
STATE_FILE = "sitemap_state.json"


def load_sitemap_urls(filepath):
    """Lädt die zu überwachenden Sitemaps aus einer externen Textdatei."""
    if not os.path.exists(filepath):
        print(f"Fehler: Die Datei '{filepath}' wurde nicht gefunden!")
        return []

    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def fetch_sitemap_urls(url):
    """Lädt eine Sitemap herunter und extrahiert alle URLs."""
    headers = {"User-Agent": "SitemapMonitorBot/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Fehler beim Abrufen von {url}: {e}")
        return set()

    urls = set()
    try:
        root = ET.fromstring(response.content)
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"
        for url_elem in root.findall(f".//{namespace}loc"):
            if url_elem.text:
                urls.add(url_elem.text.strip())
    except Exception as e:
        print(f"Fehler beim Parsen der XML für {url}: {e}")
    return urls


def load_state():
    """Lädt den gespeicherten Zustand aus der JSON-Datei."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    """Speichert den aktuellen Zustand in der JSON-Datei."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    sitemap_urls = load_sitemap_urls(SITEMAPS_FILE)
    if not sitemap_urls:
        print("Keine Sitemaps in der sitemaps.txt gefunden.")
        return

    state = load_state()
    total_new_urls = []

    for sitemap_url in sitemap_urls:
        print(f"\nPrüfe Sitemap: {sitemap_url}")
        current_urls = fetch_sitemap_urls(sitemap_url)

        if not current_urls:
            print("  -> Keine URLs gefunden oder Fehler beim Abruf.")
            continue

        known_urls = set(state.get(sitemap_url, []))

        if not known_urls:
            print(
                f"  -> Initialisiere Sitemap mit {len(current_urls)} URLs."
            )
            state[sitemap_url] = sorted(current_urls)
            continue

        new_urls = current_urls - known_urls

        if new_urls:
            print(f"  -> {len(new_urls)} neue URL(s) gefunden!")
            for u in sorted(new_urls):
                print(f"     + {u}")
                total_new_urls.append(f"[{sitemap_url}] {u}")

        state[sitemap_url] = sorted(current_urls)

    save_state(state)

    if total_new_urls:
        print(f"\nInsgesamt {len(total_new_urls)} neue URL(s) entdeckt.")
    else:
        print("\nKeine neuen URLs in allen Sitemaps gefunden.")


if __name__ == "__main__":
    main()
