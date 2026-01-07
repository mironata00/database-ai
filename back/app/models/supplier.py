from sqlalchemy import Column, String, Text, Enum as SQLEnum, ARRAY, Float, Boolean, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class SupplierStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    BLACKLIST = "BLACKLIST"
    INACTIVE = "INACTIVE"


class Supplier(BaseModel):
    __tablename__ = "suppliers"

    # Basic Info
    name = Column(String(500), nullable=False, index=True)
    inn = Column(String(12), unique=True, nullable=False, index=True)
    kpp = Column(String(9))
    ogrn = Column(String(15))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(500))

    # Contact Person
    contact_person = Column(String(255))
    contact_position = Column(String(255))
    contact_phone = Column(String(50))
    contact_email = Column(String(255))

    # Business Info
    status = Column(SQLEnum(SupplierStatus), nullable=False, default=SupplierStatus.ACTIVE, index=True)
    legal_address = Column(Text)
    actual_address = Column(Text)
    delivery_regions = Column(ARRAY(String))
    payment_terms = Column(Text)
    min_order_sum = Column(DECIMAL(12, 2))

    # Rating & Blacklist
    rating = Column(Float, default=0.0)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text)

    # File References
    raw_data_url = Column(String(1000))

    # Tags (denormalized for quick access)
    tags_array = Column(ARRAY(String))
    
    # Categories/Directions (электрика, сантехника, etc.)
    categories = Column(ARRAY(String), nullable=True, default=[])
    
    # Color for visual categorization
    color = Column(String(7), nullable=False, server_default='#3B82F6')

    # Email Thread Tracking
    last_email_sent_at = Column(DateTime)
    email_thread_id = Column(String(255))

    # Import Tracking
    import_source = Column(String(100))

    # Activity tracking
    last_activity_at = Column(DateTime)

    # Notes
    notes = Column(Text)

    # Relationships
    ratings = relationship("Rating", back_populates="supplier", cascade="all, delete-orphan")
    email_threads = relationship("EmailThread", back_populates="supplier", cascade="all, delete-orphan")
    product_imports = relationship("ProductImport", back_populates="supplier", cascade="all, delete-orphan")
    campaign_recipients = relationship("CampaignRecipient", back_populates="supplier", cascade="all, delete-orphan")

    # Relationship to products
    products = relationship(
        "Product",
        back_populates="supplier",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Supplier {self.name} ({self.inn})>"