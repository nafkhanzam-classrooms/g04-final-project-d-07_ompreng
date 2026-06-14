import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

targets = [
    DATA / "mbg.db",
    DATA / "mbg.db-wal",
    DATA / "mbg.db-shm",
    DATA / "server.log",
]

log_patterns = ["*.log", "*.err", "*.out"]
uploads_dir = DATA / "uploads"


def main():
    for target in targets:
        if target.exists():
            target.unlink()
            print(f"Deleted {target.relative_to(ROOT)}")

    for pattern in log_patterns:
        for f in DATA.glob(pattern):
            f.unlink()
            print(f"Deleted {f.relative_to(ROOT)}")

    if uploads_dir.exists():
        shutil.rmtree(uploads_dir)
        uploads_dir.mkdir()
        print(f"Cleared {uploads_dir.relative_to(ROOT)}/")

    print("Done. Database, logs, and uploads reset.")


if __name__ == "__main__":
    main()
