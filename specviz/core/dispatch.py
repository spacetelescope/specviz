"""
Object Event Handling

The singleton `Dispatch` object manages the
set of `EventNode` events. Handlers or **listeners** are attached
to `EventNode`s. The `DispatchHandle` decorator is used to
decorate classes that handle events.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import inspect
import traceback
import logging
from functools import wraps


class EventNode(object):
    """An event

    An event is defined by the arguments the listeners
    of the event expect to be given.

    Parameters
    ----------
    args: [arg, ...]
        The list of keyword arguments that the event
        will provide to its listeners
    """
    def __init__(self, *args):
        self._args = args
        self.__handlers = []

    def __iadd__(self, other):
        """
        Add a listener via the addition operator
        """
        self.__handlers.append(other)
        return self

    def __isub__(self, other):
        """
        Remove a listener via the subtraction operator
        """
        self.__handlers.remove(other)
        return self

    def emit(self, *args, **kwargs):
        """
        Call the hanlders of this event

        Parameters
        ----------
        args: [arg, ...]
            The keyword arguments being provided to the event.

        kwargs: {arg: value, ...}
            The keyword/value pairs passed to the listeners.

        Raises
        ------
        ValueError
            An keyword is being passed that does not belong
            to this event.
        """
        if len(args) != len(self._args) and not set(kwargs.keys()).issubset(
                set(self._args)):
            raise ValueError("Unknown keyword in event emit arguments.")

        for handler in self.__handlers:
            # logging.info("Sending message from: '{}'".format(handler))
            if hasattr(handler, 'self'):
                handler(handler.self, *args, **kwargs)
            else:
                handler(*args, **kwargs)

    def clear(self):
        """
        Removes all handlers from object.
        """
        self.__handlers = []


class Dispatch(object):
    """
    Central communications object for all events.
    """
    def setup(self, inst):
        """
        Register all methods decorated by `register_listener`
        """
        logging.info("Dispatch is now watching: {}".format(inst))
        members = inspect.getmembers(inst, predicate=inspect.ismethod)

        for func_name, func in members:
            if hasattr(func, 'wrapped'):
                if func.wrapped:
                    for name in func.event_names:
                        self._register_listener(name, func)

    def tear_down(self, inst):
        """
        Remove all registered methods from their events
        """
        logging.info("Dispatch has stopped watching: {}".format(inst))
        members = inspect.getmembers(inst, predicate=inspect.ismethod)

        for func_name, func in members:
            if hasattr(func, 'wrapped'):
                if func.wrapped:
                    for name in func.event_names:
                        self.unregister_listener(name, func)

    def register_event(self, name, args=None):
        """
        Add an `EventNode` to the list of possible events

        Parameters
        ----------
        name: str
            The name of the event.

        args: [arg, ...]
            The list of keyword arguments this event will pass
            to its handlers.
        """
        args = args or []

        if not hasattr(self, name):
            setattr(self, name, EventNode(*args))
        else:
            logging.warning("Event '{}' already exists. Please use a "
                            "different name.".format(name))

    def _register_listener(self, name, func):
        """
        Add a listener to an event

        Parameters
        ----------
        name: str
            The event name to add the listener to.

        func: function
            The function that will be called when the is emitted
        """
        if hasattr(self, name):
            call_func = getattr(self, name)
            call_func += func
        else:
            logging.warning("No such event: {}. Event must be registered "
                            "before listeners can be assigned.".format(name))

    def register_listener(self, *args):
        """
        Decorate event listeners
        """
        def decorator(func):
            func.wrapped = True
            func.event_names = args

            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except:
                    logging.error(
                        "Exception in '{}':\n{}".format(func.__name__,
                                                        traceback.format_exc())
                    )
            return wrapper
        return decorator

    def unregister_listener(self, name, func):
        """
        Remove a listener from an event

        Parameters
        ----------
        name: str
            The event from wich the listener should be removed.

        func: function
            The function to be removed
        """
        if hasattr(self, name):
            call_func = getattr(self, name)
            call_func -= func
        else:
            logging.warning("No such event: {}.".format(name))