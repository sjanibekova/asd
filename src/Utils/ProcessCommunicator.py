import json
import zlib
import sys
from . import JSONNormalize


############################################
####Межпроцессное взаимодействие
############################################
#ProcessParentReadWaitString
def ProcessParentReadWaitString():
    #Выполнить чтение строки
    #ctypes.windll.user32.MessageBoxW(0, "Hello", "Your title", 1)
    lResult = sys.stdin.buffer.readline()
    #Вернуть потенциальные \n
    lResult = lResult.replace(b'{{n}}',b'\n')
    lResult = zlib.decompress(lResult[0:-1])
    lResult = lResult.decode("utf-8")
    #Вернуть результат
    return lResult

#ParentProcessWriteString
def ProcessParentWriteString(lString):
    lByteString = zlib.compress(lString.encode("utf-8"))
    #Выполнить отправку строки в родительский процесс
    #Вернуть потенциальные \n
    lByteString = lByteString.replace(b'\n',b'{{{n}}}')
    #Вернуть \r
    lByteString = lByteString.replace(b'\r',b'{{{r}}}')
    #Вернуть \0
    lByteString = lByteString.replace(b'\0',b'{{{0}}}')
    #Вернуть \a
    lByteString = lByteString.replace(b'\a',b'{{{a}}}')
    #Вернуть \b
    lByteString = lByteString.replace(b'\b',b'{{{b}}}')
    #Вернуть \t
    lByteString = lByteString.replace(b'\t',b'{{{t}}}')
    #Вернуть \v
    lByteString = lByteString.replace(b'\v',b'{{{v}}}')
    #Вернуть \f
    lByteString = lByteString.replace(b'\f',b'{{{f}}}')
    ############################
    #lByteString= b'x\x9c\xdd\x95]O\xc20\x14\x86\xffJ\xb3[5\xa1Cqz\x07\xc4\xe8\x8d\x1fQ\x13.\x0cYJw\xb6U\xbav\xe9\xce"\x84\xf0\xdfm\'"\xb8\xa0L%Q\xb3\x9b\xf6=\xdfO\x9a\xb3\x99\x17\x97\x8a\xa3\xd0\xea\x8ae\xe0\x9d\x12\xaf[\xa2\xce\x98S\xee\x80\x19\x9e^\xea\xb2\x803\t\x19(\xbc\x10`\x9c6\xf5\xf6\x89\xc7LRt\x8daS\x1b\xf5\xf00\xf3\xd4"\xc1u\x0e\xea\xf6\xa6K\x0e\xc8\xb9\xd6\x89\x04\xd2O\x8d\xb6&\x1bb\x04OC\x84\t~\xe2\x97\x1b\xcd\xa1(B\x11YG\xdaj\xfb\xc1\x9b\xb8\xa2\xa4LE\xd2\xd5\xa4\xf6\xdenY\x85Kf\xc3^;yI\x18\x0eD\x94\x00\x0e\x84{{n}}\xa9K\xce\xb5B\xa3e\x88\xd3\xbc\xf2Z\xd5\xaa\x82\xaa\x94\xd25\x0b\x1c\x99J\xaa\x023OB\xec\xbavEP\xe7\x8b\x93\x11I\xeaTz\xe2\xbb\xebH\xa3eW5\xe8\xb7\xe6\xce^*\x14\xb6\x83e\xda\xf9phe]b^\xe2\xf5\xe8\xd1Vp\xf0\xfe.\xbb\x1b\xa6`\x87\xfc8\x1a\x9bSE0q\xa2\x15\xeer\xe0"\x16\xbcz\x9f\xfdT\xc8h\x9d\xdf\xc7\xd4\xbe\xcdj1\xd9:\xa9\x1f\xe1B7\x81\xa1\xef\xc0\xd0:\x98\xc3-\xc0\xd4X\xfc\xda\xf1i\xbb\xe9\xfc\xdb<\x8c\xff2\x7f\'\xa8\x8d\xdf\xdab\xfc\x9e\xd6\xe3\x8c\x99qQ\xe3\xb0f\xd9\x19\x90{\xade\x8f\x99/3\xa1AC(\xfe\x16P\x06F \x90\xb3\t\x07Iba\x17\x83P\xa4\xbf\xb7G\x9e\x04\xa6vE\x13\xb6\xfc\x13\xd6\xa85\x0b\xdd\x19\xd6^i\x11\xa8FT;G\xfe\x06\xac\xc1q\xb0N\x956\xd84\xae\xe4p\xbe\xfa=\x03\x01\xce\x95\x9a'
    #lByteString = b"x\x9c\xb5\x91\xcfO\xc3 \x14\xc7\xff\x95\xa6\xd7uI\xf9Q\x8a\xde\xd4\x93\x07\xbdx\xf00\x97\x05)[I(\x90\x8ef3\xcb\xfew\x81M\xbb\xd9M]\x8c!y\xd0\xf7}\xbc\xef\xe3\xd3\xc9&\xd5\xac\x11\xe9u\x92j\xb1J@2N\x1e\x8d\x13\x96U\xa3Q\x9a%i+y=sb\xed\xceV\xd8\xd6p\xb1\\\xced\xe5K{{n}}\x80`\x9f\xeb\x135\xd3\x95{{n}}.\x08RR\xe4>\xc3\x15\xf3\x97>\xbc\x8f:r\xa3]k\xd4\xcc\xbd\xd9(>K]\x99\xd5\xa1\x12\xbd\x00\xc6\xb0\xcc\xcb0\xa4\xe0\x8e\xe9E4\xd8\xa4J\xcc\xc3\xb44\x07^r\xc6\xfa3\x04(\xbeeQ\x07\x05P\x1a\xa4W\xe3\x9ci\xfc\xf7\x15(\xb6A\xee\xb4\x93\x8d\xd85\x9f`?\xf6n\xd8i0v\xadw\xd5\x95X\x87n>\xf1d\x05\x97s\xc9\x99\x93F\xdf\xd5R\xc5K=\xcc\x1bk\xd5^\x1d`\xfc\xa2]\x06PwJ\r\xf0\x9d\xa2\xf6 tw\xcb\xda\x01\xb6}\x83\xd3\xcc\x00\xec\x99\x15\xf4\x88Y\x99\x1f2\x83\xb4\xfc\x8e\x99\xdf\xb3d\x0c\x01.1E\x04\x93l\xff\x8e\xcf\x7f6\xa4Z\xfc\x82\xeaK\x97c BD\xf3\x101\x89g\xba\x8b\x03\xd0?\x97\xff#\xfb{'\x9a\x8b\xe0\x03H\xc89\xfa\x08\x15\x7f\xa2\x0f >\x80_\x0e\xe0\x93\xb3\xf0\xc3\xc4\xd3m\\\xef\xf8\x958\xa0"
    #lt=open("logSendByteStringWithoutN.log","wb")
    #lt.write(lByteString)
    #lt.close()
    ############################
    sys.stdout.buffer.write(lByteString+bytes("\n","utf-8"))
    sys.stdout.flush();
    return
#ProcessParentWriteObject
def ProcessParentWriteObject(inObject):
    #Выполнить нормализацию объекта перед форматированием в JSON
    JSONNormalize.JSONNormalizeDictList(inObject)
    #Выполнить отправку сконвертированного объекта в JSON
    ProcessParentWriteString(json.dumps(inObject))
    return
#ProcessParentReadWaitObject
def ProcessParentReadWaitObject():
    #Выполнить получение и разбор объекта
    lResult=json.loads(ProcessParentReadWaitString());
    return lResult;

#ProcessChildSendString
def ProcessChildSendString(lProcess,lString):
    lByteString = zlib.compress(lString.encode("utf-8"))
    #Вернуть потенциальные \n
    lByteString = lByteString.replace(b'\n',b'{{n}}')
    #Отправить сообщение в дочерний процесс
    lProcess.stdin.write(lByteString+bytes('\n',"utf-8"))
    lProcess.stdin.flush()
    #Вернуть результат
    return

#ProcessChildReadWaitString
def ProcessChildReadWaitString(lProcess):
    #Ожидаем ответ от процесса
    #pdb.set_trace()
    lResult = lProcess.stdout.readline()
    #Обработка спец символов
    #Вернуть потенциальные \n
    lResult = lResult.replace(b'{{{n}}}',b'\n')
    #Вернуть \r
    lResult = lResult.replace(b'{{{r}}}',b'\r')
    #Вернуть \0
    lResult = lResult.replace(b'{{{0}}}',b'\0')
    #Вернуть \a
    lResult = lResult.replace(b'{{{a}}}',b'\a')
    #Вернуть \b
    lResult = lResult.replace(b'{{{b}}}',b'\b')
    #Вернуть \t
    lResult = lResult.replace(b'{{{t}}}',b'\t')
    #Вернуть \v
    lResult = lResult.replace(b'{{{v}}}',b'\v')
    #Вернуть \f
    lResult = lResult.replace(b'{{{f}}}',b'\f')
    try:
        lResult = zlib.decompress(lResult[0:-1])
        lResult = lResult.decode("utf-8")
    except zlib.error as e:
        raise Exception(f"Exception from child process: {lProcess.stderr.read()}")
    #Вернуть результат
    return lResult

#ProcessChildSendObject
def ProcessChildSendObject(inProcess,inObject):
    #Выполнить отправку сконвертированного объекта в JSON
    ProcessChildSendString(inProcess,json.dumps(inObject))
    return
#ProcessChildReadWaitObject
def ProcessChildReadWaitObject(inProcess):
    #Выполнить получение и разбор объекта
    lResult=json.loads(ProcessChildReadWaitString(inProcess));
    return lResult;

#ProcessChildSendReadWaitString
def ProcessChildSendReadWaitString(lProcess,lString):
    ProcessChildSendString(lProcess,lString)
    #Вернуть результат
    return ProcessChildReadWaitString(lProcess)
#ProcessChildSendReadWaitObject
def ProcessChildSendReadWaitObject(inProcess,inObject):
    ProcessChildSendObject(inProcess,inObject)
    #Вернуть результат
    return ProcessChildReadWaitString(inProcess)
#ProcessChildSendReadWaitQueue
#QueueObject - [Object,Object,...]
def ProcessChildSendReadWaitQueueObject(inProcess,inQueueObject):
    lOutputObject=[]
    #Циклическая отправка запросов в дочерний объект
    for lItem in inQueueObject:
        #Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessChildSendObject(inProcess,lItem)
        #Получить ответ от дочернего процесса
        lResponseObject=ProcessChildReadWaitObject(inProcess)
        #Добавить в выходной массив
        lOutputObject.append(lResponseObject)
    #Сформировать ответ
    return lOutputObject
