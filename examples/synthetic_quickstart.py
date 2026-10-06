import numpy as np
import pandas as pd

from universal_cutoff import CapacityConfig, Module2Config, run_framework

rng = np.random.RandomState(719)
score = rng.randint(0, 101, 12000)
response_probability = 0.05 + 0.92 / (1 + np.exp(-(score - 45) / 8))
data = pd.DataFrame({"score": score, "response": rng.binomial(1, response_probability)})

result = run_framework(
    data, score_col="score", response_col="response",
    module2=Module2Config(), capacity=CapacityConfig(K=1000, period="synthetic cohort"),
)
print(result.module2.anchors.to_string(index=False))
print(result.capacity.table.to_string(index=False))

