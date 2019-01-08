#----------------------------------------------------------------------

#このプログラムをPC1で実行してください。
#機能：
#1.ローカル(PC1)の音圧レベルを取得、ローカルのMMDagent.exeのログを取得
#2.リモート(PC2)から音圧レベルを受信する。
#3.音圧が閾値を超えたかどうかを判断して、人が話してるかどうかを判断する
#4.誰も話していないと判断できたら、2秒のタイマーがスタート
#5.2秒のタイマーが終わると、ローカルのMMDagent.exeへ音声合成コマンドを発信


#このプログラムを実行する前に、必ずPC1でMMDagent.exeを開く

#（Agent数が1の場合のみに適用）
#----------------------------------------------------------------------

import string
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

  NUM_SAMPLES = 2000      # pyAudio　バッファーのサイズ
  SAMPLING_RATE = 20000    # サンプリング率
  LEVEL = 1500            # 音圧のレベルが1500を超えない限り、保存・認識しない
  #COUNT_NUM = 20          
  #SAVE_LENGTH = 8         

  pa = PyAudio()

  stream = pa.open(format=paInt16, channels=1, rate=SAMPLING_RATE, input=True, 
                frames_per_buffer=NUM_SAMPLES) 


  address0 = ('localhost', 39390)#Local（PC1）のIPアドレスとポート番号
  #mmdAgentと通信するためのソケットを作成し、address0を代入
  mmdSocket0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  mmdSocket0.connect(address0)
  mmdSocket0.setblocking(0)
  

  remoteAddress = ('', 12345)#Remote（PC1）のIPアドレス(発信がないためいらない)とポート番号
  
  #PC2と通信するためのソケットを作成し、remoteAddressを代入
  
  remoteSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
  remoteSocket.bind(remoteAddress)
  
  print ("-----------connect success-------------")


  #実験の時、事前に準備完了のシステムを[sキー+enterキー]を押すだけで起動できる
  #この遅延はagentの機能に関係がない。
  start=input("push s:")
  time.sleep(5)



  synthCMD="SYNTH_START|mei|mei_normal|"#音声合成コマンドの冒頭部分、後ろに発話内容の文字列を追加すればok
  motionCMD="MOTION_ADD|mei|idle|Motion\mei_idle\mei_idle_yawn.vmd|PART|ONCE"#yawnモーションのコマンド
  idleCMD="MOTION_ADD|mei|base|Motion\mei_wait\mei_wait.vmd|FULL|ONCE|ON|OFF"#idleモーションのコマンド


  therapist = eliza();
  recv = 'nothing'


  silenceStartTime=-1 #初期値
 
  NSspeaking=True
  NNSspeaking=True
  AIspeaking=False
  
  
  while True:
   
    log='' #MMDagentからログを取得
    
    data0=0 # Localの音圧　(PC1)
    data1=0 # Remoteの音圧　（PC2）

  #PC2から話者の状態を取得し、data_PC2に保存
    
    try:
      data_PC2, remoteAddress = remoteSocket.recvfrom(512)
      data_PC2=data1.decode('utf8')
      data_PC2=int(data_PC2)
      print('PC2:',data_PC2)
    except:
      #print(' ')
      a=1
    else:
      if data_PC2=1:
        NNSspeaking=True
      elif data_PC2=0:
        NNSspeaking=False

        
    try:
      log = mmdSocket0.recv(512)
      #print('agent log:',log)
      log=log.decode('sjis')

    except:
      #print(' ')
      a=1
    else:
      if 'SYNTH_EVENT_STOP' in log:
        AIspeaking=False
        #mmdSocket0.send((idleCMD+'\n').encode('sjis'))


  

    string_audio_data = stream.read(NUM_SAMPLES) 
    audio_data = np.fromstring(string_audio_data, dtype=np.short) 
    large_sample_count = np.sum( audio_data > LEVEL )

    
    data0=np.max(audio_data) #Localの音圧の値を取得し、data0に保存
    print ('local:',data0)

'''
#音圧が1500以上か以下か、話してるかどうかを判断
    
    if data0>1500:
      #print('local話している')
      NSspeaking=True
    else:
      #print('local話していない')
      NSspeaking=False

    if data1>1500:
      #print('remote話している')
      NNSspeaking=True
    else:
      #print('remote話していない')
      NNSspeaking=False
'''



    if NSspeaking==True or NNSspeaking==True or AIspeaking==True:
      silenceStartTime=-1
      continue
    
    else:
      if silenceStartTime==-1: #誰も話していない　& タイマー実行していない
        silenceStartTime=time.time()
        #print('タイマースタート，silenceStartTime:',silenceStartTime)
        
      elif silenceStartTime!=-1 and time.time()-silenceStartTime>=1:#誰も話していない　& タイマー実行中
        #print('agent介入')
        #print("介入時間:",time.time())
        while recv[-1] in '!.':
          recv = recv[:-1]
        resp=therapist.respond(recv)

        #print("agent発話:",resp)
        #MMDagentへ音声合成コマンド・モーションコマンドを送る
        mmdSocket0.send((synthCMD+resp+'\n').encode('sjis'))#
        #mmdSocket0.send((motionCMD+'\n').encode('sjis'))
        
        AIspeaking=True
        silenceStartTime=-1

  mmdSocket0.close()
  remoteSocket.close()  


if __name__ == "__main__":
  command_interface()

