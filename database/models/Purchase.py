from database.models.Base import Base
from sqlalchemy import String, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from utils.enums import PurchaseStatus
import uuid

class Purchase(Base):
    # To set a table name 
    __tablename__ = "purchases"

    # To define your columns, follow this format
    # column_name = Mapped[type for column] = mapped_column(specific details about type for column, constraints)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    # Notice the distinction. This is so we can get the information regarding the purchase of the subscription from Stripe
    stripe_subscription_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # By default when you purchase a subscription the status will be set to "ACTIVE"
    status: Mapped[PurchaseStatus] = mapped_column(Enum(PurchaseStatus), nullable=False, default=PurchaseStatus.ACTIVE)

    # Note - Think of the "createdAt" now as the "startDate" for when the subscription payment started happening
    createdAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    updatedAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Assocations

    # A Purchase must be tied to a Single Subscription
    subscription_id: Mapped[str] = mapped_column(String(36), ForeignKey('subscriptions.id'), nullable=True)
    subscription: Mapped['Subscription'] = relationship("Subscription", back_populates="purchases")

    # A Purchase must be tied to a Single User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user: Mapped['User'] = relationship("User", back_populates="purchases_made")

    # It's not enough for you to set "nullable" to "False". You can still enter in an empty string for a column 
    # and satisfy the critiera for a row to be added to the users table. So to fix that we will use whats called the
    # validates decorator and pass in bunch of strings matching the column name we would like the validator logic 
    # we define to run on.
    @validates('stripe_subscription_id', 'subscription_id', 'user_id')
    def validate_not_empty(self, key, value):
        # Skip validation if the value is explicitly None (e.g., during deletion or nullifying operations)
        if value is None:
            return value
        if not value or value.strip() == '':
            raise ValueError(f"Validation Error: {key} cannot be empty! Found value: {value}")
        return value
    
    # To define the string representation of an instance/object of type Subscription
    def __repr__(self):
        return f"Purchase('{self.id}', '{self.createdAt}', '{self.updatedAt}')"