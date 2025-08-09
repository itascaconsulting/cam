import numpy as np
import joblib
import glob
import json
import os.path
from collections import defaultdict


results = "demo/set1/done-*"
number_of_unknowns = 5

cubes = defaultdict(list)

print("building result hash")
for i, result_file in enumerate(glob.glob(results)):
    data = json.load(open(result_file))

    end_load = data["result"]["end_load"]

    cohesion_array = data["parameters"]["cohesion_array"]
    cube_id = data["cube_id"]


    row = cohesion_array + [end_load]
    cubes[cube_id].append(row)


print("done reading")
print(cubes.keys())
for cube_id in cubes.keys():
        np.save(f"result_cube_5_{cube_id}.npy", cubes[cube_id])
