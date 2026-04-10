import uuid
import gc
import torch


def generate_unic_name(filename):
    return uuid.uuid5(uuid.NAMESPACE_DNS, filename)


def allowed_file(filename):
    return filename.split('.')[-1].lower() == "txt"

def clear_hardware_cache():
    """
    Очищает оперативную память и видеопамять.
    """
    gc.collect()
    if torch.cuda.is_available():
        with torch.cuda.device('cuda'):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    gc.collect()