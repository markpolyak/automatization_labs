

### получить тело письма типа TEXT (не надо HTML) если multipart то тело письма из двух частей text, html
def _get_email_as_text(message):
    maintype = message.get_content_maintype()

    if maintype == 'text':
        return message.get_payload(decode=True)

    if maintype == 'multipart':
        for part in message.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload(decode=True)

    return None


def _decode_line(line, encoding):
    try:
        decoded_line = line.decode(encoding)
    except:
        decoded_line = ''  # если была ошибка по строка пустая
    return decoded_line


def _html_to_str(body):
    return body.replace(b'<div>', b'').split(b'</div>')


def parse_data_from_email(message):
    try:
        # вернуть кодировку для расшифровки тела письма (там 3 элемента беру 2, может не очень правильно)
        type_code = message.get_charsets()[1]
    except:
        # вернуть кодировку для расшифровки тела письма (там 3 элемента беру 2, может не очень правильно)
        type_code = message.get_charsets()[0]

    message_text = _get_email_as_text(message)
    # разбор строк по символу \n  split(b'\n')-Разделить на список по кодам 10,13.
    message_lines = message_text.split(b'\n')
    # print('message_lines ', message_lines)

    if message_lines[0][0:5] == b'<div>':
        message_lines = _html_to_str(message_lines[0])

    # декодировать из набора байт в строку ! с кодировкой полученной в начале процедуры
    decoded_lines = [_decode_line(line, type_code) for line in message_lines]

    # убрать пробелы в начале и конце
    decoded_lines = [line.strip() for line in decoded_lines]

    # оставить только непустые строки
    decoded_lines = list(filter(None, decoded_lines))

    # нужны тольк первые три строки
    group_name = decoded_lines[0]
    student_name = decoded_lines[1]
    repo_url = decoded_lines[2]

    return group_name, student_name, repo_url


def get_variant_number_from_travis_log(log, num_lab):
    if log is None:
        return None

    number_variant = None

    if num_lab == 1:  # Для 1 лабораторной
        start = log.find('The script is run on Linux machine')
        if start > 0:
            beg_line = log.find('Solution for task ')
            if beg_line > 0:
                b = log[beg_line:].replace(' ', '\r').split('\r')
                number_variant = int(b[3])

    if num_lab == 2:  # Для 2 лабораторной
        start = log.find('Task')
        if start > 0:
            a = log[start:].replace(' ', '\r').split('\r')
            number_variant = int(a[1].replace(':', ''))

    return number_variant
