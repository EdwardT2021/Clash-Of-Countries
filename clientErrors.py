class ConnectionError(Exception):

    def __init__(self, message: str):

        super(ConnectionError, self).__init__("Connection Error: " + message)


class InitialConnectionError(ConnectionError):
    
    def __init__(self):

        message = "Servers are offline/unreachable!"
        super(InitialConnectionError, self).__init__(message)

class GraphicsError(Exception):

    def __init__(self, message: str):

        super(GraphicsError, self).__init__(self, "Graphics Error: " + message)

class TextBoxFitError(GraphicsError):

    def __init__(self):

        message = "Too much text to fit into assigned text box size"
        super(TextBoxFitError, self).__init__(message)

class GameError(Exception):

    def __init__(self, message: str):

        super(GameError, self).__init__("Game Error: " + message)

class ActionNotUniqueError(GameError):

    def __init__(self):

        super(ActionNotUniqueError, self).__init__("Action is not unique!")