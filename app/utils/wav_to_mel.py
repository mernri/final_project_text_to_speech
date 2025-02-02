import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from argparse import Namespace


from data import get_audio_files_from_ljspeech
from app.params import PATH_MELSPEC,SAMPLE_RATE,N_FFT,HOP_LENGTH,N_MELS
from app.utils.preprocess_audio import get_padded_melspecs

_mel_basis = None


hparams = Namespace(sample_rate = SAMPLE_RATE,
                    n_fft = N_FFT,
                    num_mels = N_MELS,
                    hop_size = HOP_LENGTH,
                    win_size = N_FFT,
                    fmin = 0,
                    fmax = 8000,
                    preemphasis = 0.97,
                    preemphasize = False,
                    # Settings for hifigan-style mel preprocessing
                    use_hifigan_spectrograms = True,
                    # Settings for RTVC-style mel preprocessing
                    min_level_db = -100,
                    ref_level_db = 20,
                    max_abs_value = 4.,
                    symmetric_mels = True,
                    signal_normalization = True,
                    allow_clipping_in_normalization = True,
                    # Griffin-Lim settings
                    power = 1.2,
                    griffin_lim_iters = 30,
                    # HiFi-GAN settings
                    hifigan_model_path = "saved_models/generator_v3",
                    resblock = "2",
                    upsample_rates = [8,8,4],
                    upsample_kernel_sizes = [16,16,8],
                    upsample_initial_channel = 256,
                    resblock_kernel_sizes = [3,5,7],
                    resblock_dilation_sizes = [[1,2], [2,6], [3,12]],
)

def load_wav(path, hparams):
    # Loads an audio file and returns the waveform data.
    wav, _ = librosa.load(str(path), sr=hparams.sample_rate)
    return wav

def save_wav(wav, path, hparams):
    # Saves waveform data to audio file.
    sf.write(path, wav, hparams.sample_rate)

def melspectrogram(wav, hparams):
    # Converts a waveform to a mel-scale spectrogram.
    # Output shape = (num_mels, frames)

    # Apply preemphasis
    if hparams.preemphasize:
        wav = _preemphasis(wav, hparams)

    # Short-time Fourier Transform (STFT)
    D = librosa.stft(y=wav,
                     n_fft=hparams.n_fft,
                     hop_length=hparams.hop_size,
                     win_length=hparams.win_size)

    # Convert complex-valued output of STFT to absolute value (real)
    S = np.abs(D)

    # Build and cache mel basis
    # This improves speed when calculating thousands of mel spectrograms.
    global _mel_basis
    if _mel_basis is None:
        _mel_basis = _build_mel_basis(hparams)

    # Transform to mel scale
    S = np.dot(_mel_basis, S)

    if hparams.use_hifigan_spectrograms:
        # Dynamic range compression
        S = np.log(np.clip(S, a_min=1e-5, a_max=None))
    else:
        # Convert amplitude to dB
        min_level = np.exp((hparams.min_level_db + hparams.ref_level_db)/ 20 * np.log(10))
        S = 20 * np.log10(np.maximum(min_level, S)) - hparams.ref_level_db

        # Normalize
        if hparams.signal_normalization:
            S = (S - hparams.min_level_db) / (-hparams.min_level_db)
            if hparams.symmetric_mels:
                S = 2 * hparams.max_abs_value * S - hparams.max_abs_value
                min_value = -hparams.max_abs_value
                max_value = hparams.max_abs_value
            else:
                S = hparams.max_abs_value * S
                min_value = 0
                max_value = hparams.max_abs_value

            if hparams.allow_clipping_in_normalization:
                S = np.clip(S, min_value, max_value)

    return S.astype(np.float32)


def _preemphasis(wav, hparams):
    # Amplifies high frequency content in a waveform.
    wav = signal.lfilter([1, -hparams.preemphasis], [1], wav)
    return wav

def _inv_preemphasis(wav, hparams):
    # Inverts the preemphasis filter.
    wav = signal.lfilter([1], [1, -hparams.preemphasis], wav)
    return wav

def _build_mel_basis(hparams):
    return librosa.filters.mel(sr=hparams.sample_rate, n_fft=hparams.n_fft, n_mels=hparams.num_mels,
                               fmin=hparams.fmin, fmax=hparams.fmax)

def _griffin_lim(S, hparams):
    angles = np.exp(2j * np.pi * np.random.rand(*S.shape))
    S = np.abs(S).astype(complex)
    wav = librosa.istft(S * angles, hop_length=hparams.hop_size, win_length=hparams.win_size)
    for i in range(hparams.griffin_lim_iters):
        angles = np.exp(1j * np.angle(librosa.stft(wav, n_fft=hparams.n_fft, hop_length=hparams.hop_size, win_length=hparams.win_size)))
        wav = librosa.istft(S * angles, hop_length=hparams.hop_size, win_length=hparams.win_size)

    return wav

# def process_all_wavs_in_folder(folder_path, hparams):

#     # Get all .wav files in the folder
#     wav_files = glob.glob(os.path.join(folder_path, "*.wav"))

#     for wav_file in wav_files:

#         # Load waveform
#         wav = load_wav(wav_file, hparams)

#         # Convert mel spectrogram
#         mel = melspectrogram(wav, hparams)

#         # Save mel spectrogram
#         save_path = os.path.splitext(wav_file)[0].replace('wavs','melspectrogram') + ".npy"
#         np.save(save_path, mel)


#def process_all_wavs_in_folder():
    all_wav_paths = get_audio_files_from_ljspeech()

    for key, value in all_wav_paths.items():
        # Load waveform
        wav = load_wav(value, hparams)

        # Convert mel spectrogram
        mel = melspectrogram(wav, hparams)

        # build path + filename
        file_path_and_name = f"{PATH_MELSPEC}/{key}.npy"

        # Save mel spectrogram
        np.save(file_path_and_name, mel)
        print('Files saved successfully')

#if __name__ == '__main__':
    print(process_all_wavs_in_folder())


def process_all_wavs_in_folder_padded():
    all_wav_paths = get_audio_files_from_ljspeech()
    mel_dict = dict()

    for key, value in all_wav_paths.items():
        # Load waveform
        wav = load_wav(value, hparams)
        # Convert mel spectrogram
        mel = melspectrogram(wav, hparams)
        # Lets build a dict
        mel_dict[key] = mel
    return mel_dict



if __name__ == '__main__':
    non_padded_dict = process_all_wavs_in_folder_padded()
    print(non_padded_dict)
    print(len(non_padded_dict))
    mel_padded_dict = get_padded_melspecs(non_padded_dict)
    print(len(mel_padded_dict))
    print(mel_padded_dict)

    for key, value in mel_padded_dict.items():
        # build path + filename
        file_path_and_name = f"{PATH_MELSPEC}/{key}.npy"
        # Save mel spectrogram
        np.save(file_path_and_name, value)
    print('Files saved successfully')
