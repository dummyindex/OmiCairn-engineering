"""
API Client for Claude Code container to communicate with backend servers.
"""
import requests
import os
from typing import Any, Dict, Optional


def ensure_url_scheme(url: str) -> str:
    """Ensure URL has http:// or https:// scheme prefix."""
    if not url:
        return url
    url = url.rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        # Default to http:// for internal services
        url = f"http://{url}"
    return url


COMPUTATION_SERVER_HOST = ensure_url_scheme(os.getenv("COMPUTATION_SERVER_HOST", ""))
MAIN_SERVER_HOST = ensure_url_scheme(os.getenv("MAIN_SERVER_HOST", ""))
SYSTEM_AGENT_KEY = os.getenv("SYSTEM_AGENT_KEY")


class APIClient:
    """API Client for reporting Claude Code execution status."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.headers = {}
        self._login()

    def _login(self):
        """Login to main server and get token."""
        if not MAIN_SERVER_HOST:
            print("[APIClient] MAIN_SERVER_HOST not configured, skipping login")
            return

        try:
            response = requests.post(
                f"{MAIN_SERVER_HOST}/server/user/login-by-system",
                params={
                    "user_id": self.user_id
                },
                headers={"X-System-Agent-Key": SYSTEM_AGENT_KEY or ""},
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if result.get('code') == 200:
                self.headers = {"token": result.get('data')}
                print(f"[APIClient] Login successful")
            else:
                print(f"[APIClient] Login failed with code {result.get('code')}: {result.get('message')}")
                print("[APIClient] Continuing without authentication...")
        except requests.exceptions.RequestException as e:
            print(f"[APIClient] Network error during login: {str(e)}")
            print("[APIClient] Continuing without authentication...")
        except Exception as e:
            print(f"[APIClient] Login error: {str(e)}")
            print("[APIClient] Continuing without authentication...")

    def report_finished(
        self,
        computation_id: str,
        logs: str = "",
        job_review_passed: bool = True,
        review_error: Optional[str] = None
    ) -> bool:
        """
        Report computation finished to the backend.

        This is the critical callback that updates the node state to FINISHED.

        Args:
            computation_id: The computation ID
            logs: Execution logs
            job_review_passed: Whether the job passed review
            review_error: Optional review error message

        Returns:
            True if report was successful, False otherwise
        """
        url = f"{COMPUTATION_SERVER_HOST}/computation-server/task/finished-report"
        params = {"computation_id": computation_id}

        post_data = {
            "logs": logs,
            "job_review_passed": job_review_passed
        }
        if review_error:
            post_data["review_error"] = review_error

        print(f"[APIClient] Reporting finished state for computation {computation_id}")

        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                response = requests.post(
                    url,
                    params=params,
                    json=post_data,
                    headers=self.headers,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 200:
                        print(f"[APIClient] Successfully reported finished state")
                        return True
                    else:
                        print(f"[APIClient] Report finished failed: {result.get('message')}")
                else:
                    print(f"[APIClient] Report finished HTTP error: {response.status_code}")

                attempts += 1
                if attempts < max_attempts:
                    import time
                    time.sleep(2)

            except requests.exceptions.RequestException as e:
                print(f"[APIClient] Network error reporting finished: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    import time
                    time.sleep(2)
            except Exception as e:
                print(f"[APIClient] Error reporting finished: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    import time
                    time.sleep(2)

        print(f"[APIClient] Failed to report finished state after {max_attempts} attempts")
        return False

    def report_failed(
        self,
        computation_id: str,
        error_description: str,
        logs: str = ""
    ) -> bool:
        """
        Report computation failed to the backend.

        Args:
            computation_id: The computation ID
            error_description: Description of the error
            logs: Execution logs

        Returns:
            True if report was successful, False otherwise
        """
        url = f"{COMPUTATION_SERVER_HOST}/computation-server/task/failed-report"
        params = {"computation_id": computation_id}

        post_data = {
            "logs": logs,
            "error_description": error_description
        }

        print(f"[APIClient] Reporting failed state for computation {computation_id}")

        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                response = requests.post(
                    url,
                    params=params,
                    json=post_data,
                    headers=self.headers,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 200:
                        print(f"[APIClient] Successfully reported failed state")
                        return True
                    else:
                        print(f"[APIClient] Report failed: {result.get('message')}")
                else:
                    print(f"[APIClient] Report failed HTTP error: {response.status_code}")

                attempts += 1
                if attempts < max_attempts:
                    import time
                    time.sleep(2)

            except requests.exceptions.RequestException as e:
                print(f"[APIClient] Network error reporting failed: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    import time
                    time.sleep(2)
            except Exception as e:
                print(f"[APIClient] Error reporting failed: {str(e)}")
                attempts += 1
                if attempts < max_attempts:
                    import time
                    time.sleep(2)

        print(f"[APIClient] Failed to report failed state after {max_attempts} attempts")
        return False

    def create_figure(
        self,
        computation_id: str,
        figure_name: str,
        suffix: str,
        node_id: str
    ) -> Optional[dict]:
        """
        Create a figure entry and get S3 upload keys.

        This registers a figure with the backend and returns the S3 keys
        for uploading both the original image and its thumbnail.

        Args:
            computation_id: The computation ID
            figure_name: Name of the figure file
            suffix: File extension (e.g., 'png', 'jpg', 'pdf')
            node_id: The node ID

        Returns:
            Dict with 'key' and 'thumbnailKey' for S3 upload, or None on failure
        """
        url = f"{MAIN_SERVER_HOST}/server/figure/create"
        params = {
            "computation_id": computation_id,
            "figure_name": figure_name,
            "suffix": suffix,
            "node_id": node_id
        }

        print(f"[APIClient] Creating figure: {figure_name} (suffix: {suffix})")

        try:
            response = requests.post(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    data = result.get('data')
                    print(f"[APIClient] Figure created successfully: key={data.get('key')}")
                    return data
                else:
                    print(f"[APIClient] Create figure failed: {result.get('message')}")
            else:
                print(f"[APIClient] Create figure HTTP error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"[APIClient] Network error creating figure: {str(e)}")
        except Exception as e:
            print(f"[APIClient] Error creating figure: {str(e)}")

        return None

    def get_computation_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get computation details for a node"""
        try:
            latest_computation_response = requests.get(
                f"{MAIN_SERVER_HOST}/server/computation/latest-by-node/get?node_id={node_id}",
                timeout=30,
                headers=self.headers
            )
            latest_computation_response.raise_for_status()
            latest_computation_result = latest_computation_response.json()
            if latest_computation_result.get('code') != 200:
                return None
            computation_basic_info = latest_computation_result.get('data', {})
        except Exception as e:
            print(f"Error getting computation details: {str(e)}")
            return None
        
        computation_id = latest_computation_result.get('data', {}).get('id')
        try:
            response = requests.get(
                f"{COMPUTATION_SERVER_HOST}/computation-server/computation/get-logs?computation_id={computation_id}",
                timeout=30,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()    
            computation_logs = result.get('data', None)
        except Exception as e:
            print(f"Error getting computation logs: {str(e)}")
            computation_logs = None

        function_block_id = computation_basic_info.get('functionBlockId')
        function_block_version_id = computation_basic_info.get('functionBlockVersionId')
        if not function_block_id or not function_block_version_id:
            function_block_info = None
            function_block_version_info = None
        else:
            try:
                response = requests.get(
                    f"{MAIN_SERVER_HOST}/server/function-block-v1/get-information?function_block_id={function_block_id}",
                    timeout=30,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()    
                if result.get('code') == 200:
                    function_block_info = result.get('data', None)
                else:
                    function_block_info = None
            except Exception as e:
                print(f"Error getting function block info: {str(e)}")
                function_block_info = None

            try:
                response = requests.get(
                    f"{MAIN_SERVER_HOST}/server/function-block-v1/get-version-information?function_block_version_id={function_block_version_id}",
                    timeout=30,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()    
                if result.get('code') == 200:
                    function_block_version_info = result.get('data', None)
                else:
                    function_block_version_info = None

            except Exception as e:
                print(f"Error getting function block version info: {str(e)}")
                function_block_version_info = None
        return {
            "computation_basic_info": computation_basic_info,
            "computation_logs": computation_logs,
            "function_block_info": function_block_info,
            "function_block_version_info": function_block_version_info
        }
