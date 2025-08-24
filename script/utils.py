from datetime import datetime


def calculate_cycle_phase(period_start, period_end, cycle_length=30):
    today = datetime.utcnow().date()

    if period_start <= today <= period_end:
        return "Fase Menstrual 🩸"

    days_since_period_start = (today - period_start).days
    day_in_cycle = days_since_period_start % cycle_length

    if 1 <= day_in_cycle < 6:
        return "Fase Folicular 🌿"
    elif 6 <= day_in_cycle <= 11:
        return "Fase Fértil 🌱"
    elif day_in_cycle == 12:
        return "Ovulação 🌸"
    else:
        return "Fase Lútea 🌙"

def generate_phase_message(phase):
    messages = {
        "Fase Menstrual 🩸": "Ei, amorzinho 😘… seu corpo tá descansando e você merece mimos! Hidrate-se e relaxe, sem descontar no(a) parceiro(a). 💖",
        "Fase Folicular 🌿": "Energia subindo! Aproveita pra fazer o que gosta e se sentir poderosa. Continua distribuindo amor! 😘",
        "Fase Fértil 🌱": "Alerta fofura! 🌱 Seu corpo tá vibrando energia positiva. Carinho nunca é demais 💕",
        "Ovulação 🌸": "Ovulação ativa! Criatividade e bem-estar lá em cima. Espalha amor e sorrisos 😄",
        "Fase Lútea 🌙": "Fase lútea: um pouco sensível é normal. Respira fundo e lembra: seu(a) parceiro(a) só quer te ver bem ❤️",
    }
    return messages.get(phase, "Não foi possível determinar a fase.")

def load_email_template(phase, message):
    template_path = 'script/template.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    return template.replace('{{ phase }}', phase).replace('{{ message }}', message)
