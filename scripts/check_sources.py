import sys
import time
import hashlib
import json
import csv
import io
import requests

USER_AGENT = "hdb-elt-student-project/1.0"
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = 30

def check_hdb():
    print("--- 1. Testing HDB Resale API ---")
    dataset_id = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
    base_url = "https://api-open.data.gov.sg/v1/public/api/datasets"
    initiate_url = f"{base_url}/{dataset_id}/initiate-download"
    poll_url = f"{base_url}/{dataset_id}/poll-download"

    t0 = time.time()
    print(f"GET {initiate_url}")
    try:
        r_init = requests.get(initiate_url, headers=HEADERS, timeout=TIMEOUT)
        t_init = time.time() - t0
        print(f"Initiate status: {r_init.status_code} in {t_init:.2f}s")
        print(f"Initiate body: {r_init.text[:300]}")
    except Exception as e:
        print(f"Error initiating HDB download: {e}")
        return {"status": "failed", "error": str(e)}

    # Poll download
    download_url = None
    poll_count = 0
    poll_start = time.time()
    while poll_count < 15:
        poll_count += 1
        t_poll_start = time.time()
        try:
            r_poll = requests.get(poll_url, headers=HEADERS, timeout=TIMEOUT)
            t_poll = time.time() - t_poll_start
            print(f"Poll #{poll_count} status: {r_poll.status_code} in {t_poll:.2f}s")
            poll_json = r_poll.json()
            status_val = poll_json.get("data", {}).get("status")
            url_val = poll_json.get("data", {}).get("url")
            print(f"Poll data status: {status_val}, url present: {bool(url_val)}")
            if status_val == "DOWNLOAD_SUCCESS" or url_val:
                download_url = url_val
                break
        except Exception as e:
            print(f"Poll error: {e}")
        time.sleep(2)

    if not download_url:
        return {"status": "failed", "error": "No download url received after polling"}

    print(f"Downloading CSV from: {download_url[:60]}...")
    t_dl_start = time.time()
    try:
        r_dl = requests.get(download_url, headers=HEADERS, timeout=120)
        t_dl = time.time() - t_dl_start
        print(f"Download completed in {t_dl:.2f}s, size: {len(r_dl.content)} bytes")
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return {"status": "failed", "error": str(e)}

    sha256 = hashlib.sha256(r_dl.content).hexdigest()
    print(f"CSV SHA-256: {sha256}")

    # Inspect CSV
    f = io.StringIO(r_dl.text)
    reader = csv.reader(f)
    header = next(reader)
    row_count = 0
    months = set()
    month_idx = header.index("month") if "month" in header else -1

    for row in reader:
        row_count += 1
        if month_idx != -1 and len(row) > month_idx:
            months.add(row[month_idx])

    min_month = min(months) if months else "N/A"
    max_month = max(months) if months else "N/A"

    print(f"Columns ({len(header)}): {header}")
    print(f"Row count: {row_count}")
    print(f"Min month: {min_month}, Max month: {max_month}")

    return {
        "status": "success",
        "initiate_status": r_init.status_code,
        "initiate_latency_s": round(t_init, 2),
        "poll_status": r_poll.status_code,
        "poll_count": poll_count,
        "download_latency_s": round(t_dl, 2),
        "sha256": sha256,
        "columns": header,
        "column_count": len(header),
        "row_count": row_count,
        "min_month": min_month,
        "max_month": max_month,
        "csv_content": r_dl.content,
        "csv_size_bytes": len(r_dl.content),
    }

def check_mrt():
    print("\n--- 2. Testing LTA MRT Station Exits API ---")
    dataset_id = "d_b39d3a0871985372d7e1637193335da5"
    base_url = "https://api-open.data.gov.sg/v1/public/api/datasets"
    initiate_url = f"{base_url}/{dataset_id}/initiate-download"
    poll_url = f"{base_url}/{dataset_id}/poll-download"

    t0 = time.time()
    try:
        r_init = requests.get(initiate_url, headers=HEADERS, timeout=TIMEOUT)
        t_init = time.time() - t0
        print(f"MRT Initiate status: {r_init.status_code} in {t_init:.2f}s")
        time.sleep(1)
        r_poll = requests.get(poll_url, headers=HEADERS, timeout=TIMEOUT)
        poll_json = r_poll.json()
        data_obj = poll_json.get("data") or {}
        status_val = data_obj.get("status")
        url_val = data_obj.get("url")
        print(f"MRT Poll status: {r_poll.status_code}, data status: {status_val}, url present: {bool(url_val)}")
        mrt_dl_size = 0
        sha256 = ""
        if url_val:
            r_dl = requests.get(url_val, headers=HEADERS, timeout=TIMEOUT)
            mrt_dl_size = len(r_dl.content)
            sha256 = hashlib.sha256(r_dl.content).hexdigest()
            print(f"MRT Downloaded: {mrt_dl_size} bytes, SHA-256: {sha256}")
        return {
            "status": "success" if url_val else "poll_incomplete",
            "initiate_status": r_init.status_code,
            "poll_status": r_poll.status_code,
            "data_status": status_val,
            "download_url_present": bool(url_val),
            "size_bytes": mrt_dl_size,
            "sha256": sha256
        }
    except Exception as e:
        print(f"MRT check error: {e}")
        return {"status": "failed", "error": str(e)}

def check_nus3d():
    print("\n--- 3. Testing NUS 3D HDB Repository ---")
    url = "https://raw.githubusercontent.com/ualsg/hdb3d-data/master/README.md"
    t0 = time.time()
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        latency = time.time() - t0
        print(f"NUS 3D README status: {r.status_code} in {latency:.2f}s, size: {len(r.content)} bytes")
        license_mention = "MIT" in r.text or "license" in r.text.lower()
        return {
            "status": "success" if r.status_code == 200 else "failed",
            "http_status": r.status_code,
            "latency_s": round(latency, 2),
            "license_mention": license_mention
        }
    except Exception as e:
        print(f"NUS 3D check error: {e}")
        return {"status": "failed", "error": str(e)}

def check_onemap():
    print("\n--- 4. Testing OneMap Search API (1 minimal request) ---")
    url = "https://www.onemap.gov.sg/api/common/elastic/search"
    params = {"searchVal": "101", "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": "1"}
    t0 = time.time()
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        latency = time.time() - t0
        print(f"OneMap status: {r.status_code} in {latency:.2f}s")
        data = r.json()
        found = data.get("found", 0)
        print(f"OneMap results found: {found}")
        return {
            "status": "success" if r.status_code == 200 else "failed",
            "http_status": r.status_code,
            "latency_s": round(latency, 2),
            "results_found": found
        }
    except Exception as e:
        print(f"OneMap check error: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    hdb_res = check_hdb()
    mrt_res = check_mrt()
    nus_res = check_nus3d()
    onemap_res = check_onemap()

    results = {
        "hdb": {k: v for k, v in hdb_res.items() if k != "csv_content"},
        "mrt": mrt_res,
        "nus3d": nus_res,
        "onemap": onemap_res
    }

    with open("docs/source_check_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nCheck summary written to docs/source_check_raw.json")
