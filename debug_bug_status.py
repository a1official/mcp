import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from redmine_cache import cache

async def test():
    # Refresh cache
    await cache.refresh(force=True)
    
    # Get all issues
    df = cache.get_issues()
    
    # Filter NCEL project
    ncel_df = df[df['project_id'] == 6]
    
    # Filter bugs
    bugs_df = ncel_df[ncel_df['tracker_name'] == 'Bug']
    
    print(f"=== Total NCEL Bugs: {len(bugs_df)} ===\n")
    
    # Show status breakdown
    print("Status breakdown:")
    status_counts = bugs_df['status_name'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print("\n=== What we consider 'open' ===")
    open_bugs = bugs_df[~bugs_df['status_name'].isin(['Closed', 'Resolved'])]
    print(f"NOT Closed/Resolved: {len(open_bugs)}")
    
    print("\n=== What Redmine considers 'open' ===")
    # Check if there's an is_closed field or similar
    print("Unique statuses:", bugs_df['status_name'].unique())
    
    print(f"\n=== Cache loaded {len(df)} issues total ===")
    print(f"NCEL has {len(ncel_df)} issues in cache")
    print(f"NCEL has {len(bugs_df)} bugs in cache")

asyncio.run(test())
