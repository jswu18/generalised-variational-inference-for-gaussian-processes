import os

import jax
import jax.numpy as jnp
import numpy as np
import yaml

from experiments.regression.plotters import plot_data, plot_prediction
from experiments.regression.runners import (
    run_plot_experiment_data,
    run_set_up_experiment_data_chunked_test_data,
)
from experiments.regression.toy_curves.curves import CURVE_FUNCTIONS
from experiments.regression.trainers import meta_train_reference_gp
from experiments.shared.data import Data, ExperimentData
from experiments.shared.nn_means import MLP
from experiments.shared.nngp_kernels import MLPGPKernel
from experiments.shared.plotters import plot_losses, plot_two_losses
from experiments.shared.resolvers import kernel_resolver, mean_resolver
from experiments.shared.schemes import (
    EmpiricalRiskScheme,
    OptimiserScheme,
    RegularisationScheme,
)
from experiments.shared.trainer import TrainerSettings
from experiments.shared.trainers import train_approximate_gp, train_tempered_gp
from src.gps import ApproximateGPRegression
from src.kernels import CustomKernel, TemperedKernel
from src.kernels.svgp.kernelised_svgp_kernel import KernelisedSVGPKernel
from src.means import CustomMean

jax.config.update("jax_enable_x64", True)

with open(
    os.path.join(
        "configs",
        "regression",
        "reference",
        "constant-mean-mlp-kernel-negative-log-likelihood.yaml",
    ),
    "r",
) as file:
    reference_config = yaml.safe_load(file)

assert "mean" in reference_config, "Mean must be specified."
assert "mean_scheme" in reference_config["mean"], "Mean scheme must be specified."
assert "mean_kwargs" in reference_config["mean"], "Mean kwargs must be specified."
assert (
    "mean_parameters" in reference_config["mean"]
), "Mean parameters must be specified."

mean, mean_parameters = mean_resolver(
    mean_scheme=reference_config["mean"]["mean_scheme"],
    mean_kwargs=reference_config["mean"]["mean_kwargs"],
    mean_parameters=reference_config["mean"]["mean_parameters"],
)

assert "kernel" in reference_config, "Kernel must be specified."
assert "kernel_scheme" in reference_config["kernel"], "Kernel scheme must be specified."
assert "kernel_kwargs" in reference_config["kernel"], "Kernel kwargs must be specified."
assert (
    "kernel_parameters" in reference_config["kernel"]
), "Kernel parameters must be specified."

kernel, kernel_parameters = kernel_resolver(
    kernel_scheme=reference_config["kernel"]["kernel_scheme"],
    kernel_kwargs=reference_config["kernel"]["kernel_kwargs"],
    kernel_parameters=reference_config["kernel"]["kernel_parameters"],
)

assert "key" in reference_config, "Key must be specified."
assert "optimiser_scheme" in reference_config, "Optimiser scheme must be specified."
assert "learning_rate" in reference_config, "Learning rate must be specified."
assert "number_of_epochs" in reference_config, "Number of epochs must be specified."
assert "batch_size" in reference_config, "Batch size must be specified."
assert "batch_shuffle" in reference_config, "Batch shuffle must be specified."
assert "batch_drop_last" in reference_config, "Batch drop last must be specified."
reference_gp_trainer_settings = TrainerSettings(
    key=reference_config["key"],
    optimiser_scheme=reference_config["optimiser_scheme"],
    learning_rate=reference_config["learning_rate"],
    number_of_epochs=reference_config["number_of_epochs"],
    batch_size=reference_config["batch_size"],
    batch_shuffle=reference_config["batch_shuffle"],
    batch_drop_last=reference_config["batch_drop_last"],
)

# Experiment settings
output_directory = "outputs"
checkpoints_folder_name = "training-checkpoints"
number_of_data_points = 1000
x = jnp.linspace(-2, 2, number_of_data_points).reshape(-1, 1)
number_of_test_intervals = 5
total_number_of_intervals = 20
train_data_percentage = 0.8
sigma_true = 0.5
number_of_inducing_points = int(np.sqrt(number_of_data_points))
nn_architecture = [10, 1]

reference_number_of_iterations = 5
reference_nll_break_condition = -10

approximate_kernel_diagonal_regularisation = 1e-10

reference_gp_empirical_risk_scheme = EmpiricalRiskScheme.negative_log_likelihood
approximate_gp_empirical_risk_scheme = EmpiricalRiskScheme.negative_log_likelihood
tempered_gp_empirical_risk_scheme = EmpiricalRiskScheme.negative_log_likelihood

reference_save_checkpoint_frequency = 1000
approximate_save_checkpoint_frequency = 1000
tempered_save_checkpoint_frequency = 1000

reference_gp_trainer_settings = TrainerSettings(
    key=0,
    optimiser_scheme=OptimiserScheme.adabelief,
    learning_rate=1e-5,
    number_of_epochs=20000,
    batch_size=1000,
    batch_shuffle=True,
    batch_drop_last=False,
)
approximate_gp_trainer_settings = TrainerSettings(
    key=0,
    optimiser_scheme=OptimiserScheme.adabelief,
    learning_rate=1e-3,
    number_of_epochs=20000,
    batch_size=1000,
    batch_shuffle=True,
    batch_drop_last=False,
)
tempered_gp_trainer_settings = TrainerSettings(
    key=0,
    optimiser_scheme=OptimiserScheme.adabelief,
    learning_rate=1e-3,
    number_of_epochs=2000,
    batch_size=1000,
    batch_shuffle=True,
    batch_drop_last=False,
)

# Run experiment
nngp_kernel = MLPGPKernel(
    features=nn_architecture,
)
nngp_kernel_parameters = nngp_kernel.initialise_parameters()
nn_mean = MLP(
    features=nn_architecture,
)
nn_mean_parameters = nn_mean.init(jax.random.PRNGKey(0), x[:1, ...])

experiment_data_path = os.path.join(output_directory, "experiment-data")

for curve_function in CURVE_FUNCTIONS:
    pass
    # curve_directory = os.path.join(
    #     output_directory, type(curve_function).__name__.lower()
    # )
    # if not os.path.exists(curve_directory):
    #     os.makedirs(curve_directory)

    # run_set_up_experiment_data_chunked_test_data(
    #     name=type(curve_function).__name__.lower(),
    #     key=jax.random.PRNGKey(curve_function.seed),
    #     x=x,
    #     y=curve_function(
    #         key=jax.random.PRNGKey(curve_function.seed),
    #         x=x,
    #         sigma_true=sigma_true,
    #     ),
    #     number_of_test_intervals=number_of_test_intervals,
    #     total_number_of_intervals=total_number_of_intervals,
    #     train_data_percentage=train_data_percentage,
    #     save_path=experiment_data_path,
    # )
    # run_plot_experiment_data(
    #     experiment_data_path=experiment_data_path,
    #     name=type(curve_function).__name__.lower(),
    #     title=curve_function.__name__,
    #     save_path=experiment_data_path,
    # )

    # (
    #     reference_gp,
    #     reference_gp_parameters,
    #     reference_post_epoch_histories,
    # ) = meta_train_reference_gp(
    #     data=experiment_data.train,
    #     empirical_risk_scheme=reference_gp_empirical_risk_scheme,
    #     trainer_settings=reference_gp_trainer_settings,
    #     kernel=CustomKernel(
    #         kernel_function=nngp_kernel,
    #     ),
    #     kernel_parameters=CustomKernel.Parameters.construct(
    #         custom=nngp_kernel_parameters.dict(),
    #     ),
    #     number_of_inducing_points=number_of_inducing_points,
    #     number_of_iterations=reference_number_of_iterations,
    #     empirical_risk_break_condition=reference_nll_break_condition,
    #     save_checkpoint_frequency=reference_save_checkpoint_frequency,
    #     checkpoint_path=os.path.join(
    #         curve_directory,
    #         checkpoints_folder_name,
    #         "reference -gp",
    #     ),
    # )
    # plot_prediction(
    #     experiment_data=experiment_data,
    #     inducing_data=Data(
    #         x=reference_gp.x,
    #         y=reference_gp.y,
    #     ),
    #     gp=reference_gp,
    #     gp_parameters=reference_gp_parameters,
    #     title=f"Reference GP: {curve_function.__name__}",
    #     save_path=os.path.join(
    #         curve_directory,
    #         "reference-gp.png",
    #     ),
    # )
    # plot_losses(
    #     losses=[
    #         [x["empirical-risk"] for x in reference_post_epoch_history]
    #         for reference_post_epoch_history in reference_post_epoch_histories
    #     ],
    #     labels=[f"iteration-{i}" for i in range(reference_number_of_iterations)],
    #     loss_name=reference_gp_empirical_risk_scheme.value,
    #     title=f"Reference GP Empirical Risk: {curve_function.__name__}",
    #     save_path=os.path.join(
    #         curve_directory,
    #         "reference-gp-losses.png",
    #     ),
    # )
    #
    # for approximate_gp_regularisation_scheme_str in RegularisationScheme:
    #     approximate_experiment_directory = os.path.join(
    #         curve_directory,
    #         approximate_gp_regularisation_scheme_str,
    #     )
    #     if not os.path.exists(approximate_experiment_directory):
    #         os.makedirs(approximate_experiment_directory)
    #     approximate_gp = ApproximateGPRegression(
    #         mean=CustomMean(
    #             mean_function=lambda parameters, x: nn_mean.apply(parameters, x),
    #         ),
    #         kernel=KernelisedSVGPKernel(
    #             reference_kernel=reference_gp.kernel,
    #             reference_kernel_parameters=reference_gp_parameters.kernel,
    #             log_observation_noise=reference_gp_parameters.log_observation_noise,
    #             inducing_points=reference_gp.x,
    #             training_points=experiment_data.train.x,
    #             diagonal_regularisation=approximate_kernel_diagonal_regularisation,
    #             base_kernel=reference_gp.kernel,
    #         ),
    #     )
    #     initial_approximate_gp_parameters = ApproximateGPRegression.Parameters(
    #         mean=CustomMean.Parameters(
    #             custom=nn_mean_parameters,
    #         ),
    #         kernel=KernelisedSVGPKernel.Parameters(
    #             base_kernel=reference_gp_parameters.kernel.construct(
    #                 **reference_gp_parameters.kernel.dict()
    #             )
    #         ),
    #     )
    #     (
    #         approximate_gp_parameters,
    #         approximate_post_epoch_history,
    #     ) = train_approximate_gp(
    #         data=experiment_data.train,
    #         empirical_risk_scheme=approximate_gp_empirical_risk_scheme,
    #         regularisation_scheme=RegularisationScheme(
    #             approximate_gp_regularisation_scheme_str
    #         ),
    #         trainer_settings=approximate_gp_trainer_settings,
    #         approximate_gp=approximate_gp,
    #         approximate_gp_parameters=initial_approximate_gp_parameters,
    #         regulariser=reference_gp,
    #         regulariser_parameters=reference_gp_parameters,
    #         save_checkpoint_frequency=approximate_save_checkpoint_frequency,
    #         checkpoint_path=os.path.join(
    #             output_directory,
    #             type(curve_function).__name__.lower(),
    #             checkpoints_folder_name,
    #             "approximate-gp",
    #             approximate_gp_regularisation_scheme_str,
    #         ),
    #     )
    #     plot_prediction(
    #         experiment_data=experiment_data,
    #         inducing_data=Data(
    #             x=reference_gp.x,
    #             y=reference_gp.y,
    #         ),
    #         gp=approximate_gp,
    #         gp_parameters=approximate_gp_parameters,
    #         title=" ".join(
    #             [
    #                 f"Approximate GP ({approximate_gp_regularisation_scheme_str}):",
    #                 f"{curve_function.__name__}",
    #             ]
    #         ),
    #         save_path=os.path.join(
    #             approximate_experiment_directory,
    #             "approximate-gp.png",
    #         ),
    #     )
    #     plot_losses(
    #         losses=[x["gvi-objective"] for x in approximate_post_epoch_history],
    #         labels="gvi-objective",
    #         loss_name=f"{approximate_gp_empirical_risk_scheme.value}+{approximate_gp_regularisation_scheme_str}",
    #         title=" ".join(
    #             [
    #                 f"Approximate GP Objective ({approximate_gp_regularisation_scheme_str}):",
    #                 f"{curve_function.__name__}",
    #             ]
    #         ),
    #         save_path=os.path.join(
    #             approximate_experiment_directory,
    #             "approximate-gp-loss.png",
    #         ),
    #     )
    #     plot_two_losses(
    #         loss1=[x["empirical-risk"] for x in approximate_post_epoch_history],
    #         loss1_name=approximate_gp_empirical_risk_scheme.value,
    #         loss2=[x["regularisation"] for x in approximate_post_epoch_history],
    #         loss2_name=approximate_gp_regularisation_scheme_str,
    #         title=" ".join(
    #             [
    #                 f"Approximate GP Objective Breakdown ({approximate_gp_regularisation_scheme_str}):",
    #                 f"{curve_function.__name__}",
    #             ]
    #         ),
    #         save_path=os.path.join(
    #             approximate_experiment_directory,
    #             "approximate-gp-loss-breakdown.png",
    #         ),
    #     )
    #
    #     tempered_approximate_gp = type(approximate_gp)(
    #         mean=approximate_gp.mean,
    #         kernel=TemperedKernel(
    #             base_kernel=approximate_gp.kernel,
    #             base_kernel_parameters=approximate_gp_parameters.kernel,
    #             number_output_dimensions=approximate_gp.kernel.number_output_dimensions,
    #         ),
    #     )
    #     initial_tempered_gp_parameters = approximate_gp.Parameters.construct(
    #         log_observation_noise=approximate_gp_parameters.log_observation_noise,
    #         mean=approximate_gp_parameters.mean,
    #         kernel=TemperedKernel.Parameters.construct(
    #             log_tempering_factor=jnp.log(1.0)
    #         ),
    #     )
    #     tempered_gp_parameters, tempered_post_epoch_history = train_tempered_gp(
    #         data=experiment_data.validation,
    #         empirical_risk_scheme=tempered_gp_empirical_risk_scheme,
    #         trainer_settings=tempered_gp_trainer_settings,
    #         tempered_gp=tempered_approximate_gp,
    #         tempered_gp_parameters=initial_tempered_gp_parameters,
    #         save_checkpoint_frequency=tempered_save_checkpoint_frequency,
    #         checkpoint_path=os.path.join(
    #             output_directory,
    #             type(curve_function).__name__.lower(),
    #             checkpoints_folder_name,
    #             "tempered-gp",
    #             approximate_gp_regularisation_scheme_str,
    #         ),
    #     )
    #     plot_prediction(
    #         experiment_data=experiment_data,
    #         inducing_data=Data(
    #             x=reference_gp.x,
    #             y=reference_gp.y,
    #         ),
    #         gp=tempered_approximate_gp,
    #         gp_parameters=tempered_gp_parameters,
    #         title=" ".join(
    #             [
    #                 f"Tempered Approximate GP ({approximate_gp_regularisation_scheme_str}):",
    #                 f"{curve_function.__name__}",
    #             ]
    #         ),
    #         save_path=os.path.join(
    #             approximate_experiment_directory, "tempered-approximate-gp.png"
    #         ),
    #     )
    #     plot_losses(
    #         losses=[x["empirical-risk"] for x in tempered_post_epoch_history],
    #         labels="empirical-risk",
    #         loss_name=tempered_gp_empirical_risk_scheme.value,
    #         title=" ".join(
    #             [
    #                 f"Tempered Approximate GP Empirical Risk ({approximate_gp_regularisation_scheme_str}):",
    #                 f"{curve_function.__name__}",
    #             ]
    #         ),
    #         save_path=os.path.join(
    #             approximate_experiment_directory,
    #             "tempered-approximate-gp-loss.png",
    #         ),
    #     )
