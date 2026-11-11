"""Shared canonical complaint creation policy used by API and conversation intake."""

from fastapi import HTTPException, status

from app.models.complaint import ComplaintCreate, ComplaintStatus


def create_complaint_record(payload: ComplaintCreate, *, complaint_repo, dept_repo, history_repo):
    """Validate category, apply trusted routing/priority, then use canonical repositories."""
    category = dept_repo.get_category_by_id(payload.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category_id '{payload.category_id}'. Category does not exist.",
        )

    department_id = dept_repo.get_department_for_category(payload.category_id)
    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No mapped department found for category '{category.get('name')}'.",
        )
    department = dept_repo.get_department_by_id(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid department_id '{department_id}'. Department does not exist.",
        )

    created = complaint_repo.create_complaint(
        description=payload.description,
        category_id=payload.category_id,
        department_id=department_id,
        patient_name=payload.patient_name,
        patient_phone=payload.patient_phone,
        language=payload.language or "en",
        priority=category.get("default_priority", "medium"),
        status=ComplaintStatus.RECEIVED.value,
    )
    history_repo.record_transition(
        complaint_id=created["id"],
        new_status=ComplaintStatus.RECEIVED.value,
        old_status=None,
        note=f"Complaint lodged via {payload.language.upper()} voice interface. Routed to {department.get('name')}.",
    )
    created["department_name"] = department.get("name")
    created["category_name"] = category.get("name")
    return created
