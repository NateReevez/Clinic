#!/bin/bash

set -e

COUCHDB_URL="http://admin:password@localhost:5990"

# 🏥 РАСШИРЕННЫЕ ДАННЫЕ О ВРАЧАХ
doctors_json='[
{
  "_id": "1234",
  "name": "Иванов Иван Иванович",
  "speciality": "Терапевт",
  "speciality_en": "Therapist",
  "experience": "15 лет",
  "room": "101",
  "photo": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=300&h=300&fit=crop&crop=face",
  "education": "Медицинский институт им. Сеченова",
  "qualification": "д-р мед. наук",
  "achievements": [
    "Доктор медицинских наук",
    "Врач высшей категории",
    "Автор 25 научных публикаций"
  ],
  "description": "Опытный терапевт с глубокими знаниями внутренних болезней. Специализируется на диагностике сложных случаев.",
  "schedule": {
    "monday": "09:00-17:00",
    "tuesday": "09:00-17:00",
    "wednesday": "09:00-17:00",
    "thursday": "09:00-17:00",
    "friday": "09:00-15:00"
  },
  "rating": 4.8,
  "reviews_count": 156
},
{
  "_id": "2222",
  "name": "Берия Лаврентий Павлович",
  "speciality": "Хирург",
  "speciality_en": "Surgeon",
  "experience": "20 лет",
  "room": "203",
  "photo": "https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=300&h=300&fit=crop&crop=face",
  "education": "Военно-медицинская академия",
  "qualification": "д-р мед. наук",
  "achievements": [
    "Доктор медицинских наук",
    "Заведующий хирургическим отделением",
    "Лауреат премии Минздрава"
  ],
  "description": "Опытный хирург общего профиля. Специализируется на лапароскопических операциях и онкохирургии.",
  "schedule": {
    "monday": "07:00-15:00",
    "tuesday": "07:00-15:00",
    "wednesday": "07:00-15:00",
    "thursday": "07:00-15:00",
    "friday": "07:00-13:00"
  },
  "rating": 4.9,
  "reviews_count": 278
},
{
  "_id": "3333",
  "name": "Сидоров Михаил Иванович",
  "speciality": "Терапевт",
  "speciality_en": "Therapist",
  "experience": "30 лет",
  "room": "205",
  "photo": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=300&h=300&fit=crop&crop=face",
  "education": "Московская медицинская академия",
  "qualification": "д-р мед. наук",
  "achievements": [
    "Доктор медицинских наук",
    "Профессор кафедры терапии",
    "Заслуженный врач РФ"
  ],
  "description": "Ведущий специалист по внутренним болезням. Занимается лечением сахарного диабета и эндокринных нарушений.",
  "schedule": {
    "monday": "10:00-18:00",
    "tuesday": "10:00-18:00",
    "wednesday": "10:00-18:00",
    "thursday": "10:00-18:00",
    "friday": "10:00-16:00"
  },
  "rating": 4.7,
  "reviews_count": 89
},
{
  "_id": "4444",
  "name": "Иванова Мария Владимировна",
  "speciality": "Дерматолог",
  "speciality_en": "Dermatologist",
  "experience": "12 лет",
  "room": "215",
  "photo": "https://images.unsplash.com/photo-1594824883007-1ad91b5e71da?w=300&h=300&fit=crop&crop=face",
  "education": "СПбГМУ им. Павлова",
  "qualification": "д-р мед. наук",
  "achievements": [
    "Врач высшей категории",
    "Сертификат по дерматоскопии",
    "Стажировка в Германии"
  ],
  "description": "Специалист по заболеваниям кожи. Проводит диагностику и лечение акне, псориаза, онкодерматологии.",
  "schedule": {
    "monday": "09:00-17:00",
    "tuesday": "09:00-17:00",
    "wednesday": "09:00-17:00",
    "thursday": "09:00-17:00",
    "friday": "09:00-15:00"
  },
  "rating": 4.6,
  "reviews_count": 124
},
{
  "_id": "5555",
  "name": "Смирнов Алексей Дмитриевич",
  "speciality": "Дерматолог",
  "speciality_en": "Dermatologist",
  "experience": "8 лет",
  "room": "217",
  "photo": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=300&h=300&fit=crop&crop=face",
  "education": "РНИМУ им. Пирогова",
  "qualification": "канд. мед. наук",
  "achievements": [
    "Кандидат медицинских наук",
    "Специалист по детской дерматологии",
    "Участник международных конференций"
  ],
  "description": "Молодой специалист по кожным заболеваниям. Специализируется на детской дерматологии и аллергических реакциях.",
  "schedule": {
    "monday": "08:00-16:00",
    "tuesday": "08:00-16:00",
    "wednesday": "08:00-16:00",
    "thursday": "08:00-16:00",
    "friday": "08:00-14:00"
  },
  "rating": 4.5,
  "reviews_count": 67
},
{
  "_id": "6666",
  "name": "Петрова Анна Сергеевна",
  "speciality": "Кардиолог",
  "speciality_en": "Cardiologist",
  "experience": "12 лет",
  "room": "301",
  "photo": "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=300&h=300&fit=crop&crop=face",
  "education": "РНИМУ им. Пирогова",
  "qualification": "канд. мед. наук",
  "achievements": [
    "Врач высшей категории",
    "Сертификат по интервенционной кардиологии",
    "Участник международных конференций"
  ],
  "description": "Специалист по заболеваниям сердечно-сосудистой системы. Проводит эхокардиографию и холтеровское мониторирование.",
  "schedule": {
    "monday": "08:00-16:00",
    "tuesday": "08:00-16:00",
    "wednesday": "08:00-16:00",
    "thursday": "08:00-16:00",
    "friday": "08:00-14:00"
  },
  "rating": 4.9,
  "reviews_count": 203
},
{
  "_id": "7777",
  "name": "Волков Дмитрий Александрович",
  "speciality": "Невролог",
  "speciality_en": "Neurologist",
  "experience": "18 лет",
  "room": "308",
  "photo": "https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=300&h=300&fit=crop&crop=face",
  "education": "Московская медицинская академия",
  "qualification": "д-р мед. наук",
  "achievements": [
    "Доктор медицинских наук",
    "Профессор кафедры неврологии",
    "Заслуженный врач РФ"
  ],
  "description": "Ведущий специалист по заболеваниям нервной системы. Занимается лечением головных болей, эпилепсии, рассеянного склероза.",
  "schedule": {
    "monday": "10:00-18:00",
    "tuesday": "10:00-18:00",
    "wednesday": "10:00-18:00",
    "thursday": "10:00-18:00",
    "friday": "10:00-16:00"
  },
  "rating": 4.7,
  "reviews_count": 89
}
]'

patients_json='[
{"_id":"132-343-23 46","name":"Байден Джозеф Робинеттович","phone":"+1-847-389-23-45","address":"Вашингтон, Колумбия","email":"ex@potus.us","birthdate":"11.20.1942","password":"1234","eligibility":null},
{"_id":"456-789-12 34","name":"Петрова Анна Сергеевна","phone":"+7-916-555-44-33","address":"Санкт-Петербург, Невский пр-т, д. 25","email":"petrova.anna@example.ru","birthdate":"07.22.1990","password":"secure123","eligibility":null},
{"_id":"567-123-45 67","name":"Сухарь Иван Иванович","phone":"+7-999-123-45-67","address":"Москва, ул. Пушкина, д. 10","email":"ivanov@example.com","birthdate":"05.15.1985","password":"qwerty","eligibility":null}
]'

appointments_json='[
{"_id":"cb83a30a2d7411184e53791fb1008c43","date":"2025-05-30T10:00:00","room":"102","doctor_id":"1111","patient_id":"132-343-23 46","status":"Archive"},
{"_id":"ecac06c73bb7763ca0ee68759b003238","date":"2025-05-31T10:00:00","room":"203","doctor_id":"2222","patient_id":"132-343-23 46","status":"Confirmed"},
{"_id":"ecac06c73bb7763ca0ee68759b01ac5e","date":"2025-05-31T10:00:00","room":"217","doctor_id":"5555","patient_id":"456-789-12 34","status":"Confirmed"},
{"_id":"ecac06c73bb7763ca0ee68759b01eb07","date":"2025-05-31T14:30:00","room":"215","doctor_id":"4444","patient_id":"567-123-45 67","status":"Confirmed"}
]'

services_json='[
{"_id":"services","list_services":["Терапевт","Хирург","Дерматолог","Кардиолог","Невролог"]}
]'

schedule_json='[
{"_id":"schedule","schedule":{"2025-06-01":["2025-06-01T09:00:00","2025-06-01T09:30:00","2025-06-01T10:00:00","2025-06-01T10:30:00","2025-06-01T11:00:00","2025-06-01T11:30:00","2025-06-01T12:00:00","2025-06-01T12:30:00","2025-06-01T13:00:00","2025-06-01T13:30:00","2025-06-01T14:00:00","2025-06-01T14:30:00","2025-06-01T15:00:00","2025-06-01T15:30:00","2025-06-01T16:00:00","2025-06-01T16:30:00","2025-06-01T17:00:00","2025-06-01T17:30:00","2025-06-01T18:00:00"]}}
]'

medical_records_json='[
{"_id":"HL132-343-23 46","medical_history":{"2025-05-28T09:00:00":{"Направление":"surgery","Врач":"Иванов Иван Иванович","Комментарий":"Первый приём"},"2025-05-30T10:00:00":{"Направление":"therapy","Врач":"Фролов Фёдор Фёдорович","Комментарий":"Жалобы на головную боль"},"2025-05-31T10:00:00":{"Направление":"surgery","Врач":"Берия Лаврентий Павлович","Комментарий":"Тест отчёта через API"}},"diseases":["Старость не радость"],"test_results":["Анализ крови"],"prescription":["Узболительноe"]},
{"_id":"HL456-789-12 34","medical_history":{},"diseases":["Аллергия на пыль"],"test_results":["Анализ крови"],"prescription":["Цетрин"]},
{"_id":"HL567-123-45 67","medical_history":{},"diseases":[],"test_results":[],"prescription":[]}
]'

# --- Функция для импорта документов в выбранную базу (с поддержкой обновления) ---
import_docs() {
  local db="$1"
  local json_array="$2"
  local update_mode="${3:-false}"

  echo "🏥 Создаём базу $db ..."
  curl -sf -X PUT "$COUCHDB_URL/$db" || echo "ℹ️  База $db уже существует"

  if [ "$update_mode" = "true" ]; then
    echo "🔄 Обновляем документы в $db с проверкой существующих..."
    import_docs_with_update "$db" "$json_array"
  else
    echo "📝 Вставляем документы в $db ..."
    # Обычный bulk insert
    response=$(curl -s -X POST "$COUCHDB_URL/$db/_bulk_docs" \
      -H "Content-Type: application/json" \
      -d "{\"docs\":$json_array}")
    
    echo "📊 Результат: $response"
  fi

  echo "✅ Готово с $db"
}

# --- Функция для импорта с обновлением существующих документов ---
import_docs_with_update() {
  local db="$1"
  local json_array="$2"
  
  # Парсим JSON массив и обрабатываем каждый документ отдельно
  echo "$json_array" | jq -c '.[]' | while read -r doc; do
    local doc_id=$(echo "$doc" | jq -r '._id')
    
    echo "🔍 Проверяем документ $doc_id..."
    
    # Проверяем, существует ли документ
    existing_doc=$(curl -s "$COUCHDB_URL/$db/$doc_id" || echo '{"error":"not_found"}')
    
    if echo "$existing_doc" | jq -e '.error' > /dev/null; then
      # Документ не существует - создаём новый
      echo "➕ Создаём новый документ $doc_id"
      result=$(curl -s -X PUT "$COUCHDB_URL/$db/$doc_id" \
        -H "Content-Type: application/json" \
        -d "$doc")
    else
      # Документ существует - обновляем с _rev
      local rev=$(echo "$existing_doc" | jq -r '._rev')
      local updated_doc=$(echo "$doc" | jq --arg rev "$rev" '. + {"_rev": $rev}')
      
      echo "🔄 Обновляем существующий документ $doc_id (rev: $rev)"
      result=$(curl -s -X PUT "$COUCHDB_URL/$db/$doc_id" \
        -H "Content-Type: application/json" \
        -d "$updated_doc")
    fi
    
    # Проверяем результат
    if echo "$result" | jq -e '.ok' > /dev/null; then
      echo "✅ Документ $doc_id успешно обработан"
    else
      echo "❌ Ошибка с документом $doc_id: $result"
    fi
  done
}

# --- Основной процесс импорта ---
echo "🚀 Начинаем импорт данных в CouchDB..."
echo "========================================"

# Импортируем врачей с обновлением существующих
import_docs "medcare-doctors" "$doctors_json" "true"

# Остальные базы импортируем обычным способом
import_docs "medcare-patients" "$patients_json"
import_docs "medcare-appointments" "$appointments_json"
import_docs "medcare-services" "$services_json"
import_docs "medcare-schedule" "$schedule_json"
import_docs "medcare-records" "$medical_records_json"

echo ""
echo "🎉 Всё успешно импортировано!"
echo "📊 Статистика:"
echo "   👨‍⚕️ Врачи: 7 записей (с фото и подробностями)"
echo "   👥 Пациенты: 3 записи"
echo "   📅 Записи: 4 записи"
echo "   🏥 Сервисы: обновлены специальности"
echo ""
echo "🌐 Проверить можно тут:"
echo "   http://localhost:5990/_utils"
echo "   http://localhost:8000/doctors"