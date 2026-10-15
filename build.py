from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
PUBLIC = ROOT / "public"


def main():
    subprocess.run(["npm", "ci"], cwd=FRONTEND, check=True)
    subprocess.run(["npm", "run", "build"], cwd=FRONTEND, check=True)
    PUBLIC.mkdir(exist_ok=True)
    shutil.copytree(DIST, PUBLIC, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
