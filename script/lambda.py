import os
import uuid
from datetime import datetime
from functools import lru_cache

import boto3
import serverless_wsgi
from boto3.dynamodb.conditions import Attr
from flask import Flask, render_template, request

from utils import calculate_cycle_phase, generate_phase_message, load_email_template


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
DEFAULT_CYCLE_LENGTH = 30


@lru_cache(maxsize=1)
def get_aws_services():
    region = os.getenv('AWS_REGION', 'us-east-1')
    dynamodb = boto3.resource('dynamodb', region_name=region)
    ses = boto3.client('ses', region_name=region)
    table = dynamodb.Table(os.environ['DYNAMO_TABLE'])
    return table, ses, os.getenv('DYNAMO_PK', 'user_id'), os.environ['SENDER_EMAIL']



def verify_email(email, ses):
    response = ses.list_verified_email_addresses()
    if email in response["VerifiedEmailAddresses"]:
        return True
    else:
        ses.verify_email_identity(EmailAddress=email)
        return False


@app.route('/')
def home():
    return render_template('form.html')


@app.route('/register', methods=['POST'])
def register():
    pk_hash = str(uuid.uuid4())
    name = request.form['name']
    email = request.form['email']
    period_start = request.form['period_start']
    period_end = request.form['period_end']
    cycle_length = DEFAULT_CYCLE_LENGTH

    try:
        period_start_date = datetime.strptime(period_start, '%Y-%m-%d').date()
        period_end_date = datetime.strptime(period_end, '%Y-%m-%d').date()
    except ValueError:
        return 'Informe datas válidas para o início e o fim do período.', 400
    if period_end_date < period_start_date:
        return 'A data de fim não pode ser anterior à data de início.', 400

    table, ses, pk_dynamo, sender_email = get_aws_services()

    response = table.scan(
        FilterExpression=Attr('email').eq(email)
    )
    if response['Items']:
        user = response['Items'][0]
        if not user.get('verified', False) and not verify_email(email, ses):
            user.update({
                'name': name,
                'period_start': period_start,
                'period_end': period_end,
                'cycle_length': cycle_length,
            })
            table.put_item(Item=user)
            return (
                f"💌 {name}, já temos seu cadastro mas seu e-mail ainda não foi confirmado. "
                "Verifique sua caixa de entrada e confirme o e-mail da AWS para ativar seu cadastro. 🌸"
            )

        user.update({
            'name': name,
            'period_start': period_start,
            'period_end': period_end,
            'cycle_length': cycle_length,
            'verified': True,
        })
        table.put_item(Item=user)
        success = send_email_to_user(
            email, period_start, period_end, cycle_length, ses, sender_email
        )
        if success:
            return f"{name}, seu cadastro existente foi atualizado e a mensagem foi enviada! 💖"
        return f"{name}, seu cadastro foi atualizado, mas houve um problema ao enviar o e-mail. 💌"

    if not verify_email(email, ses):
        table.put_item(Item={
            pk_dynamo: pk_hash,
            'email': email,
            'name': name,
            'period_start': period_start,
            'period_end': period_end,
            'cycle_length': cycle_length,
            'verified': False
        })
        return (
            f"💌 {name}, quase lá! Verificamos que seu e-mail ainda não está confirmado. "
            "Você vai receber uma mensagem da Amazon Web Services na sua caixa de entrada. "
            "Clique no link dentro do e-mail para confirmar e começar a receber suas atualizações fofinhas do ciclo! 🌸"
        )
    else:
        table.put_item(Item={
            pk_dynamo: pk_hash,
            'email': email,
            'name': name,
            'period_start': period_start,
            'period_end': period_end,
            'cycle_length': cycle_length,
            'verified': True
        })

        success = send_email_to_user(
            email, period_start, period_end, cycle_length, ses, sender_email
        )

        if success:
            return f"{name}, seu cadastro foi realizado com sucesso! 💖 Você já recebeu o primeiro e-mail do seu ciclo."
        else:
            return f"{name}, seu cadastro foi salvo, mas houve um problema ao enviar o e-mail. Tente novamente mais tarde. 💌"


def send_email_to_user(email, period_start, period_end, cycle_length, ses, sender_email):
    period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
    period_end = datetime.strptime(period_end, '%Y-%m-%d').date()

    phase = calculate_cycle_phase(period_start, period_end, cycle_length)
    message_text = generate_phase_message(phase)
    html_body = load_email_template(phase, message_text)

    response = ses.send_email(
        Source=sender_email,
        Destination={'ToAddresses': [email]},
        Message={
            'Subject': {'Data': f"[Ciclo Menstrual] Sua fase da semana: {phase}"},
            'Body': {
                'Text': {'Data': message_text},
                'Html': {'Data': html_body}
            }
        }
    )
    if 'MessageId' in response:
        print(f"E-mail enviado com sucesso! MessageId: {response['MessageId']}")
    else:
        print("E-mail não foi enviado.")
    return 'MessageId' in response


def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG') == '1')