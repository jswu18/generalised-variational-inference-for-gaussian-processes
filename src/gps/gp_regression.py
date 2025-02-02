from typing import Dict, Union

import jax.numpy as jnp
import pydantic
from flax.core import FrozenDict

from src.gps.base.base import GPBaseParameters
from src.gps.base.exact_base import ExactGPBase
from src.gps.base.regression_base import GPRegressionBase
from src.kernels.base import KernelBase
from src.means.base import MeanBase
from src.module import PYDANTIC_VALIDATION_CONFIG


class GPRegressionParameters(GPBaseParameters):
    """
    The parameters of an exact Gaussian process regressor.
    The parameters are the mean function, the kernel, and the observation noise.
    """

    pass


class GPRegression(ExactGPBase, GPRegressionBase):
    """
    A Gaussian process regressor.
    """

    Parameters = GPRegressionParameters

    def __init__(
        self,
        mean: MeanBase,
        kernel: KernelBase,
        x: jnp.ndarray,
        y: jnp.ndarray,
    ):
        """
        Defining the mean function, and the kernel for the Gaussian process.

        Args:
            mean: the mean function of the Gaussian process
            kernel: the kernel of the Gaussian process
        """
        GPRegressionBase.__init__(
            self,
            mean=mean,
            kernel=kernel,
        )
        ExactGPBase.__init__(
            self,
            mean=mean,
            kernel=kernel,
            x=x,
            y=y,
        )

    @pydantic.validate_arguments(config=PYDANTIC_VALIDATION_CONFIG)
    def generate_parameters(
        self, parameters: Union[FrozenDict, Dict]
    ) -> GPRegressionParameters:
        """
        Generates a Pydantic model of the parameters for exact Gaussian process regression.

        Args:
            parameters: A dictionary of the parameters for exact Gaussian process regression.

        Returns: A Pydantic model of the parameters for exact Gaussian process regression.

        """
        return GPRegression.Parameters(
            log_observation_noise=parameters["log_observation_noise"],
            mean=self.mean.generate_parameters(parameters["mean"]),
            kernel=self.kernel.generate_parameters(parameters["kernel"]),
        )
