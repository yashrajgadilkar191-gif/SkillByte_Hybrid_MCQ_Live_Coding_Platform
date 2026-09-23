import os
import time

import requests


JUDGE0_URL = os.getenv("JUDGE0_URL", "http://localhost:2358")

LANGUAGE_IDS = {
    "python": 71,
    "java": 62,
    "cpp": 54,
}


class Judge0Service:
    """Client for communicating with the self-hosted Judge0 API."""

    @staticmethod
    def submit_code(
        source_code,
        language_id,
        stdin="",
        expected_output=None,
        cpu_time_limit=None,
        memory_limit=None,
    ):
        """Submit source code to Judge0 and return the submission token."""

        payload = {
            "language_id": language_id,
            "source_code": source_code,
            "stdin": stdin,
        }

        if expected_output is not None:
            payload["expected_output"] = expected_output

        if cpu_time_limit is not None:
            payload["cpu_time_limit"] = cpu_time_limit

        if memory_limit is not None:
            payload["memory_limit"] = memory_limit

        response = requests.post(
            f"{JUDGE0_URL}/submissions",
            params={
                "base64_encoded": "false",
                "wait": "false",
            },
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()["token"]

    @staticmethod
    def get_submission(token):
        """Get the current result of a Judge0 submission."""

        response = requests.get(
            f"{JUDGE0_URL}/submissions/{token}",
            params={
                "base64_encoded": "false",
            },
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def wait_for_result(token, timeout=30, poll_interval=1):
        """Poll Judge0 until the submission finishes."""

        start_time = time.time()

        while time.time() - start_time < timeout:
            result = Judge0Service.get_submission(token)

            status_id = result.get("status", {}).get("id")

            # 1 = In Queue
            # 2 = Processing
            # 3+ = Finished
            if status_id not in (1, 2):
                return result

            time.sleep(poll_interval)

        raise TimeoutError("Judge0 submission timed out.")

    @staticmethod
    def execute_test_case(
        source_code,
        language_id,
        test_case,
    ):
        """Execute one SkillByte test case through Judge0."""

        memory_limit_kb = test_case.memory_limit * 1024

        token = Judge0Service.submit_code(
            source_code=source_code,
            language_id=language_id,
            stdin=test_case.input_data,
            expected_output=test_case.expected_output,
            cpu_time_limit=test_case.time_limit,
            memory_limit=memory_limit_kb,
        )

        result = Judge0Service.wait_for_result(token)

        return {
            "token": token,
            "result": result,
            "status_id": result.get("status", {}).get("id"),
            "status_description": result.get("status", {}).get("description"),
            "stdout": result.get("stdout"),
            "stderr": result.get("stderr"),
            "compile_output": result.get("compile_output"),
            "message": result.get("message"),
            "time": result.get("time"),
            "memory": result.get("memory"),
        }