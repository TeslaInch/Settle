import asyncio
from typing import Dict

# In-memory lock for agreements
# In production, use Redis or similar for distributed locking
agreement_locks: Dict[str, asyncio.Lock] = {}


def get_agreement_lock(agreement_id: str) -> asyncio.Lock:
    """Get or create a lock for an agreement."""
    if agreement_id not in agreement_locks:
        agreement_locks[agreement_id] = asyncio.Lock()
    return agreement_locks[agreement_id]


async def release_agreement_lock(agreement_id: str) -> None:
    """Release the lock for an agreement."""
    if agreement_id in agreement_locks:
        del agreement_locks[agreement_id]
