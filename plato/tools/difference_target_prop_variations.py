from general.numpy_helpers import get_rng
from plato.interfaces.decorators import symbolic_stateless, symbolic_updater
from plato.tools.difference_target_prop import DifferenceTargetLayer, ITargetPropLayer
import numpy as np
from plato.tools.optimizers import AdaMax
import theano

__author__ = 'peter'



class ReversedDifferenceTargetLayer(DifferenceTargetLayer):
    """
    This is an experimental modification where we switch the order of the linear/nonlinear
    operations.  That is, instead of the usual
        f(x) = activation(x.dot(w))
    We do
        f(x) = activation(x).dot(w)

    We just want to see if this works (it does!  Maybe even better!)
    """

    @symbolic_stateless
    def predict(self, x):
        pre_sigmoid = x.dot(self.w)+self.b
        output = self.hidden_activation(pre_sigmoid)
        output.pre_sigmoid = pre_sigmoid
        return output

    def backpropagate_target(self, x, target):

        back_output_pre_sigmoid = self.predict(x).dot(self.w_rev) + self.b_rev
        back_target_pre_sigmoid = target.dot(self.w_rev) + self.b_rev
        return self.input_activation(x.pre_sigmoid - back_output_pre_sigmoid + back_target_pre_sigmoid)


class PerceptronLayer(ITargetPropLayer):

    def __init__(self, w, b, w_rev, b_rev, lin_dtp = True):

        self.w = theano.shared(w, name = 'w')
        self.b = theano.shared(b, name = 'b')
        self.w_rev = theano.shared(w_rev, name = 'w_rev')
        self.b_rev = theano.shared(b_rev, name = 'b_rev')
        self.lin_dtp = lin_dtp

    @symbolic_stateless
    def predict(self, x):
        pre_sign = x.dot(self.w) + self.b
        output = (pre_sign > 0).astype('int32')
        output.pre_sign = pre_sign
        return output

    @symbolic_stateless
    def backward(self, x):
        pre_sign = x.dot(self.w_rev) + self.b_rev
        return (pre_sign > 0).astype('int32')

    @symbolic_updater
    def train(self, x, target):

        out = self.predict(x)
        delta_w = x.T.dot(target - out)
        delta_b = (target - out).sum(axis = 0)

        recon = self.backward(out)
        delta_w_rev = out.T.dot(x - recon)
        delta_b_rev = (x - recon).sum(axis = 0)

        return [(self.w, self.w+delta_w), (self.b, self.b+delta_b), (self.w_rev, self.w_rev+delta_w_rev), (self.b_rev, self.b_rev+delta_b_rev)]

        # optimizer = AdaMax(alpha = 0.001)
        # updates = optimizer.update_from_gradients(parameters = [self.w, self.b, self.w_rev, self.b_rev], gradients = [-delta_w, -delta_b, -delta_w_rev, -delta_b_rev])
        # return updates

    def backpropagate_target(self, x, target):

        if self.lin_dtp:
            back_output_pre_sigmoid = self.predict(x).dot(self.w_rev) + self.b_rev
            back_target_pre_sigmoid = target.dot(self.w_rev) + self.b_rev
            return (x.pre_sign - back_output_pre_sigmoid + back_target_pre_sigmoid > 0).astype('int32')
        else:
            output = self.predict(x)
            back_output = self.backward(output)
            back_target = self.backward(target)
            return x - back_output + back_target

    @classmethod
    def from_initializer(cls, n_in, n_out, initial_mag, rng=None, **kwargs):

        rng = get_rng(rng)

        return PerceptronLayer(
            w = rng.randint(low = -initial_mag, high=initial_mag+1, size = (n_in, n_out)).astype('float'),
            b = np.zeros(n_out).astype('float'),
            w_rev = rng.randint(low = -initial_mag, high=initial_mag+1, size = (n_out, n_in)).astype('float'),
            b_rev = np.zeros(n_in).astype('float'),
            **kwargs
            )
