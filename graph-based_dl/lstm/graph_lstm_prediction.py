import os

import tensorflow.keras.backend as K
import matplotlib.pyplot as plt
import numpy as np
from itertools import product
from tensorflow.keras.regularizers import l2
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss, accuracy_score, roc_auc_score
from sklearn.utils import shuffle
from spektral.brain import get_fc
import sys
sys.path.append("....")
from utils.utils import add_experiment, save_experiments, generate_indices
from utils.load_data import load_data

os.environ["CUDA_VISIBLE_DEVICES"] = "2"
np.random.seed(0)

X, y, dataset, seizure = load_data()

# -----------------------------------------------------------------------------
# DATA PREPROCESSING
# -----------------------------------------------------------------------------
""" Select training set and test set """
X_train = np.concatenate((X[2], X[3]), axis=0)
y_train = np.concatenate((y[2], y[3]), axis=0)
X_test = X[1]
y_test = y[1]

n_positive = np.sum(y_train)
n_negative = len(y_train) - n_positive

""" Normalize data """
scaler = StandardScaler()
scaler.fit(dataset)
X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)

""" Neural network hyperparameters """
num = 1

epochs = [10]
batch_size = 64
depth_lstm = [1]     # search
depth_dense = [2]
units_lstm = [256]
reg_n = ['5e-1']      #['5e-3', '5e-2', '5e-1']
activation = ['relu']
batch_norm = [True]
dropout = [0.4]        #[0.5, 0.4, 0.3]
class_weight = {0: (len(y_train) / n_negative), 1: (len(y_train) / n_positive)}

""" Functional connectivity hyperparameters """
band_freq = (70., 100.)
sampling_freq = [100.]
# samples_per_graph = 500
# fc_measure = 'corr'
# link_cutoff = 0.
percentiles = (40, 60)
# band_freq_hi = (20., 45.)
# nfft = 128
# n_overlap = 64
# nf_mode = 'mean'
# self_loops = True

""" Sequences hyperparameters """
subsampling_factor = [2]
stride = [10]
look_back = [1000]
target_steps_ahead = [2000]  # starting from the position len(sequence)
predicted_timestamps = 1

original_X_train = X_train
original_y_train = y_train
original_X_test = X_test
original_y_test = y_test

tunables = [epochs, depth_lstm, depth_dense, units_lstm, reg_n, activation,
            batch_norm, dropout, sampling_freq,
            subsampling_factor, stride, look_back, target_steps_ahead]

for epochs, depth_lstm, depth_dense, units_lstm, reg_n, activation,\
    batch_norm, dropout, sampling_freq, subsampling_factor, stride, look_back,\
    target_steps_ahead in product(*tunables):

    reg = l2(float(reg_n))

    """ Generate subsampled sequences """
    # Generate sequences by computing indices for training data
    inputs_indices_seq, target_indices_seq = \
        generate_indices([original_y_train],  # Targets associated to X_train (same shape[0])
                         look_back,  # Length of input sequences
                         stride=stride,  # Stride between windows
                         target_steps_ahead=target_steps_ahead,  # How many steps ahead to predict (x[t], ..., x[t+T] -> y[t+T+k])
                         subsample=True,  # Whether to subsample
                         subsampling_factor=subsampling_factor  # Keep this many negative samples w.r.t. to positive ones
                         )
    X_train = original_X_train[inputs_indices_seq]
    y_train = original_y_train[target_indices_seq]

    # Generate sequences by computing indices for test data
    inputs_indices_seq, target_indices_seq = \
        generate_indices([original_y_test],  # Targets associated to X_train (same shape[0])
                         look_back,  # Length of input sequences
                         stride=stride,  # Stride between windows
                         target_steps_ahead=target_steps_ahead,  # How many steps ahead to predict (x[t], ..., x[t+T] -> y[t+T+k])
                         )
    X_test = original_X_test[inputs_indices_seq]
    y_test = original_y_test[target_indices_seq]

    """ Shuffle training data """
    X_train_shuffled, y_train_shuffled = shuffle(X_train, y_train)

    print(X_train.shape, y_train.shape)
    print(X_test.shape, y_test.shape)

    """ Generate graphs from sequences """
    for i in range(1):
        seq = X_train_shuffled[i]
        print(f"Dim of a single sequence: {seq.shape}")
        seq = np.transpose(seq)
        print(f"Single sequence transposed: {seq.shape}")
        g = get_fc(seq, band_freq, sampling_freq, percentiles=percentiles)
        print(f"Turned into fc graph: {g.shape}")
        print(g)


    # -----------------------------------------------------------------------------
    # MODEL BUILDING, TRAINING AND TESTING
    # -----------------------------------------------------------------------------
    """ Build the model """
    # exp = "exp" + str(num)
    # file_name = exp + "_conv_pred.txt"
    # print(f"\n{exp}\n")

