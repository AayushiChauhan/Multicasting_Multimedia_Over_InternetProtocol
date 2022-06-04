# Computer Networks Final Project

from concurrent.futures import ThreadPoolExecutor
import cv2
import imutils
import socket
import numpy as np
import time
import os
import base64 			# converts buffer into string
import threading
import wave
import pyaudio
import pickle
import struct
BUFF_SIZE = 65536  # setting the buffer size

BREAK = False

# create a datagram socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# The setsockopt() function provides an application program with the means to control socket behavior.
# try to lower the receiver's socket buffer size
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
host_ip = '127.0.0.1'		# socket.gethostbyname(host_name)
print(host_ip)
port = 9688         		# assigning port number on which we have to connect
message = b'Hello'			# send message 'Hello' from client

# Send to server using created UDP socket
client_socket.sendto(message, (host_ip, port))


def video_stream():
    # window name is 'RECEIVING VIDEO' in which the frame will be displayed
    cv2.namedWindow('RECEIVING VIDEO')
    cv2.moveWindow('RECEIVING VIDEO', 10, 360)
    fps, st, frames_to_count, cnt = (0, 0, 20, 0)
    while True:
        # receive reply from server
        packet, _ = client_socket.recvfrom(BUFF_SIZE)
        # returns the decoded packet
        data = base64.b64decode(packet, ' /')
        # using numpy to construct an array from the bytes
        # uint8 datatype contains all whole numbers from 0 to 255.
        npdata = np.fromstring(data, dtype=np.uint8)

        # decode the array
        frame = cv2.imdecode(npdata, 1)
        # to draw a text string on any image
        frame = cv2.putText(frame, 'FPS: '+str(fps), (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # cv2.imshow() methods is used here to display the frame in a window
        cv2.imshow("RECEIVING VIDEO", frame)

        # cv2.waitkey() function is used to bind the code with keyboard and any thing we type will be
        # by this function. It returns a 32-bit intger value. The key input is in ASCII which is 8-bit integer value.
        # So using bitwise AND, it can return the binary form of the input key
        key = cv2.waitKey(1) & 0xFF

        # comparing the value of key and if the pressed key is 'q' then cv.waitKey() will return q in binary form
        if key == ord('q'):
            client_socket.close()
            os._exit(1)
            break

        if cnt == frames_to_count:
            try:
                fps = round(frames_to_count/(time.time()-st))
                st = time.time()
                cnt = 0
            except:
                pass
        cnt += 1

    client_socket.close()
    # closing all the windows
    cv2.destroyAllWindows()

# go to pyaudio.get lib and fetch it and then send it


def audio_stream():

    # instantiating PyAudio which sets up the portaudio system
    p = pyaudio.PyAudio()
    CHUNK = 1024									# number of frames in the buffer
    # openinf the stream to record or play the audio
    stream = p.open(format=p.get_format_from_width(2),
                    channels=2,						# number of audio streams to use
                    rate=44100,						# number of samples collected per second, each frame will have 2 samples
                    output=True,
                    frames_per_buffer=CHUNK)

    # creating a client socket that will accept the connections
    # socket family -> AF_INET, Type -> SOCK_STREAM, Protocol -> TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socket_address = (host_ip, port-1)
    print('server listening at', socket_address)
    # connecting the client with the server
    client_socket.connect(socket_address)
    print("CLIENT CONNECTED TO", socket_address)
    data = b""
    payload_size = struct.calcsize("Q")

    # Running a loop to send and receive data from the server continuously
    while True:
        try:
            while len(data) < payload_size:
                packet = client_socket.recv(4*1024)  # 4K
                if not packet:
                    break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            # retrieve all data based on message size
            while len(data) < msg_size:
                data += client_socket.recv(4*1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            # extract frame
            frame = pickle.loads(frame_data)
            # playing audio using pyaudio.Stream.write()
            stream.write(frame)

        except:

            break

    client_socket.close()
    print('Audio closed', BREAK)
    os._exit(1)


with ThreadPoolExecutor(max_workers=2) as executor:
    executor.submit(audio_stream)  # to obtain stream of audio data
    executor.submit(video_stream)  # to obtain video stream
