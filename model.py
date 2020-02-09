from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
import copy
from scipy import misc

class Normalization(nn.Module):
        def __init__(self, mean, std):
            super(Normalization, self).__init__()
            self.mean = torch.tensor(mean).view(-1, 1, 1)
            self.std = torch.tensor(std).view(-1, 1, 1)

        def forward(self, img):
            return (img - self.mean) / self.std

class StyleLoss(nn.Module):
        def __init__(self, target_feature):
            super(StyleLoss, self).__init__()
            self.target = self.gram_matrix(target_feature).detach()
            self.loss = F.mse_loss(self.target, self.target)

        def forward(self, input_v):
            G = self.gram_matrix(input_v)
            self.loss = F.mse_loss(G, self.target)
            return input_v
        
        def gram_matrix(self, input_v):
                batch_size , h, w, f_map_num = input_v.size()
                features = input_v.view(batch_size * h, w * f_map_num)
                G = torch.mm(features, features.t())
                return G.div(batch_size * h * w * f_map_num)

class ContentLoss(nn.Module):

        def __init__(self, target,):
            super(ContentLoss, self).__init__()
            self.target = target.detach()
            self.loss = F.mse_loss(self.target, self.target)

        def forward(self, input_v):
            self.loss = F.mse_loss(input_v, self.target)
            return input_v

class StyleTransferModel:
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.imsize = 128
        self.cnn = models.vgg19(pretrained=True).features.to(device).eval()
    
    def image_loader(self, img_stream):
        loader = transforms.Compose([
            transforms.Resize(self.imsize),
            transforms.CenterCrop(self.imsize),
            transforms.ToTensor()])
        image = Image.open(img_stream)
        image = loader(image).unsqueeze(0)
        return image.to(self.device, torch.float)

    def transfer_style(self, content_img_stream, style_img_stream,
                                                            num_steps=500,
                                                            style_weight=100000,
                                                            content_weight=1):
        print(f'Device is {self.device}.\nBuilding the style transfer model...')
        style_img = self.image_loader(style_img_stream)
        content_img = self.image_loader(content_img_stream)
        input_img = content_img.clone()
        model, style_losses, content_losses = self.get_style_model_and_losses(style_img, content_img)
        optimizer = self.get_input_optimizer(input_img)
        print('Optimizing...')
        run = [0]
        while run[0] <= num_steps:
        
            def closure():
                input_img.data.clamp_(0, 1)
                optimizer.zero_grad()
                model(input_img)
                style_score = 0
                content_score = 0
                for sl in style_losses:
                    style_score += sl.loss
                for cl in content_losses:
                    content_score += cl.loss
                style_score *= style_weight
                content_score *= content_weight
                loss = style_score + content_score
                loss.backward()
                run[0] += 1
                if run[0] % 50 == 0:
                    print("run {}:".format(run))
                    print('Style Loss : {:4f} Content Loss: {:4f}'.format(
                        style_score.item(), content_score.item()))
                    print()
                return style_score + content_score
            
            optimizer.step(closure)

        input_img.data.clamp_(0, 1)
        return input_img            
    #    return misc.toimage(self.image_loader(content_img_stream)[0])
    
    def get_style_model_and_losses(self, style_img, content_img,
                                   content_layers=['conv_4'],
                                   style_layers=['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']):
        cnn = copy.deepcopy(self.cnn)
        normalization_mean = torch.tensor([0.485, 0.456, 0.406]).to(self.device)
        normalization_std = torch.tensor([0.229, 0.224, 0.225]).to(self.device)
        normalization = Normalization(normalization_mean, normalization_std).to(self.device)
        content_losses = []
        style_losses = []
        model = nn.Sequential(normalization)
        i = 0
        for layer in cnn.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = 'conv_{}'.format(i)
            elif isinstance(layer, nn.ReLU):
                name = 'relu_{}'.format(i)
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = 'pool_{}'.format(i)
            elif isinstance(layer, nn.BatchNorm2d):
                name = 'bn_{}'.format(i)
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))
            model.add_module(name, layer)
            if name in content_layers:
                target = model(content_img).detach()
                content_loss = ContentLoss(target)
                model.add_module("content_loss_{}".format(i), content_loss)
                content_losses.append(content_loss)
            if name in style_layers:
                target_feature = model(style_img).detach()
                style_loss = StyleLoss(target_feature)
                model.add_module("style_loss_{}".format(i), style_loss)
                style_losses.append(style_loss)
        for i in range(len(model) - 1, -1, -1):
            if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
                break
        model = model[:(i + 1)]
        return model, style_losses, content_losses    

    def get_input_optimizer(self, input_img):
            optimizer = optim.LBFGS([input_img.requires_grad_()]) 
            return optimizer
