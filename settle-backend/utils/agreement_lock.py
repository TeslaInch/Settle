#import neededfiles and make sure logic works as expected
import hashlib
import json
from datetime import datetime, timezone


def seal_agreement(
    agreement: dict,
    initiator_phone: str,
    counterparty_phone: str,
) -> dict:
    """
    Pure function — builds a deterministic seal payload and SHA256 hash.
    Same inputs always produce the same hash.

    Returns:
        {
            "seal_payload": dict,   # the canonical payload that was hashed
            "seal_hash":    str,    # hex SHA256 of the JSON-serialised payload
        }
    """
    payload = {
        "title":              agreement["title"],
        "amount":             str(agreement["amount"]),   # str for float stability
        "terms":              agreement["terms"],
        "repayment_date":     str(agreement["repayment_date"]),
        "initiator_phone":    initiator_phone,
        "counterparty_phone": counterparty_phone,
        "sealed_at":          datetime.now(timezone.utc).isoformat(),
    }

    # Deterministic serialisation — sorted keys, no extra whitespace
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    seal_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {"seal_payload": payload, "seal_hash": seal_hash}
