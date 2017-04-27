import logging
import json


class OOClientError(Exception):
    def __init__(self, msg):
        self.log = logging.getLogger(self.__class__.__name__)
        self.msg = msg
        self.log.error(msg)


class HTTPNon200(OOClientError):
    def __init__(self, status_code, response):
        self.msg = '{0}: {1}'.format(status_code, response)
        self.status_code = status_code
        try:
            self.response = json.loads(response)
        except Exception:
            self.response = response
        OOClientError(self.msg)


class ReleaseAlreadyExists(OOClientError):
    def __init__(self, version):
        self.msg = 'Version {0} has already been released, please pick a'\
                   'different version number'.format(version)
        self.version = version
        OOClientError(self.msg)


class NoFlowsFound(OOClientError):
    def __init__(self, filter):
        self.msg = 'No flows found with filter {0}'.format(filter)
        OOClientError(self.msg)


class TimeoutError(OOClientError):
    def __init__(self, function, time):
        self.msg = 'Timed out after waiting {0}s in {1}'.format(time, function)
        OOClientError(self.msg)


class NotFound(OOClientError):
    pass
