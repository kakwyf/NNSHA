# -*- coding: utf-8 -*-
#----------------------------------------------------------------------

#このプログラムをPC3で実行してください。

#機能：マイクからの音圧レベルを取得して、PC1へ発信する

#（Agent数が3の場合のみに適用）
#----------------------------------------------------------------------



from pyaudio import PyAudio, paInt16 
import numpy as np
from datetime import datetime 
import wave
import socket
import time


print('これから27秒睡眠します')
print('fn+f3でコピーモードに設定')

time.sleep(27)

NUM_SAMPLES = 2000     
SAMPLING_RATE = 20000    
LEVEL = 1500            
COUNT_NUM = 20         
SAVE_LENGTH = 8         


pa = PyAudio() 
stream = pa.open(format=paInt16, channels=1, rate=SAMPLING_RATE, input=True, 
                frames_per_buffer=NUM_SAMPLES) 



address = ('192.168.1.33', 12345)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)



while True: 
  
    string_audio_data = stream.read(NUM_SAMPLES) 

    audio_data = np.fromstring(string_audio_data, dtype=np.short) 

    large_sample_count = np.sum( audio_data > LEVEL )
    
    data=np.max(audio_data)
    data=str(data)
    s.sendto(data.encode('utf8'), address)
    print ('remote 発信:',data)
