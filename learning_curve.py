import matplotlib; matplotlib.rcParams["savefig.directory"] = "."
import numpy as np
import pylab as plt
import sklearn as skl
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.inspection import permutation_importance
import time
import os
import joblib

start_time = time.time()


def train_and_test(X_train, y_train, X_test, y_test):
    lsize = len(X_train[0])
    sizes = (lsize, lsize, lsize)
    print(sizes)

    scaler = skl.preprocessing.StandardScaler()
    scaler.fit(X_train)

    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    mlpr = MLPRegressor(
        hidden_layer_sizes=sizes,
        activation='tanh',
        solver='lbfgs',
        alpha=1e-6,
        max_iter=4*1600,
        random_state=1

        # solver='sgd',
        # learning_rate='adaptive',
        # learning_rate_init=0.1,
        # momentum=0.90,
        # max_iter=10 * 160,
        # tol=2.5e-5,
        # n_iter_no_change=10,
        # random_state=2,
        # shuffle=True,
        # verbose=False
    )

    mlpr.fit(X_train_scaled, y_train)

    y_pred = mlpr.predict(X_test_scaled)

    ts = mlpr.score(X_train_scaled, y_train)
    vs = mlpr.score(X_test_scaled, y_test)
    print(ts, vs)

    return (scaler, mlpr), ts, vs, X_train_scaled, y_train, X_test_scaled, y_test, y_pred



lhc_sizes = range(0, 20)
number_of_unknowns = 3
X_train, X_test = [], []
Y_train, Y_test = [], []
test_score, validation_score = [], []

sizes = []
cube_size = []
for size, filename in zip(lhc_sizes,[f"result_cube_5_{_}.npy" for _ in lhc_sizes]):
    if not os.path.exists(filename):
        continue
    print(f"training {filename}")
    XY = np.load(filename)

    Y = XY[:, -1]
    if len(Y) < 0.95 * 2**size:
        print("skipping partial cube", size, 2**size, len(Y))
        #continue

    sizes.append(len(XY)+sum(cube_size))
    cube_size.append(len(XY))


    Y = XY[:, -1]
    X = XY[:, :-1]
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.20, random_state=2)
    X_train += x_train.tolist()
    X_test += x_test.tolist()
    Y_train += y_train.tolist()
    Y_test += y_test.tolist()

    res = train_and_test(np.array(X_train), np.array(Y_train),
                         np.array(X_test), np.array(Y_test))
    (scaler, mlpr), ts, vs, X_train_scaled, y_train, X_test_scaled, y_test, y_pred = res
    test_score.append(ts)
    validation_score.append(vs)
    print(len(X_train)+len(X_test), vs)
    print(' ')

joblib.dump((scaler, mlpr), "final_model.pkl")
joblib.dump((X_train, X_test, y_train, y_test), "tts.pkl")

# = joblib.load("tts.pkl")

plt.semilogx(sizes, -np.log10(1-np.array(validation_score)), "o-")
plt.semilogx(sizes, -np.log10(1-np.array(test_score)), "o-")
plt.ylabel("Model score [$-log_{10}(1-R^2)$]")
plt.xlabel("Number of samples []")
bbox = dict(boxstyle='round', facecolor='white')
plt.axhline(-np.log10(1-0.9), color="black")
plt.axhline(-np.log10(1-0.99), color="black")
plt.axhline(-np.log10(1-0.999), color="black")
plt.axhline(-np.log10(1-0.9999), color="black")
plt.text(20, 1.0, "$R^2=0.9$", bbox=bbox, verticalalignment="center")
plt.text(20, 2.0, "$R^2=0.99$", bbox=bbox, verticalalignment="center")
plt.text(20, 3.0, "$R^2=0.999$", bbox=bbox, verticalalignment="center")
plt.ylim(None, 3.3)
plt.xlim(8, 1e6)
plt.show()


print(sizes, test_score)
print(sizes, validation_score)
