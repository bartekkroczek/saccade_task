from abc import ABCMeta, abstractmethod


class AbstractAdaptive(object):
    """
    Abstract class that defines API for all adaptive algorithms.
    All subclasses inhering from this class will be iterable.

    Usage:

    ```
    for val in class:
        ... calculations with val...
        class.set_corr(...)
    ```

    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __iter__(self):
        pass

    @abstractmethod
    def __next__(self):
        pass

    @abstractmethod
    def set_corr(self, corr):
        pass

