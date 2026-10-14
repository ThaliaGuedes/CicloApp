import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / 'script'
sys.path.insert(0, str(SCRIPT_DIR))
import utils

spec = importlib.util.spec_from_file_location('ciclo_lambda', SCRIPT_DIR / 'lambda.py')
ciclo_lambda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ciclo_lambda)


def test_home_page_loads_without_aws():
    response = ciclo_lambda.app.test_client().get('/')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'Cadastre seu Ciclo' in html
    assert 'name="period_start"' in html
    assert 'name="period_end"' in html
    assert 'name="cycle_length"' not in html
    assert 'name="viewport"' in html


def test_register_stores_both_dates_and_uses_default_cycle(monkeypatch):
    table = Mock()
    table.scan.return_value = {'Items': []}
    ses = Mock()
    ses.list_verified_email_addresses.return_value = {
        'VerifiedEmailAddresses': ['pessoa@example.com']
    }
    ses.send_email.return_value = {'MessageId': 'message-id'}
    monkeypatch.setattr(
        ciclo_lambda,
        'get_aws_services',
        lambda: (table, ses, 'user_id', 'remetente@example.com'),
    )

    response = ciclo_lambda.app.test_client().post('/register', data={
        'name': 'Pessoa',
        'email': 'pessoa@example.com',
        'period_start': '2026-10-01',
        'period_end': '2026-10-05',
    })

    assert response.status_code == 200
    assert 'cadastro foi realizado com sucesso' in response.get_data(as_text=True)
    saved_user = table.put_item.call_args.kwargs['Item']
    assert saved_user['cycle_length'] == 30
    assert saved_user['period_start'] == '2026-10-01'
    assert saved_user['period_end'] == '2026-10-05'
    ses.send_email.assert_called_once()


def test_register_rejects_end_date_before_start(monkeypatch):
    services = Mock()
    monkeypatch.setattr(ciclo_lambda, 'get_aws_services', services)

    response = ciclo_lambda.app.test_client().post('/register', data={
        'name': 'Pessoa',
        'email': 'pessoa@example.com',
        'period_start': '2026-10-05',
        'period_end': '2026-10-01',
    })

    assert response.status_code == 400
    services.assert_not_called()


def test_cycle_phase_uses_reported_period_duration(monkeypatch):
    class FixedDateTime:
        @staticmethod
        def utcnow():
            return datetime(2026, 10, 7)

    monkeypatch.setattr(utils, 'datetime', FixedDateTime)

    short_period_phase = utils.calculate_cycle_phase(
        datetime(2026, 10, 1).date(), datetime(2026, 10, 4).date(), 30
    )
    longer_period_phase = utils.calculate_cycle_phase(
        datetime(2026, 10, 1).date(), datetime(2026, 10, 7).date(), 30
    )

    assert short_period_phase == 'Fase Folicular 🌿'
    assert longer_period_phase == 'Fase Menstrual 🩸'


@pytest.mark.parametrize(
    ('ses_response', 'expected'),
    [({'MessageId': 'message-id'}, True), ({}, False)],
)
def test_send_email_returns_delivery_result(monkeypatch, ses_response, expected):
    ses = Mock()
    ses.send_email.return_value = ses_response
    monkeypatch.setattr(ciclo_lambda, 'calculate_cycle_phase', Mock(return_value='Fase teste'))
    monkeypatch.setattr(ciclo_lambda, 'generate_phase_message', Mock(return_value='Mensagem teste'))
    monkeypatch.setattr(ciclo_lambda, 'load_email_template', Mock(return_value='<p>Mensagem teste</p>'))

    result = ciclo_lambda.send_email_to_user(
        'pessoa@example.com', '2026-10-01', '2026-10-05', 30, ses,
        'remetente@example.com'
    )

    assert result is expected
    ses.send_email.assert_called_once()
    assert ses.send_email.call_args.kwargs['Source'] == 'remetente@example.com'