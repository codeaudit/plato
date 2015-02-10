import inspect
import sys
from abc import abstractproperty, abstractmethod
from theano.compile.sharedvalue import SharedVariable
from theano.gof.graph import Variable
import theano.tensor as ts
from theano.tensor.type import TensorType
import theano
import numpy as np

"""
It is better not to look at the things happening in here.  It's beautiful on the outside but not on the inside.
All you need to know is this:

You can decorate a symbolic function, method, or callable class with the following decorators:

@symbolic_stateless: If the function just returns a single variable and does not update state.
@symbolic_updater: If the function returns only state updates.
@symbolic_standard: If the function returns (outputs, updates) as a tuple.

A decorated function has methods bound to it which allow it to be compiled and called in a standard format.
These methods are described in the ISymbolicFunction interface below.
"""

__author__ = 'peter'


ENABLE_OMNISCENCE = True


class ISymbolicFunction(object):

    def compile(self, **kwargs):
        """
        :return: A compiled version of function that takes and returns numpy arrays.

        Note: Compilation actually happens the first time the function is called, because it needs the inputs to tell it
        what kind of symbolic variables to instatiate.
        """

    @abstractproperty
    def symbolic_stateless(self):
        """
        :return: A function of the form:
            out = fcn(in_0, in_1, ...)
            Where out and in are tensors.  If the function cannot be cast to this form (for instance because it returns
            multiple outputs or updates) an exception will be raised when it is called.
        """

    @abstractproperty
    def symbolic_standard(self):
        """
        :return: A function of the form:
            (out_0, out_1, ...), ((shared_0, new_shared_0), (shared_1, new_shared_1), ...) = fcn(in_0, in_1, ...)
            Where all variables are symbolic, and shared_x variables are theano shared variables.
        """

    @abstractmethod
    def __call__(self, *args, **kwargs):
        """
        Call the function as it was defined, but do input/output type checking to confirm that it was implemented correctly
        """


class BaseSymbolicFunction(ISymbolicFunction):

    def __new__(cls, *args, **kwargs):

        obj = object.__new__(cls)
        BaseSymbolicFunction.__init__(obj, fcn = obj, instance = None)
        return obj

    def __init__(self, fcn, instance = None):

        self._fcn = fcn
        self._instance = instance
        self._locals = None

    def _assert_is_tensor(self, arg, name):
        if not isinstance(arg, Variable):
            raise SymbolicFormatError('%s of function %s should have been a tensor, but was %s' % (name, self._fcn, arg))

    def _assert_all_tensors(self, args, name):
        if not (isinstance(args, tuple) and all(isinstance(arg, Variable) for arg in args)):
            raise SymbolicFormatError('%s of %s must a tuple of tensors.  They were %s instead' % (name, self._fcn, args, ))

    def _assert_all_updates(self, updates):
        if not (isinstance(updates, list) and all(len(up)==2 for up in updates) and
                all(isinstance(old, SharedVariable) and isinstance(new, Variable) for old, new in updates)):
            raise SymbolicFormatError('Updates from %s must be a list of 2-tuples of (shared_variable, update_tensor).  It was %s instead' % (self._fcn, updates, ))

    def _assert_standard_return(self, return_val):
        if isinstance(return_val, SymbolicReturn):  # It's been checked already, you're clear.
            return
        else:  # Possibly remove this entirely and only allow SymbolicReturn
            if not (isinstance(return_val, tuple) and len(return_val)==2):
                raise SymbolicFormatError('Function %s was expected to return a 2-tuple of (outputs, updates) but returned %s instead' % (self._fcn, return_val))
            outputs, updates = return_val
            self._assert_all_tensors(outputs, 'Outputs')
            self._assert_all_updates(updates)

    def __get__(self, instance, owner):
        return self.__class__(self._fcn, instance=instance)

    def compile(self, **kwargs):
        return AutoCompilingFunction(self, **kwargs)

    def _call_fcn(self, *args, **kwargs):

        if ENABLE_OMNISCENCE:
            # Look inside the function that this decorator is wrapping, and grab the local variables.  This is
            # inherently evil, but useful for debugging purposes.  Use the trick from
            # http://stackoverflow.com/questions/9186395/python-is-there-a-way-to-get-a-local-function-variable-from-within-a-decorator
            def tracer(frame, event, arg):
                if event == 'return':
                    self._locals = frame.f_locals.copy()

            sys.setprofile(tracer)
            try:
                return_val = self._fcn(*args, **kwargs) if self._instance is None else self._fcn(self._instance, *args, **kwargs)
            finally:
                sys.setprofile(None)
        else:
            return_val = self._fcn(*args, **kwargs) if self._instance is None else self._fcn(self._instance, *args, **kwargs)
        return return_val

    @property
    def locals(self):
        return self._locals

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError()


class SymbolicStatelessFunction(BaseSymbolicFunction):
    """
    Use this to decorate a symbolic fcntion of the form:
    out = fcn(in_0, in_1, ...)    OR
    (out_0, out_1, ...) = fcn(in_0, in_1, ...)
    """

    def __call__(self, *args):
        self._assert_all_tensors(args, 'Arguments')
        out = self._call_fcn(*args)
        self._assert_is_tensor(out, 'Output')
        return out

    @property
    def symbolic_stateless(self):
        return self

    @property
    def symbolic_standard(self):
        return SymbolicStandardFunction(self._standard_function)

    def _standard_function(self, *args, **kwargs):
        out = self._call_fcn(*args, **kwargs)
        return (out, ), []


class SymbolicUpdateFunction(BaseSymbolicFunction):

    def __call__(self, *args, **kwargs):
        self._assert_all_tensors(args, 'Arguments')
        updates = self._call_fcn(*args, **kwargs)
        self._assert_all_updates(updates)
        return updates

    @property
    def symbolic_stateless(self):
        raise Exception("Tried to get the symbolic_stateless function from an %s\n, which is a SymbolicUpdateFunction. - "
            "This won't work because updaters have state.")

    @property
    def symbolic_standard(self):
        return SymbolicStandardFunction(self._standard_function)

    def _standard_function(self, *args, **kwargs):
        updates = self._call_fcn(*args, **kwargs)
        return (), updates


class SymbolicStandardFunction(BaseSymbolicFunction):

    def __call__(self, *args):
        self._assert_all_tensors(args, 'Arguments')
        return_val = self._call_fcn(*args)
        self._assert_standard_return(return_val)
        return return_val

    @property
    def symbolic_standard(self):
        return self

    @property
    def symbolic_stateless(self):
        return SymbolicStatelessFunction(self._stateless_function)

    def _stateless_function(self, *args, **kwargs):
        outputs, updates = self._fcn(*args, **kwargs)
        assert len(updates)==0, "You tried to call %s as a stateless function, but it returns updates, so this can't be done." \
            % self._fcn
        assert len(outputs)==1, "You tried to call %s as a stateless function, but it returns multiple outputs, so this can't be done." \
            % self._fcn
        out, = outputs
        return out


def symbolic_stateless(fcn):
    return _decorate_anything(SymbolicStatelessFunction, fcn)


def symbolic_standard(fcn):
    return _decorate_anything(SymbolicStandardFunction, fcn)


def symbolic_updater(fcn):
    return _decorate_anything(SymbolicUpdateFunction, fcn)


def _decorate_anything(symbolic_function_class, callable_thing):
    """
    Decorate a callable thing as with a symbolic decorator

    # Cases to consider:
    # 1) Function: called directly with instance = None
    # 2) Method: Called from __get__ when the method is requested.  instance is the object to which the method is bound
    # 3) Callable class:
    """
    if inspect.isclass(callable_thing): # Case 3: Class with __call__ method
        return _decorate_callable_class(symbolic_function_class = symbolic_function_class, callable_class = callable_thing)
    else:  # Cases 1 and 2: Function or method
        return symbolic_function_class(callable_thing)


def _decorate_callable_class(symbolic_function_class, callable_class):

    assert hasattr(symbolic_function_class, '__call__'), "If you decorate a class with a symbolic decorator, it must "\
        "be callable.  If there's a specific method you want to decorate, decorate that instead."

    # Strategy 1: Return a new constructor that dynamically binds the function_type as a base-class when the object
    # is instantiated. (Now defunct - see git log if you want)

    # Strategy 2: Bind the function_type as a base-class to the class - the __new__ method of function_type will then be
    # called when the object is instantiated.
    class CallableSymbolicFunction(callable_class, symbolic_function_class):
        """
        This is a dynamic class that binds together the callable class with the symbolic function.  The idea is to make
        the callable class comply to the ISymbolicFunction interface.
        """

        # Also decorate the __call__ method, so that type checking is done.
        __call__ = symbolic_function_class(callable_class.__call__)

        def __init__(self, *args, **kwargs):
            callable_class.__init__(self, *args, **kwargs)

    return CallableSymbolicFunction


class SymbolicFormatError(Exception):
    pass


class AutoCompilingFunction(object):
    """
    Given a Symbolic function, turn it into a compiled function that will accept and return numpy arrays.

    Actual compilation happens on the first use of the function, since it needs to see the arguments in order to
    instantiate the input tensors.
    """

    def __init__(self, fcn, cast_floats_to_floatX = True, mode = 'test_and_run'):
        """
        :param fcn: A symbolic function (decorated with one of the above decorators)
        :param cast_floats_to_floatX: Case all floats to the global float type (define this in ~/.theanorc).
        :param mode: There are 3 modes:
            'run': Just compile and run - use this if you're confident in your code and just want to go.
            'test_and_run': Same as run, but you pass through test values once before compilation.  This lets you
                catch all sorts of errors.  You can also view test values by placing breakpoints, and viewing the
                value var.tag.test_value where var is some tensor variable.
            'debug': Never compile - just keep passing through test values.  This is basically like running the code
                in numpy, except to see variable values, you have to go var.tag.test_value
        :return:
        """
        assert isinstance(fcn, ISymbolicFunction), 'You must pass a symbolic function.  Decorate it!'
        if mode == 'tr':
            mode = 'test_and_run'
        assert mode in ('run', 'test_and_run', 'debug', 'omniscent')
        self._fcn = fcn
        self._format = format
        self._compiled_fcn = None
        self._cast_floats_to_floatX = cast_floats_to_floatX
        self._mode = mode
        self._locals = None
        if mode in ('test_and_run', 'debug'):
            theano.config.compute_test_value = 'warn'
            if mode == 'debug':
                __builtins__['showloc'] = show_all_locals

    def __call__(self, *args):
        """
        :param args, kwargs are the arguments that would go into fcn, but as real numpy arrays instead of symbols
        returns the result, in numpy arrays.
        """
        if self._compiled_fcn is None:
            tensor_args = [_data_to_tensor(arg, cast_floats_to_floatx = self._cast_floats_to_floatX,
                test = self._mode in ('test_and_run', 'debug', 'omniscent')) for arg in args]
            return_value = self._fcn(*tensor_args)
            if isinstance(self._fcn, SymbolicStatelessFunction):
                outputs = return_value
                updates = []
            elif isinstance(self._fcn, SymbolicStandardFunction):
                outputs, updates = return_value
            elif isinstance(self._fcn, SymbolicUpdateFunction):
                outputs = ()
                updates = return_value
            else:
                raise Exception("Get OUT!")

            if self._mode == 'omniscent':
                single_output = not isinstance(outputs, (list, tuple))
                if single_output:
                    outputs = [outputs]
                self._local_keys = self._fcn.locals.keys()
                outputs_and_internals = outputs+tuple(self._fcn.locals.values())
                self._compiled_fcn = theano.function(inputs = tensor_args, outputs = outputs_and_internals, updates = updates)
            elif self._mode == 'debug':  # Never compile - just keep passing through test values
                for (shared_var, new_val) in updates:  # Need to manually update shared vars
                    try:
                        shared_var.set_value(new_val.tag.test_value)
                    except AttributeError as err:
                        if err.message == "scratchpad instance has no attribute 'test_value'":
                            print 'Check - are you using randomstreams instead of shared_randomstreams?'
                        raise
                return [o.tag.test_value for o in outputs] if isinstance(outputs, (list, tuple)) else outputs.tag.test_value
            else:
                self._compiled_fcn = theano.function(inputs = tensor_args, outputs = outputs, updates = updates)

        if self._mode == 'omniscent':
            all_out = self._compiled_fcn(*args)
            self._locals = {k: v for k, v in zip(self._local_keys, all_out[-len(self._local_keys):])}
            true_out = all_out[:-len(self._local_keys)]
            if single_output:
                true_out, = true_out
            return true_out

        else:
            return self._compiled_fcn(*args)

    @property
    def locals(self):
        assert self._mode == 'omniscent', "You must set mode = 'omniscent' to view locals.  Current mode is '%s'." % (self._mode, )
        if self._locals is None:
            raise Exception('Locals not available yet.  You must call this function before asking for locals.')
        return self._locals

def _is_symbol_or_value(var):
    return isinstance(var, ts.TensorType) or isinstance(var, np.ndarray) or np.isscalar(var)


def _data_to_tensor(data, name = None, cast_floats_to_floatx = True, test = True):
    ndim = 0 if np.isscalar(data) else data.ndim
    dtype = theano.config.floatX if (cast_floats_to_floatx and (isinstance(data, float) or isinstance(data, np.ndarray) and data.dtype == 'float')) \
        else 'int64' if isinstance(data, int) \
        else 'float64' if isinstance(data, float) \
        else data.dtype
    tensor = TensorType(dtype, (None, )*ndim)(name)
    if test:
        tensor.tag.test_value = data
    return tensor


def get_shared_ancestors(variable):
    pass


def show_all_locals():
    locals_of_calling_frame = inspect.currentframe().f_back.f_locals
    print '=== Locals ==='
    for k in locals_of_calling_frame.keys():
        v = locals_of_calling_frame[k]
        print '%s = %s' % (k, var_info(v))
    print '--------------'


def var_info(var):

    if isinstance(var, Variable) and hasattr(var.tag, 'test_value'):
        return '%s with test_value = %s' % (str(var), var_info(var.tag.test_value))
    elif isinstance(var, SharedVariable):
        return 'Shared %s value = %s' % (str(var), var_info(var.get_value()))
    elif isinstance(var, np.ndarray):
        return array_info(var)
    else:
        return str(var)


def array_info(arr):
    if arr.size <= 10:
        return '%s(%s)' % (arr.__class__.__name__, str(arr).replace('\n', ', '))
    elif arr.size <= 200000:
        return '%s of shape %s in %s<=arr<=%s' % (arr.__class__.__name__, arr.shape, np.min(arr), np.max(arr))
    else:
        return '%s of shape %s' % (arr.__class__.__name__, arr.shape, )


def find_shared_ancestors(variable):
    """
    Given a variable, return a list of all shared variables that it depends upon.  This can be useful for
    finding the parameters to update when trying to optimize this variable in some way.
    :param variable: A theano variable
    :return: A list of SharedVariables.
    """
    if isinstance(variable, SharedVariable):
        return [variable]
    else:
        return list(set(sum([find_shared_ancestors(p) for p in variable.get_parents()], [])))


class SymbolicReturn(object):

    def __init__(self, outputs = (), updates = []):
        if not (isinstance(outputs, tuple) and all(isinstance(out, Variable) for out in outputs)):
            raise SymbolicFormatError('%s must a tuple of tensors.  They were %s instead' % (self._fcn, outputs, ))
        if not (isinstance(updates, list) and all(len(up)==2 for up in updates) and
                all(isinstance(old, SharedVariable) and isinstance(new, Variable) for old, new in updates)):
            raise SymbolicFormatError('Updates from %s must be a list of 2-tuples of (shared_variable, update_tensor).  It was %s instead' % (self._fcn, updates, ))
        self.outputs = outputs
        self.updates = updates

    def __iter__(self):
        return (self.outputs, self.updates).__iter__()
