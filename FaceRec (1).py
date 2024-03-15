import os
import pickle
import re

import click
import cv2
import face_recognition
import numpy as np
import requests


class SimpleFaceRec:
    
    def __init__(self, verbose):
        self.__verbose = verbose
        self.__known_face_names = []
        self.__known_face_encodings = []
        self.__frame_resizing = 0.25 # Resize frame for a faster speed

    def __image_files_in_folder(self, folder):
        return [os.path.join(folder, f) for f in os.listdir(folder) if re.match(r'.*\.(jpg|jpeg|png)', f, flags=re.I)]

    def __load_lists(self, encodings, names):
        # Load Names List  
        if os.path.exists(names):
            if self.__verbose: print(f"> Loading Names From: {names}")
            with open(names, 'rb') as f:
                self.__known_face_names = pickle.load(f)
        
        # Load Encodings List     
        if os.path.exists(encodings):
            if self.__verbose: print(f"> Loading Encodings From: {encodings}")
            with open(encodings, 'rb') as f:
                self.__known_face_encodings = pickle.load(f)

    def __save_lists(self, encodings, names):
        # Save Names List  
        if len(self.__known_face_names) > 0:
            with open(names, 'wb') as file:
                pickle.dump(self.__known_face_names, file)
            if self.__verbose: print(f"> Names Saved To: {names}")
        elif os.path.exists(names):
            os.remove(names)
            if self.__verbose: print(f"> Names Removed From: {names}")
        
        # Save Encodings List   
        if len(self.__known_face_encodings) > 0:  
            with open(encodings, 'wb') as file:
                pickle.dump(self.__known_face_encodings, file)
            if self.__verbose: print(f"> Encodings Saved To: {encodings}")
        elif os.path.exists(encodings):
            os.remove(encodings)
            if self.__verbose: print(f"> Encodings Removed From: {names}")
                
    def load_faces_encodings(self, images_folder):
        self.__load_lists(encodings=os.path.join(images_folder, "encodings.p"), names=os.path.join(images_folder, "names.p"))
        
        # Load Images Paths
        images_paths = self.__image_files_in_folder(images_folder)
        
        # Removing Non-Existing Encoded Images
        indices = []
        if len(self.__known_face_names) > 0:
            if self.__verbose: print("> Removing Non-Existing Encoded Images", end=": ")
            indices = [i for i in range(len(self.__known_face_names)) if self.__known_face_names[i] not in [os.path.splitext(os.path.basename(name))[0] for name in images_paths]]
            for index in reversed(indices):
                del self.__known_face_names[index]
                del self.__known_face_encodings[index]
            if self.__verbose: print(f"{len(indices)} Image(s) Removed.")
        
        # Excluding Previously Encoded Images
        if len(self.__known_face_names) > 0:
            if self.__verbose: print("> Excluding Previously Encoded Images", end=": ")
            excluded = len(images_paths)
            images_paths = [path for path in images_paths if os.path.splitext(os.path.basename(path))[0] not in self.__known_face_names]
            excluded -= len(images_paths)
            if self.__verbose: print(f"{excluded} Image(s) Excluded.")
        
        # Encoding New Images
        encoded, failed = 0, 0
        if len(images_paths) > 0:
            if self.__verbose: print("> Encoding New Images")
            for image_path in images_paths:
                img = cv2.imread(image_path)
                image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # image = face_recognition.load_image_file(image_path)
                faces_in_image = len(face_recognition.face_locations(image))
                
                # Get The Image Name Without Extension
                basename = os.path.basename(image_path)
                (filename, ext) = os.path.splitext(basename)
                if self.__verbose:  print(f"    Encoding:\t{filename}", end="\t")
                
                if faces_in_image != 1:
                    # If There are No People (Or Too Many People) in a Training Image, Skip It.
                    if self.__verbose:  print(f"[FAILED] {'No Face Founded.' if faces_in_image == 0 else 'Found More Than One Face.'}")
                    failed += 1
                else:           
                    # Get & Store Image Encoding
                    img_encoding = face_recognition.face_encodings(image)[0]
                    self.__known_face_encodings.append(img_encoding)
                    self.__known_face_names.append(filename)
                    if self.__verbose:  print("[ DONE ]")
                    encoded += 1
            if self.__verbose: print(f"> {encoded} / {encoded + failed} New Image(s) Encoded")
        
        if encoded > 0 or len(indices) > 0:
            self.__save_lists(encodings=os.path.join(images_folder, "encodings.p"), names=os.path.join(images_folder, "names.p"))

    def recognize_face(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=self.__frame_resizing, fy=self.__frame_resizing)
        
        # Find All The Faces and Face Encodings in The Current Frame of Video
        # Convert the Image From BGR Color (which OpenCV uses) to RGB Color (which face_recognition uses)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # Check If The Face Matched From The Known Faces
            matches = face_recognition.compare_faces(self.__known_face_encodings, face_encoding)
            name = "unknown"

            # Find The Known Face With The Smallest Distance
            face_distances = face_recognition.face_distance(self.__known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.__known_face_names[best_match_index]
            face_names.append(name)

        # Convert to numpy array to adjust coordinates with frame resizing quickly
        face_locations = np.array(face_locations)
        face_locations = face_locations / self.__frame_resizing
        return face_locations.astype(int), face_names

@click.command()
@click.argument("known_faces_folder")
@click.option("--camera-url", "-u", help="The Camera Url.")
@click.option("--camera-index", "-i", default=0, help="The Camera Index. Default is 0.")
@click.option("--verbose", "-v", default=False, type=bool, help="Print Details While Running. Default is False.")
def main(known_faces_folder, verbose, camera_url, camera_index):  
    # Encode Faces From at `known_faces_folder`
    sfr = SimpleFaceRec(verbose)
    sfr.load_faces_encodings(known_faces_folder)

    # Load Camera
    cap = cv2.VideoCapture(camera_index if camera_url == None else camera_url)

    # New Super Loop
    while True:
        ret, frame = cap.read()

        # Detect Faces
        face_locations, face_names = sfr.recognize_face(frame)
        for face_loc, name in zip(face_locations, face_names):
            y1, x1, y2, x2 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]

            if name == "Unknown":
                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)
            else:
                data = { "photo": f"{name}.jpeg" }
                endpoint = "http://localhost:3001/api/v1/checkValidation"
                response = requests.post(endpoint, json=data)
                validation = response.json()['status']
                cv2.putText(frame, validation, (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0 if validation == 'invalid' else 200, 200 if validation == 'invalid' else 0), 4)

        cv2.imshow("Camera", frame)
        
        key = cv2.waitKey(1)
        if key == 27 or key == 113: # Esc Key or q key
            break 

    if verbose: print("> Module Terminated.")
    cap.release()
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    main()