import pyDOE
import numpy as np
np.random.seed(12344)
import boto3
import json
import random
import hashlib
import base64
import uuid
from io import BytesIO
import joblib

np.random.seed(12344)

min_coh, max_coh = 0.5e5, 5e5
assert max_coh > min_coh
delta_coh = max_coh - min_coh

number_of_unknowns = 5

lhc_sizes = range(2, 8)

for lhc_size in lhc_sizes:
    print("creating cube 2**{}".format(lhc_size))
    case_ids = [str(uuid.uuid4()) for _ in range(2**lhc_size)]
    hyper_cube = pyDOE.lhs(number_of_unknowns, 2**lhc_size)
    cohesion_hyper_cube = min_coh + hyper_cube*delta_coh
    full_cube = np.hstack((hyper_cube, cohesion_hyper_cube))
    joblib.dump((case_ids, full_cube), f"cube_{number_of_unknowns}_{lhc_size}.pkl")
