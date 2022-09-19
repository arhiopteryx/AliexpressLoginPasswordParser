import shelve
from time import sleep
import random
from urllib import request
import requests
import pandas as pd


from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

from selenium.webdriver.common.action_chains import ActionChains


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from bs4 import BeautifulSoup as bs

#названия полей для excel
EXCEL_LOGINS_NAME = 'Login'
EXCEL_PASSWORD_NAME = 'Password'



dataList = []   #Список данных пропарсенных на аккаунте
errorsOrder = []    #список ошибочных аккаунтов

#список аккаунтов

excel = pd.read_excel('Accounts.xlsx')
logins = excel[EXCEL_LOGINS_NAME].tolist()
passwords = excel[EXCEL_PASSWORD_NAME].tolist()

dictAccounts = dict(zip(logins, passwords))


#создаем объект браузера
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36")
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option('useAutomationExtension', False)
#options.set_headless(True)
browser = webdriver.Chrome(options=options)

#текущий номер аккаунта(для отладки)
curAccNumber = 0

#цикл прохода по каждому аккаунту
for loginAccount in dictAccounts:

    #вывести счетчик аккаунтов
    curAccNumber = curAccNumber + 1
    print('account   ' + str(curAccNumber) + ' / ' + str(len(logins)))

    #цикл для успешного входа на аккаунт. Даеться 3 попытки, иначе заноситься в базу, как не валид
    for attempt in range(3):
        
        print('Попытка №' + str(attempt+1))
        
        #переходим по ссылке входа и сразу попадаем на страницу заказов
        #browser.get('https://login.aliexpress.com/?returnUrl=https://trade.aliexpress.com/orderList.htm')        
        browser.get('https://login.aliexpress.com/setCommonCookie.htm?currency=USD&region=UA&bLocale=en_US&site=glo&return=https://trade.aliexpress.com/orderList.htm')
        
        #если не полностью вышло с акка
        try:        
            submit = browser.find_element(By.CLASS_NAME, 'fm-link')
            submit.click()
            sleep(1)
        except:
            print()

        try:        
            #вводим логин
            username = browser.find_element(By.NAME, "fm-login-id")
            username.send_keys(loginAccount)  
        except:
            print()

  
        
        #пытаемся вызвать слайдер верификации кликнув на корневой элемент
        try:        
            submit = browser.find_element(By.ID, 'root')
            submit.click()
            sleep(1)
        except:
            print()

        try:        
            #вводим пароль
            password = browser.find_element(By.NAME, "fm-login-password")
            password.send_keys(dictAccounts[loginAccount])

            #кликаем по кнопке входа
            submit = browser.find_element(By.CLASS_NAME, 'login-submit')
            submit.click()

        except:
            print()

        #ждем чтобы появился слайдер верификации
        sleep(3)

        #пытаемся провести слайдер, если он есть    
        try:     
            #frame_0 = WebDriverWait(browser, 10).until(expected_conditions.presence_of_element_located((By.ID, "baxia-dialog-content")))

            #переходим на фрейм слайдера
            frame_0 = browser.find_element(By.ID, 'baxia-dialog-content')
            browser.switch_to.frame(frame_0)

            #находим элементы ползунок и линия слайдера
            slider = browser.find_element(By.ID, "nc_1_n1z")       
            container = browser.find_element(By.ID, "nc_1__scale_text")   

            #пытаемся потянуть слайдер
            move = ActionChains(browser)
            move.click_and_hold(slider)
            move.perform()
            countBit = 4

            #перетягиваем по чу-чуть, чтобы эмулировать человека
            for i in range(countBit):
                move.move_by_offset(container.size['width']/(countBit*1.0), 0)
                sleep(0.01)
                move.perform()
           

            #выход с фрейма
            browser.switch_to.default_content()  
            #опять кликаем кнопку входа
            submit = browser.find_element(By.CLASS_NAME, 'login-submit')
            submit.click()
            
        except:
            print("Слайдер не найдено или ошибка слайдера")
        
        #ждем 3 секунды
        sleep(3)

        #пытемся найти на странице надпись order чтобы проверить, вошли ли мы на аккаунт
        html = browser.page_source
        soup = bs(html, "lxml")
        if soup.find_all('tbody', class_='order-item-wraper') or soup.find_all('div', class_='order-item'):
            print('Удачный вход')
            break
        else:
            print('Ну удалось войти на аккаунт')
            if attempt == 2:
                print('Акаунт   ' + str(loginAccount) + ' ошибочный')
                errorsOrder.append([loginAccount, dictAccounts[loginAccount]])
            continue

    if soup.find_all('tbody', class_='order-item-wraper'):
        #пытаемся спарсить данные заказов
        try:
            ordersValue = soup.find_all('tbody', class_='order-item-wraper')
            i = 0
            for order in ordersValue:
                orderStatus = order.find('td', class_='order-status').find('span', class_='f-left').text.strip()
                orderName = order.find('a',  class_= 'baobei-name').text.strip()
                orderPrice = order.find('p',  class_= 'amount-num').text.strip()

                trackCode = ''

                if orderStatus == 'Awaiting delivery':
                    trackCodeLink = 'https://trade.aliexpress.com/' + order.find('a', class_='view-detail-link').get('href')
                    browser.get(trackCodeLink)
                    sleep(2)
                    soup2 = bs(browser.page_source, "lxml")  
                    trackCode = soup2.find('td', class_='no').find('div').text.strip()

                dataList.append([loginAccount, dictAccounts[loginAccount], orderStatus, orderName, orderPrice, i, trackCode])
                i = i+1
        except:
            print('Ошибка считывания с аккаунта')
            dataList.append([loginAccount, dictAccounts[loginAccount], 'Error', 'Error', 'Error', 'Error'])

    if soup.find_all('div', class_='order-item'):
        #пытаемся спарсить данные заказов
        try:
            ordersValue = soup.find_all('div', class_='order-item')
            i = 0
            for order in ordersValue:
                orderStatus = order.find('span', class_='order-item-header-status-text').text.strip()
                orderName = order.find('div',  class_= 'order-item-content-info-name').find('span').text.strip()
                orderPrice = order.find('span',  class_= 'order-item-content-opt-price-total').text.strip()

                trackCode = ''

                if orderStatus == 'Awaiting delivery':
                    trackCodeLink = "https:" + order.find('a', class_='order-item-btn').get('href')
                    #print(trackCodeLink)
                    browser.get(trackCodeLink)
                    sleep(2)
                    soup2 = bs(browser.page_source, "lxml")  
                    trackCode = soup2.find('div', class_='tracking-no').find('span').text.strip()

                dataList.append([loginAccount, dictAccounts[loginAccount], orderStatus, orderName, orderPrice, i, trackCode])
                i = i+1
        except:
            print('Ошибка считывания с аккаунта')
            dataList.append([loginAccount, dictAccounts[loginAccount], 'Error', 'Error', 'Error', 'Error'])

    #выходм с аккаунта
    browser.get('https://login.aliexpress.com/xman/xlogout.htm')

#список данных с базы
lastDataList = []

#открываем базу
try:
	shalveData = shelve.open('database')
	lastDataList = shalveData['data']
	shalveData.close()
except:
    print('Видимо первый запуск')

#заполняем список изменений
changedData = []
for lastData in lastDataList:
    for curData in dataList:
        if lastData[0] == curData[0] and lastData[5] == curData[5]:     #если логины и идентификаторы совпадают
            if lastData[2] != curData[2]:       #если статусы заказов не совпадают
                changedData.append([lastData[0], lastData[1], lastData[2], curData[2], curData[3], curData[4], curData[6]])

#данные для заполнения таблицы
dfLogin = []
dfPassword = []
dfStatus = []
dfName = []
dfPrice = []
dfTrackCode = []

for curData in dataList:        
    dfLogin.append(curData[0])
    dfPassword.append(curData[1])
    dfStatus.append(curData[2])
    dfName.append(curData[3])
    dfPrice.append(curData[4])
    dfTrackCode.append(curData[6])

df = pd.DataFrame({'Логин': dfLogin,
                   'Пароль': dfPassword,
                   'Статус': dfStatus,
                   'Имя': dfName,
                   'Цена': dfPrice,
                   'Трек': dfTrackCode})

df.to_excel('Orders_Data.xlsx', sheet_name='Данные', index=False)


#данные для заполнения таблицы
dfLogin = []
dfPassword = []
dfOldStatus = []
dfNewStatus = []
dfName = []
dfPrice = []
dfTrackCode = []

for change in changedData:        
    dfLogin.append(change[0])
    dfPassword.append(change[1])
    dfOldStatus.append(change[2])
    dfNewStatus.append(change[3])
    dfName.append(change[4])
    dfPrice.append(change[5])
    dfTrackCode.append(change[6])

df = pd.DataFrame({'Логин': dfLogin,
                   'Пароль': dfPassword,
                   'Статус старый': dfOldStatus,
                   'Статус новый': dfNewStatus,
                   'Имя': dfName,
                   'Цена': dfPrice,
                   'Трек': dfTrackCode})

df.to_excel('Changed_data.xlsx', sheet_name='Данные', index=False)

#данные для заполнения таблицы
dfLogin = []
dfPassword = []

for account in errorsOrder:        
    dfLogin.append(account[0])
    dfPassword.append(account[1])

df = pd.DataFrame({'Логин': dfLogin,
                   'Пароль': dfPassword})

df.to_excel('Error_data.xlsx', sheet_name='Данные', index=False)

#изменение базы данных
shalveData = shelve.open('database')
shalveData['data'] = dataList
shalveData.close()
