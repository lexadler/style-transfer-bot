from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from scipy import misc

class StyleTransferModel:
    def __init__(self):
        pass

    def transfer_style(self, content_img_stream, style_img_stream):
        return style_img_stream
