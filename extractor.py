'''
Batik VGG16 feature extractor

Author: yohanes.gultom@gmail.com
'''

import os
import tables
import sys
import numpy as np
from keras.applications.vgg16 import VGG16
from keras.models import Model
from keras.layers import Input, Flatten


# params
BATCH_SIZE = 40

# const
EXPECTED_SIZE = 224
EXPECTED_CHANNELS = 3
# EXPECTED_DIM = (EXPECTED_CHANNELS, EXPECTED_SIZE, EXPECTED_SIZE)  # Theano
EXPECTED_DIM = (EXPECTED_SIZE, EXPECTED_SIZE, EXPECTED_CHANNELS)  # Tensorflow
FEATURES_FILE = 'features.h5'
# FEATURES_DIM = (512, 7, 7) # Theano
FEATURES_DIM = (7, 7, 512) # TensorFlow
EXPECTED_CLASS = 5

if __name__ == '__main__':
    # command line arguments
    dataset_file = sys.argv[1]
    features_file = sys.argv[2] if len(sys.argv) > 2 else FEATURES_FILE

    # loading dataset
    print('Loading preprocessed dataset: {}'.format(dataset_file))
    datafile = tables.open_file(dataset_file, mode='r')
    dataset = datafile.root
    print((dataset.data.nrows,) + dataset.data[0].shape)

    # feature extractor    
    vgg16 = VGG16(weights='imagenet', include_top=False)
    input = Input(shape=EXPECTED_DIM, name='input')
    output = vgg16(input)
    x = Flatten(name='flatten')(output)
    extractor = Model(input=input, output=x)    

    print('Feature extraction')
    flatten_dim = np.prod(FEATURES_DIM)
    features_datafile = tables.open_file(features_file, mode='w')
    features_data = features_datafile.create_earray(features_datafile.root, 'data', tables.Float32Atom(shape=flatten_dim), (0,), 'dream')
    features_labels = features_datafile.create_earray(features_datafile.root, 'labels', tables.UInt8Atom(shape=(EXPECTED_CLASS)), (0,), 'dream')

    i = 0
    while i < dataset.data.nrows:
        end = i + BATCH_SIZE
        data_chunk = dataset.data[i:end]
        label_chunk = dataset.labels[i:end]
        i = end
        features = extractor.predict(data_chunk, verbose=1)
        features_data.append(features)
        features_labels.append(label_chunk)

    assert features_datafile.root.data.nrows == dataset.data.nrows
    assert features_datafile.root.labels.nrows == dataset.labels.nrows

    # close feature file
    features_datafile.close()