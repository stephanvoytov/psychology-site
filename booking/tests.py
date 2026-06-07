"""
Unit and integration tests for the psychology booking app.
"""
from datetime import date, time, timedelta
from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core import mail
from django.utils import timezone

from .models import Psychologist, AppointmentType, TimeSlot, Appointment
from .forms import AppointmentForm
from .slot_generator import SlotGeneratorForm
from .email_utils import send_appointment_notification


# =============================================================================
# Fixture helpers
# =============================================================================

def create_psychologist(**kwargs):
    defaults = {
        'name': 'Иванова Анна Петровна',
        'grades': '5-11 классы',
        'cabinet': '201',
        'phone': '+7 (999) 123-45-67',
        'email': 'psychologist@school.ru',
    }
    defaults.update(kwargs)
    return Psychologist.objects.create(**defaults)


def create_appointment_type(psychologists=None, **kwargs):
    defaults = {
        'name': 'Обычная консультация',
        'form_type': 'consultation',
    }
    defaults.update(kwargs)
    apt = AppointmentType.objects.create(**defaults)
    if psychologists:
        apt.psychologists.set(psychologists)
    return apt


def create_timeslot(psychologist, **kwargs):
    defaults = {
        'date': date.today() + timedelta(days=1),
        'time': time(10, 0),
        'is_available': True,
    }
    defaults.update(kwargs)
    return TimeSlot.objects.create(psychologist=psychologist, **defaults)


# =============================================================================
# 1. MODEL TESTS
# =============================================================================

class PsychologistModelTest(TestCase):
    def test_creation(self):
        """Psychologist created with all fields."""
        p = create_psychologist()
        self.assertEqual(p.name, 'Иванова Анна Петровна')
        self.assertEqual(p.grades, '5-11 классы')
        self.assertEqual(p.cabinet, '201')

    def test_str(self):
        """__str__ returns name and grades."""
        p = create_psychologist()
        self.assertEqual(str(p), 'Иванова Анна Петровна (5-11 классы)')

    def test_str_empty_grades(self):
        """__str__ works even with empty grades."""
        p = create_psychologist(grades='')
        self.assertIn('Иванова Анна Петровна', str(p))


class AppointmentTypeModelTest(TestCase):
    def test_creation_consultation(self):
        apt = create_appointment_type()
        self.assertEqual(apt.form_type, 'consultation')
        self.assertEqual(str(apt), 'Обычная консультация')

    def test_creation_preschool(self):
        apt = create_appointment_type(
            name='Обследование дошкольника',
            form_type='preschool_exam',
        )
        self.assertEqual(apt.form_type, 'preschool_exam')

    def test_psychologist_relation(self):
        p = create_psychologist()
        apt = create_appointment_type(psychologists=[p])
        self.assertIn(p, apt.psychologists.all())
        self.assertIn(apt, p.appointment_types.all())


class TimeSlotModelTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()

    def test_creation(self):
        slot = create_timeslot(psychologist=self.psychologist)
        self.assertTrue(slot.is_available)
        self.assertEqual(slot.psychologist, self.psychologist)

    def test_str(self):
        slot = create_timeslot(
            psychologist=self.psychologist,
            date=date(2026, 6, 10),
            time=time(14, 30),
        )
        self.assertIn('10.06.2026', str(slot))
        self.assertIn('14:30', str(slot))
        self.assertIn('✓', str(slot))

    def test_str_unavailable(self):
        slot = create_timeslot(
            psychologist=self.psychologist,
            is_available=False,
        )
        self.assertIn('✗', str(slot))

    def test_unique_together(self):
        create_timeslot(
            psychologist=self.psychologist,
            date=date(2026, 6, 10),
            time=time(10, 0),
        )
        with self.assertRaises(Exception):
            create_timeslot(
                psychologist=self.psychologist,
                date=date(2026, 6, 10),
                time=time(10, 0),
            )

    def test_ordering(self):
        slot1 = create_timeslot(
            psychologist=self.psychologist,
            date=date(2026, 6, 11),
            time=time(10, 0),
        )
        slot2 = create_timeslot(
            psychologist=self.psychologist,
            date=date(2026, 6, 10),
            time=time(14, 0),
        )
        slots = list(TimeSlot.objects.all())
        self.assertEqual(slots[0], slot2)  # earlier date first
        self.assertEqual(slots[1], slot1)


class AppointmentModelTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()
        self.apt_type = create_appointment_type(psychologists=[self.psychologist])
        self.slot = create_timeslot(psychologist=self.psychologist)

    def _create_appointment(self, **kwargs):
        defaults = {
            'slot': self.slot,
            'appointment_type': self.apt_type,
            'full_name': 'Петров Иван Сергеевич',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        }
        defaults.update(kwargs)
        return Appointment.objects.create(**defaults)

    def test_creation_consultation(self):
        app = self._create_appointment()
        self.assertEqual(app.full_name, 'Петров Иван Сергеевич')
        self.assertEqual(app.who, 'student')
        self.assertEqual(str(app.appointment_type), 'Обычная консультация')

    def test_creation_preschool(self):
        apt_preschool = create_appointment_type(
            name='Обследование дошкольника',
            form_type='preschool_exam',
            psychologists=[self.psychologist],
        )
        app = self._create_appointment(
            appointment_type=apt_preschool,
            full_name='',
            who='',
            child_name='Петров Иван Иванович',
            child_birthdate=date(2020, 5, 15),
            kindergarten='Детский сад №15',
            address='ул. Ленина, д.1',
            parent_name='Петрова Мария Сергеевна',
            parent_phone='+7 (999) 333-44-55',
        )
        self.assertEqual(app.child_name, 'Петров Иван Иванович')
        self.assertEqual(app.parent_name, 'Петрова Мария Сергеевна')

    def test_str_consultation(self):
        app = self._create_appointment()
        expected = f'{app.full_name} → {self.psychologist} | {self.apt_type}'
        self.assertEqual(str(app), expected)

    def test_str_preschool(self):
        apt_preschool = create_appointment_type(
            name='Обследование дошкольника',
            form_type='preschool_exam',
            psychologists=[self.psychologist],
        )
        app = self._create_appointment(
            appointment_type=apt_preschool,
            full_name='',
            child_name='Петров Иван Иванович',
        )
        self.assertIn('Петров Иван Иванович', str(app))

    def test_slot_onetoone(self):
        app = self._create_appointment()
        self.assertEqual(app.slot.appointment, app)

    def test_ordering(self):
        slot2 = create_timeslot(
            psychologist=self.psychologist,
            date=date.today() + timedelta(days=2),
            time=time(9, 0),
        )
        app1 = self._create_appointment(slot=self.slot)
        app2 = self._create_appointment(slot=slot2)
        apps = list(Appointment.objects.all())
        self.assertEqual(apps[0], app1)
        self.assertEqual(apps[1], app2)


# =============================================================================
# 2. FORM TESTS
# =============================================================================

class AppointmentFormTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()
        self.apt_consultation = create_appointment_type(
            name='Консультация',
            form_type='consultation',
            psychologists=[self.psychologist],
        )
        self.apt_preschool = create_appointment_type(
            name='Обследование',
            form_type='preschool_exam',
            psychologists=[self.psychologist],
        )
        self.appointment_types = AppointmentType.objects.filter(
            psychologists=self.psychologist,
        )

    def test_form_renders_with_types(self):
        form = AppointmentForm(appointment_types=self.appointment_types)
        types_qs = form.fields['appointment_type'].queryset
        self.assertEqual(types_qs.count(), 2)

    def test_form_without_types(self):
        """Form renders even with empty appointment_types queryset."""
        empty_qs = AppointmentType.objects.none()
        form = AppointmentForm(appointment_types=empty_qs)
        self.assertEqual(form.fields['appointment_type'].queryset.count(), 0)

    # --- Consultation validation ---

    def test_consultation_valid(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_consultation.id,
            'full_name': 'Тестов Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        }, appointment_types=self.appointment_types)
        self.assertTrue(form.is_valid(), form.errors)

    def test_consultation_missing_full_name(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_consultation.id,
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        }, appointment_types=self.appointment_types)
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)

    def test_consultation_missing_who(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_consultation.id,
            'full_name': 'Тест',
            'phone': '+7 (999) 111-22-33',
        }, appointment_types=self.appointment_types)
        self.assertFalse(form.is_valid())
        self.assertIn('who', form.errors)

    def test_consultation_missing_phone(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_consultation.id,
            'full_name': 'Тест',
            'who': 'student',
        }, appointment_types=self.appointment_types)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    # --- Preschool validation ---

    def test_preschool_valid(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_preschool.id,
            'child_name': 'Иванов Иван',
            'child_birthdate': '2020-05-15',
            'kindergarten': 'ДС №15',
            'address': 'ул. Ленина, д.1',
            'parent_name': 'Иванова Мария',
            'parent_phone': '+7 (999) 333-44-55',
        }, appointment_types=self.appointment_types)
        self.assertTrue(form.is_valid(), form.errors)

    def test_preschool_missing_child_name(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_preschool.id,
            'child_birthdate': '2020-05-15',
            'kindergarten': 'ДС №15',
            'address': 'ул. Ленина, д.1',
            'parent_name': 'Иванова Мария',
            'parent_phone': '+7 (999) 333-44-55',
        }, appointment_types=self.appointment_types)
        self.assertFalse(form.is_valid())
        self.assertIn('child_name', form.errors)

    def test_preschool_missing_child_birthdate(self):
        form = AppointmentForm(data={
            'appointment_type': self.apt_preschool.id,
            'child_name': 'Иванов Иван',
            'kindergarten': 'ДС №15',
            'address': 'ул. Ленина, д.1',
            'parent_name': 'Иванова Мария',
            'parent_phone': '+7 (999) 333-44-55',
        }, appointment_types=self.appointment_types)
        self.assertFalse(form.is_valid())
        self.assertIn('child_birthdate', form.errors)

    def test_no_appointment_type(self):
        """Form with no appointment_type returns cleaned but doesn't validate type-specific fields."""
        form = AppointmentForm(data={
            'full_name': 'Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        }, appointment_types=self.appointment_types)
        self.assertTrue(form.is_valid(), form.errors)

    def test_wrong_appointment_type_not_in_queryset(self):
        """An appointment_type not in the filtered queryset should be rejected."""
        other_psych = create_psychologist(
            name='Другой Психолог',
            email='other@school.ru',
        )
        other_apt = create_appointment_type(
            name='Для другого',
            form_type='consultation',
            psychologists=[other_psych],
        )
        form = AppointmentForm(data={
            'appointment_type': other_apt.id,
            'full_name': 'Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        }, appointment_types=self.appointment_types)
        # appointment_type field has a filtered queryset so this should fail
        self.assertFalse(form.is_valid())


# =============================================================================
# 3. EMAIL UTILS TESTS
# =============================================================================

class SendAppointmentNotificationTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()
        self.apt_type = create_appointment_type(psychologists=[self.psychologist])
        self.slot = create_timeslot(psychologist=self.psychologist)
        self.appointment = Appointment.objects.create(
            slot=self.slot,
            appointment_type=self.apt_type,
            full_name='Тестов Тест',
            who='student',
            phone='+7 (999) 111-22-33',
        )

    @patch('booking.email_utils.send_mail')
    def test_sends_email(self, mock_send_mail):
        """send_mail is called with correct arguments for consultation."""
        send_appointment_notification(self.appointment)
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertIn('Новая запись', kwargs['subject'])
        self.assertIn('Тестов Тест', kwargs['message'])
        self.assertIn(self.psychologist.email, kwargs['recipient_list'])

    @patch('booking.email_utils.send_mail')
    def test_preschool_email_content(self, mock_send_mail):
        """Preschool email contains child details."""
        apt_preschool = create_appointment_type(
            name='Обследование дошкольника',
            form_type='preschool_exam',
            psychologists=[self.psychologist],
        )
        new_slot = create_timeslot(
            psychologist=self.psychologist,
            date=date.today() + timedelta(days=2),
            time=time(11, 0),
        )
        appointment = Appointment.objects.create(
            slot=new_slot,
            appointment_type=apt_preschool,
            full_name='',
            child_name='Петров Иван',
            child_birthdate=date(2020, 5, 15),
            kindergarten='ДС №15',
            address='ул. Ленина, д.1',
            parent_name='Петрова Мария',
            parent_phone='+7 (999) 333-44-55',
        )
        send_appointment_notification(appointment)
        _, kwargs = mock_send_mail.call_args
        self.assertIn('ФИО ребёнка: Петров Иван', kwargs['message'])
        self.assertIn('Детский сад: ДС №15', kwargs['message'])

    @patch('booking.email_utils.send_mail')
    def test_no_email_if_psychologist_has_no_email(self, mock_send_mail):
        """If psychologist has no email, send_mail is not called."""
        self.psychologist.email = ''
        self.psychologist.save()
        send_appointment_notification(self.appointment)
        mock_send_mail.assert_not_called()

    @patch('booking.email_utils.send_mail')
    def test_bcc_list_included(self, mock_send_mail):
        """BCC email from settings is included in recipient list."""
        with self.settings(NOTIFICATION_BCC_LIST=['admin@school.ru']):
            send_appointment_notification(self.appointment)
            _, kwargs = mock_send_mail.call_args
            self.assertIn('admin@school.ru', kwargs['recipient_list'])

    @patch('booking.email_utils.send_mail')
    def test_default_from_email(self, mock_send_mail):
        """Email is sent from DEFAULT_FROM_EMAIL."""
        send_appointment_notification(self.appointment)
        _, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['from_email'], 'stepanvoytov@yandex.ru')

    @patch('booking.email_utils.send_mail')
    def test_recipient_list_includes_psychologist(self, mock_send_mail):
        """Psychologist's email is the primary recipient."""
        send_appointment_notification(self.appointment)
        _, kwargs = mock_send_mail.call_args
        self.assertIn(self.psychologist.email, kwargs['recipient_list'])


# =============================================================================
# 4. VIEW TESTS (Integration)
# =============================================================================

@override_settings(SECURE_SSL_REDIRECT=False)
class HomeViewTest(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/home.html')


@override_settings(SECURE_SSL_REDIRECT=False)
class ChoosePsychologistViewTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()
        self.url = reverse('schedule')

    def test_page_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_has_psychologists(self):
        response = self.client.get(self.url)
        self.assertIn('psychologists', response.context)
        self.assertEqual(len(response.context['psychologists']), 1)

    def test_context_has_multiple_psychologists(self):
        create_psychologist(name='Петров Петр', grades='1-4 классы', email='petrov@school.ru')
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['psychologists']), 2)


@override_settings(SECURE_SSL_REDIRECT=False)
class ScheduleViewTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()
        self.slot = create_timeslot(psychologist=self.psychologist)
        self.url = reverse('psychologist_schedule', args=[self.psychologist.id])

    def test_page_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_has_psychologist(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['psychologist'], self.psychologist)

    def test_context_has_slots(self):
        response = self.client.get(self.url)
        self.assertIn('slots_by_date', response.context)
        self.assertGreater(len(response.context['slots_by_date']), 0)

    def test_only_available_slots_shown(self):
        create_timeslot(
            psychologist=self.psychologist,
            date=date.today() + timedelta(days=3),
            time=time(11, 0),
            is_available=False,
        )
        response = self.client.get(self.url)
        total_slots = sum(len(v) for v in response.context['slots_by_date'].values())
        self.assertEqual(total_slots, 1)  # only the available one

    def test_old_slots_excluded(self):
        """Slots in the past should not be shown."""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        create_timeslot(psychologist=self.psychologist, date=yesterday, time=time(9, 0))
        response = self.client.get(self.url)
        for slot_date in response.context['slots_by_date']:
            self.assertGreaterEqual(slot_date, today)

    def test_404_for_invalid_psychologist(self):
        response = self.client.get(reverse('psychologist_schedule', args=[999]))
        self.assertEqual(response.status_code, 404)


@override_settings(SECURE_SSL_REDIRECT=False)
class BookViewTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()
        self.apt_type = create_appointment_type(psychologists=[self.psychologist])
        self.slot = create_timeslot(psychologist=self.psychologist)
        self.url = reverse('book', args=[self.slot.id])

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/book.html')

    def test_context_has_slot_and_psychologist(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['slot'], self.slot)
        self.assertEqual(response.context['psychologist'], self.psychologist)

    def test_context_has_form(self):
        response = self.client.get(self.url)
        self.assertIn('form', response.context)

    def test_context_has_appointment_types(self):
        response = self.client.get(self.url)
        self.assertIn('appointment_types', response.context)
        self.assertEqual(len(response.context['appointment_types']), 1)

    @patch('booking.views.send_appointment_notification')
    def test_post_valid_consultation(self, mock_notify):
        """Valid consultation POST creates appointment, marks slot unavailable, redirects."""
        response = self.client.post(self.url, {
            'appointment_type': self.apt_type.id,
            'full_name': 'Тестов Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        })
        self.assertRedirects(response, reverse('success'))
        # Slot should now be unavailable
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_available)
        # Notification should have been sent
        mock_notify.assert_called_once()

    def test_post_invalid_consultation(self):
        """Missing required fields → form errors."""
        response = self.client.post(self.url, {
            'appointment_type': self.apt_type.id,
            'full_name': '',
            'who': '',
            'phone': '',
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)
        self.assertIn('who', form.errors)
        self.assertIn('phone', form.errors)

    def test_post_valid_preschool(self):
        """Valid preschool POST creates appointment."""
        apt_preschool = create_appointment_type(
            name='Обследование дошкольника',
            form_type='preschool_exam',
            psychologists=[self.psychologist],
        )
        response = self.client.post(self.url, {
            'appointment_type': apt_preschool.id,
            'child_name': 'Иванов Иван',
            'child_birthdate': '2020-05-15',
            'kindergarten': 'ДС №15',
            'address': 'ул. Ленина, д.1',
            'parent_name': 'Иванова Мария',
            'parent_phone': '+7 (999) 333-44-55',
        })
        self.assertRedirects(response, reverse('success'))

    def test_404_for_unavailable_slot(self):
        """Booked/unavailable slot returns 404."""
        self.slot.is_available = False
        self.slot.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_post_unavailable_slot_returns_404(self):
        """POST to unavailable slot returns 404."""
        self.slot.is_available = False
        self.slot.save()
        response = self.client.post(self.url, {
            'full_name': 'Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        })
        self.assertEqual(response.status_code, 404)

    @patch('booking.views.send_appointment_notification')
    def test_email_failure_does_not_block_booking(self, mock_notify):
        """If email sending fails, the booking is still created."""
        mock_notify.side_effect = Exception('SMTP error')
        response = self.client.post(self.url, {
            'appointment_type': self.apt_type.id,
            'full_name': 'Тестов Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        })
        self.assertRedirects(response, reverse('success'))
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_available)

    def test_appointment_type_filtered_by_psychologist(self):
        """Only appointment types for this psychologist are in the form."""
        other_psych = create_psychologist(name='Другой', email='other@school.ru')
        other_apt = create_appointment_type(
            name='Для другого',
            form_type='consultation',
            psychologists=[other_psych],
        )
        response = self.client.get(self.url)
        types = response.context['appointment_types']
        self.assertNotIn(other_apt, types)

    def test_preschool_success_message(self):
        """Preschool booking shows special message."""
        apt_preschool = create_appointment_type(
            name='Обследование дошкольника',
            form_type='preschool_exam',
            psychologists=[self.psychologist],
        )
        response = self.client.post(self.url, {
            'appointment_type': apt_preschool.id,
            'child_name': 'Иванов Иван',
            'child_birthdate': '2020-05-15',
            'kindergarten': 'ДС №15',
            'address': 'ул. Ленина, д.1',
            'parent_name': 'Иванова Мария',
            'parent_phone': '+7 (999) 333-44-55',
        }, follow=True)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('кабинете психолога' in str(m) for m in messages_list))

    def test_consultation_success_message(self):
        response = self.client.post(self.url, {
            'appointment_type': self.apt_type.id,
            'full_name': 'Тестов Тест',
            'who': 'student',
            'phone': '+7 (999) 111-22-33',
        }, follow=True)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('успешно записались' in str(m) for m in messages_list))


@override_settings(SECURE_SSL_REDIRECT=False)
class SuccessViewTest(TestCase):
    def test_success_page(self):
        response = self.client.get(reverse('success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/success.html')


@override_settings(SECURE_SSL_REDIRECT=False)
class ContactsViewTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()

    def test_contacts_page(self):
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/contacts.html')

    def test_context_has_psychologists(self):
        create_psychologist(name='Петров Петр', grades='1-4', email='petrov@school.ru')
        response = self.client.get(reverse('contacts'))
        self.assertEqual(len(response.context['psychologists']), 2)


# =============================================================================
# 5. ADMIN / SLOT GENERATOR TESTS
# =============================================================================

class SlotGeneratorFormTest(TestCase):
    def setUp(self):
        self.psychologist = create_psychologist()

    def test_valid_form(self):
        form = SlotGeneratorForm(data={
            'psychologist': self.psychologist.id,
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=6),
            'weekdays': ['0', '1', '2', '3', '4'],  # Mon-Fri
            'time_from': '09:00',
            'time_to': '12:00',
            'interval': '60',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_from_after_date_to(self):
        form = SlotGeneratorForm(data={
            'psychologist': self.psychologist.id,
            'date_from': date.today() + timedelta(days=10),
            'date_to': date.today(),
            'weekdays': ['0'],
            'time_from': '09:00',
            'time_to': '12:00',
            'interval': '60',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('Дата начала', str(form.errors))

    def test_time_from_after_time_to(self):
        form = SlotGeneratorForm(data={
            'psychologist': self.psychologist.id,
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=6),
            'weekdays': ['0'],
            'time_from': '12:00',
            'time_to': '09:00',
            'interval': '60',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('Время начала', str(form.errors))


class TimeSlotAdminCreateSlotsTest(TestCase):
    """Test the _create_slots logic directly."""

    def setUp(self):
        from booking.admin import TimeSlotAdmin
        self.psychologist = create_psychologist()
        # Instantiate the admin class to access _create_slots
        self.admin = TimeSlotAdmin(model=TimeSlot, admin_site=None)

    def test_create_slots_generates_correct_count(self):
        """_create_slots creates slots for the right weekdays in a range."""
        data = {
            'psychologist': self.psychologist,
            'date_from': date(2026, 6, 8),   # Monday
            'date_to': date(2026, 6, 14),     # Sunday
            'weekdays': ['0', '1', '2'],       # Mon, Tue, Wed
            'time_from': time(9, 0),
            'time_to': time(12, 0),
            'interval': 60,
        }
        created, skipped = self.admin._create_slots(data)
        # 3 days × 3 slots (09:00, 10:00, 11:00) = 9 slots
        self.assertEqual(created, 9)
        self.assertEqual(skipped, 0)

    def test_create_slots_skips_existing(self):
        """Duplicate slots are skipped, not recreated."""
        # Create one slot manually
        TimeSlot.objects.create(
            psychologist=self.psychologist,
            date=date(2026, 6, 8),  # Monday
            time=time(9, 0),
        )
        data = {
            'psychologist': self.psychologist,
            'date_from': date(2026, 6, 8),
            'date_to': date(2026, 6, 8),
            'weekdays': ['0'],  # Monday only
            'time_from': time(9, 0),
            'time_to': time(12, 0),
            'interval': 60,
        }
        created, skipped = self.admin._create_slots(data)
        # 3 slots possible, 1 exists → 2 created, 1 skipped
        self.assertEqual(created, 2)
        self.assertEqual(skipped, 1)

    def test_create_slots_no_weekend_work(self):
        """No slots for Saturday/Sunday."""
        data = {
            'psychologist': self.psychologist,
            'date_from': date(2026, 6, 13),  # Saturday
            'date_to': date(2026, 6, 14),    # Sunday
            'weekdays': ['0', '1', '2', '3', '4'],
            'time_from': time(9, 0),
            'time_to': time(12, 0),
            'interval': 60,
        }
        created, skipped = self.admin._create_slots(data)
        self.assertEqual(created, 0)

    def test_create_slots_outside_time_range(self):
        """Slots are not created outside time_from-time_to."""
        data = {
            'psychologist': self.psychologist,
            'date_from': date(2026, 6, 8),  # Monday
            'date_to': date(2026, 6, 8),
            'weekdays': ['0'],
            'time_from': time(10, 0),
            'time_to': time(10, 30),  # only 30 min window
            'interval': 30,
        }
        created, skipped = self.admin._create_slots(data)
        # Only 10:00 fits (10:30 is not < 10:30)
        self.assertEqual(created, 1)
