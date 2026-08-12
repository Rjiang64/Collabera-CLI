"""
Handles all HTTP routes for customers.
Talks to CustomerService, does not do any banking logic itself.
"""

from fastapi import APIRouter, HTTPException

from app.models.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

# one shared service so data doesn't reset between requests
service = CustomerService()


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(payload: CustomerCreate):
    return service.create_customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        branch_id=payload.branch_id,
    )


@router.get("", response_model=list[CustomerResponse])
def list_customers():
    return service.get_all_customers()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int):
    customer = service.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerUpdate):
    # exclude_unset -> only fields the client actually sent get updated;
    # untouched fields are left alone rather than overwritten with defaults
    updates = payload.model_dump(exclude_unset=True)
    customer = service.update_customer(customer_id, updates)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return customer


@router.delete("/{customer_id}")
def deactivate_customer(customer_id: int):
    # this is a soft delete (sets is_active = False)
    # DELETE from the table — keeps customer history/records intact
    customer = service.deactivate_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return {"message": f"Customer {customer_id} deactivated", "customer": customer}

# NOTE: no role/auth dependency declared on this router — anyone with a
# valid session can create/update/deactivate customers. If Manager-only
# access is expected for write routes, that check isn't enforced here yet.