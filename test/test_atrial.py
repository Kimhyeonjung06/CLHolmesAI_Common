import config
from ecg.ecg_afib import DDNN

from scipy.signal import resample
import numpy as np


def run(np_data: dict, gt_data: dict, raw_signal: dict, raw_fs: dict):
    model = DDNN().ddnn()

    pid_list = np.unique(np_data['pid'])

    for pid in pid_list:
        signal_split_10s = []
        raw_nparray = np.array(raw_signal[pid])
        pid_fs = raw_fs[pid]
        resample_raw_signal = resample(raw_nparray, (int)(len(raw_nparray)/pid_fs * config.FS))
        len_10s_sample = 250 * 10

        for idx in range(len(resample_raw_signal)//len_10s_sample):
            signal_10s = np.array(resample_raw_signal[idx*len_10s_sample : (idx+1)*len_10s_sample])
            signal_split_10s.append(signal_10s)

        if len(resample_raw_signal)%len_10s_sample != 0:
            signal_10s_last = np.array(
                resample_raw_signal[(idx+1)*len_10s_sample : ]).reshape(-1, 1)
            signal_10s_last = np.pad(signal_10s_last, ((0, 2500 - len(signal_10s_last)), (0, 0)), mode='constant',
                                     constant_values=0).flatten()
            signal_split_10s.append(signal_10s_last)

        ecg_pid_array = np.concatenate([arr[np.newaxis, :, np.newaxis] for arr in signal_split_10s], axis=0)

        confidence_AFL = model.predict(ecg_pid_array, batch_size=config.BATCH_SIZE)

        tmp_probability_AFL = confidence_AFL.copy()
        scaled_probability_AFL = np.where(confidence_AFL <= config.AF_THRESHOLD, 0.5 * confidence_AFL / config.AF_THRESHOLD,
                                          0.5 + 0.5 * (confidence_AFL - config.AF_THRESHOLD) / (1 - config.AF_THRESHOLD))

        tmp_probability_AFL[scaled_probability_AFL < 0.5] = 0  # AFIB
        tmp_probability_AFL[scaled_probability_AFL >= 0.5] = 1  # AFL


