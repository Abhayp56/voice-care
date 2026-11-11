"""Operational context shared by patient conversation and routing agents.

The database category-to-department mapping is the routing authority. This
module adds plain-language guidance without treating a ward as a department.
"""

from typing import Any


LOCATION_POLICY = (
    "A ward, room, ICU, emergency area, OPD, laboratory, washroom, or corridor is a "
    "reported location, not a department. Use only the ward or area the patient names; "
    "do not invent ward numbers or infer a department from a ward number. Do not ask for "
    "a patient's bed number, diagnosis, or other unnecessary medical details."
)

CATEGORY_GUIDANCE = {
    "drinking water": "Facilities response: check the reported tap or supply, arrange a safe alternative if needed, and route suspected water-quality concerns to the hospital's responsible safety process.",
    "washroom cleanliness": "Sanitation response: inspect the named washroom or area, clean it, restock supplies if needed, and report any maintenance issue separately.",
    "medicine availability": "Pharmacy response: check stock and the normal dispensing process. Do not recommend a substitute medicine, dose, or change to treatment.",
    "bed availability": "Administration or bed-management response: check the reported availability issue and follow the hospital's placement process. Do not promise a bed.",
    "electricity problem": "Facilities response: inspect the reported electrical issue and follow hospital safety procedures. Do not instruct patients to touch equipment or attempt repairs.",
    "staff availability": "Administration response: check the reported service area and staffing or roster process. Do not infer negligence or identify an individual as responsible.",
}


def build_hospital_context(
    categories: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    departments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build prompt context from the live, approved hospital directory."""
    mappings_by_category = {str(item.get("category_id")): item for item in mappings}
    departments_by_id = {str(item.get("id")): item for item in departments}
    routes = []
    for category in categories:
        category_id = str(category.get("id", ""))
        category_name = category.get("name")
        if not category_name:
            continue
        mapping = mappings_by_category.get(category_id, {})
        department_id = mapping.get("department_id")
        department = departments_by_id.get(str(department_id), {}) if department_id else {}
        guidance = CATEGORY_GUIDANCE.get(
            str(category_name).strip().casefold(),
            "Use the mapped department's published responsibility and normal hospital workflow. Ask a brief clarifying question if the reported issue does not fit clearly.",
        )
        routes.append({
            "approved_category_id": category_id,
            "approved_category": category_name,
            "mapped_department_id": department_id,
            "mapped_department": department.get("name") or mapping.get("department_name"),
            "department_responsibility": department.get("description"),
            "suggested_operational_response": guidance,
            "default_priority": category.get("default_priority"),
        })
    return {
        "location_policy": LOCATION_POLICY,
        "routing_policy": "Only a configured category-to-department mapping determines the receiving dashboard. If no category or mapping fits, ask for clarification; never invent a route.",
        "service_routes": routes,
    }
