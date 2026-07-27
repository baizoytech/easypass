<div align="center"><strong>English</strong> | <a href="README.zh-CN.md">中文</a></div>

EasyPass is a local password manager built with Flask and SQLite. It organizes data in a “Country -> Company -> Website/App -> Account” hierarchy.

## Start from source

### Recommended: double-click `start.bat`

1. Install Python 3.9 or later, and check `Add Python to PATH` during installation.
2. Open the repository root and double-click `start.bat`.
3. The script will look for a local Python installation.
4. The script will install dependencies into the local `libs/` directory.
5. When startup succeeds, the app will open your browser at `http://127.0.0.1:5000`.

### Command-line start

If you prefer to run commands manually, execute the following in the repository root:

```powershell
python -m pip install -r requirements.txt -t libs
python -m src.app
```

Notes:

- `requirements.txt` contains only the runtime dependencies.
- Dependencies are installed into the project-local `libs/` directory, not the global Python environment.
- If Python is not installed on your machine, these commands will not work until Python is installed.

### Do not double-click `src/app.py`

Please use `start.bat` or `python -m src.app` to start the app. Do not run `src/app.py` directly.

## First run creates

- `data/passwords.db`: main database
- `data/flask_secret.key`: Flask secret key file
- `data/archive/`: archived data
- `libs/`: local dependency cache

## Useful scripts

- `start.bat`: launch the app and handle dependencies automatically
- `reset_and_start.bat`: clear the main database and restart
- `package_release.bat`: build the release package
- `scripts/maintenance/publish_release.ps1`: release packaging logic

Packaging requires `PyInstaller` in the current Python environment. If it is missing, install it with `python -m pip install pyinstaller`.

## Release flow

1. Make sure Python 3.9+ is installed and available in PATH.
2. Make sure `PyInstaller` is installed in that Python environment.
3. Run `package_release.bat` from the repository root.
4. The script builds `dist/EasyPass.exe` and uses `build/` for temporary files.
5. Distribute the generated `EasyPass.exe` together with any packaging assets you need to keep.

## Directory overview

- `src/`: source code
- `data/`: runtime data
- `libs/`: local dependency cache
- `scripts/`: maintenance and release scripts

## Packaged build

If you are using the packaged release, you usually only need to run the generated `EasyPass.exe` directly. Python is not required.

If you previously used the older packaged app name, the first EasyPass launch will copy your existing data into the new app data directory automatically.
