from PIL import Image
import numpy as np
import face_recognition

img = Image.open("../dataset/Musfiqur/img1.jpg").convert("RGB")
arr = np.array(img, dtype=np.uint8)
print("shape:", arr.shape, "dtype:", arr.dtype)
locs = face_recognition.face_locations(arr)
print("faces found:", len(locs))