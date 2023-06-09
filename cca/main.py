import os
import sys

from matplotlib import pyplot as plt

sys.path.insert(0, os.path.abspath(".."))
import math
import numpy as np
import scipy.io as sio
from sklearn.cross_decomposition import CCA
from sklearn.metrics import confusion_matrix
import util as u

data_path = os.path.abspath('data')
all_segment_data = dict()
all_acc = list()
window_len = 1
shift_len = 1
sample_rate = 256
duration = int(window_len * sample_rate)
flicker_freq = np.array([9.25, 11.25, 13.25, 9.75, 11.75, 13.75,
                         10.25, 12.25, 14.25, 10.75, 12.75, 14.75])


# reference signal
def get_cca_reference_signals(data_len, target_freq, sampling_rate):
    reference_signals = []
    t = np.arange(0, (data_len / sampling_rate), step=1.0 / (sampling_rate))
    reference_signals.append(np.sin(np.pi * 2 * target_freq * t))
    reference_signals.append(np.cos(np.pi * 2 * target_freq * t))
    reference_signals.append(np.sin(np.pi * 4 * target_freq * t))
    reference_signals.append(np.cos(np.pi * 4 * target_freq * t))
    reference_signals = np.array(reference_signals)
    return reference_signals


def find_correlation(n_components, np_buffer, freq):
    cca = CCA(n_components)
    corr = np.zeros(n_components)
    result = np.zeros(freq.shape[0])
    for freq_idx in range(0, freq.shape[0]):
        cca.fit(np_buffer.T, np.squeeze(freq[freq_idx, :, :]).T)
        O1_a, O1_b = cca.transform(np_buffer.T, np.squeeze(freq[freq_idx, :, :]).T)
        ind_val = 0
        for ind_val in range(0, n_components):
            corr[ind_val] = np.corrcoef(O1_a[:, ind_val], O1_b[:, ind_val])[0, 1]
            result[freq_idx] = np.max(corr)

    return result


def cca_classify(segmented_data, reference_templates):
    predicted_class = []
    labels = []
    for target in range(0, segmented_data.shape[0]):
        for trial in range(0, segmented_data.shape[2]):
            for segment in range(0, segmented_data.shape[3]):
                labels.append(target)
                result = find_correlation(1, segmented_data[target, :, trial, segment, :],
                                          reference_templates)
                predicted_class.append(np.argmax(result) + 1)
    labels = np.array(labels) + 1
    predicted_class = np.array(predicted_class)

    return labels, predicted_class


for subject in np.arange(0, 10):
    dataset = sio.loadmat(f'{data_path}/s{subject + 1}.mat')
    eeg = np.array(dataset['eeg'], dtype='float32')

    num_classes = eeg.shape[0]
    n_ch = eeg.shape[1]
    total_trial_len = eeg.shape[2]
    num_trials = eeg.shape[3]

    filtered_data = u.get_filtered_eeg(eeg, 6, 80, 4, sample_rate)
    all_segment_data[f's{subject + 1}'] = u.get_segmented_epochs(filtered_data, window_len,
                                                                  shift_len, sample_rate)

# 生成每个类别的参考模板矩阵
reference_templates = []
for fr in range(0, len(flicker_freq)):
    reference_templates.append(get_cca_reference_signals(duration, flicker_freq[fr], sample_rate))
reference_templates = np.array(reference_templates, dtype='float32')


fig, ax = plt.subplots(figsize=(7, 5))
plt.rcParams.update({'font.size': 12})
ax.set_title('Accuracy (%)')
for subject in all_segment_data.keys():
    labels, predicted_class = cca_classify(all_segment_data[subject], reference_templates)
    c_mat = confusion_matrix(labels, predicted_class)
    accuracy = np.divide(np.trace(c_mat), np.sum(np.sum(c_mat)))
    ax.bar(subject, accuracy, color="#BA55D3", capsize=5)
    all_acc.append(accuracy)
    print(f'Subject: {subject}, Accuracy: {accuracy * 100} %')
ax.set(xticks=np.arange(1, 10), xlabel='Subject',
           yticks=np.arange(0, 1, step=0.1), ylabel='Accuracy')
ax.grid(axis='y', alpha=0.5)
plt.show()

