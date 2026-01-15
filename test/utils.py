from typing import Callable, Optional, Dict, Any


def get_institution_id_from_token(token: Optional[str]) -> Optional[str]:
    """Extract selected institution id from a JWT token if present."""
    if not token:
        return None
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        inst_id = decoded.get("tolkevarav", {}).get("selectedInstitution", {}).get("id")
        return inst_id or None
    except Exception:
        return None


def extract_tag_id(tag_response: Dict[str, Any]) -> Optional[str]:
    """Extract a tag id from API response payloads."""
    if not isinstance(tag_response, dict):
        return None
    tag = tag_response.get("tag")
    if isinstance(tag, dict) and tag.get("id"):
        return tag.get("id")
    if tag_response.get("id"):
        return tag_response.get("id")
    return None


def find_tag_id_by_name(tags_data: Dict[str, Any], tag_name: str) -> Optional[str]:
    """Find tag id by name from a tags list payload."""
    if not isinstance(tags_data, dict):
        return None
    for tag in tags_data.get("tags", []):
        if tag.get("name") == tag_name:
            return tag.get("id")
    return None


def get_tag_id(tag_response: Dict[str, Any], tag_name: str, list_tags_fn: Callable[[], Dict[str, Any]]) -> Optional[str]:
    """Get tag id from create response, fallback to list by name."""
    tag_id = extract_tag_id(tag_response)
    if tag_id:
        return tag_id
    try:
        tags_data = list_tags_fn()
    except Exception:
        return None
    return find_tag_id_by_name(tags_data, tag_name)

