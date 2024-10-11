from enum import Enum

class Role(Enum):
    USER = "user"
    CREATOR = "creator"
    ADMIN = "admin"

class CreatorRequestStatus(Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

class PurchaseStatus(Enum):
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"

class CashoutStatus(Enum):
    PENDING = "PENDING"
    PAID = "PAID"