# Computer Networks Final Project

from concurrent.futures import ThreadPoolExecutor
import cv2
import imutils
import socket
import numpy as np
import time
import base64
import threading
import wave
import pyaudio
import pickle
import struct
import sys
import queue
import os
# queue of size 10
q = queue.Queue(maxsize=10)

filename = r'C:\Users\Dhruvi\Downloads\Y2Mate.is - Selena Gomez - Lose You To Love Me (Official Music Video)-zlJDTxahav0-720p-1644877914747.mp4'
command = "ffmpeg -i {} -ab 160k -ac 2 -ar 44100 -vn {}".format(
    filename, 'temp.wav')
os.system(command)

BUFF_SIZE = 65536  # setting the buffer size

# Create a datagram based server socket that uses IPv4 addressing scheme
# Protocol Family=AF_INET (internet family), semantics of communication=SOCK_DGRAM

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# The setsockopt() function provides an application program with the means to control socket behavior.
# Here SO_RCVBUF is given as option which sets receive buffer size to BUFF_SIZE
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

host_ip = '127.0.0.1'  # socket.gethostbyname(host_name)
print(host_ip)
port = 9688  # defining port number
# defining socket address which will be used to bind server_socket
socket_address = (host_ip, port)
# binding the server_socket
server_socket.bind(socket_address)
# print the address where server_socket is listening at
print('Listening at:', socket_address)

# Obtain the inherent frames per second (FPS) of MP4 file

# Create a video capture object, here we start reading video from the file frame by frame.
vid = cv2.VideoCapture(filename)  # this method returns a tuple
# we use the isOpened() method to confirm that the video file was opened successfully
# isOpened() method returns boolean value
if(vid.isOpened() == False):
    print("Error opening the video file")
else:
    # we use get() method to retrieve important metadata associated with the video stream.
    # CAP_PROP_FPS retrieves frame rate
    FPS = vid.get(cv2.CAP_PROP_FPS)  # fps capture into our video
global TS  # rendering sample time
TS = (0.5/FPS)
BREAK = False
print('FPS:', FPS, TS)

# CAP_PROP_FRAME_COUNT, counts the number of frames in the video file
totalCountOfFrames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
# total time taken by the frames, given total no. of frames and frames per second
totalTimeInSeconds = float(totalCountOfFrames) / float(FPS)
# Current position of the video file in milliseconds.
d = vid.get(cv2.CAP_PROP_POS_MSEC)
print(totalTimeInSeconds, d)

# Put this funcn into thread


def generate_video_stream():

    WIDTH = 400  # defining width of video frame/window
    # when video is not completed
    # else it will throw 0
    while(vid.isOpened()):
        try:
            # vid.read() method returns a tuple, first element is a boolean and the second element is frame
            _, frame = vid.read()
            # resize frame along the width
            frame = imutils.resize(frame, width=WIDTH)
            q.put(frame)  # enqueue/put frame in the queue defined as q
        except:
            os._exit(1)
    print('Player closed')
    BREAK = True
    vid.release()  # release the video capture object (named vid here)


def video_stream():
    global TS
    fps, st, frames_to_count, cnt = (0, 0, 1, 0)
    # create a named window. Here we named window as "TRANSMITTING VIDEO"
    cv2.namedWindow('TRANSMITTING VIDEO')
    cv2.moveWindow('TRANSMITTING VIDEO', 10, 30)  # Move this window to (10,30)
    while True:
        # recvfrom() method reads number of bytes send from a UDP socket
        # then this method returns a bytes object read from a UDP socket and the address of the client socket as a tuple.
        # note buffer size for UDP is defined at the start of this program
        msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
        # display client address from where server got a connection
        print('GOT connection from ', client_addr)
        WIDTH = 400

        while(True):
            # get() method removes and returns an item from the queue. If queue is empty, wait until an item is available.
            frame = q.get()
            # imencode() encodes image format into streaming data
            # here, extention of the image to be encoded is .jpeg
            # imencode() method returns boolean describing whether the operation was successful or not and the encoded image
            encoded, buffer = cv2.imencode(
                '.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])  # the JPEG image quality can be controlled with cv2.IMWRITE_JPEG_QUALITY parameter and its value (between 0 & 100).
            # Here we have explicitly mentioned parameter value as 80. (default value is 95)
            # encode buffer string into binary form
            message = base64.b64encode(buffer)
            # sendto() sends datagrams to a UDP socket. sendto() takes data to be sent(in bytes format) & tuple consisting of IP address and port as parameters
            # sendto() returns no. of bytes sent
            server_socket.sendto(message, client_addr)

            # cv2.putText() method is used to draw a text string on any image.
            # 1st parameter -> frame ->image on which text is to be drawn
            # 2nd parameter -> text string to be drawn
            # 3rd parameter -> co-ordinates of bottom-left corner of the text string in the image
            # 4th parameter -> denotes the font type (here, it is FONT_HERSHEY_SIMPLEX)
            # 5th parameter -> denotes font scale
            # 6th parameter -> denotes color of the text string
            # 7th parameter -> thickness of line in px

            frame = cv2.putText(frame, 'FPS: '+str(round(fps, 1)),
                                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # To keep the inherent frame rate of video while rendering, we stabilize the rendering sample time (TS) in the loop
            # by current fram erate (ie. fps) is higher or lower than the desired inherent frame rate(ie. FPS) and according increment or decrement TS
            if cnt == frames_to_count:
                try:
                    fps = (frames_to_count/(time.time()-st))
                    st = time.time()
                    cnt = 0
                    if fps > FPS:
                        TS += 0.001
                    elif fps < FPS:
                        TS -= 0.001
                    else:
                        pass
                except:
                    pass
            cnt += 1
# cv2.imshow() displays frame in the named window
            cv2.imshow('TRANSMITTING VIDEO', frame)
            # allow users to display a window for given milliseconds. (Note: if 0 is passed as an argument of waitkey() then it waits till any key is pressed)
            key = cv2.waitKey(int(1000*TS)) & 0xFF
            # ord returns the unicode equivalence of passed character.
            if key == ord('q'):
                os._exit(1)
                TS = False
                break


def audio_stream():
    s = socket.socket()
    s.bind((host_ip, (port-1)))

    s.listen(5)
    CHUNK = 1024
    wf = wave.open("temp.wav", 'rb')
    p = pyaudio.PyAudio()
    print('server listening at', (host_ip, (port-1)))
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    input=True,
                    frames_per_buffer=CHUNK)

    client_socket, addr = s.accept()

    while True:
        if client_socket:
            while True:
                data = wf.readframes(CHUNK)
                a = pickle.dumps(data)
                message = struct.pack("Q", len(a))+a
                client_socket.sendall(message)


with ThreadPoolExecutor(max_workers=3) as executor:
    executor.submit(audio_stream)  # to generate and send stream of audio data
    executor.submit(generate_video_stream)  # to generate stream of frames
    # to obtain and send video stream, with a synchronized fps
    executor.submit(video_stream)
