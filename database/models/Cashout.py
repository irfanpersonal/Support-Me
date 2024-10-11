from database.models.Base import Base
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from utils.enums import CashoutStatus
import uuid

class Cashout(Base):
    # To set a table name 
    __tablename__ = "cashouts"

    # To define your columns, follow this format
    # column_name = Mapped[type for column] = mapped_column(specific details about type for column, constraints)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CashoutStatus] = mapped_column(Enum(CashoutStatus), nullable=False, default=CashoutStatus.PENDING)

    # Note - Think of the "createdAt" now as the "startDate" for when the subscription payment started happening
    createdAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    updatedAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Assocations

    # A Cashout must be tied to a Single User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user: Mapped['User'] = relationship("User", back_populates="cashouts_made")

    # It's not enough for you to set "nullable" to "False". You can still enter in an empty string for a column 
    # and satisfy the critiera for a row to be added to the users table. So to fix that we will use whats called the
    # validates decorator and pass in bunch of strings matching the column name we would like the validator logic 
    # we define to run on.
    @validates('amount')
    def notNegative(self, key, value):
        if not value:
            raise ValueError(f'Please provide a valid value for {key}!')
        elif int(value) < 0:
            raise ValueError('Price must be a positive number!')
        return value
    
    # To define the string representation of an instance/object of type Subscription
    def __repr__(self):
        return f"Cashout('{self.id}', '{self.createdAt}', '{self.updatedAt}')"