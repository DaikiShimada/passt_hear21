import torch

from .models.passt import get_model as get_model_passt
from .models.preprocess import AugmentMelSTFT
from .wrapper import PasstBasicWrapper


def load_model(model_path="", mode="all"):
    model = get_concat_2level_model(mode=mode)
    if torch.cuda.is_available():
        model.cuda()
    return model


def get_scene_embeddings(audio, model):
    """
    audio: n_sounds x n_samples of mono audio in the range [-1, 1]. All sounds in a batch will be padded/trimmed to the same length.
    model: Loaded Model.
    Returns:
    embedding: A float32 Tensor with shape (n_sounds, model.scene_embedding_size).
    """
    model.eval()
    with torch.no_grad():
        return model.get_scene_embeddings(audio)


def get_timestamp_embeddings(audio, model):
    """
    audio: n_sounds x n_samples of mono audio in the range [-1, 1]. All sounds in a batch will be padded/trimmed to the same length.
    model: Loaded Model.
    Returns:
    embedding: A float32 Tensor with shape (n_sounds, n_timestamps, model.timestamp_embedding_size).
    timestamps: A float32 Tensor with shape (`n_sounds, n_timestamps). Centered timestamps in milliseconds corresponding to each embedding in the output.
    """
    return get_2lvl_timestamp_embeddings(audio, model)



def get_concat_2level_model(**kwargs):
    mel = AugmentMelSTFT(n_mels=128, sr=32000, win_length=800, hopsize=320, n_fft=1024, freqm=48,
                         timem=192,
                         htk=False, fmin=0.0, fmax=None, norm=1, fmin_aug_range=10,
                         fmax_aug_range=2000)

    net = get_model_passt(arch="passt_s_swa_p16_128_ap476")
    model = PasstBasicWrapper(mel=mel, net=net, timestamp_embedding_size=1295 * 2, **kwargs)
    return model


def get_2lvl_timestamp_embeddings(audio, model):
    """
    audio: n_sounds x n_samples of mono audio in the range [-1, 1]. All sounds in a batch will be padded/trimmed to the same length.
    model: Loaded Model.
    Returns:
    embedding: A float32 Tensor with shape (n_sounds, n_timestamps, model.timestamp_embedding_size).
    timestamps: A float32 Tensor with shape (`n_sounds, n_timestamps). Centered timestamps in milliseconds corresponding to each embedding in the output.
    """
    model.eval()
    with torch.no_grad():
        embed1, t1 = model.get_timestamp_embeddings(audio)
        embed2, t2 = model.get_timestamp_embeddings(audio, window_size=model.timestamp_window * 5)  # larger window
        embed = torch.cat((embed1, embed2), dim=-1)
        return embed, t1

