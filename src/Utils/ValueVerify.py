#valueVerify
#inTypeClass int, str, dict, list, NoneType
def valueVerify(inValue,inTypeClass,inNotValidValue):
    lResult = inNotValidValue
    if inValue is not None:
        if type(inValue) == inTypeClass:
            lResult = inValue
    #Вернуть результат
    return lResult
#valueVerifyDict
def valueVerifyDict(inDict,inKey,inTypeClass,inNotValidValue):
    lResult = inNotValidValue
    if inKey in inDict:
        lResult = valueVerify(inDict[inKey],inTypeClass,inNotValidValue)
    return lResult
#valueVerifyList
def valueVerifyList(inList,inIndex,inTypeClass,inNotValidValue):
    lResult = inNotValidValue
    if inIndex in inList:
        lResult = valueVerify(inList[inIndex],inTypeClass,inNotValidValue)
    return lResult
