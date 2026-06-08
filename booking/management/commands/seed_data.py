from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import datetime

from booking.models import Psychologist, AppointmentType, TimeSlot, Appointment


class Command(BaseCommand):
    help = 'Наполняет БД демо-данными для просмотра в админке'

    def handle(self, *args, **options):
        slots = list(TimeSlot.objects.filter(is_available=True).order_by('date', 'time'))
        self.stdout.write(f'Доступно слотов: {len(slots)}')

        if len(slots) < 11:
            self.stdout.write(self.style.WARNING(
                'Мало свободных слотов. Сначала сгенерируйте расписание в админке.'
            ))
            return

        psych2 = Psychologist.objects.get(id=2)  # Ганьева
        psych3 = Psychologist.objects.get(id=3)  # Ворожеикина
        type_consult = AppointmentType.objects.get(id=1)
        type_preschool = AppointmentType.objects.get(id=2)

        appointments_data = [
            # (index в списке slots, appointment_type, поля)
            (0, type_consult, {
                'full_name': 'Смирнова Елена Викторовна',
                'who': 'parent', 'grade': '3Б',
                'phone': '+7 (912) 345-67-89',
                'email': 'elena.smirnova@mail.ru',
                'message': 'Беспокоит успеваемость по математике, стала хуже учиться',
            }),
            (1, type_consult, {
                'full_name': 'Козлов Андрей Сергеевич',
                'who': 'teacher', 'grade': '7А',
                'phone': '+7 (922) 111-22-33',
                'email': 'andrey.kozlov@school.ru',
                'message': 'Конфликт с учеником, нужна рекомендация',
            }),
            (2, type_consult, {
                'full_name': 'Морозова Дарья',
                'who': 'student', 'grade': '9В',
                'phone': '+7 (933) 444-55-66',
                'message': 'Сложности с выбором профиля, профориентация',
            }),
            (3, type_preschool, {
                'child_name': 'Иван Петров',
                'child_birthdate': datetime.date(2020, 3, 15),
                'kindergarten': 'Детский сад №45',
                'address': 'ул. Ленина, д. 10, кв. 25',
                'parent_name': 'Петрова Ольга Ивановна',
                'parent_phone': '+7 (944) 777-88-99',
                'phone': '+7 (944) 777-88-99',
                'message': 'Ребёнок не говорит, логопед направил к психологу',
            }),
            (4, type_consult, {
                'full_name': 'Зайцева Анна Павловна',
                'who': 'parent', 'grade': '5Г',
                'phone': '+7 (955) 123-45-67',
                'message': '',
            }),
            # Для Ворожеикиной
            (8, type_consult, {
                'full_name': 'Соколова Марина Игоревна',
                'who': 'parent', 'grade': '1А',
                'phone': '+7 (966) 333-22-11',
                'email': 'sokolova.m@yandex.ru',
                'message': 'Адаптация к школе, тревожность',
            }),
            (9, type_preschool, {
                'child_name': 'Тимофей Кузнецов',
                'child_birthdate': datetime.date(2019, 11, 2),
                'kindergarten': 'Детский сад №12',
                'address': 'ул. Победы, д. 5, кв. 12',
                'parent_name': 'Кузнецова Наталья Сергеевна',
                'parent_phone': '+7 (977) 555-66-77',
                'phone': '+7 (977) 555-66-77',
                'message': 'Гиперактивность, не может сидеть на месте, нужна диагностика',
            }),
            (10, type_consult, {
                'full_name': 'Белова Татьяна',
                'who': 'student', 'grade': '10А',
                'phone': '+7 (988) 999-00-11',
                'message': 'Экзамены, стресс',
            }),
        ]

        created_count = 0
        for idx, app_type, fields in appointments_data:
            slot = slots[idx]
            if hasattr(slot, 'appointment'):
                self.stdout.write(f'  [SKIP] Слот {slot.id} {slot.date} {slot.time} — уже занят')
                continue

            Appointment.objects.create(
                slot=slot,
                appointment_type=app_type,
                **fields,
            )
            slot.is_available = False
            slot.save()
            created_count += 1
            self.stdout.write(
                f'  [OK] {slot.psychologist.name} | {slot.date} {slot.time} | {app_type.name}'
            )

        # ── Архивные записи (прошлые даты) ──
        try:
            psych = Psychologist.objects.get(id=2)  # Ганьева
        except Psychologist.DoesNotExist:
            psych = None

        archive_created = 0
        if psych:
            archive_data = [
                (datetime.date(2026, 5, 12), datetime.time(10, 0), type_consult, {
                    'full_name': 'Архипова Мария Сергеевна',
                    'who': 'parent', 'grade': '2А',
                    'phone': '+7 (911) 111-11-11',
                    'message': 'Проблемы с поведением',
                }),
                (datetime.date(2026, 5, 12), datetime.time(11, 0), type_consult, {
                    'full_name': 'Громов Денис Павлович',
                    'who': 'teacher', 'grade': '8Б',
                    'phone': '+7 (922) 222-22-22',
                    'message': 'Конфликт в классе',
                }),
                (datetime.date(2026, 5, 15), datetime.time(14, 0), type_preschool, {
                    'child_name': 'Фёдоров Миша',
                    'child_birthdate': datetime.date(2020, 7, 20),
                    'kindergarten': 'Детский сад №3',
                    'address': 'ул. Мира, д. 15',
                    'parent_name': 'Фёдорова Анна Петровна',
                    'parent_phone': '+7 (933) 333-33-33',
                    'phone': '+7 (933) 333-33-33',
                    'message': 'Диагностика перед школой',
                }),
            ]
            for date_val, time_val, app_type, fields in archive_data:
                slot, _ = TimeSlot.objects.get_or_create(
                    psychologist=psych,
                    date=date_val,
                    time=time_val,
                    defaults={'is_available': True},
                )
                if hasattr(slot, 'appointment'):
                    continue
                Appointment.objects.create(slot=slot, appointment_type=app_type, **fields)
                slot.is_available = False
                slot.save()
                archive_created += 1

        remaining = TimeSlot.objects.filter(is_available=True).count()
        self.stdout.write(self.style.SUCCESS(f'\nСоздано записей: {created_count}'))
        if archive_created:
            self.stdout.write(self.style.SUCCESS(f'Создано архивных записей: {archive_created}'))
        self.stdout.write(f'Осталось свободных слотов: {remaining}')
