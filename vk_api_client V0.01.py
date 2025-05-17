import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import webbrowser
import requests
import json
from pathlib import Path
import os
import time


TOKEN_USER = '' #ваш токен
VERSION = 5.199 # версия api vk
time_active = 120000    # макс. количество секунд оффлайн для фильтрации
count_followers = 1200  #  Количество подписчиков для фильтрации
true = True
false = False
lst_links = []
group_id = 'eofru' #  Не доработано, поиск в открытых группах по тем же фильтрам
dct = {}
next_from = ''
city = 'Санкт-Петербург' # город, в котором ожидаем найти человека для фильтрации
user_id = '199592366'  # числа, чтобы не вводить

class VKFriendsApp:
        def __init__(self, root):
                self.root = root
                self.root.title("VK Friends List")
                self.root.geometry("800x700")

                # Доступные поля для выбора
                self.available_fields = {
                        'first_name': 'Имя',
                        'last_name': 'Фамилия',
                        'photo_200_orig': 'Фото 200px',
                        'photo_100': 'Фото 100px',
                        'domain': 'Адрес страницы',
                        'online': 'Онлайн статус',
                        'last_seen': 'Последний визит',
                        'city': 'Город',
                        'education': 'Образование',
                        'bdate': 'Дата рождения',
                        'sex': 'Пол',
                        'status': 'Статус',
                        "relation": "Отношения"
                }

                # Создание элементов интерфейса
                self.create_widgets()

        def create_widgets(self):
                # Основной контейнер
                main_frame = tk.Frame(self.root, padx=10, pady=10)
                main_frame.pack(fill=tk.BOTH, expand=True)

                # Фрейм для ввода данных
                input_frame = tk.LabelFrame(main_frame, text="Параметры запроса", padx=5, pady=5)
                input_frame.pack(fill=tk.X, pady=5)

                # Поле для ввода токена
                tk.Label(input_frame, text="Access Token:").grid(row=0, column=0, sticky='w', pady=2)
                self.token_entry = tk.Entry(input_frame, width=70)
                self.token_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=2, sticky='ew')
                self.token_entry.insert(0, TOKEN_USER)

                # Поле для ввода ID пользователя
                tk.Label(input_frame, text="User ID:").grid(row=1, column=0, sticky='w', pady=2)
                self.user_id_entry = tk.Entry(input_frame, width=20)
                self.user_id_entry.grid(row=1, column=1, padx=5, pady=2, sticky='w')
                self.user_id_entry.bind('<FocusIn>', self.clear_entry)
                self.user_id_entry.insert(0, user_id)

                # Поле для ввода ID группы (опционально)
                tk.Label(input_frame, text="Group ID (опционально):").grid(row=2, column=0, sticky='w', pady=2)
                self.group_id_entry = tk.Entry(input_frame, width=20)
                self.group_id_entry.grid(row=2, column=1, padx=5, pady=2, sticky='w')
                self.group_id_entry.bind('<FocusIn>', self.clear_entry)

                # Фрейм для выбора полей
                fields_frame = tk.LabelFrame(main_frame, text="Выберите поля", padx=5, pady=5)
                fields_frame.pack(fill=tk.X, pady=5)

                # Чекбоксы для выбора полей
                self.field_vars = {}
                for i, (field_code, field_name) in enumerate(self.available_fields.items()):
                        self.field_vars[field_code] = tk.BooleanVar(
                                value=True if field_code in ['first_name', 'last_name', 'photo_100', 'photo_200_orig', 'domain',
                                                             'online','last_seen','city','education', 'bdate',
                                                             'sex', 'status', 'relation'] else False)
                        cb = tk.Checkbutton(
                                fields_frame,
                                text=field_name,
                                variable=self.field_vars[field_code],
                                onvalue=True,
                                offvalue=False
                        )
                        cb.grid(row=i // 3, column=i % 3, sticky='w', padx=5, pady=2)

                # Фрейм для кнопок
                button_frame = tk.Frame(main_frame)
                button_frame.pack(fill=tk.X, pady=5)

                # Кнопка получения друзей
                self.get_friends_btn = tk.Button(
                        button_frame,
                        text="Получить список друзей",
                        command=self.get_friends,
                        bg="#4a76a8",
                        fg="white",
                        width=20
                )
                self.get_friends_btn.pack(side=tk.LEFT, padx=5)

                # Кнопка сохранения в HTML
                self.save_html_btn = tk.Button(
                        button_frame,
                        text="Сохранить в HTML",
                        command=self.save_to_html,
                        state=tk.DISABLED,
                        width=15
                )
                self.save_html_btn.pack(side=tk.LEFT, padx=5)

                # Кнопка открытия в браузере
                self.open_browser_btn = tk.Button(
                        button_frame,
                        text="Открыть в браузере",
                        command=self.open_in_browser,
                        state=tk.DISABLED,
                        width=15
                )
                self.open_browser_btn.pack(side=tk.LEFT, padx=5)

                # супер Кнопка
                self.search_friends_btn = tk.Button(
                        button_frame,
                        text="Найти кандидатов в друзья",
                        command=self.get_friends_list,
                        bg="#4a76a8",
                        fg="white",
                        width=20
                )
                self.search_friends_btn.pack(side=tk.LEFT, padx=5)

                # Область вывода результатов
                self.result_area = scrolledtext.ScrolledText(main_frame, width=90, height=20)
                self.result_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                # Переменная для хранения HTML контента
                self.html_content = ""

        def clear_entry(self, event):
                """Очищает поле ввода при фокусе"""
                event.widget.delete(0, tk.END)

        def get_selected_fields(self):
                """Возвращает строку с выбранными полями через запятую"""
                return ','.join([field for field, var in self.field_vars.items() if var.get()])

        def get_friends(self):
                token = self.token_entry.get().strip()
                user_id = self.user_id_entry.get().strip()
                group_id = self.group_id_entry.get().strip()
                fields = self.get_selected_fields()

                if not token:
                        messagebox.showerror("Ошибка", "Токен доступа обязателен!")
                        return
                if not user_id:
                        messagebox.showerror("Ошибка", "ID пользователя обязателен!")
                        return

                params = {
                        'access_token': token,
                        'user_id': user_id,
                        'v': '5.199'
                }

                if fields:
                        params['fields'] = fields

                if group_id:
                        params['group_id'] = group_id

                try:
                        self.result_area.delete('1.0', tk.END)
                        self.result_area.insert(tk.INSERT, "Загрузка данных...")
                        self.root.update()

                        response = requests.get(
                                'https://api.vk.com/method/friends.get',
                                params=params
                        )
                        result = response.json()
##########################################################


                        if 'error' in result:
                                error_msg = result['error']['error_msg']
                                self.show_result(f"Ошибка API: {error_msg}")
                                messagebox.showerror("Ошибка API", error_msg)
                        else:
                                friends = result.get('response', {}).get('items', [])
                                print(json.dumps(friends, indent=4, ensure_ascii=False))
                                # friends2 = self.filter_friends(friends)
                                self.process_friends(friends)

                except requests.exceptions.RequestException as e:
                        self.show_result(f"Ошибка сети: {str(e)}")
                        messagebox.showerror("Ошибка сети", str(e))
                except Exception as e:
                        self.show_result(f"Ошибка: {str(e)}")
                        messagebox.showerror("Ошибка", str(e))
# мои друзья
        def requests_my_friends(self) -> list:
                response = requests.get('https://api.vk.com/method/friends.get',
                                        params={'access_token': TOKEN_USER,
                                                'v': VERSION,
                                                'user_id': user_id,
                                                'fields': 'city',
                                                'offset': 0
                                                })
                data = response.json()
                # print(json.dumps(data, indent=4, ensure_ascii=False))
                data_lst = data['response']['items']
                if data['response']['count'] == 5000:
                        response = requests.get('https://api.vk.com/method/friends.get',
                                                params={'access_token': TOKEN_USER,
                                                        'v': VERSION,
                                                        'user_id': user_id,
                                                        'fields': 'city',
                                                        'offset': 5000
                                                        })
                        data = response.json()
                        data_lst2 = data['response']['items']
                        data_lst.extend(data_lst2)
                data_lst3 = []

                for n_friend in data_lst:
                        cond = None
                        if n_friend['is_closed'] == True:
                                continue
                        cond = n_friend.get('deactivated')
                        if cond:
                                continue
                        data_lst3.append(n_friend['id'])

                return data_lst3
        # получение списка друзей
        def friends_list(self, user_id1) -> list:
                response = requests.get('https://api.vk.com/method/friends.get',
                                        params={'access_token': TOKEN_USER,
                                                'v': VERSION,
                                                'user_id': user_id1,
                                                'fields': 'city,relation,sex,education,last_seen',
                                                'offset': 0
                                                })
                data = response.json()
                # print(json.dumps(data, indent=4, ensure_ascii=False))
                data_lst = data['response']['items']
                if data['response']['count'] == 5000:
                        response = requests.get('https://api.vk.com/method/friends.get',
                                                params={'access_token': TOKEN_USER,
                                                        'v': VERSION,
                                                        'user_id': user_id1,
                                                        'fields': 'city,relation,sex,education,last_seen',
                                                        'offset': 5000
                                                        })
                        data = response.json()
                        data_lst2 = data['response']['items']
                        data_lst.extend(data_lst2)

                return data_lst

        # функция удаления дубликата по айди
        def remove_duplicates_by_key(self, list_of_dicts, key):
                seen = set()
                unique_dicts = []
                for d in list_of_dicts:
                        if d[key] not in seen:
                                seen.add(d[key])
                                unique_dicts.append(d)
                return unique_dicts

        # кнопка Найти кандидатов в друзья
        def get_friends_list(self):
                friends_list1 = self.requests_my_friends()

                friends_list2 = []
                print('check the friends')
                for i, n_id in enumerate(friends_list1):
                        friends_list2.extend(self.friends_list(n_id))
                        print(f'friends_list {i}/{len(friends_list1)}')
                        time.sleep(0.3)
                print(f'Суммарное количество друзей у друзей {len(friends_list2)}')

                friends_list3 = self.filter_friends(friends_list2)

                # print(json.dumps(friends_list3, indent=4, ensure_ascii=False))
                print('\n\n==================================================================\n\n')

                data_my = self.requests_my_friends()
                lst = [n for n in friends_list3 if n['id'] not in data_my]

                unique_data = self.remove_duplicates_by_key(friends_list3, "id")
                print(f'фильтрованные друзья {len(unique_data)}')
                self.process_friends(unique_data)

        # фильтрация Списка друзей + запросы пользователей после фильтрации для более глубокой фильтрации списка
        def filter_friends(self, friends) -> list:
                data = []
                for n_friend in friends:
                        cond = None
                        if n_friend['is_closed'] == True:
                                continue
                        if n_friend['sex'] == 2:  # если женщина 1, мужчина 2, то продолжить
                                continue

                        cond = n_friend.get('deactivated')
                        if cond:
                                continue
                        cond = n_friend.get('relation')
                        if cond:
                                if cond == 4 or cond == 8 or cond == 7 or cond == 3:
                                        continue
                        cond = n_friend.get('last_seen')
                        if cond:
                                if int(time.time()) - n_friend['last_seen']['time'] > time_active:
                                        continue
                        cond = n_friend.get('university')
                        if cond == 0 or cond == None:
                                continue
                        cond = n_friend.get('city')
                        if cond:
                                cond = n_friend.get('city').get('title')
                                if cond != city:
                                        continue
                        else:
                                continue
                        data.append(n_friend)


                data_my = self.requests_my_friends()
                # Для фильтрации по количеству друзей и города
                lst_bd2 = []
                n_count = 0
                print('check users')
                for n_friend in data:
                        n_count += 1
                        if n_friend['id'] in data_my:
                                continue
                        dct = self.user_get(n_friend['id'])
                        cond = dct.get('followers_count')
                        if not cond:
                                continue
                        if dct['followers_count'] < count_followers:
                                continue
                        if dct['counters']['followers'] > dct['counters']['friends']:
                                continue
                        if dct['can_send_friend_request'] == 0:
                                continue
                        # print(json.dumps(dct, indent=4, ensure_ascii=False))
                        cond = dct.get('home_town')
                        cond2 = n_friend.get('city')
                        if cond and cond2 == None:
                                if dct['home_town'] != city:
                                        continue
                        if cond == None and cond2:
                                if n_friend['city']['title'] != city:
                                        continue
                        if cond and cond2:
                                if n_friend['city']['title'] != city:
                                        continue
                        if (cond == None or cond == '') and cond2 == None:
                                continue
                        print(f'check users {n_count}/{len(data)}')
                        lst_bd2.append(dct)
                print('итого', len(lst_bd2))
                return lst_bd2

        # запрос пользователя
        def user_get(self, user_id: str) -> dict:
                response = requests.get('https://api.vk.com/method/users.get',
                                        params={'access_token': TOKEN_USER,
                                                'v': VERSION,
                                                'user_id': user_id,
                                                'fields': 'is_verified,followers_count,can_send_friend_request,'
                                                          'home_town,counters,city,relation,sex,education,last_seen,'
                                                          'bdate,photo_max_orig,status,domain,online'
                                                })
                result = response.json()
                if 'error' in result:
                        error_msg = result['error']['error_msg']
                        self.show_result(f"Ошибка API: {error_msg}")
                        messagebox.showerror("Ошибка API", error_msg)
                else:
                        # print("===================================================== Респонс")
                        # print(json.dumps(data, indent=4, ensure_ascii=False))
                        data2 = result['response'][0]
                # print(json.dumps(data2, indent=4, ensure_ascii=False))
                time.sleep(0.3)
                return data2

        # Сохранение результирующего списка в виде html
        def process_friends(self, friends):
                if not friends:
                        self.show_result("Друзей не найдено или доступ ограничен.")
                        return

                # Формируем текстовый вывод
                text_result = f"Найдено друзей: {len(friends)}\n\n"

                # Формируем HTML вывод
                html_result = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Друзья пользователя VK</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #45688E; }}
                .friend {{ margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .name {{ font-weight: bold; font-size: 16px; }}
                .online {{ color: green; }}
                .offline {{ color: gray; }}
                .photo {{ margin-right: 10px; float: left; }}
                .info {{ margin-left: 10px; }}
                a {{ color: #45688E; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .clear {{ clear: both; }}
            </style>
        </head>
        <body>
            <h1>Друзья пользователя VK</h1>
            <p>Всего друзей: {len(friends)}</p>
        """
                # print(json.dumps(friends, indent=4, ensure_ascii=False))

                for i, friend in enumerate(friends, 1):
                        first_name = friend.get('first_name', '')
                        last_name = friend.get('last_name', '')
                        domain = friend.get('domain', '')
                        online = friend.get('online', 0)

                        # Текстовый вывод
                        text_result += (
                                f"{i}. {first_name} {last_name}\n"
                                f"   Страница: vk.com/{domain}\n"
                                f"   Онлайн: {'✓' if online == 1 else '✗'}\n"
                        )

                        if 'photo_max_orig' in friend:
                                text_result += f"   Фото: {friend['photo_max_orig']}\n"

                        text_result += "\n"

                        # HTML вывод
                        html_result += '<div class="friend">\n'

                        if 'photo_max_orig' in friend:
                                html_result += f'<img class="photo" src="{friend["photo_max_orig"]}" width="150" height="150">\n'

                        html_result += '<div class="info">\n'
                        html_result += f'<div class="name">{first_name} {last_name}</div>\n'
                        html_result += f'<div>Страница: <a href="https://vk.com/{domain}" target="_blank">vk.com/{domain}</a></div>\n'
                        html_result += f'<div class="{"online" if online == 1 else "offline"}">{"В сети" if online == 1 else "Не в сети"}</div>\n'

                        if 'city' in friend and friend['city']:
                                html_result += f'<div>Город: {friend["city"]["title"]}</div>\n'

                        if 'bdate' in friend:
                                html_result += f'<div>Дата рождения: {friend["bdate"]}</div>\n'
                        if 'last_seen' in friend:
                                html_result += f'<div>Видели в последнший раз: {time.strftime('%d/%m/%Y %H:%M', time.localtime(friend["last_seen"]['time']))} </div>\n'
                        if 'education' in friend:
                                html_result += f'<div>Образование: {friend["education"]}</div>\n'
                        if 'sex' in friend:
                                sex = 'оно'
                                if friend["sex"] == 2:
                                        sex = "Мужчина"
                                elif friend["sex"] == 1:
                                        sex = "Женщина"
                                html_result += f'<div>Пол: {sex}</div>\n'
                        if 'relation' in friend:

                                html_result += f'<div>Отношения: {friend["relation"]}</div>\n'

                        if 'status' in friend:
                                html_result += f'<div>Статус: {friend["status"]}</div>\n'

                        html_result += '</div>\n'
                        html_result += '<div class="clear"></div>\n'
                        html_result += '</div>\n'

                html_result += "</body>\n</html>"

                self.html_content = html_result
                self.show_result(text_result)
                self.save_html_btn.config(state=tk.NORMAL)
                self.open_browser_btn.config(state=tk.NORMAL)

        def show_result(self, text):
                self.result_area.delete('1.0', tk.END)
                self.result_area.insert(tk.INSERT, text)

        # сохранение файла
        def save_to_html(self):
                try:
                        home = str(Path.home())
                        file_path = os.path.join(home, "vk_friends.html")

                        with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(self.html_content)

                        messagebox.showinfo("Сохранение", f"Файл успешно сохранен: {file_path}")
                except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

        # кнопка Открыть в браузере
        def open_in_browser(self):
                try:
                        home = str(Path.home())
                        file_path = os.path.join(home, "vk_friends.html")

                        with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(self.html_content)

                        webbrowser.open(f"file://{file_path}")
                except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось открыть в браузере: {str(e)}")


if __name__ == "__main__":
        root = tk.Tk()
        app = VKFriendsApp(root)
        root.mainloop()