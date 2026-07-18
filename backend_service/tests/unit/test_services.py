"""Unit tests for Services."""

# pyrefly: ignore [missing-import]
import pytest
from backend_service.core.services import (
    CustomerService,
    SessionService,
    ContextService,
    MessageService,
    AuthenticationService,
)
from backend_service.core.repositories import (
    CustomerRepository,
    SessionRepository,
    ContextRepository,
    MessageRepository,
    AuditRepository,
)
from backend_service.shared.exceptions.backend_exceptions import (
    CustomerNotFoundError,
    SessionExpiredError,
    AuthenticationError,
)

def test_customer_service(db_session):
    cust_repo = CustomerRepository(db_session)
    audit_repo = AuditRepository(db_session)
    service = CustomerService(cust_repo, audit_repo)
    
    cust = service.create_customer("+15550001111", display_name="Bob")
    db_session.commit()
    assert cust.id is not None
    assert cust.display_name == "Bob"
    
    fetched = service.get_customer(cust.id)
    assert fetched.phone_number == "+15550001111"
    
    with pytest.raises(CustomerNotFoundError):
        service.get_customer(99999)

def test_session_service(db_session):
    sess_repo = SessionRepository(db_session)
    audit_repo = AuditRepository(db_session)
    service = SessionService(sess_repo, audit_repo)
    
    sess = service.create_session(customer_id=1, authed=True, session_id="test_sess_100")
    db_session.commit()
    assert sess.session_id == "test_sess_100"
    assert sess.authed is True
    
    valid = service.validate_session("test_sess_100")
    assert valid.id == sess.id
    
    service.close_session("test_sess_100")
    db_session.commit()
    with pytest.raises(SessionExpiredError):
        service.validate_session("test_sess_100")

def test_context_service(db_session):
    ctx_repo = ContextRepository(db_session)
    service = ContextService(ctx_repo)
    
    service.save_context("sess_x", "step", "greeting")
    db_session.commit()
    
    data = service.load_context("sess_x")
    assert data.get("step") == "greeting"
    
    service.update_context("sess_x", {"step": "verification", "attempts": "1"})
    db_session.commit()
    assert service.load_context("sess_x") == {"step": "verification", "attempts": "1"}

def test_message_service(db_session):
    msg_repo = MessageRepository(db_session)
    service = MessageService(msg_repo)
    
    service.save_messages("sess_x", "user", "hi")
    db_session.commit()
    history = service.load_history("sess_x")
    assert len(history) == 1
    assert history[0].message == "hi"

def test_authentication_service(db_session, test_container):
    auth_service = test_container.authentication_service
    session = auth_service.authenticate_customer("+15557778888")
    db_session.commit()
    
    assert session is not None
    assert session.authed is True
    assert session.customer_id is not None
