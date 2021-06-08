import json

####################################
#Info: Internal JSONNormalize module of the Robot app (PythonRPA - Robot)
####################################
# JSONNormalize Module - Prepare dict or list for JSON (delete object from the structure)

###############################
####Нормализация под JSON (в JSON нельзя передавать классы - только null, числа, строки, словари и массивы)
###############################
#Нормализация словаря под JSON
def JSONNormalizeDict(inDictionary):
    #Сделать копию объекта
    lResult=inDictionary.copy()
    #Перебор всех элементов
    for lItemKey,lItemValue in inDictionary.items():
        #Флаг удаления атрибута
        lFlagRemoveAttribute=False
        #Если строка или число или массив или объект или None - оставить
        if (
            type(lItemValue) is dict or
            type(lItemValue) is int or
            type(lItemValue) is str or
            type(lItemValue) is list or
            type(lItemValue) is bool or
            lItemValue is None):
            True==True
        else:
            lFlagRemoveAttribute=True
        #Рекурсивный вызов, если объект является словарем
        if type(lItemValue) is dict:
            lResult[lItemKey]=JSONNormalizeDict(lItemValue)
        #Рекурсивный вызов, если объект является списком
        if type(lItemValue) is list:
            lResult[lItemKey]=JSONNormalizeList(lItemValue)
        #############################
        #Конструкция по удалению ключа из словаря
        if lFlagRemoveAttribute:
             lResult.pop(lItemKey)
    #Вернуть результат
    return lResult
#Нормализация массива под JSON
def JSONNormalizeList(inList):
    lResult=[]
    #Циклический обход
    for lItemValue in inList:
        #Если строка или число или массив или объект или None - оставить
        if (
            type(lItemValue) is int or
            type(lItemValue) is str or
            type(lItemValue) is bool or
            lItemValue is None):
            lResult.append(lItemValue)
        #Если является словарем - вызвать функцию нормализации словаря            
        if type(lItemValue) is dict:
            lResult.append(JSONNormalizeDict(lItemValue))
        #Если является массиваом - вызвать функцию нормализации массива            
        if type(lItemValue) is list:
            lResult.append(JSONNormalizeList(lItemValue))
    #Вернуть результат
    return lResult
#Определить объект - dict or list - и нормализовать его для JSON
def JSONNormalizeDictList(inDictList):
    lResult={}
    if type(inDictList) is dict:
        lResult=JSONNormalizeDict(inDictList)
    if type(inDictList) is list:
        lResult=JSONNormalizeList(inDictList)
    return lResult;
def JSONNormalizeDictListStrIntBool(inDictListStrIntBool):
    lResult=None
    if type(inDictListStrIntBool) is dict:
        lResult=JSONNormalizeDict(inDictListStrIntBool)
    if type(inDictListStrIntBool) is list:
        lResult=JSONNormalizeList(inDictListStrIntBool)
    if type(inDictListStrIntBool) is str:
        lResult=inDictListStrIntBool
    if type(inDictListStrIntBool) is int:
        lResult=inDictListStrIntBool
    if type(inDictListStrIntBool) is bool:
        lResult=inDictListStrIntBool
    return lResult;

