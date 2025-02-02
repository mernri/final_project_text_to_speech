import os
import soundfile as sf
import pandas as pd
from io import BytesIO
from pydub import AudioSegment
import soundfile as sf
from IPython.display import Audio, display
from app.utils.text import get_phonem_tokens_from_directory, get_phonems_from_tokens, get_cleaned_transcriptions, phonems_transcript_to_49, get_tokens_from_phonems, phonemize_transcripts
from app.utils.audio import get_melspecs_from_audio_files
from app.utils.preprocess_text import get_padded_tokenized_transcripts
from app.utils.preprocess_audio import get_padded_melspecs

from app.params import PATH_1H, PATH_1h_PHONES, PATH_LJ_AUDIOS, PATH_PHONES_MAPPING, PATH_LJ_CSV, PATH_PHONES_MAPPING_LJSPEECH
import csv

# SPECIFIC TO LIBRISPEECH (OLD) 
def get_audio_files_from_directory(audio_files_path=PATH_1H):
    """
    Parcourt les dossiers imbriqués pour extraire les paths des fichiers audio.
    
    Parameters:
    - audio_files_path: path vers le répertoire contenant les fichiers audio.
    
    Return:
    - Dictionnaire avec les sequence_id comme clés et les path des fichiers audio comme valeurs.
    """
    audio_files = {}
    for root, _, files in os.walk(audio_files_path):
        for filename in files:
            if filename.endswith(".flac"):
                sequence_id = filename.strip('.flac')
                audio_path = os.path.join(root, filename)
                audio_files[sequence_id] = audio_path
    return audio_files

# SPECIFIC TO LIBRISPEECH (OLD)
def get_transcriptions_from_directory(tokenized_transcriptions_path=PATH_1h_PHONES):
    """
    Parcourt les dossiers imbriqués pour extraire les transcriptions audio.
    
    Parameters:
    - tokenized_transcriptions_path: path vers le répertoire contenant les fichiers texte.
    
    Return:
    - Dictionnaire avec les sequence_id comme clés et les transcriptions comme valeurs.
    """

    def get_transcriptions_from_file(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return {line.split()[0]: " ".join(line.split()[1:]) for line in lines}

    transcriptions = {}
    for root, _, files in os.walk(tokenized_transcriptions_path):
        transcription_files = [file for file in files if file.endswith(".txt")]
        if transcription_files:
            transcripts = get_transcriptions_from_file(os.path.join(root, transcription_files[0]))
            transcriptions.update(transcripts)
    return transcriptions

# SPECIFIC TO LIBRISPEECH (OLD)
def make_dataframe(audio_files_path=PATH_1H, tokenized_transcriptions_path=PATH_1h_PHONES, mapping_path=PATH_PHONES_MAPPING ):
    """
    FOR LIBRISPEECH 
    Crée un DataFrame à partir des informations extraites des fonctions fournies.

    Parameters:
    - audio_files_path: Chemin vers le répertoire contenant les fichiers audio et texte.
    - tokenized_transcriptions_path: Chemin vers le fichier contenant une séquence de phonem tokens pour chaque sequence_id.
    - mapping_path: Path vers le fichier JSON contenant le mapping des phonèmes en tokens.

    Returns:
    - DataFrame contenant les colonnes: sequence_id, audio_file, transcription, duration, phonems, phonem_tokens, mel_spec.
    """

    audio_files = get_audio_files_from_directory(audio_files_path)
    transcriptions = get_transcriptions_from_directory(audio_files_path)
    tokenized_transcripts = get_phonem_tokens_from_directory(tokenized_transcriptions_path)
    phonems = get_phonems_from_tokens(tokenized_transcripts, mapping_path)
    melspecs = get_melspecs_from_audio_files(audio_files)

    df = pd.DataFrame({
        'sequence_id': list(audio_files.keys()),
        'audio_file': list(audio_files.values()),
        'transcription': [transcriptions.get(seq_id, "") for seq_id in audio_files.keys()],
        'phonem_tokens': [tokenized_transcripts.get(seq_id, []) for seq_id in audio_files.keys()],
        'phonem': [phonems.get(seq_id, []) for seq_id in audio_files.keys()],
        'mel_spec': [melspecs.get(seq_id, []) for seq_id in audio_files.keys()],
    })

    return df

# SPECIFIC TO LJSPEECH (NEW)
def get_audio_files_from_ljspeech(wavs_directory_path=PATH_LJ_AUDIOS):
    """
    Parcourt les dossiers imbriqués pour extraire les paths des fichiers audio.
    
    Parameters:
    - wavs_directory_path: path vers le répertoire contenant les fichiers audio.
    
    Return:
    - Dictionnaire avec les sequence_id comme clés et les path des fichiers audio comme valeurs.
    """

    wav_files = [file for file in os.listdir(wavs_directory_path) if file.endswith('.wav')]
    
    audio_files_dict = {}
    for wav_file in wav_files:
        sequence_id = wav_file.strip('.wav')
        audio_files_dict[sequence_id] = os.path.join(wavs_directory_path, wav_file)
        
    return audio_files_dict

# SPECIFIC TO LJSPEECH (NEW)
def get_ljspeech_transcripts_from_metadata(transcripts_csv_path=PATH_LJ_CSV):
    """
    Extraire les transcriptions du fichier metadata.csv

    parameter:
    - transcripts_csv_path: path vers le fichier metadata.csv

    Returns:
    - dictionnaire: avec les sequence_id en key et les transcriptions en value
    """
    transcripts_dict = {}
    
    with open(transcripts_csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='|')
        for line in reader:
            sequence_id = line[0]
            # transcription = la normalized transcription si elle existe et est non vide, sinon transcription = transcription normale
            transcription = line[2] if len(line) > 2 and line[2].strip() else line[1]
            transcripts_dict[sequence_id] = transcription            
    return transcripts_dict

# SPECIFIC TO LJSPEECH (NEW)
def get_audio_duration_from_directory(audio_files_path=PATH_LJ_AUDIOS):
    """
    Parcourt les dossiers imbriqués pour calculer la duré des fichiers audio.
    
    Parameters:
    - directory_path: path vers le répertoire contenant les fichiers audio.
    
    Return:
    - Dictionnaire avec les sequence_id comme clés et les durées des audios comme valeurs.
    """
    
    def get_audio_duration(file_path):
        with sf.SoundFile(file_path) as f:
            return round((len(f) / f.samplerate),2)

    audio_files = get_audio_files_from_ljspeech(audio_files_path)
    durations = {sequence_id: get_audio_duration(file_path) for sequence_id, file_path in audio_files.items()}
    return durations

# SPECIFIC TO LJSPEECH (NEW)
def make_ljspeech_dataframe(wavs_directory_path=PATH_LJ_AUDIOS, transcripts_csv_path=PATH_LJ_CSV):
    """
    Crée un DataFrame à partir des informations extraites des fonctions fournies.

    Parameters:
    - wavs_directory_path: Chemin vers le répertoire contenant les fichiers audio et texte.
    - transcripts_csv_path: Chemin vers le fichier contenant une séquence de phonem tokens pour chaque sequence_id.

    Returns:
    - DataFrame contenant les colonnes: sequence_id, audio_file, transcription, cleaned_transcription, duration, phonems, phonem_tokens, mel_spec.
    """

    audio_files = get_audio_files_from_ljspeech(wavs_directory_path)
    
    transcriptions = get_ljspeech_transcripts_from_metadata(transcripts_csv_path)
    
    cleaned_transcriptions = get_cleaned_transcriptions(transcriptions)
    
    extended_phonems = phonemize_transcripts(cleaned_transcriptions)
    phonemized_transcripts = phonems_transcript_to_49(extended_phonems)

    tokenized_transcriptions= get_tokens_from_phonems(phonemized_transcripts, PATH_PHONES_MAPPING_LJSPEECH)
    
    padded_tokenized_transcriptions = get_padded_tokenized_transcripts(tokenized_transcriptions)
    
    durations = get_audio_duration_from_directory(wavs_directory_path)
    
    melspecs = get_melspecs_from_audio_files(audio_files)
    
    padded_mel_specs = get_padded_melspecs(melspecs)
    
    df = pd.DataFrame({
        'sequence_id': list(audio_files.keys()),
        'audio_file': list(audio_files.values()),
        'transcription': [transcriptions.get(sequence_id, "") for sequence_id in audio_files.keys()],
        'cleaned_transcription': [cleaned_transcriptions.get(sequence_id, "") for sequence_id in audio_files.keys()],
        'phonems': [phonemized_transcripts.get(sequence_id, "") for sequence_id in audio_files.keys()],
        'tokens': [tokenized_transcriptions.get(seq_id, []) for seq_id in audio_files.keys()],
        'padded_tokens': [padded_tokenized_transcriptions.get(seq_id, []) for seq_id in audio_files.keys()],
        'duration': [durations.get(sequence_id, 0) for sequence_id in audio_files.keys()],
        'mel_spec': [melspecs.get(sequence_id, []) for sequence_id in audio_files.keys()],
        'padded_mel_specs': [padded_mel_specs.get(seq_id, []) for seq_id in audio_files.keys()],

    })

    return df

#FOR LIBRISPEECH and LJSPEECH
def display_data_by_df_row(row, show_transcript=True, show_seq=True, show_path=True, show_phonem=True, show_tokens=True, show_duration=True):
    """
    Affiche les informations d'une ligne du dataframe et un lecteur audio pour écouter l'extrait associé
    """
    if show_transcript and 'transcription' in row.keys():
        print("transcript:\n", row['transcription'])
    if show_seq and 'sequence_id' in row.keys():
        print("sequence_id:\n", row['sequence_id'])
    if show_path and 'audio_file' in row.keys():
        print("audio_file:\n", row['audio_file'])
    if show_phonem and 'phonems' in row.keys():
        print("phonem:\n", row['phonems'])
    if show_tokens and 'phonem_tokens' in row.keys():
        print("phonem_tokens:\n", row['phonem_tokens'])
    if show_duration and 'duration' in row.keys():
        print("duration:\n", row['duration'])

    # Temporary .wav as IPython.display doesn't handle the .flac files
    audio = AudioSegment.from_file(row['audio_file'], format="flac")
    buffer = BytesIO()
    audio.export(buffer, format="wav")
    
    display(Audio(buffer.getvalue()))