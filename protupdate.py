# =========================== МОДУЛИ ===========================
from datetime import datetime, timedelta, time
from typing import Annotated, Optional, Dict, Any, List
from pydantic import BaseModel, StringConstraints, Field

from fastapi import HTTPException
import requests
import couchdb

database_url = 'http://admin:password@localhost:5990'
database_auth = ("admin", "password")

# =========================== КЛАССЫ ПОЛЬЗОВАТЕЛЕЙ ===========================

class User(BaseModel):
    """
    Класс для пользователя системы
    """
    snils: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            pattern=r'^\d{3}-\d{3}-\d{2} \d{2}'  # СНИЛС должен быть в формате XXX-XXX-XX XX
        )]

    password: Annotated[
        str,
        StringConstraints(min_length=4)
    ]

    def sign_in(self, snils, password):
        if snils == self.snils and password == self.password:
            print('Добро пожаловать')


class Patient(User):
    """
    Класс пациента — содержит персональные данные и медицинскую карту.
    """
    name: str
    phone: str
    address: str
    email: str
    birthdate: str
    eligibility: Optional[str] = None
    health_record: 'HealthRecord' = {}
    appointment_history: list[Any] = [] #предназначен для хранения объектов appointments

    def show_personal_profile(self):
        return {'ФИО': self.get_name(),
                'Телефон': self.phone,
                'Адрес:': self.address,
                'Email': self.email,
                'Дата рождения': self.birthdate
        }

    def get_snils(self):
        return self.snils

    def get_health_record_from_db(self): #достает мед карту пациента из БД
        self.health_record=References.get_health_record(self.snils)
        return self.health_record

    def get_name(self):
        return self.name

    def get_doctor(self, doctor_id):
        doctor = References.get_doctor_from_db(doctor_id)
        return doctor.show_profile()

    def get_appointments_from_db(self): #достает актуальные записи приемов из БД
        self.appointment_history = Scheduler.get_appointments({'patient_id': self.snils})
        return self.appointment_history

    def show_appointments(self): #вывод записей пациента
        self.get_appointments_from_db()
        return [record.show_info() for record in self.appointment_history]

    def check_appointments(self, appointment_date, doctor):
        self.get_appointments_from_db()
        for a in self.appointment_history:
            if (a.doctor_id == doctor.id and
                    a.get_date().date() == appointment_date.date()):
                return f'Ошибка: вы уже записаны к врачу {doctor.get_name()} на этот день.'
            elif a.get_date() == appointment_date:
                return f'Ошибка: у вас уже есть запись на это время к врачу {a.get_doctor().get_name()}.'

            elif a.get_doctor().get_speciality() == doctor.get_speciality():
                return f'Ошибка: у вас уже есть запись к врачу данного направления {a.get_doctor().get_speciality()}.'

        return True


class Doctor(BaseModel):
    """
    Класс врача — содержит информацию о квалификации, опыте и расписании.
    """
    id: Annotated[
        str,
        Field(..., min_length=4, max_length=50, description="Уникальный идентификатор врача")
    ]
    name: Annotated[
        str,
        Field(..., min_length=3, max_length=100, pattern=r"^[А-ЯЁа-яёA-Za-z\- ]+$")
    ]
    speciality: Annotated[
        str,
        Field(..., min_length=3, max_length=50)
    ]
    qualification: Annotated[
        str,
        Field(..., min_length=3, max_length=50)
    ]
    experience: Annotated[
        str,
        Field(..., min_length=3, max_length=50, description="Опыт работы")
    ]
    room: Annotated[
        str,
        Field(default='101', pattern=r"^[A-Za-z0-9\-]+$", min_length=1, max_length=10)
    ]
    schedule: Dict[str, List[str]] = Field(default_factory=lambda: Scheduler.get_schedule()) #базовое расписание для всех врачей клиники
    appointments: Optional[List[Dict]] = Field(default=None)

    def get_appointments_from_db(self): #достает актуальные записи из БД в виде экземпляров класса appointment
        self.appointments = Scheduler.get_appointments({'doctor_id': self.id})
        return self.appointments

    def show_appointments(self): #просмотр "календаря" врача на день
        self.get_appointments_from_db()
        return [record.show_info() for record in self.appointments]

    def get_available_schedule(self): #актуальное расписание врача с учетом занятых слотов
        appointments=self.get_appointments_from_db()
        occupied_slots = [dt.get_date() for dt in appointments]

        for dt in self.schedule:
            filtered_slots = list(filter(lambda slot: slot if slot not in occupied_slots else False, self.schedule[dt]))
            self.schedule[dt] = filtered_slots
        return self.schedule

    def change_room(self, room): #изменение кабинета приема
        self.room = room

    def add_medical_history(self, health_record, date, record):
        return health_record.add_medical_history({datetime.isoformat(date):
            {'Направление': self.speciality,
            'Врач': self.name,
            'Комментарий': record}})

    def show_profile(self): #служебный метод для отображения профиля врача пациенту
        doc_profile = {'ФИО': self.name,
                       'Направление': self.speciality,
                       'Ученая степень': self.qualification,
                       'Стаж': self.experience,
                       'Доступное расписание': self.get_available_schedule()
                       }
        return doc_profile

    def get_name(self):
        return self.name

    def get_room(self):
        return self.room

    def get_speciality(self):
        return self.speciality

    def get_id(self):
        return self.id

    def check_availability(self, day):
        """Проверяет доступность врача на конкретный день"""
        try:
            from datetime import datetime, date
            
            # Преобразуем day в объект date для сравнения
            if isinstance(day, str):
                # Если день передан как строка, парсим её
                try:
                    day_obj = datetime.strptime(day, '%d.%m.%Y').date()
                except ValueError:
                    try:
                        day_obj = datetime.strptime(day, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"❌ Cannot parse day: {day}")
                        return False
            elif isinstance(day, datetime):
                day_obj = day.date()
            elif isinstance(day, date):
                day_obj = day
            else:
                print(f"❌ Unsupported day type: {type(day)}")
                return False
                
            print(f"🔍 Checking availability for day: {day_obj}")
            
            # Проверяем доступность через расписание
            # Сначала проверяем, что это рабочий день (понедельник-пятница)
            if day_obj.weekday() >= 5:  # 5=суббота, 6=воскресенье
                print(f"❌ Doctor is NOT available on {day_obj} (weekend)")
                return False
                
            # Проверяем, что дата не в прошлом
            if day_obj < datetime.now().date():
                print(f"❌ Doctor is NOT available on {day_obj} (past date)")
                return False
                
            # Проверяем через расписание, если оно есть
            if hasattr(self, 'schedule') and self.schedule:
                # Ищем дату в расписании
                for schedule_date, slots in self.schedule.items():
                    if isinstance(schedule_date, str):
                        schedule_date_obj = datetime.strptime(schedule_date, '%Y-%m-%d').date()
                    elif isinstance(schedule_date, date):
                        schedule_date_obj = schedule_date
                    elif isinstance(schedule_date, datetime):
                        schedule_date_obj = schedule_date.date()
                    else:
                        continue
                        
                    if schedule_date_obj == day_obj and slots:
                        print(f"✅ Doctor is available on {day_obj} (found in schedule)")
                        return True
            
            # Если расписания нет или дата не найдена, считаем что доступен в рабочие дни
            print(f"✅ Doctor is available on {day_obj} (working day, default schedule)")
            return True
            
        except Exception as e:
            print(f"❌ Error in check_availability: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# =========================== МЕДИЦИНСКИЕ ЗАПИСИ ===========================

class HealthRecord(BaseModel):
    """
    Медицинская карта пациента.
    """
    patient_id: str
    medical_history: Dict[str, Any] = Field(default_factory=dict)
    diseases: list[str] = []
    test_results: list[str] = []
    prescription: list[str] = []

    @property
    def id(self) -> str:
        return f'HL{self.patient_id}'

    def show_info(self):
        return {'Медицинские записи': self.show_history(),
                'Заболевания': self.show_diseases(),
                'Результаты анализов': self.show_test_results(),
                'Рецепты': self.show_prescription()}

    def add_medical_history(self, report):
        '''
        Получает от врача данные и складывает в БД
        '''
        try:
            response = requests.get(f"{database_url}/medcare-health-records/{self.id}")
            response.raise_for_status()
            current_data = response.json()

            current_data['medical_history'] = {**current_data['medical_history'],**report}

            put_response= requests.put(
                f"{database_url}/medcare-health-records/{self.id}",
                json=current_data)

            return 'Запись успешно добавлена'
        except:
            return None

    def show_diseases(self):
        if not self.diseases:
            return 'Нет подтвержденных заболеваний'
        else:
            return self.diseases

    def show_test_results(self):
        if not self.test_results:
            return 'Нет результатов'
        else:
            return self.test_results

    def show_prescription(self):
        if not self.prescription:
            return 'Нет назначенных рецептов'
        else:
            return self.prescription

    def show_history(self):
        if not self.medical_history:
            return 'Пока тут пусто'
        else:
            return self.medical_history


# =========================== ЗАПИСЬ НА ПРИЁМ ===========================

class Appointment:
    """
    Объект записи к врачу.
    """
    def __init__(self, id, date, room, doctor_id, patient_id,status):
        self.id = id
        self.date = date
        self.room = room
        self.doctor_id = doctor_id
        self.patient_id = patient_id
        self.status=status

    def get_id(self):
        return self.id

    def get_status(self):
        return self.status

    def get_health_record(self):
        health_record= References.get_health_record(self.patient_id)
        return health_record

    def get_date(self):
        return datetime.fromisoformat(self.date)

    def get_doctor(self):
        doctor=References.get_doctor_from_db(self.doctor_id)
        return doctor

    def get_patient(self):
        patient=References.get_patient_from_db(self.patient_id)
        return patient

    def show_info(self): #представление объекта класса в понятном виде
        return {"ID записи": self.id,
                "Дата посещения": self.date,
                "Кабинет": self.room,
                "Врач": f'{self.get_doctor().get_name()} (id: {self.doctor_id})',
                "Пациент": self.get_patient().get_name()}


# =========================== СПРАВОЧНИК ===========================

class References():
    '''
    Справочник системы для взаимодействия с БД
    '''

    def get_doctors(speciality: str=None): #получение врачей по специальности или списка всех врачей
        try:
            response = requests.get(f"{database_url}/medcare-doctors/_all_docs?include_docs=true")
            data = response.json()
            documents = [row["doc"] for row in data.get("rows", []) if "doc" in row]

            return [
                {'id': doc['_id'], 'name': doc['name'], 'speciality': doc['speciality']}
                for doc in documents
                if not speciality or doc['speciality'] == speciality
            ]
        except:
            return None

    def get_services(): #получение списка всех услуг
        try:
            response = requests.get(f"{database_url}/medcare-services/services")
            raw = response.json()
            return {'list_services': raw['list_services']}
        except:
            return None

    @staticmethod
    def get_doctor_from_db(doctor_id):
        try:
            response = requests.get(
                f"http://admin:password@localhost:5990/medcare-doctors/{doctor_id}"
            )
            raw = response.json()
            return Doctor(
                id=raw['_id'],  # Обратите внимание - '_id' из CouchDB
                name=raw['name'],
                speciality=raw['speciality'],
                qualification=raw.get('qualification', 'Врач'),
                experience=raw.get('experience', 'Не указан'),
                room=raw.get('room', '101')
            )
        except Exception:
            return None

    def get_patient_from_db(snils): #поиск пациента в БД
        try:
            response = requests.get(f"{database_url}/medcare-patients/{snils}")
            raw = response.json()
            raw['snils'] = raw.pop('_id')
            del raw['_rev']
            patient = Patient(**raw)
            return patient
        except:
            return None

    def get_health_record(snils): #поиск медицинской карты в БД
        try:
            id= f'HL{snils}'
            response = requests.get(f"{database_url}/medcare-health-records/{id}")
            raw = response.json()
            health_record= HealthRecord(patient_id=snils,
                                        medical_history=raw['medical_history'],
                                        diseases= raw['diseases'],
                                        test_results=raw['test_results'],
                                        prescription=raw['prescription'])
            return health_record
        except:
            return None


# =========================== ПЛАНИРОВЩИК ===========================

class Scheduler:
    """
    Планировщик — отвечает за создание и подтверждение записи.
    """

    @staticmethod
    def get_appointments(params: Optional[Dict[str, str]] = None): #возвращает записи приемов, опционально принимает id для фильтра записей
        try:
            response = requests.get(f"{database_url}/medcare-appointments/_all_docs?include_docs=true")
            rows = response.json()['rows']

            current_date=datetime.now().date()
            updated=False

            #сначала проверка на наличие устаревших записей в БД, смена статуса на Archive
            for doc_info in rows:
                doc = doc_info['doc']
                try:
                    appointment_date=doc.get('date')

                    appointment_date=datetime.fromisoformat(appointment_date).date()

                    if doc.get('status')=='Confirmed' and appointment_date < current_date:
                        doc['status']='Archive'
                        update_response= requests.put(
                            f"{database_url}/medcare-appointments/{doc['_id']}",
                            json=doc)
                        updated=True
                except (ValueError, KeyError) as e:
                    print(f"Error processing document {doc.get('_id')}: {str(e)}")
                    continue

            if updated:
                response = requests.get(f"{database_url}/medcare-appointments/_all_docs?include_docs=true")
                rows = response.json()['rows']

            filter_condition = lambda doc: (
                doc.get('status') in ['Confirmed', 'Created'] and
                (not params or all(doc.get(key) == value for key, value in params.items()))
            )

            filtered_docs = [doc_info['doc'] for doc_info in rows if filter_condition(doc_info['doc'])]

            appointments = []
            for doc in filtered_docs:
                appointment = Appointment(
                    id=doc['_id'],
                    date=doc['date'],
                    room=doc['room'],
                    doctor_id=doc['doctor_id'],
                    patient_id=doc['patient_id'],
                    status=doc['status']
                )
                appointments.append(appointment)

            return appointments
        except Exception as e:
            print(f"Error getting appointments: {str(e)}")
            return []

    @staticmethod
    def get_schedule(): #базовое расписание клиники
        base_schedule = {}
        start_date = datetime.now().date()
        
        for i in range(14):  # 2 недели вперед
            current_date = start_date + timedelta(days=i)
            if current_date.weekday() < 5:  # Понедельник-пятница
                time_slots = []
                for hour in range(9, 18):  # 9:00-18:00
                    for minute in [0, 30]:  # каждые 30 минут
                        time_slot = datetime.combine(current_date, time(hour, minute))
                        time_slots.append(time_slot)
                base_schedule[current_date] = time_slots
        
        return base_schedule

@staticmethod
def confirm_appointment(datetime_str, doctor_id, patient_snils):
    """Подтверждение записи с записью в CouchDB"""
    try:
        from datetime import datetime
        
        print(f"🔍 Confirming appointment: {datetime_str}")
        
        # Безопасный парсинг даты
        try:
            if '.' in datetime_str:
                appointment_date = datetime.strptime(datetime_str, '%d.%m.%Y %H:%M')
            else:
                appointment_date = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        except ValueError as ve:
            print(f"❌ Date parsing error: {ve}")
            return {"error": f"Неверный формат даты. Используйте DD.MM.YYYY HH:MM", "code": 400}
        
        print(f"📅 Parsed appointment date: {appointment_date}")
        
        # Найти врача
        doctor = References.get_doctor_from_db(doctor_id)
        if not doctor:
            return {"error": f"Врач с ID {doctor_id} не найден", "code": 404}
            
        print(f"👨‍⚕️ Found doctor: {doctor.name}")
        
        # Проверить доступность врача на этот день
        day_check = appointment_date.date()
        if not doctor.check_availability(day_check):
            return {"error": f"Врач недоступен на {day_check.strftime('%d.%m.%Y')}", "code": 400}
        
        # Найти пациента
        patient = References.get_patient_from_db(patient_snils)
        if not patient:
            return {"error": f"Пациент с СНИЛС {patient_snils} не найден", "code": 404}
            
        print(f"👤 Found patient: {patient.name}")
        
        # Проверить, что у врача это время свободно
        appointments = Scheduler.get_appointments({'doctor_id': doctor_id})
        for appointment in appointments:
            if appointment.get_date() == appointment_date:
                return {"error": "Слот уже занят", "code": 400}
        
        # Проверить, что пациент не записан к тому же врачу в этот день
        patient_appointments = Scheduler.get_appointments({'patient_id': patient_snils})
        for appointment in patient_appointments:
            # Проверка на тот же день к тому же врачу
            if (appointment.doctor_id == doctor_id and 
                appointment.get_date().date() == appointment_date.date()):
                return {"error": "Вы уже записаны к этому врачу на этот день", "code": 400}
            
            # Проверка на точное время
            if appointment.get_date() == appointment_date:
                return {"error": "У вас уже есть запись на это время", "code": 400}
        
        # НОВОЕ: Записываем в CouchDB
        appointment_id = f"apt_{int(datetime.now().timestamp())}"
        appointment_data = {
            "_id": appointment_id,
            "date": appointment_date.isoformat(),
            "room": doctor.room,
            "doctor_id": doctor_id,
            "patient_id": patient_snils,
            "status": "Confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                f"{database_url}/medcare-appointments",
                json=appointment_data,
                auth=database_auth
            )
            if response.status_code == 201:
                print(f"✅ Appointment saved to CouchDB: {appointment_id}")
            else:
                print(f"⚠️ CouchDB save warning: {response.status_code} - {response.text}")
                return {"error": "Ошибка сохранения в базу данных", "code": 500}
        except Exception as db_error:
            print(f"❌ CouchDB error: {db_error}")
            return {"error": f"Ошибка базы данных: {str(db_error)}", "code": 500}
        
        print(f"✅ Appointment created successfully: {appointment_id}")
        return {
            "message": "Запись успешно создана", 
            "appointment": appointment_data,
            "appointment_id": appointment_id
        }
        
    except Exception as e:
        print(f"❌ Error in confirm_appointment: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Ошибка при создании записи: {str(e)}", "code": 500}
    

# =========================== НОВЫЕ ФУНКЦИИ ДЛЯ РАСПИСАНИЯ =================

def get_doctor_slots(doctor_id: str, date_str: str):
    """
    Получение доступных и занятых слотов врача на конкретную дату
    Возвращает: {"available": [...], "booked": [...]}
    """
    try:
        from datetime import datetime, timedelta
        
        # Парсим дату
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Проверяем выходные
        if target_date.weekday() >= 5:  # 5=суббота, 6=воскресенье
            return {
                "date": date_str,
                "doctor_id": doctor_id,
                "available": [], 
                "booked": []
            }
        
        # Проверяем прошедшие даты
        if target_date < datetime.now().date():
            return {
                "date": date_str,
                "doctor_id": doctor_id,
                "available": [], 
                "booked": []
            }
        
        # Получаем базовое расписание (9:00-18:00 с интервалом 30 мин, обед 13:00-14:00)
        all_slots = []
        # Утренние слоты: 9:00-13:00
        for hour in range(9, 13):
            all_slots.extend([f"{hour:02d}:00", f"{hour:02d}:30"])
        # Дневные слоты: 14:00-18:00
        for hour in range(14, 18):
            all_slots.extend([f"{hour:02d}:00", f"{hour:02d}:30"])
        
        # Получаем врача
        doctor = References.get_doctor_from_db(doctor_id)
        if not doctor:
            raise Exception("Врач не найден")
            
        # Получаем занятые слоты из записей
        appointments = doctor.get_appointments_from_db()
        booked_slots = []
        
        for appointment in appointments:
            appointment_date = appointment.get_date()
            if appointment_date.date() == target_date:
                booked_slots.append(appointment_date.strftime("%H:%M"))
        
        # Вычисляем доступные слоты
        available_slots = [slot for slot in all_slots if slot not in booked_slots]
        
        return {
            "date": date_str,
            "doctor_id": doctor_id,
            "available": available_slots,
            "booked": booked_slots
        }
        
    except Exception as e:
        print(f"Ошибка получения слотов: {e}")
        return None

def check_slot_availability(doctor_id: str, date_str: str, time_str: str):
    """
    Проверка доступности конкретного времени
    """
    try:
        slots = get_doctor_slots(doctor_id, date_str)
        if not slots:
            return {"available": False, "reason": "Ошибка получения расписания"}
            
        available = time_str in slots["available"]
        
        return {
            "available": available,
            "doctor_id": doctor_id,
            "date": date_str,
            "time": time_str,
            "reason": "Слот уже занят" if not available else None
        }
        
    except Exception as e:
        return {"available": False, "reason": f"Ошибка: {str(e)}"}

def get_patient_conflicts(patient_snils: str, date_str: str, time_str: str):
    """
    Получение конфликтующих записей пациента на указанное время
    """
    try:
        patient = References.get_patient_from_db(patient_snils)
        if not patient:
            return []
            
        appointments = patient.get_appointments_from_db()
        conflicts = []
        
        for appointment in appointments:
            appointment_date = appointment.get_date()
            appointment_date_str = appointment_date.strftime("%Y-%m-%d")
            appointment_time_str = appointment_date.strftime("%H:%M")
            
            # Проверяем конфликт времени
            if appointment_date_str == date_str and appointment_time_str == time_str:
                doctor = appointment.get_doctor()
                conflicts.append({
                    "id": appointment.get_id(),
                    "doctor_id": appointment.doctor_id,
                    "doctor_name": doctor.get_name() if doctor else "Неизвестно",
                    "date": appointment_date_str,
                    "time": appointment_time_str,
                    "status": appointment.get_status()
                })
                
        return conflicts
        
    except Exception as e:
        print(f"Ошибка проверки конфликтов: {e}")
        return []

def check_slot_availability(doctor_id: str, date_str: str, time_str: str):
    """
    УЛУЧШЕННАЯ проверка доступности с проверкой CouchDB
    """
    try:
        # Получаем слоты врача
        slots_data = get_doctor_slots(doctor_id, date_str)
        
        if "error" in slots_data:
            return {"available": False, "reason": slots_data["error"]}
            
        # Проверяем доступность времени
        available = time_str in slots_data["available"]
        
        reason = None
        if not available:
            if time_str in slots_data["booked"]:
                reason = "Слот уже занят"
            else:
                reason = "Время не входит в рабочее расписание"
        
        return {
            "available": available,
            "doctor_id": doctor_id,
            "date": date_str,
            "time": time_str,
            "reason": reason
        }
        
    except Exception as e:
        return {"available": False, "reason": f"Ошибка: {str(e)}"}

def validate_appointment(appointment_data: dict):
    """
    РАСШИРЕННАЯ валидация с проверками конфликтов
    """
    try:
        doctor_id = appointment_data.get("doctor_id")
        patient_snils = appointment_data.get("patient_snils")
        date = appointment_data.get("date")
        time = appointment_data.get("time")
        
        errors = []
        
        # Базовые проверки
        if not doctor_id:
            errors.append("ID врача обязателен")
        if not patient_snils:
            errors.append("СНИЛС пациента обязателен")
        if not date:
            errors.append("Дата обязательна")
        if not time:
            errors.append("Время обязательно")
            
        if errors:
            return {"valid": False, "errors": errors}
        
        # Проверка существования врача и пациента
        doctor = References.get_doctor_from_db(doctor_id)
        if not doctor:
            errors.append("Врач не найден")
            
        patient = References.get_patient_from_db(patient_snils)
        if not patient:
            errors.append("Пациент не найден")
            
        # Проверка формата даты и времени
        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            if appointment_date < datetime.now().date():
                errors.append("Нельзя записаться на прошедшую дату")
        except ValueError:
            errors.append("Неверный формат даты (ожидается YYYY-MM-DD)")
            
        try:
            datetime.strptime(time, '%H:%M')
        except ValueError:
            errors.append("Неверный формат времени (ожидается HH:MM)")
            
        if errors:
            return {"valid": False, "errors": errors}
        
        # НОВАЯ проверка: доступность слота
        slot_check = check_slot_availability(doctor_id, date, time)
        if not slot_check["available"]:
            errors.append(f"Слот недоступен: {slot_check.get('reason', 'Неизвестная причина')}")
        
        # НОВАЯ проверка: конфликты пациента
        patient_appointments = Scheduler.get_appointments({'patient_id': patient_snils})
        appointment_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        
        for appointment in patient_appointments:
            # Проверка на тот же день к тому же врачу
            if (appointment.doctor_id == doctor_id and 
                appointment.get_date().date() == appointment_datetime.date()):
                errors.append("Вы уже записаны к этому врачу на этот день")
                break
            
            # Проверка на точное время
            if appointment.get_date() == appointment_datetime:
                errors.append("У вас уже есть запись на это время")
                break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "doctor_name": doctor.name if doctor else None,
            "patient_name": patient.name if patient else None
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Ошибка валидации: {str(e)}"]
        }

# =========================== ОБНОВЛЕННЫЕ ФУНКЦИИ API =================

def get_services():
    """Получение списка услуг"""
    try:
        response = requests.get(f"{database_url}/medcare-services/services")
        if response.status_code == 200:
            raw = response.json()
            return raw.get('list_services', [])
        return []
    except Exception as e:
        print(f"Ошибка получения услуг: {e}")
        return []

def get_doctors_list(speciality: str = None):
    """Получение списка врачей с дополнительной информацией"""
    try:
        response = requests.get(f"{database_url}/medcare-doctors/_all_docs?include_docs=true")
        if response.status_code != 200:
            return []
            
        data = response.json()
        documents = [row["doc"] for row in data.get("rows", []) if "doc" in row]
        
        doctors = []
        for doc in documents:
            if speciality and doc.get('speciality') != speciality:
                continue
                
            doctor_info = {
                'id': doc['_id'],
                'name': doc['name'],
                'speciality': doc['speciality'],
                'specialty': doc['speciality'],  # Дублируем для совместимости
                'qualification': doc.get('qualification', 'Врач'),
                'experience': doc.get('experience', 'Не указан'),
                'room': doc.get('room', '101'),
                'cabinet': doc.get('room', '101'),  # Дублируем для совместимости
                'photo': doc.get('photo'),
                'education': doc.get('education'),
                'achievements': doc.get('achievements', []),
                'description': doc.get('description', ''),
                'rating': doc.get('rating'),
                'reviews_count': doc.get('reviews_count'),
                'price': doc.get('price'),
                'duration': doc.get('duration', '30 мин')
            }
            doctors.append(doctor_info)
            
        return doctors
    except Exception as e:
        print(f"Ошибка получения врачей: {e}")
        return []

def get_doctor(doctor_id: str):
    """Получение информации о враче с расширенными данными"""
    try:
        response = requests.get(f"{database_url}/medcare-doctors/{doctor_id}")
        if response.status_code != 200:
            return None
            
        raw = response.json()
        return {
            'id': raw['_id'],
            'name': raw['name'],
            'speciality': raw['speciality'],
            'specialty': raw['speciality'],  # Дублируем для совместимости
            'qualification': raw.get('qualification', 'Врач'),
            'experience': raw.get('experience', 'Не указан'),
            'room': raw.get('room', '101'),
            'cabinet': raw.get('room', '101'),  # Дублируем для совместимости
            'photo': raw.get('photo'),
            'education': raw.get('education'),
            'achievements': raw.get('achievements', []),
            'description': raw.get('description', ''),
            'rating': raw.get('rating'),
            'reviews_count': raw.get('reviews_count'),
            'price': raw.get('price'),
            'duration': raw.get('duration', '30 мин')
        }
    except Exception as e:
        print(f"Ошибка получения врача: {e}")
        return None

def get_patient(snils: str):
    """Получение информации о пациенте"""
    try:
        patient = References.get_patient_from_db(snils)
        if not patient:
            return None
            
        return {
            'id': patient.snils,
            'snils': patient.snils,
            'name': patient.name,
            'phone': patient.phone,
            'telephone': patient.phone,  # Дублируем для совместимости
            'email': patient.email,
            'address': patient.address,
            'birth_date': patient.birthdate,
            'birthdate': patient.birthdate,  # Дублируем для совместимости
            'eligibility': patient.eligibility
        }
    except Exception as e:
        print(f"Ошибка получения пациента: {e}")
        return None

def get_patient_appointments(snils: str):
    """Получение всех записей пациента из CouchDB"""
    try:
        appointments = Scheduler.get_appointments({'patient_id': snils})
        if not appointments:
            return []
            
        result = []
        for appointment in appointments:
            doctor = appointment.get_doctor()
            appointment_info = {
                'id': appointment.get_id(),
                'doctor_id': appointment.doctor_id,
                'doctor_name': doctor.get_name() if doctor else 'Неизвестно',
                'doctor_specialty': doctor.get_speciality() if doctor else 'Неизвестно',
                'date': appointment.get_date().strftime('%Y-%m-%d'),
                'time': appointment.get_date().strftime('%H:%M'),
                'datetime': appointment.date,
                'status': appointment.get_status(),
                'room': appointment.room,
                'created_at': appointment.date
            }
            result.append(appointment_info)
            
        return result
    except Exception as e:
        print(f"Ошибка получения записей пациента: {e}")
        return []


def get_doctor_appointments(doctor_id: str):
    """Получение всех записей к врачу из CouchDB"""
    try:
        appointments = Scheduler.get_appointments({'doctor_id': doctor_id})
        if not appointments:
            return []
            
        result = []
        for appointment in appointments:
            patient = appointment.get_patient()
            appointment_info = {
                'id': appointment.get_id(),
                'patient_snils': appointment.patient_id,
                'patient_name': patient.get_name() if patient else 'Неизвестно',
                'date': appointment.get_date().strftime('%Y-%m-%d'),
                'time': appointment.get_date().strftime('%H:%M'),
                'datetime': appointment.date,
                'status': appointment.get_status(),
                'room': appointment.room
            }
            result.append(appointment_info)
            
        return result
    except Exception as e:
        print(f"Ошибка получения записей врача: {e}")
        return []


def get_medical_records(snils: str):
    """Получение медицинской карты пациента"""
    try:
        health_record = References.get_health_record(snils)
        if not health_record:
            return None
            
        return {
            'patient_snils': snils,
            'medical_history': health_record.medical_history,
            'diseases': health_record.diseases,
            'test_results': health_record.test_results,
            'prescription': health_record.prescription,
            'records': []  # Можно преобразовать medical_history в список
        }
    except Exception as e:
        print(f"Ошибка получения медкарты: {e}")
        return None

def create_appointment(date: str, doctor_id: str, patient_id: str):
    """
    Адаптер под запрос POST /appointment/{params}
    ИСПРАВЛЕНО: теперь принимает дату в формате YYYY-MM-DD HH:MM
    """
    try:
        # Преобразуем дату из ISO формата в нужный для старой функции
        if 'T' in date:  # Если пришла дата в ISO формате
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%d.%m.%Y %H:%M')
        else:
            formatted_date = date
            
        result = Scheduler.confirm_appointment(formatted_date, doctor_id, patient_id)
        
        if isinstance(result, dict) and 'error' in result:
            raise HTTPException(
                status_code=result.get('code', 400),
                detail=result['error']
            )
        else:
            return {"message": result, "status": "success"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def add_medical_report(appointment_id: str, report_text: str):
    """Добавление медицинского отчета к записи"""
    try:
        # Получаем информацию о записи
        response = requests.get(f"{database_url}/medcare-appointments/{appointment_id}")
        if response.status_code != 200:
            raise Exception("Запись не найдена")
            
        appointment_data = response.json()
        patient_id = appointment_data.get('patient_id')
        doctor_id = appointment_data.get('doctor_id')
        
        if not patient_id or not doctor_id:
            raise Exception("Неполные данные записи")
            
        # Получаем врача
        doctor = References.get_doctor_from_db(doctor_id)
        if not doctor:
            raise Exception("Врач не найден")
            
        # Получаем медкарту пациента
        health_record = References.get_health_record(patient_id)
        if not health_record:
            raise Exception("Медкарта не найдена")
            
        # Добавляем отчет
        report_date = datetime.now()
        report = {
            datetime.isoformat(report_date): {
                'Направление': doctor.get_speciality(),
                'Врач': doctor.get_name(),
                'Комментарий': report_text,
                'ID записи': appointment_id
            }
        }
        
        result = health_record.add_medical_history(report)
        if result:
            return "Медицинский отчет успешно добавлен"
        else:
            raise Exception("Ошибка добавления отчета")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# ================= ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ЗАПИСИ К ВРАЧУ =================

def get_doctor_slots(doctor_id: str, date_str: str):
    """
    УЛУЧШЕННАЯ версия: Получение свободных слотов врача с проверкой CouchDB
    """
    try:
        from datetime import datetime, time
        
        # Парсим дату
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Проверяем выходные и прошедшие даты
        if target_date.weekday() >= 5 or target_date < datetime.now().date():
            return {
                "date": date_str,
                "doctor_id": doctor_id,
                "available": [], 
                "booked": []
            }
        
        # Получаем врача
        doctor = References.get_doctor_from_db(doctor_id)
        if not doctor:
            return {
                "date": date_str,
                "doctor_id": doctor_id,
                "available": [],
                "booked": [],
                "error": "Врач не найден"
            }
            
        # Базовое расписание: 9:00-18:00, обед 13:00-14:00, интервал 30 мин
        all_slots = []
        # Утренние слоты: 9:00-13:00
        for hour in range(9, 13):
            all_slots.extend([f"{hour:02d}:00", f"{hour:02d}:30"])
        # Дневные слоты: 14:00-18:00
        for hour in range(14, 18):
            all_slots.extend([f"{hour:02d}:00", f"{hour:02d}:30"])
        
        # УЛУЧШЕННАЯ проверка: получаем занятые слоты из CouchDB
        appointments = Scheduler.get_appointments({'doctor_id': doctor_id})
        booked_slots = []
        
        for appointment in appointments:
            appointment_date = appointment.get_date()
            if appointment_date.date() == target_date:
                booked_slots.append(appointment_date.strftime("%H:%M"))
        
        # Вычисляем доступные слоты
        available_slots = [slot for slot in all_slots if slot not in booked_slots]
        
        return {
            "date": date_str,
            "doctor_id": doctor_id,
            "doctor_name": doctor.name,
            "available": available_slots,
            "booked": booked_slots,
            "total_slots": len(all_slots),
            "available_count": len(available_slots),
            "booked_count": len(booked_slots)
        }
        
    except Exception as e:
        print(f"Ошибка получения слотов: {e}")
        return {
            "date": date_str,
            "doctor_id": doctor_id,
            "available": [],
            "booked": [],
            "error": str(e)
        }


def check_slot_availability(doctor_id: str, date_str: str, time_str: str):
    """
    УЛУЧШЕННАЯ проверка доступности с проверкой CouchDB
    """
    try:
        # Получаем слоты врача
        slots_data = get_doctor_slots(doctor_id, date_str)
        
        if "error" in slots_data:
            return {"available": False, "reason": slots_data["error"]}
            
        # Проверяем доступность времени
        available = time_str in slots_data["available"]
        
        reason = None
        if not available:
            if time_str in slots_data["booked"]:
                reason = "Слот уже занят"
            else:
                reason = "Время не входит в рабочее расписание"
        
        return {
            "available": available,
            "doctor_id": doctor_id,
            "date": date_str,
            "time": time_str,
            "reason": reason
        }
        
    except Exception as e:
        return {"available": False, "reason": f"Ошибка: {str(e)}"}

def get_patient_conflicts(patient_snils: str, date_str: str, time_str: str):
    """
    Получение конфликтующих записей пациента на указанное время
    """
    try:
        patient = References.get_patient_from_db(patient_snils)
        if not patient:
            return []
            
        appointments = patient.get_appointments_from_db()
        conflicts = []
        
        for appointment in appointments:
            appointment_date = appointment.get_date()
            appointment_date_str = appointment_date.strftime("%Y-%m-%d")
            appointment_time_str = appointment_date.strftime("%H:%M")
            
            # Проверяем конфликт времени
            if appointment_date_str == date_str and appointment_time_str == time_str:
                doctor = appointment.get_doctor()
                conflicts.append({
                    "id": appointment.get_id(),
                    "doctor_id": appointment.doctor_id,
                    "doctor_name": doctor.get_name() if doctor else "Неизвестно",
                    "date": appointment_date_str,
                    "time": appointment_time_str,
                    "status": appointment.get_status()
                })
                
        return conflicts
        
    except Exception as e:
        print(f"Ошибка проверки конфликтов: {e}")
        return []
    
    
def create_appointment_v2(datetime_str: str, doctor_id: str, patient_snils: str, 
                         patient_name: str, patient_phone: str, complaints: str):
    """
    УЛУЧШЕННАЯ версия создания записи с полными проверками и записью в CouchDB
    """
    try:
        from datetime import datetime
        
        print(f"🔄 Creating appointment v2...")
        print(f"🔄 Input datetime_str: {datetime_str}")
        print(f"👨‍⚕️ Doctor ID: {doctor_id}")
        print(f"👤 Patient SNILS: {patient_snils}")
        
        # Используем функцию confirm_appointment, которая уже делает все проверки
        result = confirm_appointment(datetime_str, doctor_id, patient_snils)
        
        print(f"📝 Scheduler result: {result}")
        
        if isinstance(result, dict) and 'error' in result:
            raise HTTPException(
                status_code=result.get('code', 400),
                detail=result['error']
            )
        
        # Дополняем результат данными пациента
        if isinstance(result, dict) and 'appointment' in result:
            result['appointment'].update({
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "complaints": complaints
            })
            
            # Можно обновить запись в CouchDB с дополнительными данными
            try:
                appointment_id = result['appointment']['_id']
                updated_data = result['appointment'].copy()
                
                response = requests.put(
                    f"{database_url}/medcare-appointments/{appointment_id}",
                    json=updated_data,
                    auth=database_auth
                )
                if response.status_code == 200:
                    print(f"✅ Updated appointment in CouchDB with additional data")
            except Exception as update_error:
                print(f"⚠️ Warning: Could not update with additional data: {update_error}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in create_appointment_v2: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))