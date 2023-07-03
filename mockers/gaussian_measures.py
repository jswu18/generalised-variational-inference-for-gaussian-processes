from typing import Any, Dict, Union

import jax.numpy as jnp
import pydantic
from flax.core.frozen_dict import FrozenDict

from mockers.kernels import ReferenceKernelMock, ReferenceKernelParametersMock
from mockers.mean_functions import (
    ReferenceMeanFunctionMock,
    ReferenceMeanFunctionParametersMock,
)
from src.gaussian_measures.gaussian_measures import GaussianMeasure
from src.parameters.gaussian_measures.gaussian_measures import GaussianMeasureParameters
from src.utils.custom_types import JaxFloatType

PRNGKey = Any  # pylint: disable=invalid-name


class GaussianMeasureParametersMock(GaussianMeasureParameters):
    mean_function: ReferenceMeanFunctionParametersMock = (
        ReferenceMeanFunctionParametersMock()
    )
    kernel: ReferenceKernelParametersMock = ReferenceKernelParametersMock()


class GaussianMeasureMock(GaussianMeasure):
    def __init__(self):
        self.kernel = ReferenceKernelMock()
        self.mean_function = ReferenceMeanFunctionMock()
        super().__init__(jnp.zeros(1), jnp.zeros(1), self.mean_function, self.kernel)

    @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def generate_parameters(
        self, parameters: Union[Dict, FrozenDict]
    ) -> GaussianMeasureParametersMock:
        return GaussianMeasureParametersMock()

    @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def initialise_random_parameters(
        self,
        key: PRNGKey,
    ) -> GaussianMeasureParametersMock:
        return GaussianMeasureParametersMock()

    def _calculate_mean(
        self,
        x: jnp.ndarray,
        parameters: GaussianMeasureParametersMock,
    ) -> jnp.ndarray:
        return self.mean_function.predict(parameters.mean_function, x)

    def _calculate_covariance(
        self,
        parameters: GaussianMeasureParametersMock,
        x: jnp.ndarray,
        y: jnp.ndarray = None,
    ) -> jnp.ndarray:
        return self.kernel.calculate_gram(parameters.kernel, x, y)

    def _calculate_observation_noise(
        self, parameters: GaussianMeasureParametersMock
    ) -> JaxFloatType:
        return jnp.float64(1)

    def _compute_negative_expected_log_likelihood(
        self,
        parameters: Union[Dict, FrozenDict, GaussianMeasureParametersMock],
        x: jnp.ndarray,
        y: jnp.ndarray,
    ) -> float:
        return jnp.log(0.5)
