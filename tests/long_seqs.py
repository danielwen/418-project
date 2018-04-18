import argparse
import os
import tensorflow as tf
import numpy as np
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from linear_recurrent_net.layers import linear_surrogate_lstm

INPUT_DIM = 128
NUM_CLASSES = 2 # +1 or -1

def gen_sample(seq_length):

    # Choose element to be predicted
    desired_class = np.random.choice([-1,1], size=1)
    desired_vec = np.zeros((1,INPUT_DIM))
    desired_vec[0,0] = desired_class

    # Make random one hot vectors for the data 
    all_vectors = np.eye(INPUT_DIM)
    X = all_vectors[np.random.choice(all_vectors.shape[0], size=seq_length)]

    X = np.concatenate((desired_vec, X), axis=0)

    desired_vec = desired_vec.squeeze(0)
    return X, desired_vec

def gen_data(batch_size, seq_length):

    data_X = []
    data_y = []

    for _ in range(batch_size):
        sample_X, sample_y = gen_sample(seq_length)
        data_X.append(sample_X)
        data_y.append(sample_y)

    batch_X = np.array(data_X)
    batch_y = np.array(data_y)

    batch_X = np.swapaxes(batch_X, 0, 1)

    return batch_X, batch_y

def ls_lstm(seq_len, X):
    n_hidden = 256
    n_classes = 2
    n_steps = seq_len
    batch_size = 65536 // seq_len
    n_input = 24
    n_layers = 2

    W = tf.get_variable('W', initializer=
                         tf.random_normal([n_hidden, INPUT_DIM]), dtype='float')
    b = tf.get_variable('b', initializer=tf.zeros([INPUT_DIM]), dtype='float')

    layer1 = linear_surrogate_lstm(X, n_hidden, name='ls-lstm')
    outputs = linear_surrogate_lstm(layer1, n_hidden, name='ls-lstm2')    
    pred = tf.matmul(outputs[-1], W) + b

    return pred

def run(args):
    seq_len = args.seq_len
    batch_size = args.batch_size
    learning_rate = 0.001
    training_iters = args.num_epochs

    X = tf.placeholder("float", [seq_len+1, batch_size, INPUT_DIM])
    y = tf.placeholder("float", [batch_size, INPUT_DIM])

    pred = ls_lstm(seq_len, X)
    errors = tf.count_nonzero(tf.sign(pred[:,0]) - y[:,0])
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    train_op = optimizer.minimize(loss)
    init = tf.global_variables_initializer()

    with tf.Session() as sess:
        sess.run(init)
        for train_iter in range(training_iters):
            X_data, y_data = gen_data(batch_size, seq_len)
            # print(X_data.shape)
            # print(y_data.shape)
            _, loss_val, errors_val = sess.run([train_op, loss, errors], feed_dict={X: X_data, y: y_data})
            print("Loss:", loss_val, "Accuracy:", 1 - errors_val / batch_size)

def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument("--seq-len", required=True, type=int)

    args.add_argument("--lr", default=1e-4)
    args.add_argument("--batch-size", type=int, default=256)
    args.add_argument("--num-epochs", default=100)

    args.add_argument("--print-epoch", default=1, help="How often to print epoch number")
    args.add_argument("--gpuid", default=-1, type=int)
    return args.parse_args()

if __name__=="__main__":
    args = parse_args()
    run(args)

