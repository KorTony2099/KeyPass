import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import uuid
import os
import sys

class PasswordManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Менеджер паролей")
        self.root.geometry("800x400")

        self.create_db()
        self.create_widgets()
        self.load_data()
        self.create_db()

    def resource_path(self, relative_path = 'passwords.db'):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def create_db(self):
        self.conn = sqlite3.connect(self.resource_path())
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS passwords
                         (id TEXT PRIMARY KEY,
                          name TEXT,
                          login TEXT,
                          password TEXT,
                          description TEXT,
                          url TEXT)''')
        self.conn.commit()

    def create_widgets(self):
        # Таблица для отображения записей
        self.tree = ttk.Treeview(self.root, columns=('name', 'login', 'password', 'description', 'url'),
                                 show='headings', selectmode='browse')

        # Настройка колонок
        columns = [
            ('name', 'Название', 150),
            ('login', 'Логин', 150),
            ('password', 'Пароль', 150),
            ('description', 'Описание', 200),
            ('url', 'URL', 150)
        ]

        for col_id, col_text, width in columns:
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=width, anchor='w')

        self.tree.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=2, sticky='ns')

        # Обработчик двойного клика
        self.tree.bind('<Double-Button-1>', self.copy_cell)

        # Кнопки управления
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)

        self.add_btn = ttk.Button(button_frame, text="Добавить", command=self.add_record)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        self.del_btn = ttk.Button(button_frame, text="Удалить", command=self.delete_record)
        self.del_btn.pack(side=tk.LEFT, padx=5)

        self.upd_btn = ttk.Button(button_frame, text="Изменить", command=self.update_record)
        self.upd_btn.pack(side=tk.LEFT, padx=5)

        # Настройка растягивания
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def load_data(self):
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Загрузка данных из БД
        self.c.execute("SELECT * FROM passwords")
        for row in self.c.fetchall():
            masked_password = '*' * len(row[3]) if row[3] else ''
            self.tree.insert('', tk.END, values=(row[1], row[2], masked_password, row[4], row[5]), iid=row[0])

    def copy_cell(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return

        column_id = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)

        if not item_id:
            return

        col_index = int(column_id[1:]) - 1
        columns = ['name', 'login', 'password', 'description', 'url']
        column_headers = ['Название скопировано', 'Логин скопирован', 'Пароль скопирован', 'Описание скопировано', 'URL скопирован']

        if col_index < 0 or col_index >= len(columns):
            return

        # Получаем значение для копирования
        if columns[col_index] == 'password':
            self.c.execute("SELECT password FROM passwords WHERE id=?", (item_id,))
            value = self.c.fetchone()[0]
        else:
            values = self.tree.item(item_id, 'values')
            value = values[col_index]

        # Копируем и показываем уведомление
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.show_autoclose_message(f"{column_headers[col_index]}")

    def show_autoclose_message(self, message):
        if hasattr(self, 'temp_msg') and self.temp_msg.winfo_exists():
            self.temp_msg.destroy()

        self.temp_msg = tk.Toplevel(self.root)
        self.temp_msg.overrideredirect(True)
        self.temp_msg.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + self.root.winfo_height() - 50
        ))
        self.temp_msg.configure(bg='lightgreen')

        label = ttk.Label(
            self.temp_msg,
            text=message,
            padding=10,
            background='lightgreen',
            font=('Arial', 10, 'bold')
        )
        label.pack()

        self.temp_msg.after(1000, self.temp_msg.destroy)

    def add_record(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить новую запись")

        fields = [
            ('name', 'Название'),
            ('login', 'Логин'),
            ('password', 'Пароль'),
            ('description', 'Описание'),
            ('url', 'URL')
        ]

        entries = {}
        for i, (field, label) in enumerate(fields):
            ttk.Label(dialog, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(dialog)
            if field == 'password':
                entry.config(show="*")
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[field] = entry

        def save():
            data = {
                'id': str(uuid.uuid4()),
                'name': entries['name'].get(),
                'login': entries['login'].get(),
                'password': entries['password'].get(),
                'description': entries['description'].get(),
                'url': entries['url'].get()
            }

            if not all(data.values()):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены")
                return

            try:
                self.c.execute('''INSERT INTO passwords VALUES 
                               (:id, :name, :login, :password, :description, :url)''', data)
                self.conn.commit()
                self.load_data()
                dialog.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка базы данных", str(e))

        ttk.Button(dialog, text="Сохранить", command=save).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        self.c.execute("SELECT name FROM passwords WHERE id=?", (item_id,))
        name = self.c.fetchone()[0]

        if messagebox.askyesno("Подтверждение", f"Удалить запись '{name}'?"):
            self.c.execute("DELETE FROM passwords WHERE id=?", (item_id,))
            self.conn.commit()
            self.load_data()

    def update_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для изменения")
            return

        item_id = selected[0]

        # Получаем текущие данные записи
        self.c.execute("SELECT * FROM passwords WHERE id=?", (item_id,))
        record = self.c.fetchone()

        # Создаем окно редактирования
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование записи")

        fields = [
            ('name', 'Название'),
            ('login', 'Логин'),
            ('password', 'Пароль'),
            ('description', 'Описание'),
            ('url', 'URL')
        ]

        entries = {}
        for i, (field, label) in enumerate(fields):
            ttk.Label(dialog, text=label + ":").grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(dialog)
            entry.grid(row=i, column=1, padx=5, pady=5)
            if field == 'password':
                entry.config(show="*")
            # Заполняем поля текущими значениями
            entry.insert(0, record[fields.index((field, label)) + 1])
            entries[field] = entry

        def save_changes():
            new_data = {
                'name': entries['name'].get(),
                'login': entries['login'].get(),
                'password': entries['password'].get(),
                'description': entries['description'].get(),
                'url': entries['url'].get(),
                'id': item_id
            }

            if not all(new_data.values()):
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены")
                return

            try:
                self.c.execute('''UPDATE passwords SET
                    name = :name,
                    login = :login,
                    password = :password,
                    description = :description,
                    url = :url
                    WHERE id = :id''', new_data)
                self.conn.commit()
                self.load_data()
                dialog.destroy()
                messagebox.showinfo("Успех", "Запись успешно обновлена")
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка базы данных", str(e))

        ttk.Button(dialog, text="Сохранить", command=save_changes).grid(
            row=len(fields), column=0, columnspan=2, pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManager(root)
    root.mainloop()
