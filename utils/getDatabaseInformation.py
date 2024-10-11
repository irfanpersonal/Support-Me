from typing import Tuple, Type, ForwardRef
from sqlalchemy.ext.asyncio import AsyncSession

# Forward reference to Models Type (defined later in the if block)
ModelsType = ForwardRef('Models')

# Type Alias with Forward Reference to AsyncSession and ModelsType
DatabaseInformation = Tuple[AsyncSession, Type['Models']]

def getDatabaseInformation() -> DatabaseInformation:
    from database.Session import Session
    from app import User as UserModel
    from app import CreatorRequest as CreatorRequestModel
    from app import Subscription as SubscriptionModel
    from app import Purchase as PurchaseModel
    from app import Cashout as CashoutModel
    class Models:
        User = UserModel
        CreatorRequest = CreatorRequestModel
        Subscription = SubscriptionModel
        Purchase = PurchaseModel
        Cashout = CashoutModel
    return (Session, Models)

# By wrapping this code inside of this  we prevent the circular dependency error.
if __name__ == '__main__':
    from app import User as UserModel
    from app import CreatorRequest as CreatorRequestModel
    from app import Subscription as SubscriptionModel
    from app import Purchase as PurchaseModel
    from app import Cashout as CashoutModel
    class Models:
        User = UserModel
        CreatorRequest = CreatorRequestModel
        Subscription = SubscriptionModel
        Purchase = PurchaseModel
        Cashout = CashoutModel