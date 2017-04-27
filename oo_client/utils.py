import time
from uuid import UUID
import oo_client.errors as errors


def timeout(timeout, interval):
    def decorate(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                result = func(*args, **kwargs)
                if result:
                    return result
                if attempts >= timeout / interval:
                    raise errors.TimeoutError(format(func.__name__), timeout)
                attempts += 1
                time.sleep(interval)
        return wrapper
    return decorate


def validate_uuid4(uuid_string):
    """
    Validate that a UUID string is in
    fact a valid uuid4.
    Happily, the uuid module does the actual
    checking for us.
    It is vital that the 'version' kwarg be passed
    to the UUID() call, otherwise any 32-character
    hex string is considered valid.
    """
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return False
    # If the uuid_string is a valid hex code,
    # but an invalid uuid4,
    # the UUID.__init__ will convert it to a
    # valid uuid4. This is bad for validation purposes.
    return val.hex == uuid_string or val.__str__() == uuid_string
