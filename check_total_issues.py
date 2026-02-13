import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_total():
    url = os.getenv("REDMINE_URL")
    key = os.getenv("REDMINE_API_KEY")
    
    async with httpx.AsyncClient() as client:
        # Get first page to see total count
        response = await client.get(
            f"{url}/issues.json",
            headers={"X-Redmine-API-Key": key},
            params={"limit": 1, "project_id": 6, "status_id": "*"},
            timeout=30.0
        )
        data = response.json()
        
        print(f"Total issues in NCEL project: {data.get('total_count')}")
        print(f"Offset: {data.get('offset')}")
        print(f"Limit: {data.get('limit')}")
        
        # Check bugs specifically
        response2 = await client.get(
            f"{url}/issues.json",
            headers={"X-Redmine-API-Key": key},
            params={"limit": 1, "project_id": 6, "status_id": "open", "tracker_id": 1},  # Assuming tracker_id 1 is Bug
            timeout=30.0
        )
        data2 = response2.json()
        print(f"\nOpen bugs (tracker_id=1): {data2.get('total_count')}")
        
        # Try without tracker filter
        response3 = await client.get(
            f"{url}/issues.json",
            headers={"X-Redmine-API-Key": key},
            params={"limit": 1, "project_id": 6, "status_id": "open"},
            timeout=30.0
        )
        data3 = response3.json()
        print(f"All open issues: {data3.get('total_count')}")

asyncio.run(check_total())
