from plato.tools.rbm import simple_rbm
from plato.tools.networks import StochasticLayer, FullyConnectedBridge
from plato.tools.optimizers import SimpleGradientDescent
from plotting.live_plotting import LiveStream
import theano
from utils.datasets.mnist import get_mnist_dataset
import numpy as np

__author__ = 'peter'


def demo_rbm():
    """
    In this demo we train an RBM on the MNIST input data (labels are ignored).  We plot the state of a markov chanin
    that is being simulaniously sampled from the RBM, and the parameters of the RBM.

    As learning progresses, we should see that the samples from the markov chain look increasingly like the data.
    """
    minibatch_size = 9

    dataset = get_mnist_dataset().process_with(inputs_processor=lambda (x, ): (x.reshape(x.shape[0], -1), ))

    rbm = simple_rbm(
        visible_layer = StochasticLayer('bernoulli'),
        bridge=FullyConnectedBridge(w = 0.001*np.random.randn(28*28, 500).astype(theano.config.floatX)),
        hidden_layer = StochasticLayer('bernoulli')
        )

    train_function = rbm.get_training_fcn(n_gibbs = 4, persistent = True, optimizer = SimpleGradientDescent(eta = 0.01)).compile()
    sampling_function = rbm.get_free_sampling_fcn(init_visible_state = np.random.randn(9, 28*28), return_smooth_visible = True).compile()

    def debug_variable_setter():
        lv = train_function.symbolic.locals()
        return {
            'hidden-neg-chain': lv.sleep_hidden.reshape((-1, 25, 20)),
            'visible-neg-chain': lv.hidden_layer.smooth(lv.bridge.reverse(lv.sleep_hidden)).reshape((-1, 28, 28)),
            'w': lv.bridge.parameters[0].T[:25].reshape((-1, 28, 28)),
            'b': lv.bridge.parameters[1].reshape((25, 20)),
            'b_rev': lv.bridge.parameters[2].reshape((28, 28)),
            }
    train_function.set_debug_variables(debug_variable_setter)

    stream = LiveStream(lambda: dict(train_function.get_debug_values().items()+[('visible-sample', visible_samples.reshape((-1, 28, 28)))]), update_every=10)
    for _, visible_data, _ in dataset.training_set.minibatch_iterator(minibatch_size = minibatch_size, epochs = 10, single_channel = True):
        visible_samples, _ = sampling_function()
        train_function(visible_data)
        stream.update()


if __name__ == '__main__':

    demo_rbm()
