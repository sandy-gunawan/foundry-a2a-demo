import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--cli", action="store_true")
    args = parser.parse_args()
    if args.cli:
        raise SystemExit("Use the web interface for interactive requests.")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()