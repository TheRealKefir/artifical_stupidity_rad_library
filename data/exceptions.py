class DatabaseError(Exception):
    pass


class NotFound(DatabaseError):
    pass


class IncorrectPassword(DatabaseError):
    pass


class UserExists(DatabaseError):
    pass


class EmailExists(DatabaseError):
    pass


class ChatNotExists(DatabaseError):
    pass


class ChatAccessForbiden(DatabaseError):
    pass
