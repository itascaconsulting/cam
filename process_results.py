import matplotlib.pyplot as plt
import numpy as np
import json
import glob

X = [] # feature matrix
Y = [] # target vector
for result_file in glob.glob("results/done-*"):
    row = []
    with open(result_file) as f:
        result = json.load(f)
    fail_load = result["result"]["end_load"]
    cohesion_array = result["parameters"]["cohesion_array"]
    raw_parameters = result["parameters"]["raw_parameters"]

    X.append(cohesion_array+raw_parameters)
    Y.append(fail_load)

X, Y = np.array(X), np.array(Y)

plt.hist(Y/1e3)
plt.ylabel("Bin count []")
plt.xlabel("Load at failure [kPa]")
plt.show()

np.save("X.npy", X)
np.save("Y.npy", Y)

# now the X and Y NumPy arrays are the features and targets to be used in machine learning training.
