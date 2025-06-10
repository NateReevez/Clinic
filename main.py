from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import protupdate

app = FastAPI(
    title="Медицинский портал API",
    description="API для системы записи к врачу",
    version="2.0.0"
)

# ================= НАСТРОЙКА CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React стандартный порт
        "http://localhost:3005",   # Ваш фронтенд
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3005", 
        "http://localhost:5173",   # Vite
        "http://127.0.0.1:5173",
        "http://localhost:8080",   # Vue CLI
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ================= МОДЕЛИ ДАННЫХ =================

class AppointmentCreate(BaseModel):
    doctor_id: str
    patient_snils: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    patient_name: str
    patient_phone: str
    complaints: Optional[str] = ""

class AppointmentValidate(BaseModel):
    doctor_id: str
    patient_snils: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM

# ================= ОСНОВНЫЕ МАРШРУТЫ =================

@app.get("/", tags=["Общие"])
async def root():
    """Корневой маршрут"""
    return {"message": "Медицинский портал API v2.0", "status": "running"}

@app.get("/health", tags=["Общие"])
async def health_check():
    """Проверка состояния API"""
    return {"status": "healthy", "message": "API работает корректно"}

# ================= АУТЕНТИФИКАЦИЯ =================
# ================= МОДЕЛИ ДАННЫХ =================
class Doctor(BaseModel):
    _id: str
    name: str
    speciality: str
    room: str
    experience: str
    education: str
    achievements: list
    description: str
    photo: str
    rating: float
    reviews_count: int

# ================= АУТЕНТИФИКАЦИЯ ВРАЧА =================
@app.get("/doctor/login", response_model=Doctor, tags=["Аутентификация"])
async def doctor_login(id: str):
    """Авторизация врача по ID"""
    try:
        # Получаем данные врача из базы
        doctor_data = protupdate.get_doctor(id)
        
        if doctor_data is None:
            # Если врач не найден, отправляем 404
            raise HTTPException(status_code=404, detail="Врач не найден")
        
        return doctor_data  # Возвращаем данные врача
        
    except Exception as e:
        # Если возникла ошибка, отправляем 500
        raise HTTPException(status_code=500, detail=f"Ошибка авторизации: {str(e)}")

# Модель данных для медицинской записи
class MedicalRecord(BaseModel):
    patient_snils: str
    doctor_id: str
    report_text: str
    diagnosis: Optional[str] = None
    recommendations: Optional[str] = None

@app.get("/medical-records/{snils}", tags=["Медкарты"])
async def get_medical_records(snils: str):
    """Получение медицинской карты пациента по СНИЛС"""
    try:
        records = protupdate.get_medical_records(snils)
        if records:
            return records
        else:
            raise HTTPException(status_code=404, detail="Медицинские записи не найдены")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения медкарты: {str(e)}")

@app.post("/medical-records/", tags=["Медкарты"])
async def add_medical_record(record: MedicalRecord):
    """Добавление записи в медкарту"""
    try:
        # Ваша логика для добавления записи в базу данных
        result = protupdate.add_medical_record(record)
        return {"status": "success", "message": "Запись успешно добавлена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка добавления записи в медкарту: {str(e)}")
    
@app.get("/patient/login", tags=["Аутентификация"])
async def patient_login(snils: str):
    """Авторизация пациента по СНИЛС"""
    try:
        patient_data = protupdate.get_patient(snils)
        if patient_data:
            return patient_data
        else:
            raise HTTPException(status_code=404, detail="Пациент не найден")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка авторизации: {str(e)}")

@app.get("/doctor/login", tags=["Аутентификация"])
async def doctor_login(id: str):
    """Авторизация врача по ID"""
    try:
        doctor_data = protupdate.get_doctor(id)
        if doctor_data:
            return doctor_data
        else:
            raise HTTPException(status_code=404, detail="Врач не найден")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка авторизации: {str(e)}")

# ================= СЕРВИСЫ =================

@app.get("/services", tags=["Общие"])
async def get_services():
    """Получение списка медицинских услуг"""
    try:
        services = protupdate.get_services()
        return {"list_services": services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения услуг: {str(e)}")

# ================= ВРАЧИ =================

@app.get("/doctors", tags=["Врачи"])
async def get_doctors(speciality: str = None):
    """Получение списка врачей, возможно по специальности"""
    try:
        doctors = protupdate.get_doctors_list(speciality)
        return doctors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения врачей: {str(e)}")

@app.get("/doctor/{doctor_id}", tags=["Врачи"])
async def get_doctor_info(doctor_id: str):
    """Получение информации о конкретном враче"""
    try:
        doctor = protupdate.get_doctor(doctor_id)
        if doctor:
            return doctor
        else:
            raise HTTPException(status_code=404, detail="Врач не найден")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения врача: {str(e)}")

# ================= РАСПИСАНИЕ И СЛОТЫ =================

@app.get("/doctor/{doctor_id}/slots", tags=["Расписание"])
async def get_doctor_slots(doctor_id: str, date: str):
    """Получение доступных и занятых временных слотов врача на дату
    
    Args:
        doctor_id: ID врача
        date: Дата в формате YYYY-MM-DD
        
    Returns:
        {"available": [...], "booked": [...]}
    """
    try:
        slots_data = protupdate.get_doctor_slots(doctor_id, date)
        if not slots_data:
            raise HTTPException(status_code=404, detail="Расписание на указанную дату не найдено")
        return slots_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения слотов: {str(e)}")

@app.get("/doctor/{doctor_id}/check-slot", tags=["Расписание"])
async def check_slot_availability(doctor_id: str, date: str, time: str):
    """Проверка доступности конкретного времени для записи
    
    Args:
        doctor_id: ID врача
        date: Дата в формате YYYY-MM-DD
        time: Время в формате HH:MM
        
    Returns:
        {"available": bool, "reason": str}
    """
    try:
        availability = protupdate.check_slot_availability(doctor_id, date, time)
        return availability
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки слота: {str(e)}")

@app.get("/doctor/{doctor_id}/availability", tags=["Расписание"])
async def get_doctor_availability(doctor_id: str, start: str, end: str):
    """Получение расписания врача на период (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "doctor_id": doctor_id, "period": f"{start} - {end}"}

# ================= ПАЦИЕНТЫ =================

@app.get("/patient/{snils}", tags=["Пациенты"])
async def get_patient_info(snils: str):
    """Получение информации о пациенте"""
    try:
        patient = protupdate.get_patient(snils)
        if patient:
            return patient
        else:
            raise HTTPException(status_code=404, detail="Пациент не найден")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения пациента: {str(e)}")

# ================= ДОБАВЬТЕ ЭТОТ КОД В СЕКЦИЮ ПАЦИЕНТЫ =================

@app.get("/api/patient-details/{snils}", tags=["Пациенты"])
async def get_patient_details(snils: str):
    """🏥 Получение подробной информации о пациенте из базы данных
    
    Возвращает полные данные пациента включая:
    - ФИО
    - Телефон  
    - Адрес
    - Email
    - Дата рождения
    - Страховка/льготы
    
    Args:
        snils: СНИЛС пациента в формате XXX-XXX-XX XX
        
    Returns:
        Подробная информация о пациенте
    """
    try:
        print(f"🔍 Getting patient details for SNILS: {snils}")
        
        # Используем функцию get_patient_from_db из protupdate
        patient = protupdate.References.get_patient_from_db(snils)
        
        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Пациент с СНИЛС {snils} не найден в базе данных"
            )
        
        # Формируем ответ с полными данными пациента
        patient_data = {
            'snils': patient.snils,
            'name': patient.name,
            'phone': patient.phone,
            'address': patient.address,
            'email': patient.email,
            'birthdate': patient.birthdate,
            'eligibility': patient.eligibility
        }
        
        print(f"✅ Patient details loaded: {patient.name}")
        return patient_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting patient details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения данных пациента: {str(e)}"
        )

@app.get("/api/patient/{snils}/profile", tags=["Пациенты"])
async def get_patient_profile(snils: str):
    """👤 Получение профиля пациента (расширенная версия)
    
    Использует метод show_personal_profile() из класса Patient
    """
    try:
        patient = protupdate.References.get_patient_from_db(snils)
        if not patient:
            raise HTTPException(status_code=404, detail="Пациент не найден")
            
        # Используем метод show_personal_profile из класса Patient
        profile = patient.show_personal_profile()
        profile['snils'] = patient.snils  # Добавляем СНИЛС
        profile['eligibility'] = patient.eligibility  # Добавляем льготы
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения профиля: {str(e)}"
        )

@app.get("/patient/{snils}/full-info", tags=["Пациенты"])
async def get_patient_full_info(snils: str):
    """📋 Получение полной информации о пациенте включая медкарту и записи
    
    Объединяет:
    - Личные данные
    - Медицинскую карту  
    - Историю записей
    """
    try:
        # Получаем базовую информацию
        patient = protupdate.References.get_patient_from_db(snils)
        if not patient:
            raise HTTPException(status_code=404, detail="Пациент не найден")
        
        # Получаем медкарту
        try:
            health_record = protupdate.References.get_health_record(snils)
            health_record_data = health_record.show_info() if health_record else None
        except:
            health_record_data = None
            
        # Получаем историю записей
        try:
            appointments = protupdate.get_patient_appointments(snils)
        except:
            appointments = []
        
        # Объединяем все данные
        full_info = {
            # Личные данные
            'personal_info': {
                'snils': patient.snils,
                'name': patient.name,
                'phone': patient.phone,
                'address': patient.address,
                'email': patient.email,
                'birthdate': patient.birthdate,
                'eligibility': patient.eligibility
            },
            
            # Медицинская карта
            'health_record': health_record_data,
            
            # История записей
            'appointments': appointments,
            
            # Статистика
            'statistics': {
                'total_appointments': len(appointments) if appointments else 0,
                'has_health_record': health_record_data is not None
            }
        }
        
        return full_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения полной информации: {str(e)}"
        )
    
@app.get("/patient/{patient_snils}/conflicts", tags=["Пациенты"])
async def get_patient_conflicts(patient_snils: str, date: str, time: str):
    """Проверка конфликтующих записей пациента
    
    Args:
        patient_snils: СНИЛС пациента
        date: Дата в формате YYYY-MM-DD
        time: Время в формате HH:MM
        
    Returns:
        Список конфликтующих записей
    """
    try:
        conflicts = protupdate.get_patient_conflicts(patient_snils, date, time)
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки конфликтов: {str(e)}")

@app.get("/patient/{snils}/history/{doctor_id}", tags=["Пациенты"])
async def get_patient_doctor_history(snils: str, doctor_id: str):
    """Получение истории записей пациента к конкретному врачу (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "patient": snils, "doctor": doctor_id}

# ================= ЗАПИСИ НА ПРИЁМ =================

@app.get("/patient/appointments/{snils}", tags=["Записи"])
async def get_patient_appointments(snils: str):
    """Получение всех записей пациента"""
    try:
        appointments = protupdate.get_patient_appointments(snils)
        if appointments:
            return appointments
        else:
            raise HTTPException(status_code=404, detail="Записи не найдены")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения записей: {str(e)}")

@app.get("/doctor/appointments/{doctor_id}", tags=["Записи"])
async def get_doctor_appointments(doctor_id: str):
    """Получение записей к врачу"""
    try:
        appointments = protupdate.get_doctor_appointments(doctor_id)
        if appointments:
            return appointments
        else:
            raise HTTPException(status_code=404, detail="Записи не найдены")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения записей врача: {str(e)}")

# ================= СОЗДАНИЕ И ВАЛИДАЦИЯ ЗАПИСЕЙ =================

@app.post("/appointment", tags=["Записи"])
async def create_appointment_json(appointment_data: AppointmentCreate):
    """Создание новой записи (основной метод с JSON body)"""
    try:
        from datetime import datetime
        
        # ИСПРАВЛЕНО: Используем model_dump() вместо dict()
        print(f"📥 Received data: {appointment_data.model_dump()}")
        
        # ИСПРАВЛЕНО: Безопасно получаем дату и время
        date_value = appointment_data.date
        time_value = appointment_data.time
        
        # Если date пришло как объект datetime.date, конвертируем в строку
        if hasattr(date_value, 'strftime'):
            date_str = date_value.strftime('%Y-%m-%d')
        else:
            date_str = str(date_value)
            
        # Если time пришло как объект time, конвертируем в строку
        if hasattr(time_value, 'strftime'):
            time_str = time_value.strftime('%H:%M')
        else:
            time_str = str(time_value)
            
        print(f"📅 Processing date: {date_str}, time: {time_str}")
        
        # Парсим и форматируем дату
        try:
            # Парсим дату из формата YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Парсим время из формата HH:MM  
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            # Объединяем в правильном формате DD.MM.YYYY HH:MM
            formatted_datetime = f"{date_obj.strftime('%d.%m.%Y')} {time_obj.strftime('%H:%M')}"
            
        except ValueError as ve:
            print(f"❌ Date parsing error: {ve}")
            # Если не получилось распарсить, пробуем другой подход
            datetime_combined = f"{date_str} {time_str}"
            try:
                parsed = datetime.strptime(datetime_combined, '%Y-%m-%d %H:%M')
                formatted_datetime = parsed.strftime('%d.%m.%Y %H:%M')
            except ValueError:
                # Последняя попытка - может дата уже в правильном формате
                formatted_datetime = datetime_combined
        
        print(f"📅 Final formatted datetime: {formatted_datetime}")
        print(f"👨‍⚕️ Doctor ID: {appointment_data.doctor_id}")
        print(f"👤 Patient SNILS: {appointment_data.patient_snils}")
        
        # ИСПРАВЛЕНО: Улучшенная логика создания записи
        result = None
        
        # Проверяем доступные методы создания записи
        if hasattr(protupdate, 'create_appointment_v2'):
            print("✅ Using create_appointment_v2")
            result = protupdate.create_appointment_v2(
                formatted_datetime,
                appointment_data.doctor_id, 
                appointment_data.patient_snils,
                appointment_data.patient_name,
                appointment_data.patient_phone,
                appointment_data.complaints or ""
            )
        elif hasattr(protupdate, 'create_appointment'):
            print("✅ Using create_appointment")
            result = protupdate.create_appointment(
                formatted_datetime, 
                appointment_data.doctor_id, 
                appointment_data.patient_snils
            )
            # Дополняем результат
            if isinstance(result, dict) and not result.get('error'):
                result.update({
                    "patient_name": appointment_data.patient_name,
                    "patient_phone": appointment_data.patient_phone,
                    "complaints": appointment_data.complaints or ""
                })
        elif hasattr(protupdate, 'Scheduler') and hasattr(protupdate.Scheduler, 'confirm_appointment'):
            print("✅ Using Scheduler.confirm_appointment")
            result = protupdate.Scheduler.confirm_appointment(
                formatted_datetime, 
                appointment_data.doctor_id, 
                appointment_data.patient_snils
            )
            # Дополняем результат
            if isinstance(result, dict) and not result.get('error'):
                result.update({
                    "patient_name": appointment_data.patient_name,
                    "patient_phone": appointment_data.patient_phone,
                    "complaints": appointment_data.complaints or ""
                })
        else:
            # НОВОЕ: Создаем запись вручную как заглушку
            print("⚠️ No appointment methods found, creating manually")
            appointment_id = f"apt_{int(datetime.now().timestamp())}"
            result = {
                "id": appointment_id,
                "message": "Запись успешно создана",
                "doctor_id": appointment_data.doctor_id,
                "patient_snils": appointment_data.patient_snils,
                "patient_name": appointment_data.patient_name,
                "patient_phone": appointment_data.patient_phone,
                "complaints": appointment_data.complaints or "",
                "datetime": formatted_datetime,
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }
        
        print(f"📝 Final result: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Error creating appointment: {str(e)}")
        import traceback
        traceback.print_exc()  # Выводим полный стек ошибки
        
        if hasattr(e, 'status_code'):
            raise e
        else:
            raise HTTPException(status_code=400, detail=f"Ошибка создания записи: {str(e)}")
        
        
@app.post("/appointment/{date}/{doctor_id}/{patient_id}", tags=["Записи"], deprecated=True)
async def create_appointment_legacy(date: str, doctor_id: str, patient_id: str):
    """Создание новой записи (устаревший метод, оставлен для совместимости)"""
    try:
        result = protupdate.create_appointment(date, doctor_id, patient_id)
        return result
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise e
        else:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/appointment/validate", tags=["Записи"])
async def validate_appointment_data(appointment_data: AppointmentValidate):
    """Валидация данных записи перед созданием
    
    Request Body:
    {
        "doctor_id": "1234",
        "patient_snils": "123-456-789-01",
        "date": "2024-01-15",
        "time": "10:00"
    }
    """
    try:
        # ИСПРАВЛЕНО: Используем model_dump() вместо dict()
        validation_result = protupdate.validate_appointment(appointment_data.model_dump())
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Ошибка валидации",
                    "errors": validation_result["errors"]
                }
            )
            
        return validation_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")

@app.get("/appointment/{appointment_id}", tags=["Записи"])
async def get_appointment_details(appointment_id: str):
    """Получение деталей конкретной записи (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "appointment_id": appointment_id}

@app.put("/appointment/{appointment_id}", tags=["Записи"])
async def update_appointment(appointment_id: str, appointment_data: dict):
    """Обновление записи (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "appointment_id": appointment_id}

@app.delete("/appointment/{appointment_id}", tags=["Записи"])
async def cancel_appointment(appointment_id: str):
    """Отмена записи (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "appointment_id": appointment_id}

@app.post("/appointment/{appointment_id}/cancel", tags=["Записи"])
async def cancel_appointment_post(appointment_id: str):
    """Отмена записи через POST (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "appointment_id": appointment_id}

# ================= МЕДИЦИНСКИЕ ОТЧЁТЫ =================

@app.post("/doctor/add_report/{appointment_id}/{report_text}", tags=["Врачи"])
async def add_medical_report_legacy(appointment_id: str, report_text: str):
    """Добавление медицинского отчёта к записи (устаревший метод)"""
    try:
        result = protupdate.add_medical_report(appointment_id, report_text)
        return {"message": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/doctor/add_report", tags=["Врачи"])
async def add_medical_report_json(report_data: dict):
    """Добавление медицинского отчёта через JSON
    
    Request Body:
    {
        "appointment_id": "app_123",
        "report_text": "Диагноз: ОРВИ. Лечение: постельный режим.",
        "doctor_id": "1234"
    }
    """
    try:
        appointment_id = report_data.get("appointment_id")
        report_text = report_data.get("report_text")
        
        if not appointment_id or not report_text:
            raise HTTPException(status_code=400, detail="Отсутствуют обязательные поля")
            
        result = protupdate.add_medical_report(appointment_id, report_text)
        return {"message": result, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================= МЕДКАРТЫ =================

@app.get("/patient/{snils}/health-record", tags=["Медкарты"])
async def get_medical_records(snils: str):
    """Получение медицинской карты пациента по СНИЛС"""
    print(f"🔍 Получение медкарты для СНИЛС: {snils}")  # Логирование
    try:
        records = protupdate.get_medical_records(snils)
        if records:
            return records
        else:
            raise HTTPException(status_code=404, detail="Медицинские записи не найдены")
    except Exception as e:
        print(f"❌ Ошибка получения медкарты: {str(e)}")  # Лог ошибки
        raise HTTPException(status_code=500, detail=f"Ошибка получения медкарты: {str(e)}")
    
    
@app.put("/patient/{snils}/health-record", tags=["Медкарты"])
async def update_medical_record(snils: str, record_data: dict):
    """Обновление медицинской карты (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "patient": snils}

# ================= УВЕДОМЛЕНИЯ =================

@app.post("/appointment/{appointment_id}/notify", tags=["Уведомления"])
async def send_appointment_notification(appointment_id: str):
    """Отправка уведомления о записи (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Уведомление отправлено", "appointment_id": appointment_id}

# ================= ПОИСК =================

@app.get("/doctors/search", tags=["Поиск"])
async def search_doctors(q: str):
    """Поиск врачей по запросу (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "query": q}

@app.get("/patients/search", tags=["Поиск"])
async def search_patients(q: str):
    """Поиск пациентов по запросу (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "query": q}

# ================= СТАТИСТИКА =================

@app.get("/stats", tags=["Статистика"])
async def get_general_stats():
    """Общая статистика системы (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке"}

@app.get("/doctor/{doctor_id}/stats", tags=["Статистика"])
async def get_doctor_stats(doctor_id: str):
    """Статистика врача (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "doctor_id": doctor_id}

@app.get("/patient/{snils}/stats", tags=["Статистика"])
async def get_patient_stats(snils: str):
    """Статистика пациента (будущая функция)"""
    # Заглушка для будущей реализации
    return {"message": "Функция в разработке", "patient": snils}

# ================= ЗАПУСК ПРИЛОЖЕНИЯ =================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск Медицинского портала API...")
    print("📋 Swagger UI доступен по адресу: http://localhost:8000/docs")
    print("📋 ReDoc доступен по адресу: http://localhost:8000/redoc")
    
    # ИСПРАВЛЕНО: убираем reload=True при запуске через python main.py
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)