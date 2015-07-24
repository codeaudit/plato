from plato.tools.cost import negative_log_likelihood_dangerous
from plato.tools.online_regressor import OnlineRegressor
from plato.tools.networks import MultiLayerPerceptron
from plato.tools.online_prediction.online_predictors import GradientBasedPredictor
from plato.tools.optimizers import SimpleGradientDescent, GradientDescent
from plato.tools.simple_sampling_regressors import GibbsRegressor, HerdedGibbsRegressor
from utils.predictors.predictor_tests import assert_online_predictor_not_broken
from pytest import raises
import numpy as np

__author__ = 'peter'


def test_mlp():

    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            GradientBasedPredictor(
                function = MultiLayerPerceptron(
                    layer_sizes = [100, n_dim_out],
                    input_size = n_dim_in,
                    output_activation='softmax',
                    w_init = lambda n_in, n_out, rng = np.random.RandomState(3252): 0.1*rng.randn(n_in, n_out)
                    ),
                cost_function=negative_log_likelihood_dangerous,
                optimizer=SimpleGradientDescent(eta = 0.1),
                ).compile(),
        categorical_target=True,
        minibatch_size=10,
        n_epochs=2
        )


def test_mlp_with_scale_learning():

    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            GradientBasedPredictor(
                function = MultiLayerPerceptron(
                    layer_sizes = [100, n_dim_out],
                    input_size = n_dim_in,
                    output_activation='softmax',
                    scale_param = True,
                    w_init = lambda n_in, n_out, rng = np.random.RandomState(3252): 0.1*rng.randn(n_in, n_out)
                    ),
                cost_function=negative_log_likelihood_dangerous,
                optimizer=SimpleGradientDescent(eta = 0.1),
                ).compile(),
        categorical_target=True,
        minibatch_size=10,
        n_epochs=2
        )


def test_gibbs_logistic_regressor():

    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            GibbsRegressor(n_dim_in = n_dim_in, n_dim_out = n_dim_out,
                n_alpha = 1,
                possible_ws= (-1, 1),
                seed = 2143
                ).compile(),
        n_extra_tests = 8,
        n_epochs=20
        )


def test_herded_logistic_regressor():

    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            HerdedGibbsRegressor(n_dim_in = n_dim_in, n_dim_out = n_dim_out,
                n_alpha = 1,
                possible_ws= (-1, 1),
                ).compile(),
        n_epochs=20
        )


def test_gibbs_logistic_regressor_full_update():
    """
    This test just demonstrates that you can't just go and update all the weights at once -
    it won't work.
    """

    with raises(AssertionError):
        assert_online_predictor_not_broken(
            predictor_constructor = lambda n_dim_in, n_dim_out:
                GibbsRegressor(n_dim_in = n_dim_in, n_dim_out = n_dim_out,
                    n_alpha = n_dim_in,  # All weights updated in one go.
                    possible_ws= (-1, 1),
                    seed = 2143
                    ).compile(),
            n_epochs=80
            )


def test_online_regressors():

    # Multinomial Regression
    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            OnlineRegressor(
                input_size = n_dim_in,
                output_size=n_dim_out,
                optimizer=GradientDescent(eta = 0.01),
                regressor_type = 'multinomial'
                ).compile(),
        categorical_target=True,
        n_epochs=20
        )

    # Logistic Regression
    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            OnlineRegressor(
                input_size = n_dim_in,
                output_size=n_dim_out,
                optimizer=GradientDescent(eta = 0.01),
                regressor_type = 'logistic'
                ).compile(),
        categorical_target=False,
        n_epochs=20
        )

    # Linear Regression
    assert_online_predictor_not_broken(
        predictor_constructor = lambda n_dim_in, n_dim_out:
            OnlineRegressor(
                input_size = n_dim_in,
                output_size=n_dim_out,
                optimizer=GradientDescent(eta = 0.01),
                regressor_type = 'linear'
                ).compile(),
        categorical_target=False,
        n_epochs=20
        )


if __name__ == '__main__':
    test_online_regressors()
    test_mlp_with_scale_learning()
    test_gibbs_logistic_regressor()
    test_herded_logistic_regressor()
    test_gibbs_logistic_regressor_full_update()
    test_mlp()
