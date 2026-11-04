import time
import requests
import logging

USER_AGENT = "hdb-elt-student-project/1.0"

class HTTPForbiddenError(Exception):
    """Raised when an HTTP 403 Forbidden is encountered. No retries allowed."""
    pass

def fetch_with_retry(
    url: str,
    method: str = "GET",
    params: dict = None,
    headers: dict = None,
    timeout: int = 60,
    max_retries: int = 3,
    backoff_seconds: int = 2,
    logger: logging.Logger = None,
    stream: bool = False
) -> requests.Response:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)

    attempt = 0
    while attempt <= max_retries:
        try:
            if logger:
                logger.info(f"HTTP {method} {url} (attempt {attempt + 1}/{max_retries + 1})")
            
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                headers=req_headers,
                timeout=timeout,
                stream=stream
            )

            if resp.status_code == 403:
                err_msg = f"HTTP 403 Forbidden received from {url}. Halting immediately per spec."
                if logger:
                    logger.error(err_msg)
                raise HTTPForbiddenError(err_msg)

            # If 5xx error or rate limit 429, retry
            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt < max_retries:
                    wait_time = backoff_seconds * (2 ** attempt)
                    if logger:
                        logger.warning(f"HTTP {resp.status_code} received. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    attempt += 1
                    continue
                else:
                    resp.raise_for_status()

            return resp

        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < max_retries:
                wait_time = backoff_seconds * (2 ** attempt)
                if logger:
                    logger.warning(f"Network error {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                attempt += 1
            else:
                if logger:
                    logger.error(f"Failed to fetch {url} after {max_retries} retries: {e}")
                raise e
