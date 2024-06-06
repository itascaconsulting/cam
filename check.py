import matplotlib; matplotlib.rcParams["savefig.directory"] = "."
from matplotlib import pyplot as plt
plt.rcParams.update({'font.size': 18})


import numpy as np
import joblib
import glob
import json
import os.path
from collections import defaultdict


results = "demo/set0/done-*"
number_of_unknowns = 5

cubes = defaultdict(list)
loads, disps = defaultdict(list), defaultdict(list)

print("building result hash")
for i, result_file in enumerate(glob.glob(results)):
    data = json.load(open(result_file))

    end_load = data["result"]["end_load"]

    cohesion_array = data["parameters"]["cohesion_array"]
    cube_id = data["cube_id"]
    loads[cube_id].append(data["result"]["load"])
    disps[cube_id].append(data["result"]["disp"])

    row = cohesion_array + [end_load]
    cubes[cube_id].append(row)


print("done reading")
print(cubes.keys())
for cube_id in cubes.keys():
    for d,l in zip(disps[cube_id], loads[cube_id]):
        plt.plot(d,l)
    1/0
