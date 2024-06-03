import numpy as np
import matplotlib; matplotlib.rcParams["savefig.directory"] = "."
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure
from scipy.spatial import cKDTree
import joblib

scaler, mlpr = joblib.load("final_model.pkl")
X_train, X_test, Y_train, Y_test = joblib.load("tts.pkl")

from scipy.spatial import cKDTree

def show_actual_predicted(actual, predicted, target_unit=""):
    assert len(actual.shape)==1
    assert len(predicted.shape)==1

    fig = plt.figure(constrained_layout=True, figsize=(15, 10))
    gs = fig.add_gridspec(3, 5) # vert the horiz
    ax1 = fig.add_subplot(gs[0:2, 0:2]) # scatter dim
    ax2 = fig.add_subplot(gs[0:2, 2:4]) # scatter percent
    ax3 = fig.add_subplot(gs[0:2, 4]) # target hist
    ax4 = fig.add_subplot(gs[2, :2]) # dimensional error hist
    ax5 = fig.add_subplot(gs[2, 2:4]) # percent error hist
    ax6 = fig.add_subplot(gs[2, 4]) # text input


    error = actual-predicted
    data_bc_error = (error) / actual
    data_bc_error = data_bc_error * 100

    points = np.array([error, actual]).T
    K=100
    if len(points)<100:
        K=10

    dist = np.log10(np.mean(cKDTree(points).query(points, k=K)[0], axis=1))
    order = np.argsort(dist)[::-1]
    dist = dist[order]
    p_error = np.array(error)[order]
    p_actual = np.array(actual)[order]
    ax1.scatter(p_error, p_actual, c=dist, cmap=plt.cm.get_cmap('jet').reversed(), s=2)
    ax1.set_ylabel(f"Actual [{target_unit}]")
    ax1.set_xlabel(f"Error [{target_unit}]")
    ax1.axvline(0, linestyle='--', color='k', lw=1.5)

    points = np.array([data_bc_error, actual]).T
    dist = np.log10(np.mean(cKDTree(points).query(points, k=K)[0], axis=1))
    order = np.argsort(dist)[::-1]
    dist = dist[order]
    p_error = np.array(data_bc_error)[order]
    p_actual = np.array(actual)[order]
    ax2.scatter(p_error, p_actual, c=dist, cmap=plt.cm.get_cmap('jet').reversed(), s=2)
    ax2.set_ylabel(f"Actual [{target_unit}]")
    ax2.set_xlabel("Error %")
    ax2.axvline(0, linestyle='--', color='k', lw=1.5)


    ax3.axvline(0, linestyle='--', color='k', lw=1.5)
    ax3.grid(axis='y')
    ax3.set_xlabel('Count ')
    ax3.set_ylabel(f'Actual [{target_unit}]')

    ax3.hist(actual, bins=200, orientation="horizontal");

    ax4.hist(actual-predicted, bins=200)
    ax4.axvline(0, linestyle='--', color='k', lw=1.5)
    ax4.set_xlabel(f'Error [{target_unit}]')
    ax4.set_ylabel('Count')

    ax5.hist(data_bc_error, bins=200)
    ax5.axvline(0, linestyle='--', color='k', lw=1.5)
    ax5.set_xlabel('Error %')
    ax5.set_ylabel('Count')


    points = np.array((predicted,actual)).T
    dist = np.log10(np.mean(cKDTree(points).query(points,k=K)[0],axis=1))
    order = np.argsort(dist)[::-1]
    dist=dist[order]
    predicted=np.array(predicted)[order]
    actual=np.array(actual)[order]
    # plt.yscale("log")
    # plt.xscale("log")
    ax6.scatter(predicted, actual, c=dist, cmap=plt.cm.get_cmap('jet').reversed(), s=2)
    ax6.set_ylabel("Actual target []")
    ax6.set_xlabel("Predicted target []")
    # ticks = (0.5,1.0,2,5,10,15,20)
    # plt.xticks(ticks)

    #plt.yticks(ticks)
    ax6.plot([actual.min(), actual.max()], [actual.min(), actual.max()], "--", color="black", linewidth=1)
    ax6.set_aspect(1)


    plt.show()

pred = mlpr.predict(scaler.transform(X_test)) # should be scaled already
act = Y_test
show_actual_predicted(act, pred)
