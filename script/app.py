import uuid
from flask import Flask, json, render_template, request
import boto3
from datetime import datetime
from utils import calculate_cycle_phase, generate_phase_message, load_email_template
from boto3.dynamodb.conditions import Attr


app = Flask(__name__)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ses = boto3.client('ses', region_name='us-east-1')
client = boto3.client("secretsmanager", region_name='us-east-1')
response = client.get_secret_value(SecretId='app-ciclo')

secret = json.loads(response['SecretString'])
table_name = secret['DYNAMO_TABLE']
table = dynamodb.Table(table_name)
pk_dynamo = secret['pk_dynamo']



def verify_email(email):
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
    cycle_length = int(request.form['cycle_length'])

    response = table.scan(
        FilterExpression=Attr('email').eq(email)
    )
    if response['Items']:
        user = response['Items'][0]
        if user.get('verified', False):
            send_email_to_user(email, period_start, period_end, cycle_length)
            return f"{email} já está cadastrado e verificado! 💖"

        else:
            send_email_to_user(email, period_start, period_end, cycle_length)
            return (
                f"💌 {name}, já temos seu cadastro mas seu e-mail ainda não foi confirmado. "
                "Verifique sua caixa de entrada e confirme o e-mail da AWS para ativar seu cadastro. 🌸"
            )

    if not verify_email(email):
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

        success = send_email_to_user(email, period_start, period_end, cycle_length)

        if success:
            return f"{name}, seu cadastro foi realizado com sucesso! 💖 Você já recebeu o primeiro e-mail do seu ciclo."
        else:
            return f"{name}, seu cadastro foi salvo, mas houve um problema ao enviar o e-mail. Tente novamente mais tarde. 💌"


def send_email_to_user(email, period_start, period_end, cycle_length):
    period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
    period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
    
    phase = calculate_cycle_phase(period_start, period_end, cycle_length)
    message_text = generate_phase_message(phase)
    html_body = load_email_template(phase, message_text)

    response = ses.send_email(
        Source='thaliaguedes@myyahoo.com',
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
        sucesso = True
    else:
        print("E-mail não foi enviado.")
        sucesso = False


if __name__ == '__main__':
    app.run(debug=True)
