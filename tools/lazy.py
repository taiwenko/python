"""Utilities for lazy evaluation."""

class LazyNamedValue(object):
    """Lazy evaluation of a named value.

    This class provides a way to couple a value to a name, with lazy evaluation
    of the value. On initial construction, a LazyNamedValue knows its name,
    and has a closure to compute its value. The value is evaluated when the
    object is called, and the object remembers the value of the last evaluation.
    This allows for printing of internal states of expressions, which is
    useful when writing scoreboard tests.

    In general, most of the methods in this class are overloading the builtin
    operators, so that an operator on a LazyNamedValue is itself a
    LazyNamedValue, which can be evaluated later.
    """

    # Disable lint checking on short function names, to allow the two letter
    # function names below.
    # pylint:disable=C0103

    def __init__(self, name, func):
        self._name = name
        self._func = func
        self._last_value_valid = False
        self._last_value = None

    def _eval_lazy(self, value):
        return value() if isinstance(value, LazyNamedValue) else value

    def __call__(self):
        self._last_value = self._func()
        self._last_value_valid = True
        return self._last_value

    def __repr__(self):
        name = self._name() if hasattr(self._name, '__call__') else self._name
        if self._last_value_valid:
            return "%s%r" % (name, self._last_value)
        else:
            return "%s" % (name)

    def __cmp__(self, other):
        """Unimplemented.

        Unimplemented as it's not expected that this will be called, given the
        other comparison operators implemented on this class. In the event it
        becomes necessary, it should be implemented like the other comparisons
        in this class.
        """
        raise NotImplementedError

    def __eq__(self, other):
        def eq():
            """Closure implementing equality."""
            return self() == self._eval_lazy(other)

        return LazyNamedValue(lambda: "(%r == %r)" % (self, other), eq)

    def __ne__(self, other):
        def ne():
            """Closure implementing non-equality."""
            return self() != self._eval_lazy(other)

        return LazyNamedValue(lambda: "(%r != %r)" % (self, other), ne)

    def __gt__(self, other):
        def gt():
            """Closure implementing greater-than.

            If either value is None, override Python2's default behavior and
            always return false."""
            other_val = self._eval_lazy(other)
            self_val = self()
            return (self_val is not None and
                    other_val is not None and
                    self_val > other_val)

        return LazyNamedValue(lambda: "(%r > %r)" % (self, other), gt)

    def __lt__(self, other):
        def lt():
            """Closure implementing less-than.

            If either value is None, override Python2's default behavior and
            always return false."""
            other_val = self._eval_lazy(other)
            self_val = self()
            return (self_val is not None and
                    other_val is not None and
                    self_val < other_val)

        return LazyNamedValue(lambda: "(%r < %r)" % (self, other), lt)

    def __ge__(self, other):
        def ge():
            """Closure implementing greater-than-or-equal-to.

            If either value is None, override Python2's default behavior and
            always return false."""
            other_val = self._eval_lazy(other)
            self_val = self()
            return (self_val is not None and
                    other_val is not None and
                    self_val >= other_val)

        return LazyNamedValue(lambda: "(%r >= %r)" % (self, other), ge)

    def __le__(self, other):
        def le():
            """Closure implementing less-than-or-equal-to.

            If either value is None, override Python2's default behavior and
            always return false."""
            other_val = self._eval_lazy(other)
            self_val = self()
            return (self_val is not None and
                    other_val is not None and
                    self_val <= other_val)

        return LazyNamedValue(lambda: "(%r <= %r)" % (self, other), le)

    def __and__(self, other):
        def and_func():
            """Closure implementing bitwise and."""
            other_val = self._eval_lazy(other)
            self_val = self()
            return self_val & other_val

        return LazyNamedValue(lambda: "(%r & %r)" % (self, other), and_func)

    def __or__(self, other):
        def or_func():
            """Closure implementing bitwise or."""
            other_val = self._eval_lazy(other)
            self_val = self()
            return self_val | other_val

        return LazyNamedValue(lambda: "(%r | %r)" % (self, other), or_func)

    def __nonzero__(self):
        """Called to evaluate the object in a boolean context.

        Intentionally unimplemented to catch cases where the user probably
        wanted to evaluate the value of the lazy expression. Returning a
        LazyNamedValue here that deferred the evaluation of the value would
        create an infinite recursion.
        """
        raise NotImplementedError

    def is_in(self, sequence):
        """Provides a lazy evaluation of 'in' expressions.

        The __contains__ hook is called for 'in' expressions, but it's a
        method on the container object, not the left hand side.
        """
        def func():
            """Closure implementing item-in-sequence."""
            return self() in self._eval_lazy(sequence)

        return LazyNamedValue(lambda: "(%r is in %r)" % (self, sequence), func)

    # This function either takes in an upper and lower bound or takes in a
    # single tuple that contains an upper and lower bound. It looks funny
    # because there's no overloading in Python.
    #TODO(aaronfan): Make this function only take tuples.
    def within(self, lower, upper=None):
        if upper is None:
            lower, upper = lower

        def func():
            lower_val = self._eval_lazy(lower)
            upper_val = self._eval_lazy(upper)
            self_val = self()
            # Bitwise 'and' is used to get around Python's inability to overload
            # the logical 'and' operator.
            return (lower_val is not None and
                    upper_val is not None and
                    self_val is not None and
                    ((self_val >= lower_val) &
                    (self_val <= upper_val)))

        return LazyNamedValue(lambda: '(%r <= %r <= %r)' % (
            lower, self, upper), func)
