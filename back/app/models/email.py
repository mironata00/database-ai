from sqlalchemy import Column, String, Text, Integer, Boolean, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class EmailDirection(str, enum.Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailTemplate(BaseModel):
    __tablename__ = "email_templates"
    
    name = Column(String(255), nullable=False, unique=True, index=True)
    subject_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)
    description = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    created_by_user = relationship("User", back_populates="email_templates")
    campaigns = relationship("EmailCampaign", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EmailTemplate {self.name}>"


class EmailCampaign(BaseModel):
    __tablename__ = "email_campaigns"
    
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id", ondelete="SET NULL"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    rendered_body = Column(Text)
    
    status = Column(SQLEnum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT, index=True)
    
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    # Rendering context
    context_data = Column(JSON)
    
    # Relationships
    template = relationship("EmailTemplate", back_populates="campaigns")
    created_by_user = relationship("User", back_populates="email_campaigns")
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<EmailCampaign {self.name} ({self.status})>"


class CampaignRecipient(BaseModel):
    __tablename__ = "campaign_recipients"
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("email_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email = Column(String(255), nullable=False)
    sent_at = Column(String)
    delivered = Column(Boolean, default=False)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    failed = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Tracking
    message_id = Column(String(500))
    
    # Relationships
    campaign = relationship("EmailCampaign", back_populates="recipients")
    supplier = relationship("Supplier", back_populates="campaign_recipients")
    
    def __repr__(self):
        return f"<CampaignRecipient campaign_id={self.campaign_id} supplier_id={self.supplier_id}>"


class EmailThread(BaseModel):
    __tablename__ = "email_threads"
    
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    subject = Column(String(500), nullable=False)
    message_id = Column(String(500), unique=True, index=True)
    in_reply_to = Column(String(500), index=True)
    references = Column(ARRAY(String))
    
    direction = Column(SQLEnum(EmailDirection), nullable=False, index=True)
    
    from_addr = Column(String(255), nullable=False)
    to_addr = Column(ARRAY(String), nullable=False)
    cc_addr = Column(ARRAY(String))
    bcc_addr = Column(ARRAY(String))
    
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Attachments stored in S3/MinIO
    attachments = Column(JSON)
    
    # Parsed data from AI/rules
    parsed_data = Column(JSON)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="email_threads")
    
    def __repr__(self):
        return f"<EmailThread {self.message_id} ({self.direction})>"
