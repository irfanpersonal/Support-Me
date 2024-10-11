# To delete a file in Python use load in the "os" built in package.
import os

def deleteFile(path: str) -> None:
    # Before we can actually delete the file we first have to make sure that the
    # file location provided is real. Like it does exist. And we do so by accessing
    # the exists method on the "os" object. 
    if os.path.exists(path):
        # Because at this point we know for certain that the file does exist we can 
        # now use the "remove()" method on the "os" object. 
        os.remove(path)
        return True
    return False