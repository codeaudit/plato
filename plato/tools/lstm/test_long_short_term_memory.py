from plato.tools.lstm.long_short_term_memory import AutoencodingLSTM
from plato.tools.optimization.optimizers import AdaMax
import theano
from utils.bureaucracy import minibatch_iterate
from utils.datasets.bounce_data import get_bounce_data
import numpy as np
from utils.tools.processors import OneHotEncoding
import pytest

__author__ = 'peter'


@pytest.mark.skipif(True, reason = 'Fails in pytest due to some weird reference-counter bug in theano.')
def test_autoencoding_lstm(
        width = 8,
        seed = 1234):

    data = get_bounce_data(width=width)
    encoder = OneHotEncoding(n_classes=width, dtype = theano.config.floatX)
    onehot_data = encoder(data)
    rng = np.random.RandomState(seed)
    aelstm = AutoencodingLSTM(n_input = 8, n_hidden=50, initializer_fcn = lambda shape: 0.01*rng.randn(*shape))

    gen_fcn = aelstm.get_generation_function(maintain_state=True, rng = rng).compile()
    train_fcn = aelstm.get_training_function(update_states=True, optimizer = AdaMax(alpha = 0.1)).compile()

    def prime_and_gen(primer, n_steps):
        onehot_primer = encoder(np.array(primer))
        onehot_generated, = gen_fcn(onehot_primer, n_steps)
        generated = encoder.inverse(onehot_generated)
        return generated

    initial_seq = prime_and_gen([0, 1, 2, 3, 4], 11)
    print initial_seq

    # Test empty, one-length primers
    prime_and_gen([], 2)
    prime_and_gen([0], 2)

    print 'Training....'
    for d in minibatch_iterate(onehot_data, minibatch_size=3, n_epochs=400):
        train_fcn(d)
    print 'Done.'

    final_seq = prime_and_gen([0, 1, 2, 3, 4], 11)
    assert np.array_equal(final_seq, [5, 6, 7, 6, 5, 4, 3, 2, 1, 0, 1]), 'Bzzzz! It was %s' % (final_seq, )

    # Assert state is maintained
    seq = prime_and_gen([], 3)
    assert np.array_equal(seq, [2, 3, 4]), 'Bzzzz! It was %s' % (seq, )
    seq = prime_and_gen([5], 3)
    assert np.array_equal(seq, [6, 7, 6]), 'Bzzzz! It was %s' % (seq, )

    # Assert training does not interrupt generation state.
    train_fcn(d)
    seq = prime_and_gen([], 3)
    assert np.array_equal(seq, [5, 4, 3]), 'Bzzzz! It was %s' % (seq, )


if __name__ == '__main__':

    test_autoencoding_lstm()
