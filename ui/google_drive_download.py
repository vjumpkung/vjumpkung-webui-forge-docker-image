import gdown
import os
import argparse
import sys


def main(path: str, url: str):
    os.makedirs(path, exist_ok=True)
    os.chdir(path)
    file = gdown.download(url, fuzzy=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download files from Google Drive and extract if ZIP"
    )

    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path where the file will be downloaded and extracted",
    )

    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Google Drive URL of the file to download",
    )

    args = parser.parse_args()
    try:
        main(args.path, args.url)
    except:
        sys.exit(1)
