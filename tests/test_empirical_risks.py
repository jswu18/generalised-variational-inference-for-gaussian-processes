import jax.numpy as jnp
import pytest

from mockers.kernel import (
    MockKernel,
    MockKernelParameters,
    calculate_regulariser_gram_eye_mock,
)
from mockers.mean import MockMean, MockMeanParameters
from src.empirical_risks import CrossEntropy, NegativeLogLikelihood
from src.gps import (
    ApproximateGPClassification,
    ApproximateGPRegression,
    GPClassification,
    GPRegression,
)
from src.kernels import MultiOutputKernel, MultiOutputKernelParameters


@pytest.mark.parametrize(
    "log_observation_noise,x_train,y_train,x,y,negative_log_likelihood",
    [
        [
            jnp.log(1.0),
            jnp.array(
                [
                    [1.0, 3.0, 2.0],
                    [1.5, 1.5, 9.5],
                ]
            ),
            jnp.array([1.0, 1.5]),
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.ones((2,)),
            1.4112988,
        ],
        [
            jnp.log(1.0),
            jnp.array(
                [
                    [1.0, 3.0, 2.0],
                    [1.5, 1.5, 9.5],
                ]
            ),
            jnp.array([1.0, 1.5]),
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.ones((12,)),
            1.4112988,
        ],
    ],
)
def test_gp_regression_nll(
    log_observation_noise: float,
    x_train: jnp.ndarray,
    y_train: jnp.ndarray,
    x: jnp.ndarray,
    y: jnp.ndarray,
    negative_log_likelihood: float,
):
    gp = GPRegression(
        mean=MockMean(),
        kernel=MockKernel(),
        x=x_train,
        y=y_train,
    )
    nll = NegativeLogLikelihood(
        gp=gp,
    )
    gp_parameters = gp.Parameters(
        log_observation_noise=log_observation_noise,
        mean=MockMean.Parameters(),
        kernel=MockKernel.Parameters(),
    )
    assert jnp.isclose(
        nll.calculate_empirical_risk(
            parameters=gp_parameters,
            x=x,
            y=y,
        ),
        negative_log_likelihood,
    )


@pytest.mark.parametrize(
    "log_observation_noise,x,y,negative_log_likelihood",
    [
        [
            jnp.log(1.0),
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.array([1.2, 4.2]),
            3.48893853,
        ],
    ],
)
def test_approximate_gp_regression_nll(
    log_observation_noise: float,
    x: jnp.ndarray,
    y: jnp.ndarray,
    negative_log_likelihood: float,
):
    gp = ApproximateGPRegression(
        mean=MockMean(),
        kernel=MockKernel(),
    )
    nll = NegativeLogLikelihood(
        gp=gp,
    )
    gp_parameters = gp.Parameters(
        log_observation_noise=log_observation_noise,
        mean=MockMean.Parameters(),
        kernel=MockKernel.Parameters(),
    )
    assert jnp.isclose(
        nll.calculate_empirical_risk(
            parameters=gp_parameters,
            x=x,
            y=y,
        ),
        negative_log_likelihood,
    )


@pytest.mark.parametrize(
    "log_observation_noise,number_of_classes,x_train,y_train,x,y,negative_log_likelihood",
    [
        [
            jnp.log(jnp.array([0.1, 0.2, 0.4, 1.8])),
            4,
            jnp.array(
                [
                    [1.0, 3.0, 2.0],
                    [1.5, 1.5, 9.5],
                ]
            ),
            jnp.array(
                [
                    [0.5, 0.1, 0.2, 0.2],
                    [0.1, 0.2, 0.3, 0.4],
                ]
            ),
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.array(
                [
                    [0.5, 0.1, 0.2, 0.2],
                    [0.1, 0.2, 0.3, 0.4],
                ]
            ),
            2.63190702,
        ],
    ],
)
def test_gp_classification_nll(
    log_observation_noise: float,
    number_of_classes,
    x_train: jnp.ndarray,
    y_train: jnp.ndarray,
    x: jnp.ndarray,
    y: jnp.ndarray,
    negative_log_likelihood: float,
):
    gp = GPClassification(
        mean=MockMean(number_output_dimensions=number_of_classes),
        kernel=MultiOutputKernel(
            kernels=[MockKernel(kernel_func=calculate_regulariser_gram_eye_mock)]
            * number_of_classes
        ),
        x=x_train,
        y=y_train,
    )
    nll = NegativeLogLikelihood(
        gp=gp,
    )
    gp_parameters = gp.Parameters(
        log_observation_noise=log_observation_noise,
        mean=MockMeanParameters(),
        kernel=MultiOutputKernelParameters(
            kernels=[MockKernelParameters()] * number_of_classes
        ),
    )
    assert jnp.isclose(
        nll.calculate_empirical_risk(
            parameters=gp_parameters,
            x=x,
            y=y,
        ),
        negative_log_likelihood,
    )


@pytest.mark.parametrize(
    "log_observation_noise,number_of_classes,x_train,y_train,x,y,cross_entropy",
    [
        [
            jnp.log(jnp.array([0.1, 0.2, 0.4, 1.8])),
            4,
            jnp.array(
                [
                    [1.0, 3.0, 2.0],
                    [1.5, 1.5, 9.5],
                ]
            ),
            jnp.array(
                [
                    [0.5, 0.1, 0.2, 0.2],
                    [0.1, 0.2, 0.3, 0.4],
                ]
            ),
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.array(
                [
                    [0, 0, 0, 1],
                    [1, 0, 0, 0],
                ]
            ),
            1.306689,
        ],
    ],
)
def test_gp_classification_cross_entropy(
    log_observation_noise: float,
    number_of_classes,
    x_train: jnp.ndarray,
    y_train: jnp.ndarray,
    x: jnp.ndarray,
    y: jnp.ndarray,
    cross_entropy: float,
):
    gp = GPClassification(
        mean=MockMean(number_output_dimensions=number_of_classes),
        kernel=MultiOutputKernel(
            kernels=[MockKernel(kernel_func=calculate_regulariser_gram_eye_mock)]
            * number_of_classes
        ),
        x=x_train,
        y=y_train,
    )
    empirical_risk = CrossEntropy(
        gp=gp,
    )
    gp_parameters = gp.Parameters(
        log_observation_noise=log_observation_noise,
        mean=MockMeanParameters(),
        kernel=MultiOutputKernelParameters(
            kernels=[MockKernelParameters()] * number_of_classes
        ),
    )
    assert jnp.isclose(
        empirical_risk.calculate_empirical_risk(
            parameters=gp_parameters,
            x=x,
            y=y,
        ),
        cross_entropy,
    )


@pytest.mark.parametrize(
    "log_observation_noise,number_of_classes,x,y,negative_log_likelihood",
    [
        [
            jnp.log(jnp.array([0.1, 0.2, 0.4, 1.8])),
            4,
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.array(
                [
                    [0.5, 0.1, 0.2, 0.2],
                    [0.1, 0.2, 0.3, 0.4],
                ]
            ),
            2.77258869,
        ],
    ],
)
def test_gp_approximate_classification_nll(
    log_observation_noise: float,
    number_of_classes,
    x: jnp.ndarray,
    y: jnp.ndarray,
    negative_log_likelihood: float,
):
    gp = ApproximateGPClassification(
        mean=MockMean(number_output_dimensions=number_of_classes),
        kernel=MultiOutputKernel(kernels=[MockKernel()] * number_of_classes),
    )
    nll = NegativeLogLikelihood(
        gp=gp,
    )
    gp_parameters = gp.Parameters(
        log_observation_noise=log_observation_noise,
        mean=MockMeanParameters(),
        kernel=MultiOutputKernelParameters(
            kernels=[MockKernelParameters()] * number_of_classes
        ),
    )
    assert jnp.isclose(
        nll.calculate_empirical_risk(
            parameters=gp_parameters,
            x=x,
            y=y,
        ),
        negative_log_likelihood,
    )


@pytest.mark.parametrize(
    "log_observation_noise,number_of_classes,x,y,cross_entropy",
    [
        [
            jnp.log(jnp.array([0.1, 0.2, 0.4, 1.8])),
            4,
            jnp.array(
                [
                    [1.0, 2.0, 3.0],
                    [1.5, 2.5, 3.5],
                ]
            ),
            jnp.array(
                [
                    [0, 0, 0, 1],
                    [0, 1, 0, 0],
                ]
            ),
            1.3862944,
        ],
    ],
)
def test_gp_approximate_classification_cross_entropy(
    log_observation_noise: float,
    number_of_classes,
    x: jnp.ndarray,
    y: jnp.ndarray,
    cross_entropy: float,
):
    gp = ApproximateGPClassification(
        mean=MockMean(number_output_dimensions=number_of_classes),
        kernel=MultiOutputKernel(kernels=[MockKernel()] * number_of_classes),
    )
    empirical_risk = CrossEntropy(
        gp=gp,
    )
    gp_parameters = gp.Parameters(
        log_observation_noise=log_observation_noise,
        mean=MockMeanParameters(),
        kernel=MultiOutputKernelParameters(
            kernels=[MockKernelParameters()] * number_of_classes
        ),
    )
    assert jnp.isclose(
        empirical_risk.calculate_empirical_risk(
            parameters=gp_parameters,
            x=x,
            y=y,
        ),
        cross_entropy,
    )
