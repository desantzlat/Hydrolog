    # НЕ ИСПОЛЬЗУЕМ 'from replit import db'
    import json # ИМПОРТИРУЕМ БИБЛИОТЕКУ ДЛЯ РАБОТЫ С JSON

    from flask import Flask, flash, redirect, render_template, request, session, url_for
    from werkzeug.security import check_password_hash, generate_password_hash

    app = Flask(__name__)
    app.secret_key = 'your_very_secret_key_12345'

    # --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ ---
    def load_db():
        """Загружает данные из JSON-файла."""
        try:
            with open('database.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_db(data):
        """Сохраняет данные в JSON-файл."""
        with open('database.json', 'w') as f:
            json.dump(data, f, indent=4)
    # ------------------------------------------------

    # --- НОВАЯ ФУНКЦИЯ ДЛЯ ГИДРОЛОГИЧЕСКИХ РАСЧЕТОВ ---
    def calculate_empirical_probability(data_series):
        """
        Рассчитывает эмпирическую ежегодную вероятность превышения (обеспеченность)
        согласно формуле (5.1) СП 33-101-2003.
        """
        try:
            # 1. Сортируем ряд в убывающем порядке
            sorted_series = sorted(data_series, reverse=True)
            n = len(sorted_series)
            results = []

            # 2. Присваиваем порядковые номера (m) от 1 до n
            for m, value in enumerate(sorted_series, 1):
                # 3. Рассчитываем вероятность по формуле Pm = (m / (n + 1)) * 100
                probability = (m / (n + 1)) * 100
                results.append({'m': m, 'value': value, 'probability': probability})

            return results
        except Exception as e:
            # Возвращаем ошибку, если что-то пошло не так
            return {'error': str(e)}

    # --- КОНЕЦ НОВОЙ ФУНКЦИИ ---


    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/calculators', methods=['GET', 'POST'])
    def calculators_page():
        # Инициализируем переменные для результатов
        discharge_result = None
        probability_results = None

        if request.method == 'POST':
            # Определяем, какая форма была отправлена
            calculator_type = request.form.get('calculator_type')

            if calculator_type == 'discharge':
                # Логика для калькулятора расхода воды
                area_str = request.form.get('area')
                velocity_str = request.form.get('velocity')
                if area_str and velocity_str:
                    area = float(area_str)
                    velocity = float(velocity_str)
                    discharge = area * velocity
                    discharge_result = discharge

            elif calculator_type == 'probability':
                # Логика для нового калькулятора обеспеченности
                data_str = request.form.get('data_series')
                if data_str:
                    # Преобразуем текст из textarea в список чисел
                    try:
                        lines = data_str.strip().splitlines()
                        data_series = [float(line.strip()) for line in lines if line.strip()]
                        if data_series:
                            probability_results = calculate_empirical_probability(data_series)
                        else:
                            flash('Введите хотя бы одно значение.', 'warning')
                    except ValueError:
                        flash('Пожалуйста, вводите только числа, каждое с новой строки.', 'danger')

        return render_template('calculators.html', 
                               discharge_result=discharge_result, 
                               probability_results=probability_results)


    @app.route('/library')
    def library_page():
        return render_template('library.html')

    @app.route('/expert')
    def expert_page():
        return render_template('expert.html')

    @app.route('/climatology')
    def climatology_page():
        climate_data = [
            {'year': 2000, 'avg_temp': 5.2, 'precipitation': 602},
            {'year': 2001, 'avg_temp': 5.5, 'precipitation': 630},
        ]
        return render_template('climatology.html', records=climate_data)

    @app.route('/hydrology')
    def hydrology_page():
        sample_data = [
            {'year': 1980, 'avg_flow': 150.5, 'max_flow': 320.1, 'min_flow': 50.2},
            {'year': 1981, 'avg_flow': 145.2, 'max_flow': 310.8, 'min_flow': 48.9},
        ]
        return render_template('hydrology.html', records=sample_data)

    # === МАРШРУТЫ ДЛЯ РЕГИСТРАЦИИ, ВХОДА, ВЫХОДА (остаются без изменений) ===
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form.get('name')
            username = request.form.get('username')
            password = request.form.get('password')

            if not name or not username or not password:
                flash('Все поля должны быть заполнены.', 'danger')
                return redirect(url_for('register'))

            users = load_db()
            if username in users:
                flash('Пользователь с таким email уже существует!', 'danger')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password)
            users[username] = {
                'password': hashed_password,
                'name': name
            }
            save_db(users)

            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            users = load_db()
            if username in users and check_password_hash(users[username]['password'], password):
                session['user_email'] = username
                session['user_name'] = users[username]['name']
                flash('Вход выполнен успешно!', 'success')
                return redirect(url_for('index'))

            flash('Неверный email или пароль.', 'danger')
            return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user_email', None)
        session.pop('user_name', None)
        flash('Вы успешно вышли из системы.', 'info')
        return redirect(url_for('index'))
    # =======================================================================

    if __name__ == '__main__':
            app.run(host='0.0.0.0', port=8080)