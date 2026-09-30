from datetime import datetime, timedelta
import sqlite3
import pytest
from medmate.store import Store, ValidationError

@pytest.fixture
def db(tmp_path):
    return Store(tmp_path / 'medmate.db')

@pytest.fixture
def accounts(db):
    p = db.register('temp@example.com', 'testpass123', 'patient', 'Tempest')
    d = db.register('doc@example.com', 'testpass123', 'doctor', 'Dr. Ama', 'TEST-123', 'General practice')
    return p['id'], d['id']

def future():
    return (datetime.now() + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat(timespec='minutes')

def test_password_and_role_are_checked(db, accounts):
    assert db.login(' TEMP@example.com ', 'testpass123', 'patient')['name'] == 'Tempest'
    for password, role in [('wrongpass', 'patient'), ('testpass123', 'doctor')]:
        with pytest.raises(ValidationError): db.login('temp@example.com', password, role)

def test_registration_validation_and_no_plain_password(db):
    for email, password, role in [('bad', 'testpass123', 'patient'), ('x@y.com', 'short', 'patient'), ('x@y.com', 'testpass123', 'admin')]:
        with pytest.raises(ValidationError): db.register(email, password, role, 'Someone')
    db.register('x@y.com', 'testpass123', 'patient', 'Someone')
    with pytest.raises(ValidationError): db.register('X@Y.COM', 'testpass123', 'patient', 'Duplicate')
    with sqlite3.connect(db.path) as connection:
        value = connection.execute('select password_hash from users').fetchone()[0]
        assert 'testpass123' not in value

def test_profiles_persist_and_are_isolated(db, accounts):
    p, d = accounts
    db.save_profile(p, {'name':'Temp', 'age':'22', 'country':'Ghana', 'allergies':'peanuts'})
    second = Store(db.path)
    assert second.profile(p)['allergies'] == 'peanuts'
    assert second.profile(d)['allergies'] == ''
    with pytest.raises(ValidationError): db.save_profile(p, {'age':'-1'})
    assert second.profile(p)['age'] == '22'

def test_doctor_access_requires_link_and_revokes(db, accounts):
    p, d = accounts
    assert db.patients(d) == []
    with pytest.raises(ValidationError): db.patient_record(d, p)
    db.link_doctor(p, d)
    assert db.patients(d)[0]['id'] == p
    assert db.patient_record(d,p)['name'] == 'Tempest'
    db.save_note(d,p,'Follow up at next visit')
    assert db.notes(d,p)[0]['text'] == 'Follow up at next visit'
    db.unlink_doctor(p,d)
    with pytest.raises(ValidationError): db.patient_record(d,p)
    with pytest.raises(ValidationError): db.save_note(d,p,'blocked')

def test_messages_are_delivered_only_to_linked_participants(db, accounts):
    p, d = accounts
    third = db.register('other@example.com','testpass123','patient','Other')['id']
    with pytest.raises(ValidationError): db.send_message(p,d,'Hello')
    db.link_doctor(p,d)
    db.send_message(p,d,'Hello doctor')
    db.send_message(d,p,'Hello Tempest')
    assert [m['text'] for m in db.messages(p,d)] == ['Hello doctor','Hello Tempest']
    assert db.messages(third,d) == []
    db.unlink_doctor(p,d)
    with pytest.raises(ValidationError): db.send_message(d,p,'blocked')
    assert len(db.messages(p,d)) == 2

def test_appointments_validate_conflicts_and_status_permissions(db, accounts):
    p,d=accounts
    db.link_doctor(p,d)
    a=db.request_appointment(p,d,future(),'Check up')
    with pytest.raises(ValidationError): db.request_appointment(p,d,future(),'Duplicate')
    with pytest.raises(ValidationError): db.update_appointment(p,a,'accepted')
    db.update_appointment(d,a,'accepted')
    assert db.appointments(p)[0]['status']=='accepted'
    db.update_appointment(d,a,'completed')
    with pytest.raises(ValidationError): db.update_appointment(p,a,'cancelled')
    assert db.request_appointment(p,d,future(),'Another visit') != a

def test_appointment_past_unlinked_and_unrelated_rejected(db,accounts):
    p,d=accounts
    with pytest.raises(ValidationError): db.request_appointment(p,d,future(),'Check up')
    db.link_doctor(p,d)
    with pytest.raises(ValidationError): db.request_appointment(p,d,'2020-01-01T10:00','Check up')
    a=db.request_appointment(p,d,future(),'Check up')
    other=db.register('other@example.com','testpass123','doctor','Other','TEST-456')['id']
    with pytest.raises(ValidationError): db.update_appointment(other,a,'cancelled')

def test_preferences_merge_without_overwriting_profile(db,accounts):
    p,d=accounts
    db.save_profile(p,{'allergies':'fish'})
    db.save_preferences(p,{'theme':'Dark','diet':'Vegan'})
    db.save_preferences(p,{'share_ai':True})
    assert db.preferences(p)['diet']=='Vegan'
    assert db.preferences(d)['theme']=='Light'
    assert db.profile(p)['allergies']=='fish'

def test_doctor_cannot_link_or_read_other_doctor_notes(db,accounts):
    p,d=accounts
    other=db.register('doc2@example.com','testpass123','doctor','Other','TEST-456')['id']
    with pytest.raises(ValidationError): db.link_doctor(d,other)
    db.link_doctor(p,d); db.link_doctor(p,other)
    db.save_note(d,p,'Private note')
    assert db.notes(other,p)==[]
