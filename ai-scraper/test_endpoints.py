import asyncio
import httpx
import pandas as pd
import os
import sys

# URL
BASE_URL = "http://localhost:8000/api"

# Create sample file
def create_sample_excel():
    data = [
        {"company_name": "Anthropic", "website": "https://anthropic.com", "country": "USA", "industry": "AI"},
        {"company_name": "OpenAI", "website": "https://openai.com", "country": "USA", "industry": "AI"},
    ]
    df = pd.DataFrame(data)
    filename = "test_batch.xlsx"
    df.to_excel(filename, index=False)
    print(f"Created {filename}")
    return filename

async def run_test():
    filename = create_sample_excel()

    async with httpx.AsyncClient(timeout=30) as client:
        # Check health
        try:
            resp = await client.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                print(f"Health Check: OK ({resp.json()['environment']})")
            else:
                print(f"Health Check Failed: {resp.status_code}")
                return
        except httpx.ConnectError:
             print("Error: Could not connect to localhost:8000. Is the server running?")
             return

        # 1. Upload
        print(f"\n1. Uploading {filename}...")
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            resp = await client.post(f"{BASE_URL}/batches/upload", files=files)

        if resp.status_code != 200:
            print(f"Upload failed: {resp.text}")
            return

        data = resp.json()
        batch_id = data["batch_id"]
        print(f"   Success! Batch ID: {batch_id}")
        print(f"   Found {data['total_companies']} companies.")

        # 2. Confirm
        print(f"\n2. Confirming batch {batch_id}...")
        resp = await client.post(f"{BASE_URL}/batches/{batch_id}/confirm")
        if resp.status_code != 200:
            print(f"Confirm failed: {resp.text}")
            return
        print(f"   Confirmed: {resp.json()['message']}")

        # 3. Poll Status
        print("\n3. Polling status (Ctrl+C to stop)...")
        while True:
            resp = await client.get(f"{BASE_URL}/batches/{batch_id}/status")
            status = resp.json()
            counts = status["counts"]

            # Print status line
            status_line = (f"   Status: {status['status']} | "
                           f"Pending: {counts['pending']} | Scraping: {counts['scraping']} | "
                           f"Scraped: {counts['scraped']} | Analyzing: {counts['analyzing']} | "
                           f"Complete: {counts['complete']} | Errors: {counts['error']}")
            sys.stdout.write(f"\r{status_line}")
            sys.stdout.flush()

            if status['status'] in ["completed", "completed_with_errors", "failed"]:
                print("\n\nBatch processing finished!")
                break

            await asyncio.sleep(2)

        # 4. Get Results
        print("\n4. Fetching results...")
        resp = await client.get(f"{BASE_URL}/companies/batch/{batch_id}")
        if resp.status_code == 200:
            companies = resp.json()
            print(f"   Got {len(companies)} companies.")
            for c in companies:
                print(f"   - {c.get('company_name')}: {c.get('status')} | Decision: {c.get('decision')} (Confidence: {c.get('confidence')})")
        else:
             print(f"   Failed to get results: {resp.status_code}")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest stopped.")
