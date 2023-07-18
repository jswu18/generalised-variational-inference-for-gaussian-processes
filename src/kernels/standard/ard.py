from typing import Any, Dict, Literal, Union

import jax.numpy as jnp
import pydantic
from flax.core.frozen_dict import FrozenDict

from src.kernels.standard.base import StandardKernelBase, StandardKernelBaseParameters
from src.utils.custom_types import JaxArrayType, JaxFloatType

PRNGKey = Any  # pylint: disable=invalid-name


class ARDParameters(StandardKernelBaseParameters):
    log_scaling: JaxFloatType
    log_lengthscales: JaxArrayType[Literal["float64"]]


class ARD(StandardKernelBase):
    Parameters = ARDParameters

    def __init__(self, number_of_dimensions: int):
        self.number_of_dimensions = number_of_dimensions

    @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def generate_parameters(self, parameters: Union[FrozenDict, Dict]) -> ARDParameters:
        """
        Generates a Pydantic model of the parameters for ARD Kernels.

        Args:
            parameters: A dictionary of the parameters for ARD Kernels.

        Returns: A Pydantic model of the parameters for ARD Kernels.

        """
        return ARD.Parameters(**parameters)

    @pydantic.validate_arguments(config=dict(arbitrary_types_allowed=True))
    def initialise_random_parameters(
        self,
        key: PRNGKey,
    ) -> ARDParameters:
        """
        Initialise the parameters of the ARD Kernel using a random key.

        Args:
            key: A random key used to initialise the parameters.

        Returns: A Pydantic model of the parameters for ARD Kernels.

        """
        pass

    @staticmethod
    def _calculate_kernel(
        parameters: ARDParameters,
        x1: jnp.ndarray,
        x2: jnp.ndarray,
    ) -> jnp.float64:
        """
        The ARD kernel function defined as:
        k(x1, x2) = scaling * exp(-0.5 * (x1 - x2)^T @ diag(1 / lengthscales) @ (x1 - x2)).
            - n is the number of points in x
            - m is the number of points in y
            - d is the number of dimensions

        Args:
            parameters: parameters of the kernel
            x1: vector of shape (1, d)
            x2: vector of shape (1, d)

        Returns: the ARD kernel function evaluated at x and y

        """
        scaling = jnp.exp(jnp.atleast_1d(parameters.log_scaling)) ** 2
        return jnp.sum(
            scaling
            * jnp.exp(
                -0.5 * jnp.atleast_1d(parameters.log_lengthscales) @ jnp.square(x1 - x2)
            )
        ).astype(jnp.float64)
