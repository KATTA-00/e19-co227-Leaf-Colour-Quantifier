"""leaf_colour_tourch.ipynb
Original file is located at
    https://colab.research.google.com/drive/1sJ8BhcUIcLDiym7bXg39-IulT69eDvXN
"""
import numpy as np
import os
from PIL import Image
import torch
import torchvision
from torchvision import transforms as T
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor


class CustDat(torch.utils.data.Dataset):
    def __init__(self , images , masks):
        self.imgs = images
        self.masks = masks

    def __getitem__(self , idx):
        img = Image.open("image_processing\\mask_r_cnn\\images\\" + self.imgs[idx]).convert("RGB")
        mask = Image.open("image_processing\\mask_r_cnn\\masks\\" + self.masks[idx])
        mask = np.array(mask)
        obj_ids = np.unique(mask)
        obj_ids = obj_ids[1:]
        num_objs = len(obj_ids)
        masks = np.zeros((num_objs , mask.shape[0] , mask.shape[1]))
        for i in range(num_objs):
            masks[i][mask == i+1] = True

        boxes = []
        for i in range(num_objs):
            pos = np.where(masks[i])
            xmin = np.min(pos[1])
            xmax = np.max(pos[1])
            ymin = np.min(pos[0])
            ymax = np.max(pos[0])
            boxes.append([xmin , ymin , xmax , ymax])

        boxes = torch.as_tensor(boxes , dtype = torch.float32)
        labels = torch.ones((num_objs,) , dtype = torch.int64)
        masks = torch.as_tensor(masks , dtype = torch.uint8)

        target = {}
        target["boxes"] = boxes
        target["labels"] = labels
        target["masks"] = masks

        return T.ToTensor()(img) , target

    def __len__(self):
        return len(self.imgs)

def main():
    model = torchvision.models.detection.maskrcnn_resnet50_fpn()

    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features , 2)
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256

    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask , hidden_layer , 2)

    transform = T.ToTensor()

    def custom_collate(data):
        return data

    images = sorted(os.listdir("image_processing\\mask_r_cnn\\images"))
    masks = sorted(os.listdir("image_processing\\mask_r_cnn\\masks"))

    num = int(0.7777 * len(images))
    num = num if num % 2 == 0 else num + 1
    train_imgs_inds = np.random.choice(range(len(images)) , num , replace = False)
    val_imgs_inds = np.setdiff1d(range(len(images)) , train_imgs_inds)

    train_imgs = np.array(images)[train_imgs_inds]
    val_imgs = np.array(images)[val_imgs_inds]
    train_masks = np.array(masks)[train_imgs_inds]
    val_masks = np.array(masks)[val_imgs_inds]

    train_dl = torch.utils.data.DataLoader(CustDat(train_imgs , train_masks) ,
                                    batch_size = 2 ,
                                    shuffle = True ,
                                    collate_fn = custom_collate ,
                                    num_workers = 1 ,
                                    pin_memory = True if torch.cuda.is_available() else False)

    val_dl = torch.utils.data.DataLoader(CustDat(val_imgs , val_masks) ,
                                    batch_size = 2 ,
                                    shuffle = True ,
                                    collate_fn = custom_collate ,
                                    num_workers = 1 ,
                                    pin_memory = True if torch.cuda.is_available() else False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device

    model.to(device)

    params = [p for p in model.parameters() if p.requires_grad]

    optimizer = torch.optim.SGD(params, lr=0.005, momentum=0.9, weight_decay=0.0005)

    all_train_losses = []
    all_val_losses = []
    flag = False

    for epoch in range(50):
        train_epoch_loss = 0
        val_epoch_loss = 0
        model.train()

        for i , dt in enumerate(train_dl):
            imgs = [dt[0][0].to(device) , dt[1][0].to(device)]
            targ = [dt[0][1] , dt[1][1]]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targ]
            loss = model(imgs , targets)
            if not flag:
                print(loss)
                flag = True
            losses = sum([l for l in loss.values()])
            train_epoch_loss += losses.cpu().detach().numpy()
            optimizer.zero_grad()
            losses.backward()
            optimizer.step()

        all_train_losses.append(train_epoch_loss)

        with torch.no_grad():
            for j , dt in enumerate(val_dl):
                imgs = [dt[0][0].to(device) , dt[1][0].to(device)]
                targ = [dt[0][1] , dt[1][1]]
                targets = [{k: v.to(device) for k, v in t.items()} for t in targ]
                loss = model(imgs , targets)
                losses = sum([l for l in loss.values()])
                val_epoch_loss += losses.cpu().detach().numpy()
            all_val_losses.append(val_epoch_loss)

        print(epoch , "  " , train_epoch_loss , "  " , val_epoch_loss)

    torch.save(model, "image_processing\\mask_r_cnn\\models\\model_4.pth")

if __name__ == "__main__":
    main()