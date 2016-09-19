# -*- coding: utf-8 -*-

import datetime
import os
from flask import Flask, jsonify, request
from menu import get_menu

app = Flask(__name__)


# get week initial and end date
def get_start_end_date():
    today = datetime.datetime.now().date()
    monday = today + datetime.timedelta(days=-today.weekday())
    friday = today + datetime.timedelta(days=(4 - today.weekday()))

    return [monday, friday]


# pretty print to Slack
def print_to_slack(start_end_date, menu, param=None):
    days = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    days_index = 0

    weekday = -1
    if (param == 'today'):
        today = datetime.datetime.now().date()

        pretty_date = '{:02d}/{:02d}/{:04d}'.format(
            today.day, today.month, today.year
        )

        resp_txt = 'Menu UPTEC para hoje ({today})'.format(
            today=pretty_date
        )

        weekday = today.weekday()
    else:
        pretty_start_date = '{:02d}/{:02d}/{:04d}'.format(
            start_end_date[0].day, start_end_date[0].month, start_end_date[0].year
        )

        pretty_end_date = '{:02d}/{:02d}/{:04d}'.format(
            start_end_date[1].day, start_end_date[1].month, start_end_date[1].year
        )

        resp_txt = 'Menu UPTEC desta semana ({start} a {end})!'.format(
            start=pretty_start_date,
            end=pretty_end_date
        )

    response = {
        'response_type': 'in_channel',
        'text': resp_txt,
        'attachments': []
    }

    if (weekday >= 0 and weekday <= 4):
        day_json = {
            'title': days[weekday],
            'text': ''
        }

        for dish in menu[weekday]:
            day_json['text'] += dish + '\n'

        response['attachments'].append(day_json)
    else:
        for day in menu:
            day_json = {
                'title': days[days_index],
                'text': ''
            }

            for dish in day:
                day_json['text'] += dish + '\n'

            response['attachments'].append(day_json)
            days_index += 1

    return response


# pretty print Slack error message
def print_error_to_slack(reason=None):
    return_txt = 'Não foi possível obter a ementa! Por favor tente mais tarde.\nMais informações em: http://assicanti.pt/home/cafetarias/uptec/'

    if (reason == 'params'):
        return_txt = 'Parâmetro inválido!'
    elif (reason == 'weekend'):
        return_txt = 'Não existe ementa para o fim-de-semana!'

    return {
        'response_type': 'in_channel',
        'text': return_txt,
    }


def check_if_weekend():
    today = datetime.datetime.now().date()
    weekday = today.weekday()

    return weekday == 5 or weekday == 6


@app.route("/")
def default():

    # get request params
    param = request.args.get("text")

    if (param is not None and len(param.strip()) == 0):
        param = None

    # if param not 'today' return a error message
    if (param is not None):

        if (param == 'hoje'):
            param = 'today'

        if (param != 'today'):
            return jsonify(print_error_to_slack('params'))

        if (param == 'today' and check_if_weekend()):
            return jsonify(print_error_to_slack('weekend'))

    start_end_date = get_start_end_date()
    menu = get_menu(start_end_date)

    if menu is False:
        return jsonify(print_error_to_slack())

    return jsonify(print_to_slack(start_end_date, menu, param))


@app.route('/status')
def status():
    return jsonify({'success': True}), 200, {'ContentType': 'application/json'}


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
