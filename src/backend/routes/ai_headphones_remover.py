import cv2
import torch
import torchvision.transforms as T
from torchvision.models.detection import maskrcnn_resnet50_fpn
import noisereduce as nr
import numpy as np

# Load Mask R-CNN (Pretrained)
model = maskrcnn_resnet50_fpn(pretrained=True)
model.eval()
transform = T.Compose([T.ToTensor()])

def reduce_noise(image):
    """Apply noise reduction to the image."""
    # Convert image to grayscale for noise reduction
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    reduced_noise = nr.reduce_noise(y=gray_image, sr=22050)  # Example sampling rate
    return cv2.merge([reduced_noise, reduced_noise, reduced_noise])

def detect_headphones(frame):
    # Apply noise reduction to the frame
    frame = reduce_noise(frame)
    
    # Convert to Tensor for Mask R-CNN
    tensor_frame = transform(frame).unsqueeze(0)
    with torch.no_grad():
        predictions = model(tensor_frame)
    
    # Extract Headphone Mask
    headphone_mask = None
    for i, label in enumerate(predictions[0]['labels']):
        if label == 1:  # Headphones (Assumption: Dataset labeling matches)
            headphone_mask = predictions[0]['masks'][i, 0].mul(255).byte().cpu().numpy()
            break
    
    return headphone_mask

# Video Capture
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Detect Headphones
    mask = detect_headphones(frame)
    if mask is not None:
        frame[mask > 128] = [0, 0, 255]  # Highlight headphones in red
    
    cv2.imshow("Headphone Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
