class ERLCAPIError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


ERROR_CODES = {
    # System
    0: "Unknown error occurred.",
    1001: "An error occurred communicating with Roblox or the in-game private server.",
    1002: "An internal system error occurred.",
    # Authentication
    2000: "You did not provide a server-key.",
    2001: "You provided an incorrectly formatted server-key.",
    2002: "You provided an invalid or expired server-key.",
    2003: "You provided an invalid global API key.",
    2004: "Your server-key is currently banned from accessing the API.",
    # Request
    3001: "You did not provide a valid command in the request body.",
    3002: "The server you are attempting to reach is currently offline (has no players).",
    # Access
    4000: "You are not authorized to perform this action on this server.",
    4001: "You are being rate limited.",
    4002: "The command you are attempting to run is restricted.",
    4003: "The message you are trying to send is prohibited.",
    # Special
    9998: "The resource you are accessing is restricted.",
    9999: "The module running on the in-game server is out of date.",
}


def get_error_message(code: int) -> str:
    return ERROR_CODES.get(code, "Unknown API error.")
