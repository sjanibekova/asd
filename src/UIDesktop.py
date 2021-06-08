from pywinauto import win32defines, win32structures, win32functions
import pywinauto
import ctypes
import struct
import win32api
import time
# asd
import Utils  # For ProcessBitness
from Utils import ProcessCommunicator
import re
import copy
from ctypes.wintypes import tagPOINT

############################################

#####Внимание#######
# TODO В перспективе нужно реализовать алгоритм определения разрядности не в Robot.py, а в UIDesktop.py, тк начинают появляться функции, на входе в которые еще неизвестна разрядность элемента + селектор может охватить сразу два элемента из 2-х разных разрядностей - обрабатываться это должно непосредственно при выполнении

####################################
# Info: GUI Module to get selectors from WINDOWS applications
####################################
# GUI Module - interaction with Desktop application

# GUI Naming convention
# <InArgument>_<ActivityName>_<OutArgument - if exist>

# UIO - UI Object (class of pywinauto UI object)
# UIOSelector - List of dict (key attributes)
# PWA - PyWinAuto
# PWASpecification - List of dict (key attributes in pywinauto.find_window notation)
# UIOTree - Recursive Dict of Dict ... (UI Parent -> Child hierarchy)
# UIOInfo - Dict of UIO attributes
# UIOActivity - Activity of the UIO (UI object) from the Pywinauto module
# UIOEI - UI Object info object



# Default parameters
mDefaultPywinautoBackend = "win32"


############################
# Новая версия
############################
# Получить список элементов, который удовлетворяет условиям через расширенный движок поиска
# [
#   {
#       "index":<Позиция элемента в родительском объекте>,
#       "depth_start" - глубина, с которой начинается поиск (по умолчанию 1)
#       "depth_end" - глубина, до которой ведется поиск (по умолчанию 1)
#       "class_name" - наименование класса, который требуется искать
#       "title" - наименование заголовка
#       "rich_text" - наименование rich_text
#   }
# ]
################
# return: List of UI Object
# inElement - Входной элемент - показатель, что не требуется выполнять коннект к процессу
# inFlagRaiseException - Флаг True - выкинуть ошибку в случае обнаружении пустого списка
# old name - PywinautoExtElementsGet
def UIOSelector_Get_UIOList(inSpecificationList, inElement=None, inFlagRaiseException=True):
    '''
     Get the UIO list by the selector

     :param inSpecificationList: UIO Selector
     :param inElement: Входной элемент - показатель, что не требуется выполнять коннект к процессу
     :param inFlagRaiseException: Флаг True - выкинуть ошибку в случае обнаружении пустого списка
     :return:
     '''

    # Создать копию входного листа, чтобы не менять массив в других верхнеуровневых функциях
    inSpecificationList = copy.deepcopy(inSpecificationList)
    lResultList = []
    lChildrenList = []
    # Получить родительский объект если на вход ничего не поступило
    if inElement is None:
        # сформировать спецификацию на получение элемента
        lRootElementSpecification = [inSpecificationList[0]]
        lRootElementList = PWASpecification_Get_UIO(lRootElementSpecification)
        for lRootItem in lRootElementList:
            if lRootItem is not None:
                lChildrenList.append(lRootItem.wrapper_object())
    # Елемент на вход поступил - выполнить его анализ
    else:
        # Получить список элементов
        lElementChildrenList = inElement.children()
        # Поступил index - точное добавление
        if 'index' in inSpecificationList[0]:
            if inSpecificationList[0]['index'] < len(lElementChildrenList):
                # Получить дочерний элемент - точное добавление
                lChildrenList.append(lElementChildrenList[inSpecificationList[0]['index']])
            else:
                if inFlagRaiseException:
                    raise ValueError('Object has no children with index: ' + str(inSpecificationList[0]['index']))
        # Поступил ctrl_index - точное добавление
        elif 'ctrl_index' in inSpecificationList[0]:
            if inSpecificationList[0]['ctrl_index'] < len(lElementChildrenList):
                # Получить дочерний элемент
                lChildrenList.append(lElementChildrenList[inSpecificationList[0]['ctrl_index']])
            else:
                if inFlagRaiseException:
                    raise ValueError('Object has no children with index: ' + str(inSpecificationList[0]['ctrl_index']))
        # Если нет точного обозначения элемента
        else:
            lFlagGoCheck = True
            # Учесть поле depth_start (если указано)
            if 'depth_start' in inSpecificationList[0]:
                if inSpecificationList[0]["depth_start"] > 1:
                    lFlagGoCheck = False
            # Циклический обход по детям, на предмет соответствия всем условиям
            for lChildrenItem in lElementChildrenList:
                # Обработка глубины depth (рекурсивный вызов для всех детей с занижением индекса глубины)
                # По умолчанию значение глубины 1
                if 'depth_end' in inSpecificationList[0]:
                    if inSpecificationList[0]['depth_end'] > 1:
                        # Подготовка новой версии спецификации
                        lChildrenItemNewSpecificationList = inSpecificationList.copy()
                        lChildrenItemNewSpecificationList[0] = lChildrenItemNewSpecificationList[0].copy()
                        lChildrenItemNewSpecificationList[0]["depth_end"] = lChildrenItemNewSpecificationList[0][
                                                                                "depth_end"] - 1
                        if 'depth_start' in lChildrenItemNewSpecificationList[0]:
                            lChildrenItemNewSpecificationList[0]["depth_start"] = lChildrenItemNewSpecificationList[0][
                                                                                      "depth_start"] - 1
                        # Циклический вызов для всех детей со скорректированной спецификацией
                        lResultList.extend(UIOSelector_Get_UIOList(lChildrenItemNewSpecificationList, lChildrenItem,
                                                                   inFlagRaiseException))
                # Фильтрация
                # TODO Сделать поддержку этих атрибутов для первого уровня селектора
                if lFlagGoCheck:
                    lFlagAddChild = True
                    # Фильтрация по title
                    if 'title' in inSpecificationList[0]:
                        if lChildrenItem.element_info.name != inSpecificationList[0]["title"]:
                            lFlagAddChild = False
                    # Фильтрация по title_re (regexp)
                    if 'title_re' in inSpecificationList[0]:
                        if re.fullmatch(inSpecificationList[0]["title_re"], lChildrenItem.element_info.name) is None:
                            lFlagAddChild = False
                    # Фильтрация по rich_text
                    if 'rich_text' in inSpecificationList[0]:
                        if lChildrenItem.element_info.rich_text != inSpecificationList[0]["rich_text"]:
                            lFlagAddChild = False
                    # Фильтрация по rich_text_re (regexp)
                    if 'rich_text_re' in inSpecificationList[0]:
                        if re.fullmatch(inSpecificationList[0]["rich_text_re"],
                                        lChildrenItem.element_info.rich_text) is None:
                            lFlagAddChild = False
                    # Фильтрация по class_name
                    if 'class_name' in inSpecificationList[0]:
                        if lChildrenItem.element_info.class_name != inSpecificationList[0]["class_name"]:
                            lFlagAddChild = False
                    # Фильтрация по class_name_re (regexp)
                    if 'class_name_re' in inSpecificationList[0]:
                        if re.fullmatch(inSpecificationList[0]["class_name_re"],
                                        lChildrenItem.element_info.class_name) is None:
                            lFlagAddChild = False
                    # Фильтрация по friendly_class_name
                    if 'friendly_class_name' in inSpecificationList[0]:
                        if lChildrenItem.friendly_class_name() != inSpecificationList[0]["friendly_class_name"]:
                            lFlagAddChild = False
                    # Фильтрация по friendly_class_name_re (regexp)
                    if 'friendly_class_name_re' in inSpecificationList[0]:
                        if re.fullmatch(inSpecificationList[0]["friendly_class_name_re"],
                                        lChildrenItem.friendly_class_name) is None:
                            lFlagAddChild = False
                    # Фильтрация по control_type
                    if 'control_type' in inSpecificationList[0]:
                        if lChildrenItem.element_info.control_type != inSpecificationList[0]["control_type"]:
                            lFlagAddChild = False
                    # Фильтрация по control_type_re (regexp)
                    if 'control_type_re' in inSpecificationList[0]:
                        if re.fullmatch(inSpecificationList[0]["control_type_re"],
                                        lChildrenItem.element_info.control_type) is None:
                            lFlagAddChild = False
                    # Фильтрация по is_enabled (bool)
                    if 'is_enabled' in inSpecificationList[0]:
                        if lChildrenItem.is_enabled() != inSpecificationList[0]["is_enabled"]:
                            lFlagAddChild = False
                    # Фильтрация по is_visible (bool)
                    if 'is_visible' in inSpecificationList[0]:
                        if lChildrenItem.is_visible() != inSpecificationList[0]["is_visible"]:
                            lFlagAddChild = False
                    #####
                    # Все проверки пройдены - флаг добавления
                    if lFlagAddChild:
                        lChildrenList.append(lChildrenItem)
    # Выполнить рекурсивный вызов (уменьшение количества спецификаций), если спецификация больше одного элемента
    # ????????Зачем в условии ниже is not None ???????????
    if len(inSpecificationList) > 1 and len(lChildrenList) > 0 is not None:
        # Вызвать рекурсивно функцию получения следующего объекта, если в спецификации есть следующий объект
        for lChildElement in lChildrenList:
            lResultList.extend(UIOSelector_Get_UIOList(inSpecificationList[1:], lChildElement, inFlagRaiseException))
    else:
        lResultList.extend(lChildrenList)
    # Условие, если результирующий список пустой и установлен флаг создания ошибки (и inElement is None - не следствие рекурсивного вызова)
    if inElement is None and len(lResultList) == 0 and inFlagRaiseException:
        raise pywinauto.findwindows.ElementNotFoundError("Robot can't find element by the UIOSelector")
    return lResultList


#################################################################################################
# Get first (in more than one) UIO (UI Object)
# inSpecificationList - UIOSelector
# inElement - Входной элемент - показатель, что не требуется выполнять коннект к процессу
# inFlagRaiseException - Флаг True - выкинуть ошибку в случае обнаружении пустого списка
# old name - PywinautoExtElementGet
def UIOSelector_Get_UIO(inSpecificationList, inElement=None, inFlagRaiseException=True):
    """
    Get the pywinauto object by the UIO selector.

    :param inSpecificationList:
    :param inElement:
    :param inFlagRaiseException:
    :return:
    """

    lResult = None
    # Получить родительский объект если на вход ничего не поступило
    # lResultList = UIOSelector_Get_UIOList(inSpecificationList, inElement, False)

    lResultList = UIOSelector_Get_UIOList(inSpecificationList, inElement, False)
    if len(lResultList) > 0:
        lResult = lResultList[0]
    # Условие, если результирующий список пустой и установлен флаг создания ошибки (и inElement is None - не следствие рекурсивного вызова)
    if lResult is None and inFlagRaiseException:
        raise pywinauto.findwindows.ElementNotFoundError("Robot can't find element by the UIOSelector")
    return lResult



#################################################################################################
# Check if UIO exist (Identified by the UIOSelector)
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# UIOSelector
# old name - -
def UIOSelector_Exist_Bool(inUIOSelector):
    """
    Check if object is exist by the UIO selector.

    :param inUIOSelector:
    :return: True - Object is exist. False - else case
    """

    lResult = False
    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        # Получить родительский объект если на вход ничего не поступило
        lResultList = UIOSelector_Get_UIOList(inUIOSelector, None, False)
        if len(lResultList) > 0:
            lResult = True
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_Exist_Bool",
                            "ArgumentList": [inUIOSelector],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lResult = lPIPEResponseDict["Result"]
    return lResult


#################################################################################################
# Wait for UIO is appear (at least one of them or all at the same time)
# inSpecificationListList - List of the UIOSelector
# inWaitSecs - Время ожидания объекта в секундах
# inFlagWaitAllInMoment - доп. условие - ожидать появление всех UIOSelector одновременно
# return: [0,1,2] - index of UIOSpecification, which is appear
# old name - -
#####Внимание#####
##Функция ожидания появления элементов (тк элементы могут быть недоступны, неизвестно в каком фреймворке каждый из них может появиться)
def UIOSelectorsSecs_WaitAppear_List(inSpecificationListList, inWaitSecs, inFlagWaitAllInMoment=False):
    """
    Wait for many UI object will appear in GUI for inWaitSecs seconds.

    :param inSpecificationListList: UIOSelector list.
        Example: [
            [{"title":"notepad"},{"title":"OK"}],
            [{"title":"notepad"},{"title":"Cancel"}]
        ]
    :param inWaitSecs: Float value (seconds) for wait UI element appear in GUI
    :param inFlagWaitAllInMoment: True - Wait all UI objects from the UIOSelector list to be appeared
    :return: List of index, which UI object UIO will be appeared. Example: [1] # Appear only UI object with UIO selector: [{"title":"notepad"},{"title":"Cancel"}]
    """

    lResultFlag = False
    lSecsSleep = 1  # Настроечный параметр
    lSecsDone = 0
    lResultList = None
    # Цикл проверки
    while lResultFlag == False and lSecsDone < inWaitSecs:
        # pdb.set_trace()
        lResultList = []
        # Итерация проверки
        lIndex = 0
        for lItem in inSpecificationListList:
            lItemResultFlag = UIOSelector_Exist_Bool(lItem)
            # Если обнаружен элемент - добавить его индекс в массив
            if lItemResultFlag:
                lResultList.append(lIndex)
            # Инкремент индекса
            lIndex = lIndex + 1
        # Проверка в зависимости от флага
        if inFlagWaitAllInMoment and len(lResultList) == len(inSpecificationListList):
            # Условие выполнено
            lResultFlag = True
        elif not inFlagWaitAllInMoment and len(lResultList) > 0:
            # Условие выполнено
            lResultFlag = True
        # Если флаг не изменился - увеличить время и уснуть
        if lResultFlag == False:
            lSecsDone = lSecsDone + lSecsSleep
            time.sleep(lSecsSleep)

    return lResultList


#################################################################################################
# Wait for UIO is Disappear (at least one of them or all at the same time)
# inSpecificationListList - List of the UIOSelector
# inWaitSecs - Время ожидания пропажи объекта в секундах
# inFlagWaitAllInMoment - доп. условие - ожидать пропажу всех UIOSelector одновременно
# return: [0,1,2] - index of UIOSpecification, which is Disappear
# old name - -
#####Внимание#####
##Функция ожидания пропажи элементов (тк элементы могут быть недоступны, неизвестно в каком фреймворке каждый из них может появиться)
def UIOSelectorsSecs_WaitDisappear_List(inSpecificationListList, inWaitSecs, inFlagWaitAllInMoment=False):
    '''
    Wait for many UI object will disappear in GUI for inWaitSecs seconds.

    :param inSpecificationListList: UIOSelector list.
        Example: [
            [{"title":"notepad"},{"title":"OK"}],
            [{"title":"notepad"},{"title":"Cancel"}]
        ]
    :param inWaitSecs: Float value (seconds) for wait UI element disappear in GUI
    :param inFlagWaitAllInMoment: True - Wait all UI objects from the UIOSelector list to be disappeared.
    :return: List of index, which UI object UIO will be disappeared. Example: [1] # Disappear only UI object with UIO selector: [{"title":"notepad"},{"title":"Cancel"}]
    :return:
    '''

    lResultFlag = False
    lSecsSleep = 1  # Настроечный параметр
    lSecsDone = 0
    lResultList = None
    # Цикл проверки
    while lResultFlag == False and lSecsDone < inWaitSecs:
        # pdb.set_trace()
        lResultList = []
        # Итерация проверки
        lIndex = 0
        for lItem in inSpecificationListList:
            lItemResultFlag = UIOSelector_Exist_Bool(lItem)
            # Если обнаружен элемент - добавить его индекс в массив
            if not lItemResultFlag:
                lResultList.append(lIndex)
            # Инкремент индекса
            lIndex = lIndex + 1
        # Проверка в зависимости от флага
        if inFlagWaitAllInMoment and len(lResultList) == len(inSpecificationListList):
            # Условие выполнено
            lResultFlag = True
        elif not inFlagWaitAllInMoment and len(lResultList) > 0:
            # Условие выполнено
            lResultFlag = True
        # Если флаг не изменился - увеличить время и уснуть
        if lResultFlag == False:
            lSecsDone = lSecsDone + lSecsSleep
            time.sleep(lSecsSleep)
    return lResultList


#################################################################################################
# Wait for UIO is appear (at least one of them or all at the same time)
# inSpecificationList - UIOSelector
# inWaitSecs - Время ожидания объекта в секундах
# return: Bool - True - UIO is appear
# old name - -
def UIOSelectorSecs_WaitAppear_Bool(inSpecificationList, inWaitSecs):
    """
    Wait for UI object will appear in GUI for inWaitSecs seconds.

    :param inSpecificationList: UIOSelector. Example: [{"title":"notepad"},{"title":"OK"}]
    :param inWaitSecs: Float value (seconds) for wait UI element appear in GUI
    :return: True - UI object will appear. False - else case
    """
    lWaitAppearList = UIOSelectorsSecs_WaitAppear_List([inSpecificationList], inWaitSecs)
    lResult = False
    if len(lWaitAppearList) > 0:
        lResult = True
    return lResult


#################################################################################################
# Wait for UIO is disappear (at least one of them or all at the same time)
# inSpecificationList - UIOSelector
# inWaitSecs - Время ожидания пропажи объекта в секундах
# return: Bool - True - UIO is Disappear
# old name - -
def UIOSelectorSecs_WaitDisappear_Bool(inSpecificationList, inWaitSecs):
    """
    Wait for UI object will disappear in GUI for inWaitSecs seconds.

    :param inSpecificationList: UIOSelector.
        Example: [{"title":"notepad"},{"title":"OK"}]
    :param inWaitSecs: Float value (seconds) for wait UI element disappear in GUI
    :return: True - UI object will disappear. False - else case
    """

    lWaitDisappearList = UIOSelectorsSecs_WaitDisappear_List([inSpecificationList], inWaitSecs)
    lResult = False
    if len(lWaitDisappearList) > 0:
        lResult = True
    return lResult


#################################################################################################
# Get process bitness (32 or 64)
# inSpecificationList - UIOSelector
# old name - None
# return None (if Process not found), int 32, or int 64
def UIOSelector_Get_BitnessInt(inSpecificationList):
    """
    Detect process bitness by the UI Object UIO Selector.
    :param inSpecificationList: UIOSelector. Example: [{"title":"notepad"},{"title":"OK"}]
    :return: int 32 or int 64
    """

    lResult = None
    # Получить объект Application (Для проверки разрядности)
    lRootElement = PWASpecification_Get_PWAApplication(inSpecificationList)
    if lRootElement is not None:
        if lRootElement.is64bit():
            lResult = 64
        else:
            lResult = 32
    return lResult


#################################################################################################
# Get process bitness ("32" or "64")
# inSpecificationList - UIOSelector
# old name - None
# return None (if Process not found), int 32, or int 64
def UIOSelector_Get_BitnessStr(inSpecificationList):
    """
    Detect process bitness by the UI Object UIO Selector.

    :param inSpecificationList: UIOSelector. Example: [{"title":"notepad"},{"title":"OK"}]
    :return: str "32" or str "64"
    """

    lResult = None
    # Получить объект Application (Для проверки разрядности)
    lRootElement = PWASpecification_Get_PWAApplication(inSpecificationList)
    if lRootElement is not None:
        if lRootElement.is64bit():
            lResult = "64"
        else:
            lResult = "32"
    return lResult


#################################################################################################
# Get OS bitness (32 or 64)
# old name - None
# return int 32, or int 64
def Get_OSBitnessInt():
    """
    Detect OS bitness.

    :return: int 32 or int 64
    """

    lResult = 32;
    if pywinauto.sysinfo.is_x64_OS():
        lResult = 64;
    return lResult;


#################################################################################################
# Safe get other process or None if destination app is the other/same bitness
# inUIOSelector - selector of the destination
# return None or process (of the other bitness)
def  UIOSelector_SafeOtherGet_Process(inUIOSelector):
    """
    Safe get other process or None if destination app is the other/same bitness

    :param inUIOSelector: UIO Selector of the UI object
    :return: None or process (of the other bitness)
    """

    # Default value
    lResult = None
    # Go check bitness if selector exists
    if inUIOSelector:
        # Get selector bitness
        lUIOSelectorAppBitness = UIOSelector_Get_BitnessStr(inUIOSelector)
        if lUIOSelectorAppBitness and Utils.ProcessBitness.mSettingsDict[
            "BitnessProcessCurrent"] != lUIOSelectorAppBitness:
            lResult = Utils.ProcessBitness.OtherProcessGet()
    return lResult


##################################################################################################
# inControlSpecificationArray - List of dict, dict in pywinauto.find_windows notation
# Backend selection - attribute "backend" ("win32" || "uia") in 1-st list element
# return list of UIO object
# old name - GetControl
def PWASpecification_Get_UIO(inControlSpecificationArray):
    """
    #Backend def selection - attribute "backend" ("win32" || "uia") in 1-st list element
    #old name - GetControl

    :param inControlSpecificationArray: List of dict, dict in pywinauto.find_windows notation
    :return: list of UIO object
    """

    # Определение backend
    lBackend = mDefaultPywinautoBackend
    if "backend" in inControlSpecificationArray[0]:
        lBackend = inControlSpecificationArray[0]["backend"]
        inControlSpecificationArray[0].pop("backend")
    # Подготовка входного массива
    inControlSpecificationOriginArray = copy.deepcopy(inControlSpecificationArray)
    inControlSpecificationArray = UIOSelector_SearchProcessNormalize_UIOSelector(inControlSpecificationArray)
    # Выполнить идентификацию объектов, если передан массив
    lResultList = [];
    lTempObject = None
    if len(inControlSpecificationArray) > 0:
        # Сформировать выборку элементов, которые подходят под первый уровень спецификации
        lSpecificationLvL1List = pywinauto.findwindows.find_elements(**inControlSpecificationArray[0])
        for lItem in lSpecificationLvL1List:
            # Сделать независимую копию и установить информацию о process_id и handle
            lItemControlSpecificationArray = copy.deepcopy(inControlSpecificationArray)
            lItemControlSpecificationArray[0]["process_id"] = lItem.process_id
            lItemControlSpecificationArray[0]["handle"] = lItem.handle
            lItemControlSpecificationOriginArray = copy.deepcopy(inControlSpecificationOriginArray)
            lItemControlSpecificationOriginArray[0]["process_id"] = lItem.process_id
            lItemControlSpecificationOriginArray[0]["handle"] = lItem.handle
            # Выполнить подключение к объекту
            lRPAApplication = pywinauto.Application(backend=lBackend)
            # Проверка разрядности
            try:
                lRPAApplication.connect(**lItemControlSpecificationArray[0])
            except Exception as e:
                UIOSelector_TryRestore_Dict(lItemControlSpecificationArray)
                try:
                    lRPAApplication.connect(**lItemControlSpecificationArray[0])
                except Exception as e:
                    lRPAApplication = None
            if lRPAApplication is not None:
                # lTempObject=lRPAApplication.window(**lItemControlSpecificationArray[0])
                # Скорректировано из-за недопонимания структуры
                lTempObject = lRPAApplication
                # Нормализация массива для целей выборки объекта (удаление конфликтующих ключей)
                lItemControlSpecificationArray = UIOSelector_SearchUIONormalize_UIOSelector(
                    lItemControlSpecificationOriginArray)
                # Циклическое прохождение к недрам объекта
                for lWindowSpecification in lItemControlSpecificationArray[0:]:
                    lTempObject = lTempObject.window(**lWindowSpecification)
                # Добавить объект в результирующий массив
                lResultList.append(lTempObject)
    return lResultList


##################################################################################################
# inControlSpecificationArray - List of dict, dict in pywinauto.find_windows notation
# Backend selection - attribute "backend" ("win32" || "uia") in 1-st list element
# return process application object
# old name - None
def PWASpecification_Get_PWAApplication(inControlSpecificationArray):
    """
    #Backend selection - attribute "backend" ("win32" || "uia") in 1-st list element

    :param inControlSpecificationArray: List of dict, dict in pywinauto.find_windows notation
    :return: process application object
    """

    inControlSpecificationArray =inControlSpecificationArray
    inControlSpecificationArray = copy.deepcopy(inControlSpecificationArray)
    # Определение backend
    lBackend = mDefaultPywinautoBackend
    if "backend" in inControlSpecificationArray[0]:
        lBackend = inControlSpecificationArray[0]["backend"]
        inControlSpecificationArray[0].pop("backend")
    # Подготовка входного массива
    inControlSpecificationOriginArray = inControlSpecificationArray
    inControlSpecificationArray = UIOSelector_SearchProcessNormalize_UIOSelector(inControlSpecificationArray)
    # Выполнить идентификацию объектов, если передан массив
    lResultList = [];
    lTempObject = None
    if len(inControlSpecificationArray) > 0:
        # Выполнить подключение к объекту
        lRPAApplication = pywinauto.Application(backend=lBackend)
        # Проверка разрядности
        try:
            lRPAApplication.connect(**inControlSpecificationArray[0])
        except Exception as e:
            UIOSelector_TryRestore_Dict(inControlSpecificationArray)
            try:
                lRPAApplication.connect(**inControlSpecificationArray[0])
            except Exception as e:
                lRPAApplication = None
        if lRPAApplication is not None:
            # lTempObject=lRPAApplication.window(**inControlSpecificationArray[0])
            # Скорректировано из-за недопонимания структуры
            lTempObject = lRPAApplication
    return lTempObject


###########################################################################################################
# inElementSpecificationList = UIOSelector (see description on the top of the document)
# result = pywinauto element wrapper instance or None
# old name - AutomationSearchMouseElement
def UIOSelector_SearchChildByMouse_UIO(inElementSpecification):
    """
    UIOSelector (see description on the top of the document)
    #old name - AutomationSearchMouseElement

    :param inElementSpecification: UIOSelector of the UI Object
    :return: pywinauto element wrapper instance or None
    """

    lGUISearchElementSelected = None
    # if inElementSpecification[0]
    # Настройка - частота обновления подсвечивания
    lTimeSleepSeconds = 0.3
    lElementFoundedList = []
    # Ветка поиска в режиме реального времени
    # Сбросить нажатие Ctrl, если оно было
    bool(win32api.GetAsyncKeyState(17))
    # Оптимизация - получить объект для опроса единажды
    # lUIORoot = UIOSelector_Get_UIO(inElementSpecification)
    lX, lY, element = UIO_Get_Current_Element_By_Cursor()

    lFlagLoop = True
    # Пересмотреть проверку процессов - TODO уточнить насколько проверка процессов может быть надежна
    # если не зажат ctrl и он находится внутри одного процесса то поиск внутри окна
    while (lFlagLoop and inElementSpecification[0]['process_id'] == element.process_id) :
        # Проверить, нажата ли клавиша Ctrl (код 17)
        lFlagKeyPressedCtrl = bool(win32api.GetAsyncKeyState(17))
        if inElementSpecification[0]['process_id'] != element.process_id:
            continue
        # Подсветить объект, если мышка наведена над тем объектом, который не подсвечивался в прошлый раз
        if not lFlagKeyPressedCtrl:
            # Получить координаты мыши - ищем внутри окна
            lX, lY, element = UIO_Get_Current_Element_By_Cursor()
            lUIORoot = UIOSelector_Get_UIO(inElementSpecification)
            # Создать карту пикселей и элементов
            #####Внимание! Функция UIOXY_SearchChild_ListDict не написана
            lElementFoundedList = UIOXY_SearchChild_ListDict(lUIORoot, lX, lY)
            # print(lElementFoundedList)
            lElementFounded = lElementFoundedList[-1]["element"]
            # Подсветить объект, если он мышь раньше стояла на другом объекте
            if lGUISearchElementSelected != lElementFounded:
                lGUISearchElementSelected = lElementFounded
                # Доработанная функция отрисовки
                if lElementFounded is not None:
                    UIO_Highlight(lElementFounded)
        # проверить зажат ли ctrl
        elif not bool(win32api.GetAsyncKeyState(17)):
            continue
        else:
            # Была нажата клавиша Ctrl - выйти из цикла
            lFlagLoop = False
            # Заснуть до следующего цикла
            time.sleep(lTimeSleepSeconds)# Вернуть результат поиска

            return lElementFoundedList
    # Если не нашелся element или не успел его обнаружить верни пустой список
    return []


####################################################################################################
# inElementSpecification - UIOSelector
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# old name - AutomationSearchMouseElementHierarchy
def UIOSelector_SearchChildByMouse_UIOTree(inUIOSelector, backend):
    print(inUIOSelector, 'inUIOSelector')
    """
    !!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!

    :param inUIOSelector: UIOSelector of the UI Object
    :return: ?
    """

    lItemInfo = []
    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        # Запустить функцию поиска элемента по мыши
        lElementList = UIOSelector_SearchChildByMouse_UIO(inUIOSelector)
        if len(lElementList) > 0:
            lElement = lElementList[-1]['element']
        else:
            lElement = None
        # Detect backend of the elements
        lFlagIsBackendWin32 = True
        # Если объект имеется (не None), то выполнить построение иерархии
        if lElement is not None:
            if lElement.backend.name == 'uia':
                lFlagIsBackendWin32 = False
            # Циклическое создание дерева
            # while lElement is not None:
            lListIterator = 0
            lItemInfo2 = lItemInfo
            for level_num, lListItem in enumerate(lElementList):
                lElement = lListItem["element"]
                # Продолжать построение иерархии во всех случаях кроме бэк uia & parent() is None
                # if not lFlagIsBackendWin32 and lElement.parent() is None:
                #    lElement = None
                # else:
                # Получить информацию про объект
                lItemInfo2.append(UIOEI_Convert_UIOInfo(lElement.element_info,backend))
                # Дообогатить информацией об индексе ребенка в родительском объекте
                if "index" in lListItem:
                    if lListItem["index"] is not None:
                        lItemInfo2[-1]['ctrl_index'] = lListItem["index"]
                    else:
                        if "ctrl_index" in lListItem:
                            lItemInfo2[-1]['ctrl_index'] = lListItem["ctrl_index"]
                else:
                    if "ctrl_index" in lListItem:
                        lItemInfo2[-1]['ctrl_index'] = lListItem["ctrl_index"]
                # Оборачиваем потомка в массив, потому что у родителя по структуре интерфейса может быть больше одного наследников
                level_number = 'Level ' + str(level_num)
                lItemInfo2[-1][level_number] = []
                lItemInfo2 = lItemInfo2[-1][level_number]
                # Переход на родительский объект
                # lElement = lElement.parent()
                lListIterator = lListIterator + 1
            # Добавить информацию о Backend в первый объект
            lItemInfo[0]["backend"] = lElement.backend.name
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_SearchChildByMouse_UIOTree",
                            "ArgumentList": [inUIOSelector],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lItemInfo = lPIPEResponseDict["Result"]
    # Вернуть результат
    return lItemInfo


####################################################################################################
# inElement- UIO (UI Object)
# old name - PywinautoExtElementCtrlIndexGet
def UIO_GetCtrlIndex_Int(inElement):
    lResult = None
    # Выполнить алгоритм, если есть Element
    if inElement is not None:
        lElementParent = inElement.parent()
        if lElementParent is not None:
            lResult = 0
            lFlagFind = True
            # Получить список потомков
            lElementParentChildrenList = lElementParent.children()
            # Циклический поиск до того момента, пока не упремся в текущий элемент
            while lFlagFind:
                if lResult < len(lElementParentChildrenList):
                    # Прекратить поиск, если элемент был обнаружен
                    if inElement == lElementParentChildrenList[lResult]:
                        lFlagFind = False
                    else:
                        # Прекратить поиски, если итератор вышел за пределы списка
                        if lResult >= len(lElementParentChildrenList):
                            lResult = None
                            lFlagFind = False
                        else:
                            lResult = lResult + 1
                else:
                    lResult = -1
                    lFlagFind = False
    # Вернуть результат
    return lResult


####################################################################################################
# Get the UIO Info list for the selected criteria
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# inSpecificationList - UIOSelector
# old name - PywinautoExtElementsGetInfo
def UIOSelector_Get_UIOInfoList(inUIOSelector, inElement=None):
    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        # Получить родительский объект если на вход ничего не поступило
        lResultList = UIOSelector_Get_UIOList(inUIOSelector, inElement)
        lIterator = 0
        for lItem in lResultList:
            lResultList[lIterator] = UIOEI_Convert_UIOInfo(lResultList[lIterator].element_info)
            lIterator = lIterator + 1
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_Get_UIOInfoList",
                            "ArgumentList": [inUIOSelector, inElement],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lResultList = lPIPEResponseDict["Result"]
    return lResultList


####################################################################################################
# Try to restore (maximize) window, if it's was minimized
# (особенность uia backend - он не может прицепиться к окну, если оно свернуто)
# inSpecificationList - UIOSelector
# old name - PywinautoExtTryToRestore
def UIOSelector_TryRestore_Dict(inSpecificationList):
    """
    Try to restore (maximize) window, if it's minimized. (!IMPORTANT! When use UIA framework minimized windows doesn't appear by the UIOSelector. You need to try restore windows and after that try to get UIO)

    :param inSpecificationList: UIOSelector - List of items, which contains condition attributes
    :return:
    """


    lResult = {}
    try:
        # Подготовка взодного массива
        inControlSpecificationArray = UIOSelector_SearchUIONormalize_UIOSelector(inSpecificationList)
        # Выполнить подключение к объекту. Восстановление необходимо только в бэке win32,
        # так как в uia свернутое окно не распознается
        lRPAApplication = pywinauto.Application(backend="win32")
        lRPAApplication.connect(**inSpecificationList[0])
        lRPAApplication.top_window().restore()
    except Exception:
        True == False
    return lResult


####################################################################################################
# Get the list of the UI object activities
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# inControlSpecificationArray - UIOSelector
# old name - ElementActionGetList
def UIOSelector_Get_UIOActivityList(inUIOSelector):
    """
     Get the list of the UI object activities

     :param inUIOSelector: UIOSelector - List of items, which contains condition attributes
     :return:
     """

    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        # Получить объект
        lObject = UIOSelector_Get_UIO(inUIOSelector)
        lActionList = dir(lObject)
        lResult = dir(lObject)
        # Выполнить чистку списка от неактуальных методов
        for lActionItem in lActionList:
            # Удалить те, которые начинаются на _
            if lActionItem[0] == '_':
                lResult.remove(lActionItem)
            # Удалить те, которые начинаются с символа верхнего регистра
            if lActionItem[0].isupper():
                lResult.remove(lActionItem)
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_Get_UIOActivityList",
                            "ArgumentList": [inUIOSelector],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lResult = lPIPEResponseDict["Result"]
    return lResult


####################################################################################################
# Run the activity in UIO (UI Object)
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# inUIOSelector
# inActionName - UIOActivity (name) from Pywinauto
# old name - ElementRunAction
def UIOSelectorUIOActivity_Run_Dict(inUIOSelector, inActionName, inArgumentList=[], inkwArgumentObject={}):
    """
    Run the activity in UIO (UI Object)

    :param inUIOSelector: UIOSelector - List of items, which contains condition attributes
    :param inActionName: UIOActivity (name) activity name string from Pywinauto
    :param inArgumentList:
    :param inkwArgumentObject:
    :return:
    """


    lResult = {}
    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    # Run activity if SafeOtherProcess is None
    if lSafeOtherProcess is None:
        # Определить объект
        lObject = UIOSelector_Get_UIO(inUIOSelector)
        # Получить метод для вызова
        lFunction = getattr(lObject, inActionName)
        # Выполнить действие
        # Обернуто в безопасную обработку, тк для некоторых объектов метод не работает и может выдавать ошибку типа: NotImplementedError: This method not work properly for WinForms DataGrid, use cells()
        try:
            return lFunction(*inArgumentList, **inkwArgumentObject)
        except Exception as e:
            # Если ошибка возникла на action get_properties
            if inActionName == "get_properties":
                lResult = {}
                # Ручное формирование
                lResult["class_name"] = lObject.class_name()
                lResult["friendly_class_name"] = lObject.friendly_class_name()
                lResult["texts"] = lObject.texts()
                lResult["control_id"] = lObject.control_id()
                lResult["control_count"] = lObject.control_count()
                lResult["automation_id"] = lObject.automation_id()
                return lResult
            else:
                raise e
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelectorUIOActivity_Run_Dict",
                            "ArgumentList": [inUIOSelector, inActionName, inArgumentList, inkwArgumentObject],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lResult = lPIPEResponseDict["Result"]
    return lResult


####################################################################################################
# Get the UIO dict of the attributes
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# old name - ElementGetInfo
def UIOSelector_Get_UIOInfo(inUIOSelector):
    """
    Get the UIO dict of the attributes

    :param inUIOSelector: UIOSelector - List of items, which contains condition attributes
    :return:
    """

    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        # Подготовка входного массива
        inUIOSelector = UIOSelector_SearchUIONormalize_UIOSelector(inUIOSelector)
        # Выполнить идентификацию объектов, если передан массив
        lResultList = [];
        if len(inUIOSelector) > 0:
            # Получить объект
            lTempObject = UIOSelector_Get_UIO(inUIOSelector)
            # Получить инфо объект
            lTempObjectInfo = lTempObject.element_info
            # Добавить информацию об обнаруженом объекте
            lResultList.append(UIOEI_Convert_UIOInfo(lTempObjectInfo))
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_Get_UIOInfo",
                            "ArgumentList": [inUIOSelector],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lResultList = lPIPEResponseDict["Result"]
    return lResultList


####################################################################################################
# Search child UIO by the: Parent UIO, X, Y
# inHierarchyList: [{"index":<>,"element":<>}] - technical argument for internal purpose
# result -List of dict [{"index":<>,"element":<>}] -- list of element hierarchy specifications
# old name - GUISearchElementByRootXY
def UIOXY_SearchChild_ListDict(inRootElement, inX, inY, inHierarchyList=[]):
    # Инициализация результирующего значения
    lResultElement = None
    lResultElementX1 = None
    lResultElementX2 = None
    lResultElementY1 = None
    lResultElementY2 = None
    lResultHierarchyList = [{'index': None, 'element': None}]
    # Получить координаты текущего объекта
    try:
        lRootElementRectX1 = inRootElement.element_info.rectangle.left
        lRootElementRectX2 = inRootElement.element_info.rectangle.right
        lRootElementRectY1 = inRootElement.element_info.rectangle.top
        lRootElementRectY2 = inRootElement.element_info.rectangle.bottom
        # Добавить объект в результирующий, если координаты попадают в него
        if inX >= lRootElementRectX1 and inX <= lRootElementRectX2 and inY >= lRootElementRectY1 and inY <= lRootElementRectY2:
            lResultElement = inRootElement
            lResultElementX1 = lRootElementRectX1
            lResultElementX2 = lRootElementRectX2
            lResultElementY1 = lRootElementRectY1
            lResultElementY2 = lRootElementRectY2
            # Сформировать результирующий обьъект
            lParentHierarchy = inHierarchyList
            if len(lParentHierarchy) == 0:
                lParentHierarchy.append({"index": None, "element": lResultElement})
            else:
                lParentHierarchy[-1]["element"] = lResultElement
            lResultHierarchyList = lParentHierarchy
            # Получить список детей и добавить в карту
            lChildIterator = 0
            for lChildElement in inRootElement.children():
                # Сформировать результирующий массив
                lChildFoundedHierarchyList = lParentHierarchy.copy()
                lChildFoundedHierarchyList.append({'index': lChildIterator})
                lChildFoundedHierarchyList = UIOXY_SearchChild_ListDict(lChildElement, inX, inY,
                                                                        lChildFoundedHierarchyList)
                lChildFoundedElement = lChildFoundedHierarchyList[-1]["element"]
                # Установить обнаруженный элемент, если текущий результат пустой
                if lResultElement is None and lChildFoundedElement is not None:
                    lResultElement = lChildFoundedElement
                    lResultElementX1 = lResultElement.element_info.rectangle.left
                    lResultElementX2 = lResultElement.element_info.rectangle.right
                    lResultElementY1 = lResultElement.element_info.rectangle.top
                    lResultElementY2 = lResultElement.element_info.rectangle.bottom
                    lResultHierarchyList = lChildFoundedHierarchyList
                # Выполнить сверку lChildFoundedElement и lResultElement если оба имеются
                elif lResultElement is not None and lChildFoundedElement is not None:
                    # Правила перезатирания карты, если имеется старый объект
                    # [Накладываемый объект] - НО - ElementNew
                    # [Имеющийся объект] - ИО - ElementOld
                    # 3 типа вхождения объектов
                    # тип 1 - [имеющийся объект] полностью входит в [накладываемый объект] (ИО X1 Y1 >= НО X1 Y1; ИО X2 Y2 <= НО X2 Y2) - не вносить НО в bitmap в эти диапазоны
                    # тип 2 - [имеющийся объект] полностью выходит за пределы [накладываемого объекта] (ИО X1 Y1 < НО X1 Y1; ИО X2 Y2 > НО X2 Y2) - вносить НО в bitmap
                    # тип 3 - [имеющийся объект] частично входит в [накладываемый объект] (все остальные случаи)- вносить НО в bitmap
                    # Получить координаты ИО
                    lChildFoundedElementInfo = lChildFoundedElement.element_info
                    # lElementNew = inElement
                    lChildFoundedElementX1 = lChildFoundedElementInfo.rectangle.left
                    lChildFoundedElementX2 = lChildFoundedElementInfo.rectangle.right
                    lChildFoundedElementY1 = lChildFoundedElementInfo.rectangle.top
                    lChildFoundedElementY2 = lChildFoundedElementInfo.rectangle.bottom
                    # Проверка вхождения по типу 1
                    if (lResultElementX1 >= lChildFoundedElementX1) and (
                            lResultElementY1 >= lChildFoundedElementY1) and (
                            lResultElementX2 <= lChildFoundedElementX2) and (
                            lResultElementY2 <= lChildFoundedElementY2):
                        False == True
                    # Проверка вхождения по типу 3
                    elif (lResultElementX1 < lChildFoundedElementX1) and (
                            lResultElementY1 < lChildFoundedElementY1) and (
                            lResultElementX2 > lChildFoundedElementX2) and (lResultElementY2 > lChildFoundedElementY2):
                        lResultElement = lChildFoundedElement
                        lResultElementX1 = lChildFoundedElementX1
                        lResultElementX2 = lChildFoundedElementX2
                        lResultElementY1 = lChildFoundedElementY1
                        lResultElementY2 = lChildFoundedElementY2
                        lResultHierarchyList = lChildFoundedHierarchyList
                    # Проверка вхождения по типу 2
                    else:
                        lResultElement = lChildFoundedElement
                        lResultElementX1 = lChildFoundedElementX1
                        lResultElementX2 = lChildFoundedElementX2
                        lResultElementY1 = lChildFoundedElementY1
                        lResultElementY2 = lChildFoundedElementY2
                        lResultHierarchyList = lChildFoundedHierarchyList
                lChildIterator = lChildIterator + 1
    except Exception as e:
        False == False
    return lResultHierarchyList


###################################################################################################
# Get list of child UIO's by Parent UIOSelector
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# inControlSpecificationArray- UIOSelector
# old name - ElementGetChildElementList
def UIOSelector_GetChildList_UIOList(inUIOSelector=[], inBackend=mDefaultPywinautoBackend):
    """
    Get list of child UIO's by the parent UIOSelector

    :param inUIOSelector: UIOSelector - List of items, which contains condition attributes
    :param inBackend: "win32" or "uia"
    :return:
    """
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        # Подготовка входного массива
        inUIOSelector = UIOSelector_SearchUIONormalize_UIOSelector(inUIOSelector)
        # Выполнить идентификацию объектов, если передан массив
        lResultList = []
        # ctypes.windll.user32.MessageBoxW(0, str(inControlSpecificationArray), "Your title", 1)
        if len(inUIOSelector) > 0:
            # Получить объект
            lTempObject = UIOSelector_Get_UIO(inUIOSelector)
            # Получить список дочерних объектов
            lTempChildList = lTempObject.children()
            lIterator = 0
            # Подготовить результирующий объект
            for lChild in lTempChildList:
                lTempObjectInfo = lChild.element_info
                # Добавить информацию об обнаруженом объекте
                lObjectInfoItem = UIOEI_Convert_UIOInfo(lTempObjectInfo, backend=inBackend)
                # Итератор внутри объекта (для точной идентификации)
                lObjectInfoItem['ctrl_index'] = lIterator
                lResultList.append(lObjectInfoItem)
                # Инкремент счетчика
                lIterator = lIterator + 1
        else:
            lResultList = BackendStr_GetTopLevelList_UIOInfo(inBackend)
            # Установка бэк-енда на первый элемент
            for lItem in lResultList:
                lItem["backend"] = inBackend
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_GetChildList_UIOList",
                            "ArgumentList": [inUIOSelector, inBackend],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            lResultList = lPIPEResponseDict["Result"]
    return lResultList


####################################################################################################
# Подготовить массив для обращшения к поиску элемементов
# inControlSpecificationArray - UIOSelector (can be dirty)
# old name 1 - ElementSpecificationArraySearchPrepare
# old name 2 - ElementSpecificationListNormalize
def UIOSelector_SearchUIONormalize_UIOSelector(inControlSpecificationArray):
    lResult = []
    # Циклический обход
    for lSpecificationItem in inControlSpecificationArray:
        lSpecificationItemNew = lSpecificationItem.copy()
        # Перебор всех элементов
        for lItemKey, lItemValue in lSpecificationItem.items():
            # Флаг удаления атрибута
            lFlagRemoveAttribute = False
            #############################
            # Если является вложенным словарем - удалить
            if type(lItemValue) is dict:
                lFlagRemoveAttribute = True
            # Является типом None
            if lItemValue is None:
                lFlagRemoveAttribute = True
            # Проверка допустимого ключевого слова
            if (
                    lItemKey == "class_name" or
                    lItemKey == "class_name_re" or
                    lItemKey == "parent" or
                    lItemKey == "process" or
                    lItemKey == "title" or
                    lItemKey == "title_re" or
                    lItemKey == "top_level_only" or
                    lItemKey == "visible_only" or
                    lItemKey == "enabled_only" or
                    lItemKey == "best_match" or
                    lItemKey == "handle" or
                    lItemKey == "ctrl_index" or
                    lItemKey == "found_index" or
                    lItemKey == "predicate_func" or
                    lItemKey == "active_only" or
                    lItemKey == "control_id" or
                    lItemKey == "control_type" or
                    lItemKey == "auto_id" or
                    lItemKey == "framework_id" or
                    lItemKey == "backend"):
                True == True
            else:
                lFlagRemoveAttribute = True

            #############################
            # Конструкция по удалению ключа из словаря
            if lFlagRemoveAttribute:
                lSpecificationItemNew.pop(lItemKey)
        # Проверит наличие ctrl_index - если он есть, то удалить control_id и control_type из-за того, что они мешают друг другу
        if 'ctrl_index' in lSpecificationItemNew:
            if "control_id" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_id")
            if "control_type" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_type")
        # Проверить наличие handle - если он есть, то удалить process, control_id и control_type из-за того, что они мешают друг другу
        if 'handle' in lSpecificationItemNew:
            if "control_id" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_id")
            if "control_type" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_type")
            if "process" in lSpecificationItemNew:
                lSpecificationItemNew.pop("process")
        # Иначе Проверить наличие process - если он есть, то удалить тк он нужен только при подключении к процессу
        if 'process' in lSpecificationItemNew:
            lSpecificationItemNew.pop("process")
        # Добавить строку в результирующий массив
        lResult.append(lSpecificationItemNew)
    # Вернуть результат
    return lResult


####################################################################################################
# Подготовить массив для обращшения к поиску процесса (отличается от поиска элемента, тк данная функция нужна для нормализации спецификации для подключения к процессу с окнами)
# inControlSpecificationArray - UIOSelector (can be dirty)
# old name 1 - ElementSpecificationArraySearchPrepare
# old name 2 - ElementSpecificationListNormalize
def UIOSelector_SearchProcessNormalize_UIOSelector(inControlSpecificationArray):
    lResult = []
    # Циклический обход
    for lSpecificationItem in inControlSpecificationArray:
        lSpecificationItemNew = lSpecificationItem.copy()
        # Перебор всех элементов
        for lItemKey, lItemValue in lSpecificationItem.items():
            # Флаг удаления атрибута
            lFlagRemoveAttribute = False
            #############################
            # Если является вложенным словарем - удалить
            if type(lItemValue) is dict:
                lFlagRemoveAttribute = True
            # Является типом None
            if lItemValue is None:
                lFlagRemoveAttribute = True
            # Проверка допустимого ключевого слова
            if (
                    lItemKey == "class_name" or
                    lItemKey == "class_name_re" or
                    lItemKey == "parent" or
                    lItemKey == "process" or
                    lItemKey == "title" or
                    lItemKey == "title_re" or
                    lItemKey == "top_level_only" or
                    lItemKey == "visible_only" or
                    lItemKey == "enabled_only" or
                    lItemKey == "best_match" or
                    lItemKey == "handle" or
                    lItemKey == "ctrl_index" or
                    lItemKey == "found_index" or
                    lItemKey == "predicate_func" or
                    lItemKey == "active_only" or
                    lItemKey == "control_id" or
                    lItemKey == "control_type" or
                    lItemKey == "auto_id" or
                    lItemKey == "framework_id" or
                    lItemKey == "backend"):
                True == True
            else:
                lFlagRemoveAttribute = True

            #############################
            # Конструкция по удалению ключа из словаря
            if lFlagRemoveAttribute:
                lSpecificationItemNew.pop(lItemKey)
        # Проверит наличие ctrl_index - если он есть, то удалить control_id и control_type из-за того, что они мешают друг другу
        if 'ctrl_index' in lSpecificationItemNew:
            if "control_id" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_id")
            if "control_type" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_type")
        # Проверить наличие handle - если он есть, то удалить process, control_id и control_type из-за того, что они мешают друг другу
        if 'handle' in lSpecificationItemNew:
            if "control_id" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_id")
            if "control_type" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_type")
            if "process" in lSpecificationItemNew:
                lSpecificationItemNew.pop("process")
        # Иначе Проверить наличие process - если он есть, то удалить title, control_id и control_type из-за того, что они мешают друг другу
        elif 'process' in lSpecificationItemNew:
            if "control_id" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_id")
            if "control_type" in lSpecificationItemNew:
                lSpecificationItemNew.pop("control_type")
            if "title" in lSpecificationItemNew:
                lSpecificationItemNew.pop("title")
        # Добавить строку в результирующий массив
        lResult.append(lSpecificationItemNew)
    # Вернуть результат
    return lResult


####################################################################################################
# Transfer UI object element info (pywinauto) to UIOInfo (dict of attributes)
# inElementInfo - UIOEI
# old name - ElementInfoExportObject
def UIOEI_Convert_UIOInfo(inElementInfo, backend):
    # Подготовить выходную структуру данных
    lResult = {"title": None, "rich_text": None, "process_id": None, "process": None, "handle": None,
               "class_name": None, "control_type": None, "control_id": None,
               "rectangle": {"left": None, "top": None, "right": None, "bottom": None}, 'runtime_id': None, 'backend': backend}
    # Проверка name
    try:
        lResult['title'] = inElementInfo.name
    except Exception as e:
        True == False
    # Проверка rich_text
    try:
        lResult['rich_text'] = inElementInfo.rich_text
    except Exception as e:
        True == False
    # Проверка process_id
    try:
        lResult['process_id'] = inElementInfo.process_id
        lResult['process'] = inElementInfo.process_id
    except Exception as e:
        True == False
    # Проверка handle
    try:
        lResult['handle'] = inElementInfo.handle
    except Exception as e:
        True == False
    # Проверка class_name
    try:
        lResult['class_name'] = inElementInfo.class_name
    except Exception as e:
        True == False
    # Проверка control_type
    try:
        lResult['control_type'] = inElementInfo.control_type
    except Exception as e:
        True == False
    # Проверка control_id
    try:
        if inElementInfo.control_id != 0:
            lResult['control_id'] = inElementInfo.control_id
    except Exception as e:
        True == False
    # Проверка rectangle left
    try:
        lResult['rectangle']['left'] = inElementInfo.rectangle.left
    except Exception as e:
        True == False
    # Проверка rectangle right
    try:
        lResult['rectangle']['right'] = inElementInfo.rectangle.right
    except Exception as e:
        True == False
    # Проверка rectangle top
    try:
        lResult['rectangle']['top'] = inElementInfo.rectangle.top
    except Exception as e:
        True == False
    # Проверка rectangle bottom
    try:
        lResult['rectangle']['bottom'] = inElementInfo.rectangle.bottom
    except Exception as e:
        True == False
    # Проверка runtime_id
    try:
        lResult['runtime_id'] = inElementInfo.runtime_id
    except Exception as e:
        True == False
    # Вернуть результат
    return lResult


###################################################################################################
# Get list of top level
# old name - GetRootElementList
def BackendStr_GetTopLevelList_UIOInfo(inBackend=mDefaultPywinautoBackend):
    # Получить список объектов
    lResultList = pywinauto.findwindows.find_elements(top_level_only=True, backend=inBackend)
    lResultList2 = []
    for lI in lResultList:
        lTempObjectInfo = lI
        lResultList2.append(UIOEI_Convert_UIOInfo(lI, backend=inBackend));
    return lResultList2


###################################################################################################
# Highlight the UI object
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# old name - ElementDrawOutlineNew
def UIOSelector_Highlight(inUIOSelector):
    """
    Highlight (draw outline) the element (in app) by the UIO selector.

    :param inUIOSelector: UIOSelector - List of items, which contains condition attributes
    :return:
    """

    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        UIO_Highlight(UIOSelector_Get_UIO(inUIOSelector))
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_Highlight",
                            "ArgumentList": [inUIOSelector],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            return lPIPEResponseDict["Result"]
    return True


###################################################################################################
# inSpecificationArray - UIOSelector
# !!!!!Safe call is included (you can set activity and UIDesktop will choose the bitness and return the result)!!!!!
# old name - ElementDrawOutlineNewFocus
def UIOSelector_FocusHighlight(inUIOSelector):
    """
    Set focus and highlight (draw outline) the element (in app) by the UIO selector.

    :param inUIOSelector: UIOSelector - List of items, which contains condition attributes
    :return:
    """
    # Check the bitness
    lSafeOtherProcess = UIOSelector_SafeOtherGet_Process(inUIOSelector)
    if lSafeOtherProcess is None:
        UIO_FocusHighlight(UIOSelector_Get_UIO(inUIOSelector))
    else:
        # Run function from other process with help of PIPE
        lPIPEResuestDict = {"ModuleName": "UIDesktop", "ActivityName": "UIOSelector_FocusHighlight",
                            "ArgumentList": [inUIOSelector],
                            "ArgumentDict": {}}
        # Отправить запрос в дочерний процесс, который отвечает за работу с Windows окнами
        ProcessCommunicator.ProcessChildSendObject(lSafeOtherProcess, lPIPEResuestDict)
        # Get answer from child process
        lPIPEResponseDict = ProcessCommunicator.ProcessChildReadWaitObject(lSafeOtherProcess)
        if lPIPEResponseDict["ErrorFlag"]:
            raise Exception(
                f"Exception was occured in child process (message): {lPIPEResponseDict['ErrorMessage']}, (traceback): {lPIPEResponseDict['ErrorTraceback']}")
        else:
            return lPIPEResponseDict["Result"]
    return True


###################################################################################################
# old name - draw_outline_new
def UIO_Highlight(lWrapperObject, colour='green', thickness=2, fill=win32defines.BS_NULL, rect=None,
                  inFlagSetFocus=False):
    if lWrapperObject is not None:
        """
        Draw an outline around the window.
        * **colour** can be either an integer or one of 'red', 'green', 'blue'
        (default 'green')
        * **thickness** thickness of rectangle (default 2)
        * **fill** how to fill in the rectangle (default BS_NULL)
        * **rect** the coordinates of the rectangle to draw (defaults to
          the rectangle of the control)
        """
        if inFlagSetFocus:
            # Установить фокус на объект, чтобы было видно выделение
            lWrapperObject.set_focus()
            time.sleep(0.5)
        # don't draw if dialog is not visible
        # if not lWrapperObject.is_visible():
        #    return
        colours = {
            "green": 0x00ff00,
            "blue": 0xff0000,
            "red": 0x0000ff,
        }
        # if it's a known colour
        if colour in colours:
            colour = colours[colour]
        if rect is None:
            rect = lWrapperObject.rectangle()
        # create the pen(outline)
        pen_handle = win32functions.CreatePen(
            win32defines.PS_SOLID, thickness, colour)
        # create the brush (inside)
        brush = win32structures.LOGBRUSH()
        brush.lbStyle = fill
        brush.lbHatch = win32defines.HS_DIAGCROSS
        brush_handle = win32functions.CreateBrushIndirect(ctypes.byref(brush))
        # get the Device Context
        dc = win32functions.CreateDC("DISPLAY", None, None, None)
        # push our objects into it
        win32functions.SelectObject(dc, brush_handle)
        win32functions.SelectObject(dc, pen_handle)
        # draw the rectangle to the DC
        win32functions.Rectangle(
            dc, rect.left, rect.top, rect.right, rect.bottom)
        # Delete the brush and pen we created
        win32functions.DeleteObject(brush_handle)
        win32functions.DeleteObject(pen_handle)
        # delete the Display context that we created
        win32functions.DeleteDC(dc)


###################################################################################################
# Аналог подсвечивания + установка фокуса
# old name - draw_outline_new_focus
def UIO_FocusHighlight(lWrapperObject, colour='green', thickness=2, fill=win32defines.BS_NULL, rect=None):
    UIO_Highlight(lWrapperObject, 'green', 2, win32defines.BS_NULL, None, True)


def UIO_Get_Current_Element_By_Cursor():
    """ :return lX, lY, element
    Get current coordinates of mouse and using pywinauto captures the element

    :arg: lX - X-coordinate
          lY - Y-coordinate
    element - UIAElementInfo with data about element
    """
    (lX, lY) = win32api.GetCursorPos()
    # получить контроль над окном через координаты
    elem = pywinauto.uia_defines.IUIA().iuia.ElementFromPoint(tagPOINT(lX, lY))
    element = pywinauto.uia_element_info.UIAElementInfo(elem)
    return lX, lY, element

# Определить разрядность процесса
lProcessBitnessStr = str(struct.calcsize("P") * 8)


