from datetime import datetime

def calculate_cycle_phase(last_period_start, cycle_length=30):
    today = datetime.utcnow().date()
    day_in_cycle = (today - last_period_start).days % cycle_length

    if day_in_cycle < 6:
        return "Fase Menstrual 🩸"
    elif 6 <= day_in_cycle < 10:
        return "Fase Folicular 🌿"
    elif 10 <= day_in_cycle <= 15:
        return "Fase Fértil 🌱"
    elif day_in_cycle == 16:
        return "Ovulação 🌸"
    else:
        return "Fase Lútea 🌙"

def generate_phase_message(phase):
    messages = {
        "Fase Menstrual 🩸": "Ei, amorzinho 😘… seu corpo tá descansando e você merece mimos! Não se preocupe se estiver sensível. Respira, se hidrate e se abrace. Não desconta no(a) parceiro(a) 💖",
        "Fase Folicular 🌿": "Oi linda 🌸! Energia subindo! Aproveita pra fazer o que gosta e se sentir poderosa. Continua distribuindo amor, tá? 😘",
        "Fase Fértil 🌱": "Alerta fofura! 🌱 Seu corpo tá vibrando energia positiva. Hora de cuidar de você e do relacionamento. Carinho nunca é demais 💕",
        "Ovulação 🌸": "Ei, estrela 🌟! Ovulação ativa, então criatividade e bem-estar lá em cima. Aproveita e espalha amor, não frustração 😄. Beijos e abraços infinitos!",
        "Fase Lútea 🌙": "Tá na fase lútea 🌙… um pouco sensível é normal. Se sentir vontade de descansar ou reclamar de algo bobo, respira fundo e lembra: seu(a) parceiro(a) só quer te ver bem ❤️",
    }
    return messages.get(phase, "Não foi possível determinar a fase.")

def load_email_template(phase, message):
    template_path = 'script/template.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    return template.replace('{{ phase }}', phase).replace('{{ message }}', message)
