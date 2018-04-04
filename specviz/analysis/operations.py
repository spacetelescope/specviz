import abc
import six

from ..core.events import dispatch


class StackOperation(type):
    """Meta class that stores the :class:`~FunctionalOperation` instance on an
    operation stack that can be used again in the future.
    """
    _operations = []

    def __call__(cls, *args, **kwargs):
        instance = super(StackOperation, cls).__call__(*args, **kwargs)
        cls._operations.append(instance)

        # Fire an event to let the application know a new operation has been
        # performed
        dispatch.performed_operation.emit(operation=instance)

        return instance

    @classmethod
    def last_operation(cls):
        return cls._operations[-1]

    @classmethod
    def operations(cls):
        return cls._operations


@six.add_metaclass(StackOperation)
class Operation(object):

    @abc.abstractmethod
    def __call__(self, flux, spectral_axis=None):
        raise NotImplementedError


class FunctionalOperation(Operation):
    """
    A generic operation that consists of just applying a
    function to each spaxel.

    Parameters
    ----------
    function : func
        The function to apply to each spaxel. This function
        should take the spectral axis and flux arrays for
        the spaxel as the first two positional arguments.
    args : list
        Additional positional arguments to pass to the function
    kwargs : dict
        Additional keyword arguments to pass to the function
    """
    def __init__(self, function, axis='spectral', keep_shape=True, args=[], kwargs={}):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.axis = axis
        self.keep_shape = keep_shape

    def __call__(self, flux, spectral_axis=None):
        return self.function(flux, spectral_axis, *self.args, **self.kwargs)