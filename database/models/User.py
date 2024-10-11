from database.models.Base import Base
from sqlalchemy import String, Integer, Boolean, DateTime, func, event, Enum
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from utils.isValidEmail import isValidEmail
from utils.enums import Role
from typing import List
import bcrypt
import uuid

class User(Base):
    # To set a table name 
    __tablename__ = "users"

    # To define your columns, follow this format
    # column_name = Mapped[type for column] = mapped_column(specific details about type for column, constraints)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    fullName: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(60), nullable=False)
    bio: Mapped[str] = mapped_column(String(1000), nullable=False)
    profilePicture: Mapped[str] = mapped_column(String(256), nullable=False)
    coverPicture: Mapped[str] = mapped_column(String(256), nullable=False)
    verificationToken: Mapped[str] = mapped_column(String(256), nullable=True)
    isVerified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verifiedAt: Mapped[DateTime] = mapped_column(DateTime, nullable=True, default=None)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.USER)
    # For Stripe purposes we need to save the "customer_id" to our database, this is necessary for
    # creating a Customer in our Stripe account. And we can then use this "customer_id" during the
    # creation of a "Subscription" object from Stripe.
    customer_id: Mapped[str] = mapped_column(String(256), nullable=True, default=None)
    # For Cashout Feature
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    createdAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now())
    updatedAt: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Assocations

    # A User can only have 1 CreatorRequest
    creator_request: Mapped['CreatorRequest'] = relationship(back_populates = "user")

    # A User can create many Subscriptions
    subscriptions_for_users: Mapped[List['Subscription']] = relationship(back_populates = "user")

    # A User can create many Purchases
    purchases_made: Mapped[List['Purchase']] = relationship(back_populates = "user")

    # A User can create many Cashouts
    cashouts_made: Mapped[List['Cashout']] = relationship(back_populates = "user")

    # It's not enough for you to set "nullable" to "False". You can still enter in an empty string for a column 
    # and satisfy the critiera for a row to be added to the users table. So to fix that we will use whats called the
    # validates decorator and pass in bunch of strings matching the column name we would like the validator logic 
    # we define to run on.
    @validates('fullName', 'username', 'password', 'bio', 'profilePicture')
    def validate_not_empty(self, _, value):
        if not value or value.strip() == '':
            raise ValueError("Please check all inputs!")
        return value
        
    @validates('email')
    def emailChecker(self, key, value):
        if not value or value.strip() == '':
            raise ValueError("Please check all inputs!")
        elif not isValidEmail(value):
            raise ValueError(f"Please provide a valid {key}!")
        return value

    # To define an instance method just use the "def" keyword as you usually do. This is super useful when you are 
    # trying to execute some logic within your objet. For example if you are comparing password this would be 
    # awesome. 
    def comparePassword(self, guess: str) -> bool:
        isCorrect = bcrypt.checkpw(guess.encode('utf-8'), self.password.encode('utf-8'))
        return isCorrect

    # To define the string representation of an instance/object of type User
    def __repr__(self):
        return f"User('{self.id}', '{self.createdAt}', '{self.updatedAt}')"

# To define any "Events" also known as "Middleware Hooks", you first need to define a listener function 
# which is defined by it having these 3 paramters: mapper, connection, and target. Once you have successfully 
# created that function you then need to load in "sqlalchemy.event" and pass into it the 3 arguments of model, 
# mapper event, and listener function. This does the actual linking to the model.  

def beforeCreatingUserListener(mapper, connection, target):
    # Before creating a User we want to hash the password. Because making it human readable allows bad
    # actors to easily steal account information
    randomBytes = bcrypt.gensalt(10)
    # Note: In Pythons version of "bcrypt" you don't have access to the "hash" method, instead we use
    # whats called the "hashpw()" method. And the first argument is the value you would like to hash, and 
    # the second is the salt (randombytes). The important thing to keep in mind is that the first argument
    # MUST be in the form of a byte object. So use the "encode()" method along with a character encoding
    # type to use the "hashpw()" method.
    target.password = bcrypt.hashpw(target.password.encode('utf-8'), randomBytes)

event.listen(User, 'before_insert', beforeCreatingUserListener)