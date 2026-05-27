import os
import time

import face_recognition


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def serial_face_search():
    start = time.time()
    known_image = face_recognition.load_image_file(os.path.join(BASE_DIR, "known_man.jpg"))
    known_encoding = face_recognition.face_encodings(known_image)[0]

    folder_path = os.path.join(BASE_DIR, "imageset")
    filenames = [file.name for file in os.scandir(folder_path) if file.is_file()]

    for filename in filenames:
        unknown_image = face_recognition.load_image_file(os.path.join(folder_path, filename))
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        for unknown_encoding in unknown_encodings:
            matches = face_recognition.compare_faces([known_encoding], unknown_encoding)
            if matches[0]:
                print(f"Match found in: {filename}")
                break

    print(f"Time taken: {time.time() - start:.2f} seconds")


if __name__ == "__main__":
    serial_face_search()
