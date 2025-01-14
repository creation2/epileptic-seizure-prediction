import os
from joblib import dump, load

import numpy as np
import matplotlib.pyplot as plt
from sklearn import svm
from sklearn.metrics import brier_score_loss, accuracy_score, roc_auc_score

os.environ["CUDA_VISIBLE_DEVICES"] = "2"


""" Variables """
n_clip = 3
X = {}
y = {}
interval = {1: {'start': 1640000, 'end': 1740000},
            2: {'start': 150000, 'end': 250000},
            3: {'start': 60000, 'end': 160000}}
seizure = {1: {'start': 1684381 - interval[1]['start'], 'end': 1699381 - interval[1]['start']},
           2: {'start': 188013 - interval[2]['start'], 'end': 201013 - interval[2]['start']},
           3: {'start': 96699 - interval[3]['start'], 'end': 110699 - interval[3]['start']}}


""" Load datasets """

for c in range(1, n_clip+1):

    path = f"/home/phait/datasets/ieeg/TWH056_Day-504_Clip-0-{c}.npz"     # server
    # path = "../../dataset/TWH056_Day-504_Clip-0-1.npz"                     # local

    with np.load(path) as data:
        data = dict(data)

    data['szr_bool'] = data['szr_bool'].astype(int)     # one-hot encoding

    X[c] = data['ieeg'].T[interval[c]['start']:interval[c]['end']]
    y[c] = data['szr_bool'][interval[c]['start']:interval[c]['end']]


""" Select training set and test set """
X_training = np.concatenate((X[2], X[3]), axis=0)
y_training = np.concatenate((y[2], y[3]), axis=0)
X_test = X[1]
y_test = y[1]

print(X_training.shape, y_training.shape)
print(X_test.shape, y_test.shape)

print("Creating the svm classifier...")
num = 1
gamma = 'scale'
weighted = False

clf = svm.SVC(gamma=gamma, probability=True)

print("Fitting training data to the svm classifier...")
if weighted is False:
    clf.fit(X_training, y_training)
else:
    weighted = class_weight = {1: 10}
    clf.fit(X_training, y_training, class_weight="balanced")

dump(clf, f"svm_model{num}.joblib")
# clf = load(f"svm_model{num}.joblib")
# clf = load(f"svm_model1.joblib")

print("Predicting values on test data...")
predictions = clf.predict(X_test)
probabilities = clf.predict_proba(X_test)[:, 1]
errors = abs(predictions - y_test)

print("Results")
loss = round(brier_score_loss(y_test, probabilities), 4)
accuracy = round(accuracy_score(y_test, predictions), 4)
roc_auc_score = round(roc_auc_score(y_test, probabilities), 4)
print(f"\tLoss:\t\t{loss}")
print(f"\tAccuracy:\t{accuracy}")
print(f"\tROC-AUC:\t{roc_auc_score}")


""" Write results into file """
exp = "exp" + str(num)
file_name = exp + "_svm.txt"

with open(file_name, 'w') as file:
    file.write(f"EXPERIMENT {num}: SVM\n\n")

    file.write("Parameters\n")
    file.write(f"\tgamma:\t\t{gamma}\n")
    file.write(f"\tweighted:\t{weighted}\n\n")

    file.write("Data shape\n")
    file.write(f"\tX_training shape:\t{X_training.shape}\n")
    file.write(f"\ty_training shape:\t{y_training.shape}\n")
    file.write(f"\tX_test shape:\t\t{X_test.shape}\n")
    file.write(f"\ty_test shape:\t\t{y_test.shape}\n\n")

    file.write("Results\n")
    file.write(f"\tLoss:\t\t{loss}\n")
    file.write(f"\tAccuracy:\t{accuracy}\n")
    file.write(f"\tROC-AUC:\t{roc_auc_score}\n\n")


""" Plots """
plt.subplot(2, 1, 1)
plt.plot(y_test)
plt.axvline(x=seizure[1]['start'], color="orange", linewidth=0.5)
plt.axvline(x=seizure[1]['end'], color="orange", linewidth=0.5)
plt.subplot(2, 1, 2)
plt.plot(predictions)
plt.axvline(x=seizure[1]['start'], color="orange", linewidth=0.5)
plt.axvline(x=seizure[1]['end'], color="orange", linewidth=0.5)
plt.savefig(f"./plots/{exp}-predictions.png")
plt.close()


def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


plt.figure(figsize=(15.0, 8.0))
plt.plot(probabilities)
plt.axvline(x=seizure[1]['start'], color="orange", linewidth=0.5)
plt.axvline(x=seizure[1]['end'], color="orange", linewidth=0.5)
plt.plot(running_mean(probabilities, 1000))
plt.savefig(f"./plots/{exp}-probabilities.png", dpi=400)
