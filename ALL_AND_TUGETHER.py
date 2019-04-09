import imaplib
import hashlib
import getpass
import email
import email.message
import time
import os.path
import subprocess
import re
import sys
import http
import gspread
import email
import smtplib
import requests, bs4
from GitHubAPI import GithubAPI
from email.mime.text import MIMEText # Модуль простого текстового сообщения
from email.header import Header as mkh # Функция кодирования заголовков для письма
from email.mime.multipart import MIMEMultipart # Модуль формирования сообщений из нескольких частей
from oauth2client.service_account import ServiceAccountCredentials
 
# ----------------------------------------------НАЧАЛО ФУНКЦИЙ --------------------
def send_mail(_email_to, _body="", _str_subject='Автоматический ответ системы приёма лабораторных работ'):
    # если надо отправить нескольким адресатам то [adr1,adr2...]
    # объяснение на http://qaru.site/questions/62570/mail-multipartalternative-vs-multipartmixed
    # https://www.programcreek.com/python/example/53141/email.MIMEMultipart.MIMEMultipart
    #http://qaru.site/questions/2280631/how-to-send-a-email-body-part-through-mimemultipart
    _result='OK'
    _msg = MIMEMultipart('alternative')
    _msg['Subject'] = mkh(_str_subject, 'UTF-8')
    _msg['From'] = email_from
    _msg['To'] = _email_to
    _text = _body
    _html='<div>'+_body+'</div>'

    # Record the MIME types of both parts - text/plain and text/html.
    _part1 = MIMEText(_text, 'plain')
    _part2 = MIMEText(_html, 'html') # не будем использовать

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    _msg.attach(_part1)
    _msg.attach(_part2)  # это для HTML не будем использовать

    try:
        server_mail.sendmail(email_from, _email_to, _msg.as_string())
    except:
        _result='NO'
        
    return _result


def html_to_str(body):
    return body.replace(b'<div>',b'').split(b'</div>')

### получить тело письма типа TEXT (не надо HTML) если multipart то тело письма из двух частей text, html
def get_first_text_block(email_message_instance):
    maintype = email_message_instance.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message_instance.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload(decode=True)
    elif maintype == 'text':
        return email_message_instance.get_payload(decode=True)

def get_body_decod(message_mail):
    _typ2, _data2 = imap.fetch(message_mail, 'RFC822')
    _add_from=''
    _list_a=['','','']
    if _typ2=='OK':
        try:
            _msg = email.message_from_string(_data2[0][1])  # извлечь письмо
        except TypeError:
            _msg = email.message_from_bytes(_data2[0][1])
        try:
            _add_from = email.utils.parseaddr(_msg['From'])[1] # извлечь адрес от кого письмо
        except TypeError:
            _add_from = _msg['From']
        
        # проверка заголовка
        if _msg['Subject']=='OS':   # если заголовок OS
            print('Subject ',_msg['Subject'],_msg.get_charsets()) # для отладки
            try:
                _type_code=_msg.get_charsets()[1]  # вернуть кодировку для расшифровки тела письма (там 3 элемента беру 2, может не очень правильно)
            except:
                _type_code=_msg.get_charsets()[0]  # вернуть кодировку для расшифровки тела письма (там 3 элемента беру 2, может не очень правильно)
           
            _list_b=get_first_text_block(_msg)
            _list_b=_list_b.split(b'\n')  # разбор строк по символу \n  split(b'\n')-Разделить на список по кодам 10,13.
            #print('list_b ',_list_b)
            if _list_b[0][0:5]==b'<div>':
                _list_b=html_to_str(_list_b[0])
            _i=0
            for _s in _list_b:
                try:
                    _s2=_s.decode(_type_code)  # декодировать из набра байт в строку ! с кодировкой полученной в начале процедуры
                except:
                    _s2=''  # если была ошибка по строка пустая
                if len(_s)>0:
                    _list_a[_i]=_s2.replace('\r','').strip() # удалить символ '\r' и пробелы в начале и в конце строки
                    if _i==2:  # нужно только первых 3 не путых строки
                        break
                    else:
                        _i=_i+1
        else:
            _typ2='NO' # не тот заголовок

    _group, _fio, _link = _list_a
    return _typ2, _add_from, _group, _fio, _link  # вернуть список строк (3)


def whats_variants(num_lab,n_stud):
        num_var=-1
        if num_lab==1:
                n_col=12
                num_var=n_stud%n_col
                if num_var==0:
                        num_var=n_col
        elif num_lab==2:
                n_col=20
                num_var=(n_stud+5)%n_col
                if num_var==0:
                        num_var=n_col
        return num_var
#-----------------------------------------------------------------------#
#---------------------- НАЧАЛО ГЛАВНОЙ ПРОГРАММЫ -=---------------------#
#-----------------------------------------------------------------------#
server = "imap.yandex.ru"
port = "993"
login = "login"
password = "password"
 
#box = poplib.IMAP4(server, port)
imap = imaplib.IMAP4_SSL(server, port)
imap.login(login, password)
imap.select() # выбираем папку, по умолчанию - INBOX

email_from = "SUAI.lab@yandex.ru"
server_mail = smtplib.SMTP_SSL('smtp.yandex.ru:465')
server_mail.ehlo()
server_mail.login(login, password)

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('OS-practic.json', scope)
conn = gspread.authorize(creds)

# инициализация github (token github, token vearon)
github_api = GithubAPI('7547080a56d95762954b919f6005ba125f1b2a61', 'v2.7w5hnu6pmhkm1rpfesuq', 'suai-os-2019')

# None здесь говорит о том, что нам всё равно, в какой кодировке искать письма
# ALL - искать все письма
# search(None, 'FROM', '"LDJ"') или search(None, '(FROM "LDJ")') - искать письма со строкой LDJ в поле From
typ, data = imap.search(None, 'ALL') # ищем письма
list_email= data[0].split()
print('')
print( 'typ=', typ)
print('')
print('data= ', list_email)
print('')
print('Начало разбора писем')
print('')    
#-----------------------------------------------------------------------------------------
#                          перебор всех полученных писем
#-----------------------------------------------------------------------------------------
for current_index_email in list_email:

    ## -------------- получение письма и его разбор ------------------------------------------------
    typ, email_stud, group_name, stud_fio, repozit = get_body_decod(current_index_email)   #Магия
    if typ=='OK':
        print('')
        print('FOR list_email ----', repozit)
        print('Email  ', email_stud, 'Группа ', group_name, 'ФИО ', stud_fio, 'Ссылка ', repozit)
        _l=repozit.replace('https://github.com/','').split('/')
        organization=_l[0]
        name=_l[1]
        print()
        num=int(name.split('-')[1].replace('task',''))
        print('Organization ', organization,' Никнэйм ',  name, ' номер лабы ',num)

    else:
        # не смогла получить письмо ( не знаю что делать )
        continue

    ## -------------- конец получение письма и его разбор ------------------------------------------------
    ## -------------- работа с google ------------------------------------------------

    """ получить доступ к нужной странице """
    flag_error=0
    try:
       worksheet = conn.open("Operation systems").worksheet(group_name)
    except:
        # ERROR вызов процедуры отправки письма с этим сообщением
        send_mail(email_stud, 'Нет группы '+group_name, 'Ошибка группы')
        flag_error=1

    # пришлось сделать в IF так как нельзя выполнять continue в except
    if flag_error==1: continue

    """ прочитала список фамилий col_value """
    #print('1 номер страницы группы ',group_name)
    list_fio=worksheet.col_values(2)[2:]

    if stud_fio in list_fio:
        #print('2 студент в группе ',group_name, ' ФИО ',stud_fio, ' номер (0..n)=', list_fio.index(stud_fio)-2)
        number_row=list_fio.index(stud_fio)+3
    else:
        # ERROR вызов процедуры отправки письма с этим сообщением
        send_mail(email_stud, 'Нет такого студента '+stud_fio+ 'в группе '+group_name, 'Ошибка ФИО')
        continue
    ## -------------- конец работы с google ------------------------------------------------
    
    ## -------------- разбор ссылки ------------------------------------------------
    """вычисление № лабораторной лаботы """
    number_lab=num
    #print ('3 лабораторная работа ', number_lab, ' никнэйм студента:', name)
    number_col=int(number_lab-1)*3+13
    worksheet.update_cell(number_row, number_col, repozit) # запись ссылки на лабу в таблицу гугла
    # print('ячейка row=', number_row, ' col=', number_col, ' на странице ', group_name, ' GOOGLE таблицы, успешно обновлена на ', repozit)
    _github=github_api.successful_commit_date(organization, number_lab, name) # проверка даты выполнения лабы 
    try:
        numvar=_github[1]
        data_comite=_github[0]
    except:
        print('работа не выполнена')
        numvar=-1
    if numvar==-1:
        continue
    print('GITHUB LABS ', data_comite, ' ВАРИАНТ ', numvar, ' в гугле ',number_row-2)
    need_number=whats_variants(number_lab, number_row-2)
    if data_comite is not None and (numvar==need_number):
        #print(data_comite, numvar, number_row-3)
        worksheet.update_cell(number_row, number_col+1, data_comite) # запись даты выполнения лабы
        print('ячейка row=', number_row, ' col=', number_col, ' на странице ', group_name, ' GOOGLE таблицы, успешно обновлена на ', data_comite)
    ## -------------- конец разбор ссылки ------------------------------------------------

#-----------------------------------------------------------------------------------------

# выход из google
#выход из почты
server_mail.quit()
imap.close()
imap.logout()
# выход из программы
sys.exit()
