#!/bin/bash
set -e

COUCHDB_URL="http://admin:password@localhost:5990"

# Функция для генерации случайных заболеваний (возвращает JSON-массив)
generate_diseases() {
    local diseases=("Гипертония" "Диабет" "Астма" "Грипп" "Растяжение связок" "Перелом" "Повышенное нервное напряжение" "Обострение язвенной болезни")
    local count=$((RANDOM % 4 + 1))
    local selected_diseases=()

    for ((i=0; i<count; i++)); do
        selected_diseases+=("\"${diseases[RANDOM % ${#diseases[@]}]}\"")
    done

    echo "[$(IFS=,; echo "${selected_diseases[*]}")]"
}

# Функция для генерации случайных результатов тестов (возвращает JSON-массив)
generate_test_results() {
    local results=("Нет результатов" "Нормально" "Паталогия обнаружена" "Повышен уровень" "Понижен уровень")
    local count=$((RANDOM % 4 + 1))
    local selected_results=()

    for ((i=0; i<count; i++)); do
        selected_results+=("\"${results[RANDOM % ${#results[@]}]}\"")
    done

    echo "[$(IFS=,; echo "${selected_results[*]}")]"
}

# Функция для генерации случайных назначений рецептов (возвращает JSON-массив)
generate_prescriptions() {
    local prescriptions=("Пить больше воды" "Регулярная физическая активность" "Принимать лекарство дважды в день" "Не есть острое и жирное" "Обратиться к дерматологу")
    local count=$((RANDOM % 4 + 1))
    local selected_prescriptions=()

    for ((i=0; i<count; i++)); do
        selected_prescriptions+=("\"${prescriptions[RANDOM % ${#prescriptions[@]}]}\"")
    done

    echo "[$(IFS=,; echo "${selected_prescriptions[*]}")]"
}

# Генерация данных медицинских записей для пациентов
medical_records_json=$(cat <<EOF
[
  {
    "_id": "record_1",
    "patient_snils": "132-343-23 46",
    "doctor_id": "1234",
    "report_text": "Осмотр на профилактическом приеме. Общее состояние удовлетворительное.",
    "diagnosis": "Гипертония",
    "recommendations": "Регулярный контроль давления, диета без соли.",
    "diseases": $(generate_diseases),
    "test_results": $(generate_test_results),
    "prescription": $(generate_prescriptions),
    "records": []
  },
  {
    "_id": "record_2",
    "patient_snils": "132-343-23 46",
    "doctor_id": "1234",
    "report_text": "Повторный осмотр. Артериальное давление в норме.",
    "diagnosis": "Гипертония",
    "recommendations": "Продолжать лечение, следить за давлением.",
    "diseases": $(generate_diseases),
    "test_results": $(generate_test_results),
    "prescription": $(generate_prescriptions),
    "records": []
  },
  {
    "_id": "record_3",
    "patient_snils": "456-789-12 34",
    "doctor_id": "2222",
    "report_text": "Осмотр на травму. Ушиб кисти, отек.",
    "diagnosis": "Растяжение связок",
    "recommendations": "Полежать, избегать нагрузки на руку, холод на 20 минут.",
    "diseases": $(generate_diseases),
    "test_results": $(generate_test_results),
    "prescription": $(generate_prescriptions),
    "records": []
  },
  {
    "_id": "record_4",
    "patient_snils": "456-789-12 34",
    "doctor_id": "2222",
    "report_text": "Контроль состояния после травмы. Ушиб меньше.",
    "diagnosis": "Улучшение состояния",
    "recommendations": "Продолжать соблюдать режим, контролировать нагрузку.",
    "diseases": $(generate_diseases),
    "test_results": $(generate_test_results),
    "prescription": $(generate_prescriptions),
    "records": []
  },
  {
    "_id": "record_5",
    "patient_snils": "567-123-45 67",
    "doctor_id": "3333",
    "report_text": "Профилактический осмотр. Рекомендован общий анализ крови.",
    "diagnosis": "Ограниченная подвижность в суставе.",
    "recommendations": "Физиотерапия, прохождение курса лечения.",
    "diseases": $(generate_diseases),
    "test_results": $(generate_test_results),
    "prescription": $(generate_prescriptions),
    "records": []
  }
]
EOF
)

# Проверка и сохранение JSON для отладки
echo "$medical_records_json" > medical_records_debug.json

# Импорт медицинских записей в базу
import_docs() {
    local db="$1"
    local json_array="$2"

    echo "🏥 Создаём базу $db ..."
    curl -sf -X PUT "$COUCHDB_URL/$db" || echo "ℹ️  База $db уже существует"

    echo "📝 Вставляем документы в $db ..."
    response=$(curl -s -X POST "$COUCHDB_URL/$db/_bulk_docs" \
      -H "Content-Type: application/json" \
      -d "{\"docs\":$json_array}")
    
    if [[ $response == *"error"* ]]; then
        echo "❌ Ошибка при вставке документов: $response"
        echo "💡 Проверьте файл medical_records_debug.json"
    else
        echo "📊 Результат: $response"
        echo "✅ Готово с $db"
    fi
}

# Основной процесс импорта
echo "🚀 Начинаем импорт данных в CouchDB..."
echo "========================================"

import_docs "medcare-medical-records" "$medical_records_json"

# Создание представления для получения записей по СНИЛС
curl -X PUT "$COUCHDB_URL/medcare-medical-records/_design/medical_records" \
-H "Content-Type: application/json" \
-d '{
  "_id": "_design/medical_records",
  "views": {
    "by_patient_snils": {
      "map": "function(doc) { if (doc.patient_snils) { emit(doc.patient_snils, doc); }}"
    }
  }
}'