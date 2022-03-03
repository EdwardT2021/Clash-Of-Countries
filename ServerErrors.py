class LogInError(Exception):

    def __init__(self, message: str):

        super(LogInError, self).__init__("LogIn Error: " + message)

class NotUniqueUsernameError(LogInError):

    def __init__(self):

        super(NotUniqueUsernameError, self).__init__("Username not unique!")

class DatabaseError(Exception):

    def __init__(self, message: str):

        super(DatabaseError, self).__init__("Database Error: " + message)

class DatabaseAccessError(DatabaseError):

    def __init__(self):

        super(DatabaseAccessError, self).__init__("Database cannot be accessed!")
