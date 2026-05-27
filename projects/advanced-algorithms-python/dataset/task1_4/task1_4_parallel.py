import time
import face_recognition
import os
import numpy as np
from multiprocessing import Pool, cpu_count
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
known_image_path = os.path.join(BASE_DIR, "known_man.jpg")
folder_path = os.path.join(BASE_DIR, "imageset")

with Image.open(known_image_path) as img:
    rgb_img = img.convert("RGB")
    known_image = np.asarray(rgb_img, dtype=np.uint8)

known_encodings = face_recognition.face_encodings(known_image)
if not known_encodings:
    print("No face found in the known image!")
    raise SystemExit(1)
known_encoding = known_encodings[0]

filenames = [file.name for file in os.scandir(folder_path) if file.is_file()]

def check_image(filename):
    try:
        image_path = os.path.join(folder_path, filename)
        unknown_image = face_recognition.load_image_file(image_path)
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        for encoding in unknown_encodings:
            match = face_recognition.compare_faces([known_encoding], encoding)[0]
            if match:
                return filename
    except Exception as e:
        print(f"Error processing {filename}: {e}")
    return None

def parallel_face_search():
    print("Searching for matching faces in parallel...")
    start = time.time()

    with Pool(processes=cpu_count()) as pool:
        results = pool.map(check_image, filenames)

    matches = [filename for filename in results if filename is not None]

    if matches:
        for match in matches:
            print(f"Match found in: {match}")
    else:
        print("No matches found.")

    print(f"\nTime taken: {time.time() - start:.2f} seconds")

if __name__ == "__main__":
    parallel_face_search()
