from __builtin__ import property
from plato.interfaces.decorators import symbolic_standard
from plato.interfaces.interfaces import IParameterized

__author__ = 'peter'


@symbolic_standard
class Chain(IParameterized):
    """
    A composition of symbolic functions:

    Chain(f, g, h)(x) is f(g(h(x)))

    Details:
    Chain calls functions in the standard format:
        out, updates = func(inputs)
        (Any symbolic-decorated function can becalled like this)

    Chain can be called in the standard format:
        outputs, updates = my_chain(inputs)  # or
        outputs, updates = my_chain.symbolic_standard(inputs)

    If none of the internals return updates, and the last function in the chain
    returns just a single output, Chain can also be called in the symbolic stateless
    format:

        output = my_chain.symbolic_simple(input_0, input_1, ...)

    If, however, internals return updates, or the last function returns multiple
    updates, this will raise an Exception.
    """

    def __init__(self, *processors):
        self._processors = processors

    def __call__(self, *args):
        out = args
        updates = []
        for p in self._processors:
            out, these_updates = p.to_format(symbolic_standard)(*out)
            updates += these_updates
        return out, updates

    @property
    def parameters(self):
        return sum([p.parameters for p in self._processors if isinstance(p, IParameterized)], [])


@symbolic_standard
class Branch(IParameterized):
    """
    Given a set of N One-in-one-out processors, make a composite processor
    that takes one in and N out.
    """

    def __init__(self, *processors):
        self._processors = processors

    def __call__(self, x):
        results = tuple(p.to_format(symbolic_standard)(x) for p in self._processors)
        outputs = sum([o for o, _ in results], ())
        updates = sum([u for _, u in results], [])
        return outputs, updates

    @property
    def parameters(self):
        return sum([p.parameters for p in self._processors if isinstance(p, IParameterized)], [])
