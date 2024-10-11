from database.models.Base import Base
from sqlalchemy import String, DateTime, func, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from utils.enums import CreatorRequestStatus
import uuid

class CreatorRequest(Base):
    # To set a table name 
    __tablename__ = "creator_requests"

    # To define your columns, follow this format
    # column_name = Mapped[type for column] = mapped_column(specific details about type for column, constraints)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    explanation: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Status of Creator Request
    status: Mapped[CreatorRequestStatus] = mapped_column(Enum(CreatorRequestStatus), nullable=False, default=CreatorRequestStatus.PENDING)

    createdAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    updatedAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Assocations

    # A CreatorRequest must be tied to Single User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    user: Mapped['User'] = relationship("User", back_populates="creator_request")

    # It's not enough for you to set "nullable" to "False". You can still enter in an empty string for a column 
    # and satisfy the critiera for a row to be added to the users table. So to fix that we will use whats called the
    # validates decorator and pass in bunch of strings matching the column name we would like the validator logic 
    # we define to run on.
    @validates('explanation')
    def validate_not_empty(self, _, value):
        if not value or value.strip() == '':
            raise ValueError("Please check all inputs!")
        return value

    # To define the string representation of an instance/object of type CreatorRequest
    def __repr__(self):
        return f"CreatorRequest('{self.id}', '{self.createdAt}', '{self.updatedAt}')"