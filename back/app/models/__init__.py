from app.models.base import Base, BaseModel
from app.models.user import User, UserRole
from app.models.supplier import Supplier, SupplierStatus
from app.models.rating import Rating
from app.models.email import (
    EmailTemplate,
    EmailCampaign,
    CampaignRecipient,
    EmailThread,
    EmailDirection,
    CampaignStatus,
)
from app.models.product_import import ProductImport, ImportStatus
from app.models.product import Product  # ДОБАВЛЕНО
from app.models.audit_log import AuditLog, AuditAction

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "UserRole",
    "Supplier",
    "SupplierStatus",
    "Rating",
    "EmailTemplate",
    "EmailCampaign",
    "CampaignRecipient",
    "EmailThread",
    "EmailDirection",
    "CampaignStatus",
    "ProductImport",
    "ImportStatus",
    "Product",  # ДОБАВЛЕНО
    "AuditLog",
    "AuditAction",
]
from app.models.supplier_request import SupplierRequest
