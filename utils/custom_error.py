class CustomError(Exception):
    def __init__(self, message, statusCode):
        super().__init__(message)
        # The message you passed into the super constructor of the base class
        # "Exception" saved the "message" in the "args" property in an array
        # where the first element is the actual "message" text.
        self.statusCode = statusCode
    def __repr__(self):
        return f"CustomError('{self.args}', '{self.statusCode}')"