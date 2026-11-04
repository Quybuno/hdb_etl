import requests
import subprocess
import sys
import os

url = "https://github.com/dbt-labs/dbt/releases/download/v2.0.11/dbt_core_experimental_parser-2.0.11-py3-none-win_amd64.whl"
whl_name = "dbt_core_experimental_parser-2.0.11-py3-none-win_amd64.whl"

print(f"Downloading {whl_name}...")
r = requests.get(url, stream=True)
with open(whl_name, "wb") as f:
    for chunk in r.iter_content(chunk_size=1024*1024):
        if chunk:
            f.write(chunk)
print(f"Downloaded: {os.path.getsize(whl_name)} bytes")

print("Installing wheel...")
res = subprocess.run([sys.executable, "-m", "pip", "install", whl_name], capture_output=True, text=True)
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)

if os.path.exists(whl_name):
    os.remove(whl_name)

print("Now installing dbt-duckdb...")
res2 = subprocess.run([sys.executable, "-m", "pip", "install", "dbt-duckdb"], capture_output=True, text=True)
print("dbt-duckdb return code:", res2.returncode)
print("dbt-duckdb stdout:", res2.stdout[-500:] if res2.stdout else "")
print("dbt-duckdb stderr:", res2.stderr[-500:] if res2.stderr else "")

