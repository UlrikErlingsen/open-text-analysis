@echo off
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
if not defined ARROW_DEFAULT_MEMORY_POOL set ARROW_DEFAULT_MEMORY_POOL=system
for /f %%H in ('powershell -NoProfile -Command "(Get-FileHash requirements.txt -Algorithm SHA256).Hash.ToLower()"') do set REQ_HASH=%%H
if not exist .venv\.textsignal-requirements-%REQ_HASH% (
  echo First launch: downloading packages. Later launches will be faster.
  python -m pip --disable-pip-version-check install --prefer-binary -r requirements.txt
  del /q .venv\.textsignal-requirements-* .venv\.textsignal-ready 2>nul
  type nul > .venv\.textsignal-requirements-%REQ_HASH%
)
if not defined TEXTSIGNAL_PORT set TEXTSIGNAL_PORT=8600
python -m streamlit run app.py --server.headless=false --server.address=127.0.0.1 --server.port=%TEXTSIGNAL_PORT% --server.maxUploadSize=50 --server.fileWatcherType=none --browser.gatherUsageStats=false
