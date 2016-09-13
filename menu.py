# -*- coding: utf-8 -*-

import requests
import os
import json
import time

menu_key = -1
menu_day_key = 0
menu = [[], [], [], [], []]


def get_pdf(start, end, filename):

    print('Getting pdf...')

    if not os.path.exists('menus'):
            os.makedirs('menus')

    url = """http://assicanti.pt/wp-content/uploads/{:04d}/{:02d}/Ementa-Uptec-{:02d}-{:02d}-{:04d}-a-{:02d}-{:02d}-{:04d}.pdf""".format(
        start.year,
        start.month,
        start.day,
        start.month,
        start.year,
        end.day,
        end.month,
        end.year
    )

    with open('./menus/' + filename + '.pdf', 'wb') as book:
        a = requests.get(url, stream=True)

        if (a.status_code != 200):
            try:
                os.remove('./menus/' + filename + '.pdf')
            except OSError:
                pass
            return False

        for block in a.iter_content(512):
            if not block:
                break
            book.write(block)

    return True


def save_to_json(filename, obj):

    print('Saving info to JSON file...')

    with open('./menus/' + filename + '.json', 'w') as fp:
        json.dump(obj, fp)


def pdf_line(line):
    global menu_key, menu_day_key, menu

    if (menu_key < 0 or len(line) == 0):
        return None

    exclude_words = [
        'CARNE',
        'PEIXE',
        'VEGETARIANO',
        'SEGUNDA',
        'TERÇA',
        'QUARTA',
        'QUINTA',
        'SEXTA'
    ]

    if (line in exclude_words):
        return None

    # check if ()
    if (line[0] == '('):
        menu[menu_key][menu_day_key - 1] += ' ' + line
    else:
        menu[menu_key].append(line)
        menu_day_key += 1


def pdf_to_text(filename):
    global menu_key, menu_day_key, menu

    print('Converting pdf to txt...')

    cmd = 'pdf2txt.py -A -c utf-8 -o ./menus/{fn}.txt ./menus/{fn}.pdf'.format(
        fn=filename
    )

    # extract text
    os.system(cmd)

    # parse text
    with open('./menus/' + filename + '.txt', 'r') as menuFile:
        content = menuFile.readlines()

        for line in content:
            if (line.strip() == 'NOTA'):
                break
            if (line.strip() == 'CARNE'):
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
    file_path = './menus/' + filename + '.pdf'

    # check if file exists
    if (os.path.isfile(file_path) is False):
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

    # extact text from PDF
    menu_json = pdf_to_text(filename)

    return menu_json
