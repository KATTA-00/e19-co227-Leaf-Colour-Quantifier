"""leaf_colour_tourch_test.ipynb
Original file is located at
    https://colab.research.google.com/drive/1ezUxo83329BlcToXJYLemygPXXgRZyzW
"""
import torch
from torchvision import transforms as T
from PIL import Image
import cv2

def main():
    device = torch.device('cpu')
    model = torch.load("image_processing\\mask_r_cnn\\models\\model_01.pth", map_location=device)
    model.eval()

    image = cv2.imread("image_processing\\mask_r_cnn\\test\\2.jpg")
    transform = T.ToTensor()
    ig = transform(image)

    with torch.no_grad():
        pred = model([ig.to(device)])

    masks = pred[0]["masks"]
    mask = masks[0 , 0]
    mask = masks[0 , 0] > 0.5
    m = mask.cpu().detach().numpy().astype("uint8") * 255
    cv2.imshow("image_mask",m)
    cv2 .waitKey(0)

    fin_img = cv2.bitwise_and(image , image , mask = m)
    cv2.imshow("image", cv2.resize(fin_img, (800,600), interpolation = cv2.INTER_AREA))
    cv2 .waitKey(0)

if __name__ == "__main__":
    main()
