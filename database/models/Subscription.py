from database.models.Base import Base
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, event
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from utils.deleteFile import deleteFile
from utils.stripe import getStripe
import uuid
from typing import List

class Subscription(Base):
    # To set a table name 
    __tablename__ = "subscriptions"

    # To define your columns, follow this format
    # column_name = Mapped[type for column] = mapped_column(specific details about type for column, constraints)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    image: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    # Stripe API requires that when creating a PaymentIntent the "amount" should be an integer value representing 
    # the smallest currency unit. So if something is $5 that would mean the price should be 500.
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stripe Product ID is needed to extract the price_id within it for Stripe to then create the "Subscription"
    # object.
    product_id: Mapped[str] = mapped_column(String(256), nullable=False)

    createdAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    updatedAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Assocations

    # A Subscription must be tied to a Single User
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user: Mapped['User'] = relationship(back_populates = "subscriptions_for_users")

    # A Subscription has many Purchases
    purchases: Mapped[List["Purchase"]] = relationship(back_populates = "subscription")

    # It's not enough for you to set "nullable" to "False". You can still enter in an empty string for a column 
    # and satisfy the critiera for a row to be added to the users table. So to fix that we will use whats called the
    # validates decorator and pass in bunch of strings matching the column name we would like the validator logic 
    # we define to run on.
    @validates('image', 'title', 'description')
    def validate_not_empty(self, _, value):
        if not value or value.strip() == '':
            raise ValueError("Please check all inputs!")
        return value
    
    @validates('price')
    def notNegative(self, key, value):
        if not value:
            raise ValueError(f'Please provide a valid value for {key}!')
        elif int(value) < 0:
            raise ValueError('Price must be a positive number!')
        return value
    
    # To define the string representation of an instance/object of type Subscription
    def __repr__(self):
        return f"Subscription('{self.id}', '{self.createdAt}', '{self.updatedAt}')"
    
# Before Deleting a Subscription Remove Image and Product from Stripe
# Note - SQLAlchemy's event listeners do not natively support asynchronous functions.
def beforeDeletingSubscriptionListener(mapper, connection, target):
    # Delete Image
    imageLocationWithoutFirstSlash = target.image[1:]
    deleteFile(imageLocationWithoutFirstSlash)
    # Set Status of Stripe Product to False
    stripe = getStripe()
    stripe.Product.modify(
        id = target.product_id,
        active = False
    )    

event.listen(Subscription, 'before_delete', beforeDeletingSubscriptionListener)