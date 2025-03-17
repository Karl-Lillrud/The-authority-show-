import cv2
import mediapipe as mp
import torch
import torchvision.transforms as T
from torchvision.models.detection import maskrcnn_resnet50_fpn

# Load MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

# Load Mask R-CNN (Pretrained)
model = maskrcnn_resnet50_fpn(pretrained=True)
model.eval()
transform = T.Compose([T.ToTensor()])

def detect_headphones(frame):
    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
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
