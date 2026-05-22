import os
import time
import requests

BASE = "http://localhost:8001"

EMAIL = "john@example.com"
PASSWORD = "testpass123"

FILE_PATH = r"F:\legal-doc-analyzer\backend\test_documents\test_contract.docx"
FILE_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def login():
    r = requests.post(f"{BASE}/auth/login", data={"username": EMAIL, "password": PASSWORD})
    print("LOGIN STATUS:", r.status_code)
    if r.status_code >= 400:
        print("LOGIN BODY:", r.text)
    r.raise_for_status()
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload(headers):
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"FILE NOT FOUND: {FILE_PATH}")

    filename = os.path.basename(FILE_PATH)

    with open(FILE_PATH, "rb") as f:
        r = requests.post(
            f"{BASE}/documents/upload",
            headers=headers,
            files={"file": (filename, f, FILE_MIME)},
        )

    print("UPLOAD STATUS:", r.status_code)
    if r.status_code >= 400:
        print("UPLOAD BODY (important):")
        print(r.text)

    r.raise_for_status()
    return r.json()["id"]


def process_async(headers, doc_id):
    r = requests.post(f"{BASE}/documents/{doc_id}/process-async?force=true", headers=headers)
    print("PROCESS-ASYNC STATUS:", r.status_code)
    if r.status_code >= 400:
        print("PROCESS-ASYNC BODY:")
        print(r.text)
    r.raise_for_status()
    return r.json()["job_id"]


def wait_job(headers, job_id, timeout_sec=300):
    start = time.time()
    while True:
        r = requests.get(f"{BASE}/jobs/{job_id}", headers=headers)
        if r.status_code >= 400:
            print("JOB STATUS ERROR:", r.status_code, r.text)
        r.raise_for_status()
        data = r.json()
        if data["status"] in ("finished", "failed"):
            return data
        if time.time() - start > timeout_sec:
            raise TimeoutError("Job did not finish in time")
        time.sleep(2)


def rag_query(headers, doc_id):
    r = requests.post(
        f"{BASE}/rag/query",
        headers=headers,
        json={
            "query": "What are the payment terms?",
            "top_k": 3,
            "document_id": doc_id,
        },
    )
    print("RAG QUERY STATUS:", r.status_code)
    if r.status_code >= 400:
        print("RAG QUERY BODY:")
        print(r.text)
    r.raise_for_status()
    return r.json()


def main():
    headers = login()

    doc_id = upload(headers)
    print("Uploaded doc_id:", doc_id)

    job_id = process_async(headers, doc_id)
    print("Job_id:", job_id)

    job = wait_job(headers, job_id)
    print("Final job status:", job["status"])
    print("Job result success:", job.get("result", {}).get("success"))

    if job["status"] != "finished" or not job.get("result", {}).get("success"):
        print("❌ Job did not succeed, stopping.")
        return

    results = rag_query(headers, doc_id)
    print("Retrieved chunks:", len(results["results"]))
    if results["results"]:
        print("Top chunk similarity:", results["results"][0]["similarity"])
        print("Top chunk preview:")
        print(results["results"][0]["text"][:250])


if __name__ == "__main__":
    main()