import sys
import os
import traceback
from datetime import datetime, time
import pandas as pd # Добавлен импорт pandas

print(f"--- init_db.py VERBOSE TEST from {os.getcwd()} ---")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"sys.path: {sys.path}")
sys.stdout.flush()

try:
    print("Attempting to import 'app' module components...")
    sys.stdout.flush()
    from app import create_app, db
    from app.models.metal import Metal, MetalPrice
    # MfdParserService больше не нужен для инициализации, если берем из Excel
    # from app.services.mfd_parser_service import MfdParserService 
    print("'create_app', 'db', models imported successfully.")
    sys.stdout.flush()
    
    app = create_app()
    print("Flask app created successfully.")
    sys.stdout.flush()

    with app.app_context():
        print("Entered app_context.")
        sys.stdout.flush()
        try:
            db.create_all()
            print("db.create_all() executed successfully.")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error during db.create_all(): {e}")
            print(traceback.format_exc())
            sys.stdout.flush()
            raise

        # --- Добавление/обновление текущих металлов ---
        # (можно оставить как есть, или адаптировать, если Excel будет основным источником)
        metals_data = [
            {"name": "Gold", "name_ru": "Золото", "unit": "gram", "current_price_rub": 0.0},
            {"name": "Silver", "name_ru": "Серебро", "unit": "gram", "current_price_rub": 0.0},
            {"name": "Platinum", "name_ru": "Платина", "unit": "gram", "current_price_rub": 0.0},
            {"name": "Palladium", "name_ru": "Палладий", "unit": "gram", "current_price_rub": 0.0},
        ]

        for metal_data in metals_data:
            metal = Metal.query.filter_by(name=metal_data["name"]).first()
            if not metal:
                metal = Metal(name=metal_data["name"], name_ru=metal_data["name_ru"], unit=metal_data["unit"], symbol=metal_data["name"].upper())
                db.session.add(metal)
                print(f"Added new metal: {metal_data['name']}")
            else:
                # Обновляем, если нужно (например, русское имя или единицу измерения)
                metal.name_ru = metal_data["name_ru"]
                metal.unit = metal_data["unit"]
                # Можно также обновить symbol, если он отличается или отсутствует
                if not metal.symbol:
                    metal.symbol = metal_data["name"].upper()
                print(f"Metal {metal_data['name']} already exists. Updated attributes if necessary.")
        db.session.commit()
        print("Committed initial metal data.")
        sys.stdout.flush()

        # --- Загрузка исторических данных из Excel ---
        excel_file_path = os.path.join(os.path.dirname(__file__), '..', 'BD', 'Книга1.xlsx') # Путь к файлу
        print(f"Attempting to load historical data from: {excel_file_path}")
        sys.stdout.flush()

        if not os.path.exists(excel_file_path):
            print(f"ERROR: Excel file not found at {excel_file_path}")
            sys.stdout.flush()
        else:
            try:
                # Заголовки на первой строке (индекс 0), данные начинаются со второй (header=0)
                df = pd.read_excel(excel_file_path, sheet_name=0, header=0) 
                print(f"Successfully read Excel file. Columns found: {df.columns.tolist()}")
                sys.stdout.flush()

                # Ожидаемые названия столбцов (исходя из фактических данных в Excel и логов)
                # Первый столбец - Дата
                # Последующие столбцы с металлами должны соответствовать name в таблице Metal
                column_map = {
                    "Дата": "date",
                    "Золото": "Gold",
                    "Серебро": "Silver",
                    "Платина": "Platinum",
                    "Палладий": "Palladium"
                }
                
                required_excel_columns = list(column_map.keys())
                missing_cols = [col for col in required_excel_columns if col not in df.columns]
                if missing_cols:
                    print(f"ERROR: Missing expected columns in Excel: {', '.join(missing_cols)}")
                    print(f"Found columns: {df.columns.tolist()}")
                    sys.stdout.flush()
                else:
                    for index, row in df.iterrows():
                        try:
                            date_str = str(row["Дата"])
                            # Пытаемся распарсить дату, ожидая формат dd.mm.yyyy или другой стандартный
                            # pandas.to_datetime более гибкий
                            record_date = pd.to_datetime(date_str, dayfirst=True).date() 
                            # Если to_datetime не справляется, можно добавить errors='coerce' 
                            # и проверять на NaT (Not a Time)

                            if pd.isna(record_date):
                                print(f"Skipping row {index+2} due to invalid date: {date_str}")
                                continue

                            for excel_col_name, metal_name_from_map in column_map.items():
                                if metal_name_from_map == "date":
                                    continue # Пропускаем столбец с датой в этом цикле

                                if excel_col_name not in df.columns:
                                    print(f"Warning: Column '{excel_col_name}' for metal '{metal_name_from_map}' not found in Excel. Skipping.")
                                    continue
                                
                                price_val = row[excel_col_name]

                                # Проверяем, не является ли значение уже объектом datetime
                                if isinstance(price_val, datetime):
                                    print(f"Skipping price for {metal_name_from_map} on {record_date} because value is a datetime object: '{price_val}'")
                                    continue

                                # Попытка конвертировать значение в число, обрабатывая ошибки
                                try:
                                    price = pd.to_numeric(price_val)
                                    if pd.isna(price):
                                        # Это условие сработает, если to_numeric вернул NaN (например, для пустой строки)
                                        print(f"Skipping price for {metal_name_from_map} on {record_date} because value is NaN after to_numeric: '{price_val}'")
                                        continue
                                except ValueError:
                                    print(f"Skipping price for {metal_name_from_map} on {record_date} due to ValueError on conversion to numeric: '{price_val}'")
                                    continue
                                
                                # Дополнительная проверка типа уже не так критична после pd.to_numeric,
                                # но оставим для ясности, что мы ожидаем int или float.
                                # if not isinstance(price, (int, float)):
                                #     print(f"Skipping price for {metal_name_from_map} on {record_date} because type is not int/float after to_numeric: {type(price)} for value '{price_val}'")
                                #     continue
                                
                                metal_obj = Metal.query.filter_by(name=metal_name_from_map).first()
                                if not metal_obj:
                                    print(f"Warning: Metal '{metal_name_from_map}' not found in database. Skipping price entry for {record_date}.")
                                    continue

                                # Проверка на дубликат цены для данного металла и даты
                                existing_price = MetalPrice.query.filter_by(
                                    metal_id=metal_obj.id, 
                                    timestamp=datetime.combine(record_date, time.min) # Сохраняем с полуночью
                                ).first()

                                if existing_price:
                                    # print(f"Price for {metal_name_en} on {record_date} already exists. Skipping.")
                                    pass # Просто пропускаем, если уже есть
                                else:
                                    metal_price_entry = MetalPrice(
                                        metal_id=metal_obj.id,
                                        price=float(price),
                                        timestamp=datetime.combine(record_date, time.min)
                                    )
                                    db.session.add(metal_price_entry)
                                    # print(f"Added price for {metal_name_en} on {record_date}: {price}")
                            
                        except Exception as e_row:
                            print(f"Error processing row {index+2} from Excel: {row.to_dict()}")
                            print(f"Row error details: {e_row}")
                            print(traceback.format_exc())
                            sys.stdout.flush()
                    
                    db.session.commit()
                    print("Successfully processed and committed historical data from Excel.")
                    sys.stdout.flush()

            except Exception as e_excel:
                print(f"Error reading or processing Excel file: {e_excel}")
                print(traceback.format_exc())
                sys.stdout.flush()

        print("Database initialization script finished.")
        sys.stdout.flush()

except ImportError as e:
    print(f"ImportError: {e}. Make sure all dependencies are installed and the script is run from the correct directory or with the app module in PYTHONPATH.")
    print(traceback.format_exc())
    sys.stdout.flush()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print(traceback.format_exc())
    sys.stdout.flush()

if __name__ == '__main__':
    print(f"--- init_db.py execution started from {os.getcwd()} ---")
    sys.stdout.flush()
    
    # Логика изменения CWD, если запускаем из корня проекта
    # Цель: CWD должна быть .../metals-site/backend для корректных относительных импортов 'app'
    # и для того, чтобы instance folder для SQLite оказался в backend/instance/
    current_script_dir = os.path.dirname(os.path.abspath(__file__)) # .../metals-site/backend
    
    if os.getcwd() != current_script_dir:
        # Если мы НЕ в .../metals-site/backend (например, в .../metals-site)
        # и backend/ существует относительно текущей директории
        if os.path.basename(os.getcwd()) != 'backend' and 'backend' in os.listdir(os.getcwd()):
            target_cwd = os.path.join(os.getcwd(), 'backend')
            if os.path.isdir(target_cwd):
                try:
                    os.chdir(target_cwd)
                    print(f"Changed CWD to: {os.getcwd()}")
                except Exception as e_chdir:
                    print(f"Failed to change CWD to {target_cwd}: {e_chdir}", file=sys.stderr)
        # Если мы находимся в директории, где лежит сам init_db.py, то CWD уже правильная.
        # Если нет, и предыдущее условие не сработало, выводим предупреждение.
        elif os.getcwd() != current_script_dir : # Дополнительная проверка, что мы не там, где должны быть
             print(f"Warning: CWD is {os.getcwd()}, but script is in {current_script_dir}. Imports might fail.")

    # Добавляем родительскую директорию от backend (т.е. корень проекта) в sys.path
    # Это стандартная практика, если структура app/module находится внутри backend/
    project_root = os.path.dirname(current_script_dir) # .../metals-site
    if project_root not in sys.path:
        print(f"Adding project root {project_root} to sys.path for imports.")
        sys.path.insert(0, project_root)
    
    # Также добавляем саму директорию backend в sys.path, так как 'app' находится внутри нее.
    if current_script_dir not in sys.path:
        print(f"Adding script directory {current_script_dir} to sys.path for imports.")
        sys.path.insert(1, current_script_dir) # insert(1) чтобы project_root был первым

    sys.stdout.flush()
    
    print(f"Final CWD for init_db before execution: {os.getcwd()}")
    print(f"Current sys.path: {sys.path}")
    sys.stdout.flush()
    
    print("--- init_db.py processing completed (если не было ошибок выше) ---")
    sys.stdout.flush() 