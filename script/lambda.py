import os
import boto3
from datetime import datetime
from utils import calculate_cycle_phase, generate_phase_message, load_email_template


sender_email = os.getenv("EMAIL_REMETENTE")
recipient = os.getenv("EMAIL_DESTINATARIO")

def main():
    last_period_start = datetime(2025, 6, 13).date()
    cycle_length = 30
    phase = calculate_cycle_phase(last_period_start, cycle_length)
    message_text = generate_phase_message(phase)
    html_body = load_email_template(phase, message_text)

    ses = boto3.client(
        'ses',
        region_name='us-east-1',
        aws_access_key_id='',
        aws_secret_access_key=''
    )

    response = ses.send_email(
        Source=sender_email,
        Destination={'ToAddresses': [recipient]},
        Message={
            'Subject': {'Data': f"[Ciclo Menstrual] Sua fase da semana: {phase}"},
            'Body': {
                'Text': {'Data': message_text},
                'Html': {'Data': html_body}
            }
        }
    )

    return {
        'statusCode': 200,
        'body': f"E-mail enviado com sucesso! Fase: {phase}. Message ID: {response['MessageId']}"
    }

if __name__ == "__main__":
    main()