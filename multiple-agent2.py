#----------------------------------------------------------------------

#このプログラムをPC1で実行してください。
#機能：
#1.ローカル(PC1)の音圧レベルを取得、ローカルのMMDagent.exeのログを取得
#2.リモート(PC2)から音圧レベルを受信する。
#3.音圧が閾値を超えたかどうかを判断して、人が話してるかどうかを判断する
#4.誰も話していないと判断できたら、2秒のタイマーがスタート
#5.2秒のタイマーが終わると、ローカルのMMDagent.exeとリモートのMMDagent.exeへ音声合成コマンドを発信


#このプログラムを実行する前に、必ずPC1でMMDagent.exeを開く
#（Agent数が2の場合のみに適用）
#----------------------------------------------------------------------import string
import time
import re
import random
import socket
import global_name
from pyaudio import PyAudio, paInt16
import numpy as np
from datetime import datetime 
import wave
import time


class eliza:
  def __init__(self):
    self.keys = list(map(lambda x:re.compile(x[0], re.IGNORECASE),gPats))
    self.values = list(map(lambda x:x[1],gPats))

  #----------------------------------------------------------------------
  # translate: take a string, replace any words found in dict.keys()
  #  with the corresponding dict.values()
  #----------------------------------------------------------------------
  def translate(self,str,dict):
    words = str.lower().split()
    keys = dict.keys();
    for i in range(0,len(words)):
      if words[i] in keys:
        words[i] = dict[words[i]]
    return ' '.join(words)

  #----------------------------------------------------------------------
  #  respond: take a string, a set of regexps, and a corresponding
  #    set of response lists; find a match, and return a randomly
  #    chosen response from the corresponding list.
  #----------------------------------------------------------------------
  def respond(self,str):
    # find a match among keys
    for i in range(0, len(self.keys)):
      match = self.keys[i].match(str)
      if match:
        # found a match ... stuff with corresponding value
        # chosen randomly from among the available options
        resp = random.choice(self.values[i])
        # we've got a response... stuff in reflected text where indicated
        pos = resp.find('%')
        while pos > -1:
          num = int(resp[pos+1:pos+2])
          resp = resp[:pos] + \
            self.translate(match.group(num),gReflections) + \
            resp[pos+2:]
          pos = resp.find('%')
        # fix munged punctuation at the end
        if resp[-2:] == '?.': resp = resp[:-2] + '.'
        if resp[-2:] == '??': resp = resp[:-2] + '?'

        return resp

#----------------------------------------------------------------------
# gReflections, a translation table used to convert things you say
#    into things the computer says back, e.g. "I am" --> "you are"
#----------------------------------------------------------------------
gReflections = {
  "am"   : "are",
  "was"  : "were",
  "わたし"    : "あなた",
  "i'd"  : "you would",
  "i've"  : "you have",
  "i'll"  : "you will",
  "my"  : "your",
  "are"  : "am",
  "you've": "I have",
  "you'll": "I will",
  "your"  : "my",
  "yours"  : "mine",
  "you"  : "me",
  "me"  : "you"
}

#----------------------------------------------------------------------
# gPats, the main response table.  Each element of the list is a
#  two-element list; the first is a regexp, and the second is a
#  list of possible responses, with group-macros labelled as
#  %1, %2, etc.
#----------------------------------------------------------------------
gPats = [
   [r'(.*)',
  [ global_name.NNS+"、どう思いますか?",
    global_name.NNS+"、どうでしょうか?",
    global_name.NNS+"、そう思わないの?",
    global_name.NNS+"もそう思いますよね。"]],
 ]



#----------------------------------------------------------------------
#  command_interface
#----------------------------------------------------------------------
def command_interface():

  NUM_SAMPLES = 2000      # pyAudio内部缓存的块的大小
  SAMPLING_RATE = 20000    # 采样率
  LEVEL = 1500            # 声音保存的阈值，小于1500不出数据
  #COUNT_NUM = 20          # NUM_SAMPLES个取样之内出现COUNT_NUM个大于LEVEL的取样则记录声音
  #SAVE_LENGTH = 8         # 声音记录的最小长度：SAVE_LENGTH * NUM_SAMPLES 个取样
  # 开启声音输入
  pa = PyAudio()

  stream = pa.open(format=paInt16, channels=1, rate=SAMPLING_RATE, input=True, 
                frames_per_buffer=NUM_SAMPLES) 


  address0 = ('localhost', 39390)
  address1 = (global_name.remoteIP, 39390)

  mmdSocket0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  mmdSocket0.connect(address0)
  mmdSocket0.setblocking(0)


  mmdSocket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  mmdSocket1.connect(address1)
  mmdSocket1.setblocking(0)

  remoteAddress = ('', 12345)
  remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
  remoteSocket.bind(remoteAddress)
  
  print ("-----------connect success-------------")

  start=input("push s and then sleep(20):")
  #time.sleep(10)
  #mmdSocket0.send("SYNTH_START|mei|mei_normal|準備お願い".encode('sjis'))
  time.sleep(18)
  #mmdSocket0.send("SYNTH_START|mei|mei_normal|一号スタンバイ、3、2、1、スタート".encode('sjis'))
  #mmdSocket1.send("SYNTH_START|mei|mei_normal|二号スタンバイ、3、2、1、スタート".encode('sjis'))

  synthCMD="SYNTH_START|mei|mei_normal|"
  #motionCMD="MOTION_ADD|mei|idle|Motion\mei_idle\mei_idle_yawn.vmd|PART|ONCE"
  idleCMD="MOTION_ADD|mei|base|Motion\mei_wait\mei_wait.vmd|FULL|ONCE|ON|OFF"


  therapist = eliza();
  recv = 'nothing'


  silenceStartTime=-1 #初识状态为-1
 
  NSspeaking=True
  NNSspeaking=True
  AI0speaking=False
  AI1speaking=False
  
  
  while True:
    #recv from MMDagent to 判断音声合成状态
    log0=''
    log1=''
    data0=0
    data1=0

  #recv from 另一台PC to 获取麦克风状态
    data1, remoteAddress = remoteSocket.recvfrom(512)
    data1=data1.decode('utf8')
    data1=int(data1)
    print('remote:',data1)
    
    try:
      log0 = mmdSocket0.recv(512)
      #print('agent0 log0:',log0)
      log0=log0.decode('sjis')

    except:
      #print(' ')
      a=1
    else:
      if 'SYNTH_EVENT_STOP' in log0:
        AI0speaking=False
        #mmdSocket0.send((idleCMD+'\n').encode('sjis'))

    try:
      log1 = mmdSocket1.recv(512)
      #print('agent1 log1:',log1)
      log1=log1.decode('sjis')

    except:
      #print(' ')
      a=1
    else:
      if 'SYNTH_EVENT_STOP' in log1:
        AI1speaking=False



  

    # 读入NUM_SAMPLES个取样
    string_audio_data = stream.read(NUM_SAMPLES) 
    # 将读入的数据转换为数组
    audio_data = np.fromstring(string_audio_data, dtype=np.short) 
    # 计算大于LEVEL的取样的个数
    large_sample_count = np.sum( audio_data > LEVEL )
    
    data0=np.max(audio_data)
    print ('local:',data0)


#判断说话状态
    if data0>1500:#阈值
      #print('local说话')
      NSspeaking=True
    else:
      #print('local沉默')
      NSspeaking=False

    if data1>1500:#阈值
      #print('remote说话')
      NNSspeaking=True
    else:
      #print('remote沉默')
      NNSspeaking=False




    if NSspeaking==True or NNSspeaking==True or AI0speaking==True or AI1speaking==True:
      silenceStartTime=-1
      continue
    
    else:
      if silenceStartTime==-1: #检测到沉默且此时未在计时（即沉默的起始点）
        silenceStartTime=time.time()
        #print('沉默区间开始，silenceStartTime:',silenceStartTime)
      #沉默，且Timer已经on
      elif silenceStartTime!=-1 and time.time()-silenceStartTime>=2: #Timer启动中
        #print('agent介入')
        #print("介入时间:",time.time())
        while recv[-1] in '!.':
          recv = recv[:-1]
        resp=therapist.respond(recv)

        #print("agent说话:",resp)
        #发送动作和语音

        select = random.randint(0,1)
        if select==0:
          mmdSocket0.send((synthCMD+resp+'\n').encode('sjis'))
          #mmdSocket0.send((motionCMD+'\n').encode('sjis'))
          AI0speaking=True
        elif select==1:
          mmdSocket1.send((synthCMD+resp+'\n').encode('sjis'))
          #mmdSocket1.send((motionCMD+'\n').encode('sjis'))
          AI1speaking=True

        silenceStartTime=-1

  mmdSocket0.close()
  mmdSocket1.close()
  remoteSocket.close()  


if __name__ == "__main__":
  command_interface()

