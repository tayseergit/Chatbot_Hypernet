"""Customer business service."""

from typing import Optional
from backend_service.core.models.customer import Customer
from backend_service.core.repositories.customer_repository import CustomerRepository
from backend_service.core.repositories.audit_repository import AuditRepository
from backend_service.shared.exceptions.backend_exceptions import CustomerNotFoundError
from backend_service.shared.decorators import log_execution, audit

class CustomerService:
    """Manages customer lifecycle and operations."""
    def __init__(self, customer_repo: CustomerRepository, audit_repo: Optional[AuditRepository] = None):
        self._customer_repo = customer_repo
        self._audit_repo = audit_repo

    @log_execution
    @audit("Create Customer")
    def create_customer(self, phone_number: str, display_name: Optional[str] = None, crm_customer_id: Optional[str] = None) -> Customer:
        """Create and persist a new customer."""
        existing = self._customer_repo.get_by_phone(phone_number)
        if existing:
            if display_name and existing.display_name != display_name:
                existing.display_name = display_name
            if crm_customer_id and not existing.crm_customer_id:
                existing.crm_customer_id = crm_customer_id
            return existing
        return self._customer_repo.create(phone_number=phone_number, display_name=display_name, crm_customer_id=crm_customer_id)

    @log_execution
    def get_customer(self, customer_id: int) -> Customer:
        """Fetch customer by ID or raise CustomerNotFoundError."""
        customer = self._customer_repo.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(f"ID:{customer_id}")
        return customer

    @log_execution
    def get_customer_by_phone(self, phone_number: str) -> Optional[Customer]:
        """Fetch customer by phone number."""
        return self._customer_repo.get_by_phone(phone_number)

    @log_execution
    @audit("Update Customer Status")
    def update_customer_status(self, customer_id: int, new_status: str) -> Customer:
        """Update a customer's lifecycle status."""
        customer = self.get_customer(customer_id)
        return self._customer_repo.update_status(customer, new_status)
