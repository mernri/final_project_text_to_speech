import matplotlib.pyplot as plt
import librosa
import numpy as np
import soundfile as sf
from app.params import SAMPLE_RATE, N_FFT, HOP_LENGTH, N_MELS

def display_mel_spectrogram(mel_spectrogram, sr=SAMPLE_RATE, hop_length=HOP_LENGTH):
    """
    Affiche une visualisation du mel spectrogramme 

    Paramètres:
    - mel_spectrogram (numpy array): Le mel spectrogramme à afficher.
    - sr: Taux d'échantillonnage. Par défaut à 16000.
    - hop_length: Longueur du saut entre les trames. Par défaut à 512.

    Retour:
    Aucun. Affiche le mel spectrogramme.
    """
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mel_spectrogram, sr=sr, hop_length=hop_length, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel Spectrogram')
    plt.tight_layout()
    plt.show()

def get_sample_rates(audio_files_dict):
    """
    Vérifie si tous les fichiers audio d'un dictionnaire ont le même taux d'échantillonnage

    Parameters:
    - audio_files_dict : Dictionnaire qui contient en key les séquence_id et en value les paths des fichiers audio

    Return:
    Le taux d’échantillonnage unique des fichiers audio ou la liste de taux d'échantillonnage.
    """
    
    # Récupère les taux d'échantillonnage de tous les fichiers audio
    sample_rates = [sf.info(audio_path).samplerate for audio_path in audio_files_dict.values()]
    unique_sample_rates = np.unique(sample_rates)

    if len(unique_sample_rates) == 1:
        print(f"Tous les fichiers ({len(audio_files_dict)} fichiers) ont un taux d'échantillonnage de {unique_sample_rates[0]} Hz.")
        return unique_sample_rates[0]
    else:
        print("Les fichiers ont des taux d'échantillonnage différents.")
        return unique_sample_rates

def waveform_to_mel_spectrogram_from_stft(audio_path, n_fft=N_FFT, hop_length=HOP_LENGTH):
    """
    Calcule le mel spectrogram (numpy array) d'un fichier audio à partir de librosa.stft
    Le mel spectrogram est une représentation de l'audio proche de la perception humaine.
    
    Parameters:
    - audio_path: path vers le fichier audio
    - sr: Taux d'échantillonnage. C'est le nombre d'échantillons de son pris chaque seconde. 16.000Hz par défaut
    - n_fft: Window size pour la transformée de Fourier. Une fenêtre plus grande donne plus de "détails" (comme un zoom)
    - hop_length: Décalage entre chaque fenêtre analysée. 
    - n_mels: Nombre de bandes de fréquences visbiles sur notre mel spectrogram. 

    Retour:
    - mel_spectrogram array
    """
    
    y, _ = librosa.load(audio_path, sr=None)
    stft = librosa.stft(y=y, n_fft=n_fft, hop_length=hop_length)
    mel_spec = librosa.amplitude_to_db(stft, ref=np.max)
    
    return mel_spec

def waveform_to_mel_spectrogram_from_spectrum(audio_path, sr=SAMPLE_RATE, n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=N_MELS):
    """
    Calcule le mel spectrogram (numpy array) d'un fichier audio à partir de librosa.feature.melspectrogram
    Le mel spectrogram est une représentation de l'audio proche de la perception humaine.
    
    Parameters:
    - audio_path: path vers le fichier audio
    - sr: Taux d'échantillonnage. C'est le nombre d'échantillons de son pris chaque seconde. 16.000Hz par défaut
    - n_fft: Window size pour la transformée de Fourier. Une fenêtre plus grande donne plus de "détails" (comme un zoom)
    - hop_length: Décalage entre chaque fenêtre analysée. 
    - n_mels: Nombre de bandes de fréquences visbiles sur notre mel spectrogram. 

    Retour:
    - mel_spectrogram array
    """
    
    y, _ = librosa.load(audio_path, sr=None)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels)
    mel_spec = librosa.power_to_db(S, ref=np.max)
    
    return mel_spec

def get_melspecs_from_audio_files(audio_files_dict, sr=SAMPLE_RATE, n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=N_MELS):
    """
    Calcule le mel spectrogramme pour chaque fichier audio
    
    Parameters:
    - audio_files_dict: Dictionnaire avec les sequence_id comme clés et les path des fichiers audio comme valeurs.
    
    Return:
    - Dictionnaire avec les sequence_id comme clés et les mel spectrogrammes comme valeurs.
    """
    melspecs_dict = {}
    
    for sequence_id, audio_path in audio_files_dict.items():
        melspecs_dict[sequence_id] = waveform_to_mel_spectrogram_from_spectrum(audio_path, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels)
    
    return melspecs_dict
    
    
    
    