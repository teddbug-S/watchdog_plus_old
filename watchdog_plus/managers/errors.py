# base exception class
class WatchDogPlusError(Exception):
    ...


# raised when no services found
class ServiceNotFound(WatchDogPlusError):
    ...


# raised when retrieving a service or an observer is not successful
class DoesNotExist(WatchDogPlusError):
    ...


# raised when two observers or services have the same name
class AlreadyExists(WatchDogPlusError):
    ...
