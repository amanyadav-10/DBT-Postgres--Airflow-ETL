"""
Extract step: downloads ball-by-ball match data from Cricsheet.org.

Cricsheet publishes free, open cricket match data as JSON, bundled per
competition as a zip file (e.g. all IPL matches in one zip). This script
downloads that zip, extracts the individual match JSON files, and saves
them to a local `data/raw_json/` folder for the load step to pick up.

Usage:
    python download_cricsheet.py --competition ipl --limit 20
    python download_cricsheet.py --competition odis --out-dir data/raw_json
"""

import argparse
import io
import json
import zipfile
from pathlib import Path

import requests

# Cricsheet publishes a zip of JSON files per competition.
# Full list of available competitions: https://cricsheet.org/downloads/
COMPETITION_URLS = {
    "ipl": "https://cricsheet.org/downloads/ipl_json.zip",
    "odis": "https://cricsheet.org/downloads/odis_json.zip",
    "t20s": "https://cricsheet.org/downloads/t20s_json.zip",
    "tests": "https://cricsheet.org/downloads/tests_json.zip",
}


def download_zip(url: str) -> zipfile.ZipFile:
    """Downloads a zip file into memory and returns a ZipFile handle."""
    print(f"Downloading {url} ...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(response.content))


def extract_matches(zf: zipfile.ZipFile, out_dir: Path, limit: int | None) -> list[Path]:
    """Extracts up to `limit` match JSON files from the zip into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_names = [n for n in zf.namelist() if n.endswith(".json")]
    if limit:
        json_names = json_names[:limit]

    saved_paths = []
    for name in json_names:
        with zf.open(name) as f:
            data = json.load(f)
        out_path = out_dir / Path(name).name
        with open(out_path, "w") as f:
            json.dump(data, f)
        saved_paths.append(out_path)

    print(f"Saved {len(saved_paths)} match files to {out_dir}")
    return saved_paths


def main():
    parser = argparse.ArgumentParser(description="Download Cricsheet match data.")
    parser.add_argument(
        "--competition",
        choices=COMPETITION_URLS.keys(),
        default="ipl",
        help="Which competition's matches to download (default: ipl)",
    )
    parser.add_argument(
        "--out-dir",
        default="data/raw_json",
        help="Directory to save extracted match JSON files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: only download the first N matches (useful for testing)",
    )
    args = parser.parse_args()

    url = COMPETITION_URLS[args.competition]
    zf = download_zip(url)
    extract_matches(zf, Path(args.out_dir), args.limit)


if __name__ == "__main__":
    main()
