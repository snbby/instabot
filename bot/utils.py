import functools

import time


def retry(max_tries=3, delay=1, backoff=1.5, exceptions=(Exception,), logger=None):
    """Function decorator implementing retrying logic.

    :param max_tries: Max number of tries
    :type max_tries: int
    :param delay: Sleep for 'backoff' seconds longer after failure
    :type delay: int
    :param backoff: Multiply delay by this factor after each failure
    :type backoff: int
    :param exceptions: A tuple of exception classes; default (Exception,)
    :type exceptions: tuple of Exception
    :param logger: Logger object
    :type logger: logging.Logger
    """
    def _retry(func):
        @functools.wraps(func)
        def _wrap(*args, **kwargs):
            current_delay = delay
            for tries_remaining in range(max_tries, -1, -1):
                try:
                    return func(*args, **kwargs)
                except exceptions as err:
                    if tries_remaining > 0:
                        if logger is not None:
                            logger.warning(
                                msg='Error was raised, {} attempts left'.format(
                                    tries_remaining
                                ),
                                extra={'error': err}
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise

        return _wrap

    return _retry
