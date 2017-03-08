# -*- coding: utf-8 -*-

import requests
import os
import json
import html2text
import io
import subprocess
import datetime

menu_key = -1
menu_day_key = 0
menu = [[], [], [], [], []]


def get_pdf(start, end, filename):

    print('Getting pdf...')

    if not os.path.exists('pdf'):
            os.makedirs('pdf')

    # "hack" for week 19-09-2016 to 23-09-2016
    suffix = ''
    week_monday = "{:02d}-{:02d}-{:04d}".format(
        start.day,
        start.month,
        start.year
    )

    url = """http://assicanti.pt/wp-content/uploads/{:04d}/{:02d}/EMENTA-PCTA-{:02d}-{:02d}-A-{:02d}-{:02d}-{:04d}.pdf""".format(
        start.year,
        start.month,
        start.day,
        start.month,
        end.day,
        end.month,
        end.year,
    )

    with open('pdf/' + filename + '.pdf', 'wb') as book:
        a = requests.get(url, stream=True)

        if (a.status_code != 200):
            try:
                os.remove('pdf/' + filename + '.pdf')
            except OSError:
                pass
            return False

        for block in a.iter_content(512):
            if not block:
                break
            book.write(block)

    return True


def convert_pdf_to_html(filename):
    print('Converting pdf to html...')

    env = os.environ.get('UPTEC_MENU')
    if (env == 'prod'):
        cmd = 'docker run -ti --rm -v ~/uptec-menu/pdf:/pdf bwits/pdf2htmlex pdf2htmlEX ' + filename + '.pdf'
    else:
        cmd = 'pdf2htmlEX --embed-css 0 --embed-image 0 --embed-javascript 0 --dest-dir pdf pdf/{fn}.pdf'.format(
            fn=filename
        )

    # extract text
    print('Running: ' + cmd)
    # os.system(cmd)
    subprocess.call(cmd, shell=True)


def get_html(filename):
    html_text = None

    h = html2text.HTML2Text()
    with io.open('pdf/' + filename + '.html', 'r', encoding='utf-8') as fp:
        content = fp.read()
        html_text = h.handle(content)

    return html_text


def save_to_json(filename, obj):

    print('Saving info to JSON file...')

    with open('pdf/' + filename + '.json', 'w') as fp:
        json.dump(obj, fp)


def pdf_line(line):
    global menu_key, menu_day_key, menu

    if (menu_key < 0 or len(line) == 0):
        return None

    exclude_words = [
        u'SOPA',
        u'CARNE',
        u'PEIXE',
        u'VEGETARIANO',
        u'SEGUNDA',
        u'TERÇA',
        u'QUARTA',
        u'QUINTA',
        u'SEXTA'
    ]

    if (line in exclude_words):
        return None

    if (menu_day_key == 0):
        line = 'Sopa de ' + line

    # check if ()
    if (line[0] == '('):
        menu[menu_key][menu_day_key - 1] += ' ' + line
    else:
        menu[menu_key].append(line)
        menu_day_key += 1


def html_to_text(filename, html_text):
    global menu_key, menu_day_key, menu

    content = html_text.split('\n')
    for line in content:
        # exclude last line
        if ('![](pdf2htmlEX' in line.strip()):
            break

        if ('SOPA ' in line.strip()):
            menu_key += 1
            menu_day_key = 0

        if (line.strip() == 'SOPA'):
            menu_key += 1
            menu_day_key = 0
        else:
            pdf_line(line.strip())

    save_to_json(filename, menu)

    return menu


def get_new_file_name(start_end_date):
    start_date = '{:04d}{:02d}{:02d}'.format(
        start_end_date[0].year, start_end_date[0].month, start_end_date[0].day
    )

    end_date = '{:04d}{:02d}{:02d}'.format(
        start_end_date[1].year, start_end_date[1].month, start_end_date[1].day
    )

    filename = "menu-{start}-{end}".format(
        start=start_date,
        end=end_date
    )

    return filename


def check_if_has_valid_pdf(filename):
    file_path = 'pdf/' + filename + '.pdf'

    # check if file exists
    if (os.path.isfile(file_path) is False):
        return False

    # check if file is older than 1 day
    today = datetime.datetime.today()
    modified_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
    duration = today - modified_date
    if (duration.days > 1):
        return False

    return True


def get_menu(start_end_date):
    global menu_key, menu_day_key, menu

    menu_key = -1
    menu_day_key = 0
    menu = [[], [], [], [], []]

    # get new filename
    filename = get_new_file_name(start_end_date)

    # check if has a valid PDF already downloaded
    # and it's newer than 1h
    is_pdf_valid = check_if_has_valid_pdf(filename)

    has_pdf = True
    if not is_pdf_valid:
        # get PDF from UPTEC website
        has_pdf = get_pdf(start_end_date[0], start_end_date[1], filename)

        if not has_pdf:
            return False

        # convert pdf to html
        convert_pdf_to_html(filename)

    # get html from file
    html_text = get_html(filename)

    if html_text is None:
        return False

    # get info from html
    menu_json = html_to_text(filename, html_text)

    return menu_json
