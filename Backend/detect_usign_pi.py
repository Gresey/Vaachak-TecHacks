# import pickle
# import cv2
# import mediapipe as mp
# import numpy as np

# dic = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","YES","NO",]

# model_dict = pickle.load(open('./model.p', 'rb'))
# model = model_dict['model']

# cap = cv2.VideoCapture("http://192.168.29.193:5000/stream")

# mp_hands = mp.solutions.hands
# mp_drawing = mp.solutions.drawing_utils
# mp_drawing_styles = mp.solutions.drawing_styles

# hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

# labels_dict = {0: 'A', 1: 'B', 2: 'L'}
# while True:

#     data_aux = []
#     x_ = []
#     y_ = []

#     ret, frame = cap.read()

#     H, W, _ = frame.shape

#     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     results = hands.process(frame_rgb)
#     if results.multi_hand_landmarks:
#         for hand_landmarks in results.multi_hand_landmarks:
#             mp_drawing.draw_landmarks(
#                 frame,  # image to draw
#                 hand_landmarks,  # model output
#                 mp_hands.HAND_CONNECTIONS,  # hand connections
#                 mp_drawing_styles.get_default_hand_landmarks_style(),
#                 mp_drawing_styles.get_default_hand_connections_style())

#         for hand_landmarks in results.multi_hand_landmarks:
#             for i in range(len(hand_landmarks.landmark)):
#                 x = hand_landmarks.landmark[i].x
#                 y = hand_landmarks.landmark[i].y

#                 x_.append(x)
#                 y_.append(y)

#             for i in range(len(hand_landmarks.landmark)):
#                 x = hand_landmarks.landmark[i].x
#                 y = hand_landmarks.landmark[i].y
#                 data_aux.append(x - min(x_))
#                 data_aux.append(y - min(y_))

#         x1 = int(min(x_) * W) - 10
#         y1 = int(min(y_) * H) - 10

#         x2 = int(max(x_) * W) - 10
#         y2 = int(max(y_) * H) - 10

#         prediction =  model.predict([np.asarray(data_aux)])
#         # print(int(prediction))
#         predicted_character = dic[int(prediction[0])]
#         confidence = max(model.predict_proba([np.asarray(data_aux)])[0])

#         cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
#         text = f"{predicted_character}"
#         if(confidence>0.65):
#             cv2.putText(frame, text, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)

#     cv2.imshow('frame', frame)
#     key = cv2.waitKey(1)
#     if key == 27:  # Press 'Esc' to exit the loop
#         break

# cap.release()
# cv2.destroyAllWindows()



#V2  NOTE(V1 can be used for simple testing of ASL detection only!!)




from flask import Flask, request
import pickle
import cv2
import mediapipe as mp
import requests
import numpy as np
import threading
import multiprocessing 
import time 
import os
import keyboard
import subprocess
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from autocorrect import Speller
import os.path
import pyttsx3
from googletrans import Translator
from gtts import gTTS 
from io import BytesIO
import pyglet


# dic = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z","YES","NO",]
global dic
# dic=['A','B','C','D','E','F']


def read_words_from_file():
    file_path="./Extra\word.txt"
    global dic
    try:
        with open(file_path, "r") as file:
            words_list = [word.strip() for word in file.readlines()]
        # print(f"Words read from {file_path}: {words_list}")
        dic= words_list
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

read_words_from_file()

# print("Updated dic list: ",dic) # Just to check teh updated list

dual_hand = os.path.isfile('Model\model2.p')

model_dict = pickle.load(open('Model\model.p', 'rb'))
model = model_dict['model']
print(dual_hand)
if dual_hand:
    model_dict2 = pickle.load(open('Model\model2.p', 'rb'))
    model2 = model_dict2['model']

current_state=0
current_switch=False

unilang='en'

globalBreak="F"
globalSentence=[]

is_detect_on=False
button_validation=0
run_once=True
localSentence=""


def validate_pi_button():
    global button_validation
    global is_detect_on
    button_validation=button_validation+1
    if button_validation==2:
        is_detect_on= not is_detect_on
        button_validation=0

def SpeakDirectly(text):
    language = 'en'
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save("output.mp3")
    player = pyglet.media.Player()
    sound = pyglet.media.load("output.mp3", streaming=False)
    player.queue(sound)
    player.play()
    return 

def translate_text(text, source_lang='auto', target_lang='en'):
    translator = Translator()
    translation = translator.translate(text, src=source_lang, dest=target_lang)
    print(translation.src)
    return translation.text

def Speak():
    global unilang
    if globalSentence[-1:]!=[]:
        stringOut = "".join(globalSentence)
        language = 'en'
        if unilang!=language:
            stringOut=translate_text(stringOut,target_lang=unilang)
        tts = gTTS(text=stringOut, lang=language, slow=False)
        tts.save("output.mp3")
        player = pyglet.media.Player()
        sound = pyglet.media.load("output.mp3", streaming=False)
        player.queue(sound)
        player.play()
        return
    
def check_change_globalSentence():
    while True:
        global globalSentence
        globalSentenceString="".join(globalSentence)
        requests.get('http://192.168.161.103:5000/oled',params={'data':globalSentenceString})    
        time.sleep(1.5)

def send_get_request(url):
    try:
        response = requests.get(url)
        # Check if the response status code is in the 2xx range for a successful request
        response.raise_for_status()
        return True# or return any other data you want from the response
    except requests.exceptions.RequestException as e:
        print("Failed to Open the video stream")
        SpeakDirectly("Failed to open the video stream")
        return False
    
def FormSentence(output):
    if(output!=globalBreak):
        if(globalSentence[-1:]==[]):
            print("Detected element: ",output)
            if(len(output)>1):
                globalSentence.append(output+" ")
            else:
                globalSentence.append(output)
            # print("globalSentence ",globalSentence) # for testing purposes only
            return
            
        if(globalSentence[-1]!=output):
            # print("Last element ",globalSentence[-1]) # for testing purposes only
            print("Detected element: ",output)
            if(len(output)>1):
                globalSentence.append(" "+output+" ")
            else:
                globalSentence.append(output)
            # print("globalSentence ",globalSentence) # Yup this too!
        else:
            return
    else:
        Speak()
        globalSentence.clear()

def read_words_from_file():
    global dic
    file_path="./Extra\word.txt"
    try:
        with open(file_path, "r") as file:
            words_list = [word.strip() for word in file.readlines()]
        # print(f"Words read from {file_path}: {words_list}")
        dic=words_list
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

read_words_from_file()

def save_word_to_file(word): # To test writing in text file
    file_path="Extra\word.txt"
    try:
        with open(file_path, "a") as file:
            file.write(word + "\n")
        print(f"The word '{word}' has been saved to {file_path}.")
    except Exception as e:
        print(f"Error occurred: {e}")

def delete_word(text):
    text_index = dic.index(text)
    if os.path.exists(f'./data/{text}'):
        for file in os.listdir(f'data_test/{text_index}'):
            os.remove(f'data_test/{text_index}/{str(file)}')
            print("Removed file ",file,'\n')
        os.rmdir(f'data_test/{text_index}')
        for file in os.listdir(f'data/{text_index}'):
            os.remove(f'data/{text_index}/{str(file)}')
            print("Removed file ",file,'\n')
        os.rmdir(f'data/{text_index}')
        print("Dir empty")
    return 

# use this only when you want to update the word.txt file automatically with hardcoded list named dic
def save_list_to_file(list):
    file_path="Extra\word.txt"
    for word in list:
        with open(file_path, "a") as file:
            file.write(word + "\n")
        print(f"The word '{word}' has been saved to {file_path}.")

def detect_using_pi():
    while True:
        global is_detect_on
        global run_once
        if run_once and is_detect_on:
            cap = cv2.VideoCapture('http://192.168.161.103:5000/stream')
            mp_hands = mp.solutions.hands
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing_styles = mp.solutions.drawing_styles
            hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)
            run_once=False
            
        while is_detect_on:
            
            data_aux = []
            x_ = []
            y_ = []
            ret, frame = cap.read()
            if not ret:
                cap.release()
                cv2.destroyAllWindows()
                return
            try:
                H, W, _ = frame.shape  
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
                results = hands.process(frame_rgb)
            except:
                print("Error while manipulating frames")
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,  # image to draw
                        hand_landmarks,  # model output
                        mp_hands.HAND_CONNECTIONS,  # hand connections
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())
                for hand_landmarks in results.multi_hand_landmarks:
                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y   
                        x_.append(x)
                        y_.append(y)   
                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        data_aux.append(x - min(x_))
                        data_aux.append(y - min(y_))   
                x1 = int(min(x_) * W) - 10
                y1 = int(min(y_) * H) - 10 
                x2 = int(max(x_) * W) - 10
                y2 = int(max(y_) * H) - 10
                predicted_character=""
                if len(data_aux)==42:
                    try:
                        prediction =  model.predict([np.asarray(data_aux)])
                        predicted_character = dic[int(prediction[0])]
                        confidence = max(model.predict_proba([np.asarray(data_aux)])[0])
                        # print(confidence," --> ",predicted_character)
                        # print(confidence)
                    except:
                        print("Hands out of frame!")

                else:
                    if dual_hand:
                        try:
                            prediction =  model2.predict([np.asarray(data_aux)])
                            predicted_character = dic[int(prediction[0])]
                            confidence = max(model2.predict_proba([np.asarray(data_aux)])[0])
                            # print(confidence)
                        except:
                            print("Hands out of frame!")

                # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                text = f"{predicted_character} {confidence}"
                if(confidence>0.50):
                    cv2.putText(frame, text, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX,  1,   (0, 0, 0), 2,  cv2.LINE_AA)
                    FormSentence(predicted_character)  

            cv2.imshow('General Cam', frame)
            key = cv2.waitKey(1)

            if key == 27:  # Press 'Esc' to exit the loop
                cap.release()
                cv2.destroyAllWindows()
                print("Resources Released, ready for next process")
                break
        if not run_once:
            cap.release()
            cv2.destroyAllWindows()
            print("Resources Released, ready for next process")
            run_once=True
 
def captureStream(folder_name,real_name,pictures):
    try:
        DATA_DIR="./data"
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_hands = mp.solutions.hands
        if not os.path.exists(os.path.join(DATA_DIR, str(folder_name))):
            os.makedirs(os.path.join(DATA_DIR, str(folder_name)))
        # if not send_get_request(0):
        #     return 
        cap = cv2.VideoCapture(0)
        # cap = cv2.VideoCapture(0) # For testing with webcam
        SpeakDirectly(f"Capturing for {real_name} will start in 5 seconds.")
        time.sleep(5)
        counter = 0
        while counter < pictures:
            with mp_hands.Hands(
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as hands:
              while cap.isOpened():
                success, image = cap.read()
                frame=image
                if not success:
                  print("Ignoring empty camera frame.")
                  # If loading a video, use 'break' instead of 'continue'.
                  continue
              
                # To improve performance, optionally mark the image as not writeable to
                # pass by reference.
                image.flags.writeable = False
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = hands.process(image)
                # Draw the hand annotations on the image.
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                if results.multi_hand_landmarks:
                  for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style())
                # Flip the image horizontally for a selfie-view display.
                final_frame=cv2.flip(image, 1)
                cv2.putText(final_frame, f'{counter}', (100, 50), cv2.FONT_HERSHEY_SIMPLEX,1.3,     (250, 250, 0), 3,cv2.LINE_AA)
                cv2.imshow('MediaPipe Hands', final_frame)
                cv2.waitKey(25)
                cv2.imwrite(os.path.join(DATA_DIR, str(folder_name), '{}.jpg'.format(counter)),     frame)
                print(counter)
                counter += 1
                if counter >= pictures : break
        SpeakDirectly("Capturing has completed")

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        SpeakDirectly("An error has occurred, Please check the logs")
        print(f"An error occurred: {e}")
        
def run_dataset_creation():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

    DATA_DIR = './data'

    data = []
    labels = []
    data2 = []
    labels2 = []
    for dir_ in os.listdir(DATA_DIR):
        for img_path in os.listdir(os.path.join(DATA_DIR, dir_)):
            data_aux = []

            x_ = []
            y_ = []

            img = cv2.imread(os.path.join(DATA_DIR, dir_, img_path))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            results = hands.process(img_rgb)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y

                        x_.append(x)
                        y_.append(y)

                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        data_aux.append(x - min(x_))
                        data_aux.append(y - min(y_))

                if len(data_aux)==42:
                    data.append(data_aux)
                    labels.append(dir_)
                else:
                    data2.append(data_aux)
                    labels2.append(dir_)



    f = open('./Model\data.pickle', 'wb')
    pickle.dump({'data': data, 'labels': labels}, f)
    SpeakDirectly("Single hand dataset ready!")
    f.close()

    f = open('./Model\data2.pickle', 'wb')
    pickle.dump({'data': data2, 'labels': labels2}, f)
    SpeakDirectly("Dual hand dataset ready!")
    f.close()
    
    return
    
def train_model():
    global dual_hand
    data_dict = pickle.load(open('./Model\data.pickle', 'rb'))
    data = np.asarray(data_dict['data'])
    labels = np.asarray(data_dict['labels'])

    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.2,   shuffle=True, stratify=labels)

    model = RandomForestClassifier()

    model.fit(x_train, y_train)

    y_predict = model.predict(x_test)

    score = accuracy_score(y_predict, y_test)

    print('{}% of samples were classified correctly !'.format(score * 100))
    SpeakDirectly('{}% of single hand samples were classified correctly !'.format(score * 100))

    f = open('model.p', 'wb')
    pickle.dump({'./Model/model': model}, f)
    f.close()
    
    if dual_hand:
        data_dict2 = pickle.load(open('./Model\data2.pickle', 'rb'))
        data2 = np.asarray(data_dict2['data'])
        labels2 = np.asarray(data_dict2['labels'])
        x_train, x_test, y_train, y_test = train_test_split(data2, labels2, test_size=0.25,     shuffle=True, stratify=labels2)

        model = RandomForestClassifier()

        model.fit(x_train, y_train)

        y_predict = model.predict(x_test)

        score = accuracy_score(y_predict, y_test)

        print('{}% of samples were classified correctly Part 2 !'.format(score * 100))
        SpeakDirectly('{}% of single dual samples were classified correctly !'.format(score * 100))
        
        f = open('./Model\model2.p', 'wb')
        pickle.dump({'model': model}, f)
        f.close()
        
    SpeakDirectly("Training Process completed successfully")
    return


# run_dataset_creation()
# detect_using_pi()
app = Flask(__name__)

detect_pi = threading.Thread(target=detect_using_pi)
detect_pi.daemon = True  # Daemonize the thread so it will be terminated when the main program exits
detect_pi.start()

check_sentence = threading.Thread(target=check_change_globalSentence)
check_sentence.daemon = True  
check_sentence.start()
 # Agar Code quality achhi ho toh itni achhi ho ki 2-2 3-3 underscore lagana pade, warna buri hi ho 


@app.route('/new-sign', methods=['POST']) # This is to receive the post data from the application
def new_sign():
    data=request.form
    print("request received ",data)
    folder = data.get('text')
    save_word_to_file(folder)
    folder_name_to_pass=str(len(dic))
    read_words_from_file()
    captureStream(folder_name_to_pass,folder,500)
    return "Success"

@app.route('/start-training', methods=['POST']) # This is to receive the post data from the application
def start_training():
    print("training request received")
    run_dataset_creation()
    train_model()
    return "Success"
       
@app.route('/delete-sign', methods=['POST']) # This is to receive the post data from the application
def delete_sign():
    data=request.form
    data=data.get('text')
    print("delete request received ",data)
    delete_word(data)
    return "Success"
    
@app.route('/switch', methods=['GET']) # Turn on and off the pi
def switch():
    global is_detect_on
    print(is_detect_on)
    validate_pi_button()
    return "Success"

@app.route('/select-language',methods=['POST']) # Set the language, kyuki bharat mei bhasha har kadam pe badalti hai
def set_language():
    global unilang
    lang=request.form
    lang=lang.get('text')
    unilang=lang
    
@app.route('/repi', methods=['GET']) # Development Feature turn off when in production
def capture():
    # print("Re-pi called!")
    global current_state
    global current_switch
    current_state+=1
    if current_state==2:
        current_switch=not current_switch 
        current_state=0
        print("Current Switch Final",current_switch)
    print(current_switch)
    return "Success"
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
    