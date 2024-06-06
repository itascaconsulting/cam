import numpy as np
import joblib

X_train, X_test, Y_train, Y_test = joblib.load("tts.pkl")

np.savetxt("X.txt", np.vstack((np.array(X_train), np.array(X_test))))
np.savetxt("Y.txt", np.hstack((np.array(Y_train), np.array(Y_test))))
