from dataclasses import asdict, dataclass
from typing import Optional

from .exceptions import InputValidationError


@dataclass(frozen=True)
class Module2Config:
    min_bin_n: int = 40
    min_valid_bins: int = 8
    target_valid_bins: int = 30
    max_valid_bins: int = 40
    min_isotonic_dynamic_range: float = 0.08
    min_logistic_bic_improvement: float = 6.0
    max_selected_changepoints: int = 2
    min_bins_per_segment: int = 5
    cp_candidate_stride: int = 2
    min_structural_bic_improvement: float = 6.0
    smooth_null_alpha: float = 0.10
    min_standardized_slope_change: float = 0.12
    min_cp_bootstrap_support: float = 0.50
    cp_support_tolerance_bins: float = 2.0
    max_alignment_bins: float = 1.0
    bin_width: Optional[float] = None

    def __post_init__(self):
        if self.min_bin_n < 1 or self.min_valid_bins < 2:
            raise InputValidationError("min_bin_n and min_valid_bins must be positive")
        if self.bin_width is not None and self.bin_width <= 0:
            raise InputValidationError("bin_width must be positive")

    def snapshot(self):
        return asdict(self)


@dataclass(frozen=True)
class CapacityConfig:
    K: int
    period: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.K, bool) or int(self.K) != self.K or self.K < 0:
            raise InputValidationError("K must be a nonnegative integer")


@dataclass(frozen=True)
class CostConfig:
    enabled: bool = False
    R: Optional[float] = None

    def __post_init__(self):
        if self.enabled and (self.R is None or self.R <= 0):
            raise InputValidationError("enabled cost audit requires R > 0")


@dataclass(frozen=True)
class BootstrapConfig:
    """Validation-only resampling configuration. Disabled in ordinary runs."""

    enabled: bool = False
    n_bootstrap: int = 200
    group_col: Optional[str] = None
    random_state: int = 42
    n_jobs: int = 1

    def __post_init__(self):
        if isinstance(self.n_bootstrap, bool) or int(self.n_bootstrap) != self.n_bootstrap or self.n_bootstrap < 1:
            raise InputValidationError("n_bootstrap must be a positive integer")
        if self.n_jobs == 0:
            raise InputValidationError("n_jobs cannot be zero")
