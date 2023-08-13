from experiments.shared import schemes
from src.empirical_risks import NegativeLogLikelihood
from src.empirical_risks.base import EmpiricalRiskBase
from src.empirical_risks.cross_entropy import CrossEntropy
from src.gps.base.base import GPBase
from src.gps.base.classification_base import GPClassificationBase


def empirical_risk_resolver(
    empirical_risk_scheme: schemes.EmpiricalRiskScheme, gp: GPBase
) -> EmpiricalRiskBase:
    if empirical_risk_scheme == schemes.EmpiricalRiskScheme.negative_log_likelihood:
        return NegativeLogLikelihood(gp=gp)
    if empirical_risk_scheme == schemes.EmpiricalRiskScheme.cross_entropy:
        assert isinstance(
            gp, GPClassificationBase
        ), "CrossEntropy is only for classification"
        return CrossEntropy(gp=gp)
    else:
        raise ValueError(f"Unknown empirical risk scheme: {empirical_risk_scheme=}")
