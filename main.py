import email
import json
import os

from appveyor_client import AppVeyorClient
from github_client import GithubAPI
from google_spreadsheet import SpreadSheet
from parsers import parse_data_from_email, get_variant_number_from_travis_log
from travis_client import TravisClient
from yandex_mail import YandexMail


def get_data_from_email(imap, message_mail):
    status, data = imap.fetch(message_mail, 'RFC822')

    email_from = None
    group_name = None
    student_name = None
    repo_url = None

    if status == 'OK':
        try:
            message = email.message_from_string(data[0][1])  # извлечь письмо
        except TypeError:
            message = email.message_from_bytes(data[0][1])

        try:
            email_from = email.utils.parseaddr(message['From'])[1]  # извлечь адрес от кого письмо
        except TypeError:
            email_from = message['From']

        # проверка заголовка
        if message['Subject'] == 'OS':
            group_name, student_name, repo_url = parse_data_from_email(message)
        else:
            status = 'NO'  # не тот заголовок

    return status, email_from, group_name, student_name, repo_url


def whats_variants(num_lab, n_stud):
    num_var = -1
    if num_lab == 1:
        n_col = 12
        num_var = n_stud % n_col
        if num_var == 0:
            num_var = n_col
    elif num_lab == 2:
        n_col = 20
        num_var = (n_stud + 5) % n_col
        if num_var == 0:
            num_var = n_col
    elif num_lab == 3:
        n_col = 20
        num_var = n_stud % n_col
        if num_var == 0:
            num_var = n_col
    return num_var


def get_checks_status(number_lab, github_api, appveyor_client):
    latest_commit_sha = github_api.get_latest_commit_sha()

    is_green = False
    # дата выполнения, найдём максимальную дату (если несколько элементов)
    date_completed = None
    number_variant = None

    if number_lab in (1, 2):
        check_runs = github_api.get_checks_info(latest_commit_sha)
        # TODO Проверить, что проверки есть???

        if check_runs is not None:
            for check_run in check_runs:
                if check_run['conclusion'] == "success" and check_run['status'] == "completed":
                    date_completed = max(check_run['completed_at'], date_completed)
                else:
                    date_completed = None
                    break

        if date_completed is not None:
            is_green = True
            external_id = check_runs[0]['external_id']
            travis_client = TravisClient(github_token=github_api.get_token(),
                                         private=github_api.repo_is_private())
            job_log = travis_client.get_first_job_log(build_id=external_id)
            number_variant = get_variant_number_from_travis_log(job_log, number_lab)
    elif number_lab == 3:
        number_variant, is_green, date_completed = appveyor_client.get_latest_build_info()
    else:
        raise Exception('Invalid lab number')

    return is_green, number_variant, date_completed


def main():
    with open('services.json') as f:
        services = json.load(f)

    yandex_mail = YandexMail(login=services['yandex']['login'],
                             password=os.environ['YANDEX_MAIL_PASSWORD'])
    imap = yandex_mail.create_imap_client()

    # None здесь говорит о том, что нам всё равно, в какой кодировке искать письма
    # ALL - искать все письма
    # search(None, 'FROM', '"LDJ"') или search(None, '(FROM "LDJ")') - искать письма со строкой LDJ в поле From
    status, data = imap.search(None, 'UNSEEN')  # ищем письма
    list_email = data[0].split()
    print('')
    print('status=', status)
    print('')
    print('data= ', list_email)
    print('')
    print('Начало разбора писем')
    print('')

    server_mail = yandex_mail.create_smpt_client()
    spreadsheet = SpreadSheet(json_keyfile='google_service_account.json',
                              name=services['google_spreadsheets']['spreadsheet_name'])
    # -----------------------------------------------------------------------------------------
    #                          перебор всех полученных писем
    # -----------------------------------------------------------------------------------------
    for current_index_email in list_email:
        ## -------------- получение письма и его разбор ------------------------------------------------
        status, student_email, group_name, student_name, repository_url = get_data_from_email(imap, current_index_email)
        if status != 'OK':
            # не смогла получить письмо ( не знаю что делать )
            continue

        print('')
        print('FOR list_email ----', repository_url)
        print('Email  ', student_email, 'Группа ', group_name, 'ФИО ', student_name, 'Ссылка ', repository_url)
        _l = repository_url.replace('https://github.com/', '').split('/')
        organization = _l[0]
        _l1 = repository_url.split('-')
        osn_ch1 = _l1[0]
        osn_ch2 = _l1[1]
        osn_ch3 = _l1[2]
        # print('--------------АСНАВНАЯ ЧАСТЬ ССЫЛКИ--------------- ', osn_ch1, osn_ch2) # 'https://github.com/suai-2019/os'
        name = _l[1]
        print()
        # номео лабораторной
        task_id = int(name.split('-')[1].replace('task', ''))
        print('Organization ', organization, ' Никнэйм ', name, ' номер лабораторной №', task_id)

        ## -------------- конец получение письма и его разбор ------------------------------------------------
        ## -------------- работа с google ------------------------------------------------

        """ получить доступ к нужной странице """
        worksheet = None
        try:
            worksheet = spreadsheet.get_worksheet(group_name)
        except:
            pass

        if worksheet is None:
            # Видимо напрвильный номер группы.
            server_mail.send(student_email, 'Нет группы ' + group_name, 'Ошибка группы')
            continue

        """ прочитала список фамилий col_value """
        # print('1 номер страницы группы ', group_name)
        list_fio = worksheet.col_values(2)[2:]

        if student_name not in list_fio:
            # ERROR вызов процедуры отправки письма с этим сообщением
            server_mail.send(student_email, 'Нет такого студента ' + student_name + 'в группе ' + group_name,
                             'Ошибка ФИО')
            continue

        # print('2 студент в группе ',group_name, ' ФИО ',student_name, ' номер (0..n)=', list_fio.index(student_name)-2)
        number_row = list_fio.index(student_name) + 3
        ## -------------- конец работы с google ------------------------------------------------

        ## -------------- разбор ссылки ------------------------------------------------
        """вычисление № лабораторной лаботы """
        if ('https://github.com/suai' == osn_ch1) and ('os' == osn_ch2) and ('2019/os' == osn_ch3):
            # МОЖНТ БЫТЬ ТУТ СТОИТ СДЕЛАТЬ ПРОВЕРКУ НА СУЩЕСТВОВАНИЕ ЛАБОРАТОРНОЙ РАБОТЫ?
            # print ('3 лабораторная работа ', task_id, ' никнэйм студента:', name)
            number_col = int(task_id - 1) * 3 + 13  # WAT?
            worksheet.update_cell(number_row, number_col, repository_url)  # запись ссылки на лабу в таблицу гугла
            # print('ячейка row=', number_row, ' col=', number_col, ' на странице ', group_name, ' GOOGLE таблицы, успешно обновлена на ', repository_url)

            github_token = os.environ['GITHUB_TOKEN']
            github_api = GithubAPI(token=github_token,
                                   organization=services['github']['organization'],
                                   repo=name)

            is_green = False
            variant_number = None
            completion_date = None
            try:
                appveyor_token = os.environ['APPVEYOR_TOKEN']  # 'v2.7w5hnu6pmhkm1rpfesuq'
                appveyor_client = AppVeyorClient(api_token=appveyor_token,
                                                 org_name=services['appveyor']['organization'],
                                                 project_name=github_api.get_repo_name())
                is_green, variant_number, completion_date = get_checks_status(task_id, github_api, appveyor_client)
            except Exception as e:
                print('ВСЁ СЛОМАЛОСЬ!!!', e)
                pass
            if not is_green:
                server_mail.send(student_email,
                                 'Не выполнена лабораторная работа №' + str(task_id),
                                 'Ошибка лабораторной работы')
                continue

            print('GITHUB LABS ', completion_date, ' ВАРИАНТ ', variant_number, ' в гугле ', number_row - 2)
            need_number = whats_variants(task_id, number_row - 2)

            if (completion_date is not None) and (variant_number == need_number):
                worksheet.update_cell(number_row, number_col + 1, completion_date)  # запись даты выполнения лабы
                print('ячейка row=', number_row, ' col=', number_col, ' на странице ', group_name,
                      ' GOOGLE таблицы, успешно обновлена на ', completion_date)
            else:
                print('дата какого-то хрена не записывается')
        else:
            # ERROR вызов процедуры отправки письма с этим сообщением
            server_mail.send(student_email, 'Проверьте вашу ссылку на репозиторий', 'Ошибка основной части ссылки')
            ## -------------- конец разбор ссылки ------------------------------------------------

    server_mail.quit()
    imap.close()
    imap.logout()


if __name__ == '__main__':
    main()
