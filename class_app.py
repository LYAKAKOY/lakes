import tkinter as tk
import sqlite3 as sq
import asyncio
import aiohttp
import pyttsx3
import threading
import re
import io
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from tkinter import ttk, messagebox
from tkinter import filedialog
from PIL import Image, ImageTk

class App:
    DB_NAME = "Russian's_lakes.db"

    @classmethod
    def get_list_of_lakes(cls) -> list:
        with sq.connect(cls.DB_NAME) as connection:
            cur = connection.cursor()
            list_of_lakes = cur.execute("SELECT name FROM lakes").fetchall()
            list_of_lakes = [lake[0] for lake in list_of_lakes]
            return list_of_lakes

    def __init__(self):
        self.root = tk.Tk()
        self.style = ttk.Style()
        self.task = None
        self.image_lake = None
        self.image_lake_refactor = None
        self.style.configure('Search.TEntry', foreground='grey')
        width = 700
        height = 400

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.title("Известные озера России")
        style = ttk.Style()
        style.configure("Close.TButton")

        # LIST_BOX
        self.list_box = tk.Listbox(self.root, selectmode=tk.SINGLE, font=('Arial', 12))
        self.list_box.insert(tk.END, '')
        self.list_of_lakes = self.get_list_of_lakes()
        for option in self.list_of_lakes:
            self.list_box.insert(tk.END, option)
        self.search_entry = ttk.Entry(self.root, style='Search.TEntry', width=100)
        self.search_entry.insert(tk.END, "Поиск...")
        self.search_entry.bind("<FocusIn>", lambda event: self.hide_text_info(event.widget, "Поиск..."))
        self.search_entry.bind('<FocusOut>', lambda event: self.set_text_info(event.widget, "Поиск..."))
        self.search_entry.grid(row=0, column=0, sticky=tk.N)
        self.list_box.grid(row=0, column=0, sticky=tk.NS + tk.EW)
        self.list_box.configure(selectbackground=self.list_box.cget('background'), selectforeground='gray')
        self.list_box.bind("<<ListboxSelect>>", self.on_select)

        # IMAGE
        self.image = None
        self.image_field = tk.Label(self.root)
        self.image_field.grid(row=0, column=1, sticky="nsew")

        # TEXT
        self.text_field = tk.Text(self.root, wrap=tk.WORD)
        self.text_field.grid(row=0, column=2, sticky=tk.NS + tk.EW)
        self.text_field.configure(state="disabled")
        # voice_button = ttk.Button(self.root, text="\U0001F4E2", command=self.voice, width=2)
        # voice_button.grid(row=0, column=2, padx=5, pady=10, sticky=tk.NE)

        self.root.rowconfigure(0, weight=1, uniform="row")
        self.root.columnconfigure(0, weight=25, uniform="column")
        self.root.columnconfigure(1, weight=50, uniform="column")
        self.root.columnconfigure(2, weight=25, uniform="column")

        self.root.rowconfigure(0, weight=1, uniform="row")
        self.root.columnconfigure(0, weight=20, uniform="column")
        self.root.columnconfigure(1, weight=55, uniform="column")
        self.root.columnconfigure(2, weight=25, uniform="column")
        self.root.bind("<Configure>", lambda event: self.on_resize(event))

        # MENU1
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Фонд", menu=file_menu)
        file_menu.add_command(label="Найти...", command=self.search_lake)
        file_menu.add_separator()
        file_menu.add_command(label="Добавить F2", command=self.add_lake)
        self.root.bind("<F2>", lambda event: self.add_lake())
        file_menu.add_command(label="Удалить F3", command=self.delete_lake_window)
        self.root.bind("<F3>", lambda event: self.delete_lake_window())
        file_menu.add_command(label="Выйти F4", command=self.root.quit)
        self.root.bind("<F4>", lambda event: self.refactor_lake())

        # Menu2
        file_menu2 = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Справка", menu=file_menu2)
        file_menu2.add_command(label="Содержание", command=self.help_window)
        self.root.bind("<F1>", lambda event: self.help_window())
        file_menu2.add_separator()
        file_menu2.add_command(label="О программе", command=self.show_modal_window)

        self.root.config(menu=menu_bar)
        self.root.mainloop()

    def voice(self):
        text_to_speak = self.text_field.get(0.1, tk.END)
        thread = threading.Thread(target=self.reading_text, args=(text_to_speak,))
        thread.start()

    @staticmethod
    def reading_text(text: str):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()

    def show_modal_window(self):
        x_child, y_child = self.pack_window(400, 170)
        modal_window = tk.Toplevel()
        modal_window.geometry(f"400x170+{x_child}+{y_child}")
        modal_window.resizable(False, False)
        modal_window.title("О программе")
        frame = tk.Frame(modal_window, padx=10, pady=10)
        image_label = tk.Label(frame, text="\U0001F6A8", font=("Arial", 40), padx=10, pady=10)
        image_label.pack(side="left")
        label3 = tk.Label(frame, text="База данных 'Известные озера России'\n(c) Simakhov D.A., Russia, 2023\n")
        label3.pack(side="right")
        frame.pack()

        close_button = ttk.Button(modal_window, text="Ок", style="Close.TButton", command=modal_window.destroy)
        close_button.pack(side=tk.RIGHT, padx=20, pady=0)

        modal_window.transient(master=self.root)
        modal_window.grab_set()
        modal_window.focus_set()
        self.root.wait_window(modal_window)

    def help_window(self):
        x_child, y_child = self.pack_window(400, 200)
        window = tk.Toplevel()
        window.focus_set()
        window.title("Справка")
        window.geometry(f"400x200+{x_child}+{y_child}")
        window.resizable(False, False)
        text = "База данных 'Знаменитые озера России'\n"
        text += "Позволяет: добавлять/ изменять/ удалять информацию.\n"
        text += "Клавиши программы:\n"
        text += "F1-вызов справки по программе,\n"
        text += "F2-добавить в базу данных,\n"
        text += "F3-удалить из базы данных,\n"
        text += "F4-изменить запись в базе данных,\n"
        text += "F10-меню программы"
        label = tk.Label(window, text=text, font=("Arial", 10))
        label.pack(padx=20, pady=10)

        close_button = ttk.Button(window, text="Закрыть", style="Close.TButton", command=window.destroy)
        close_button.pack(side=tk.RIGHT, padx=20, pady=0)

    def pack_window(self, child_width: int, child_height: int) -> (int, int):
        self.root.update_idletasks()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        x_root = self.root.winfo_x() + (root_width // 2) - (child_width // 2)
        y_root = self.root.winfo_y() + (root_height // 2) - (child_height // 2)
        return x_root, y_root

    def settings_window(self, window: tk.Toplevel) -> None:
        window.withdraw()
        window.update_idletasks()
        x_child, y_child = self.pack_window(window.winfo_width(), window.winfo_height())
        window.geometry(f'+{x_child}+{y_child}')
        window.deiconify()
        window.focus_set()

    def search_lake(self):
        def search():
            text = entry.get()
            self.search_entry.configure(foreground='black')
            self.search_entry.delete(0, tk.END)
            if text != 'Введите название озера...':
                self.search_entry.insert(0, text)
                if text != 'Поиск...' and text != '':
                    self.list_box.delete(1, tk.END)
                    for el in self.list_of_lakes:
                        if text.lower() in el.lower():
                            self.list_box.insert(tk.END, el)
                elif not text:
                    self.list_box.delete(1, tk.END)
                    for el in self.list_of_lakes:
                        self.list_box.insert(tk.END, el)
            else:
                self.search_entry.insert(tk.END, '')
            search_window.destroy()

        search_window = tk.Toplevel()
        search_window.title("Поиск")
        self.settings_window(search_window)
        entry = ttk.Entry(search_window, width=50)
        entry.configure(foreground='#999')
        entry.bind("<FocusIn>", lambda event: self.hide_text_info(event.widget, 'Введите название озера...'))
        entry.bind('<FocusOut>', lambda event: self.set_text_info(event.widget, 'Введите название озера...'))
        entry.insert(0, 'Введите название озера...')
        entry.grid(row=0, column=0, columnspan=2)

        search_button = ttk.Button(search_window, text="Найти", command=search, width=25)
        search_button.grid(row=1, column=0, pady=10)
        cancel_button = ttk.Button(search_window, text="Отмена", command=search_window.destroy, width=25)
        cancel_button.grid(row=1, column=1, pady=10)

    def on_resize(self, event: tk.Event) -> None:
        if self.image is None:
            return
        label_width = self.image_field.winfo_width()
        label_height = self.image_field.winfo_height()

        photo = Image.open(io.BytesIO(self.image)).resize((label_width, label_height), Image.BICUBIC)
        picture = ImageTk.PhotoImage(photo)
        self.image_field.configure(image=picture)
        self.image_field.image = picture

    def set_text_info(self, field: ttk.Entry | tk.Entry, text_info: str):
        if not field.get():
            field.insert(0, text_info)
            field.configure(foreground="#999")

        self.root.after_cancel(self.task)

    def hide_text_info(self, field: ttk.Entry | tk.Entry, text_info: str):
        if field.get() == text_info:
            field.delete(0, 'end')
            field.configure(foreground='black')
        self.root.after(10, self.check_value)

    def check_value(self) -> None:
        text = self.search_entry.get()
        if text != 'Поиск...' and text != '':
            self.list_box.delete(1, tk.END)
            for el in self.list_of_lakes:
                if text.lower() in el.lower():
                    self.list_box.insert(tk.END, el)
        elif not text:
            self.list_box.delete(1, tk.END)
            for el in self.list_of_lakes:
                self.list_box.insert(tk.END, el)
        self.task = self.root.after(10, self.check_value)

    def on_select(self, event: tk.Event) -> None:
        try:
            widget: tk.Listbox = event.widget
            selection = widget.curselection()
            name = widget.get(selection)
            with sq.connect(self.DB_NAME) as connection:
                cur = connection.cursor()
                image_url, description = cur.execute("SELECT picture, description FROM lakes WHERE name = ?",
                                                     (name,)).fetchone()

                self.image = image_url
                self.on_resize("<Configure>")

                self.text_field.configure(state="normal")
                self.text_field.delete(1.0, tk.END)
                self.text_field.insert(tk.END, description)
                self.text_field.configure(state="disabled")
        except tk.TclError:
            pass

    def delete_lake_window(self):
        del_window = tk.Toplevel()
        del_window.title('Удаление озера')
        self.settings_window(del_window)
        entry = ttk.Entry(del_window, width=50)
        entry.configure(foreground='#999')
        entry.bind("<FocusIn>", lambda event: self.hide_text_info(event.widget, 'Введите название озера...'))
        entry.bind('<FocusOut>', lambda event: self.set_text_info(event.widget, 'Введите название озера...'))
        entry.insert(0, 'Введите название озера...')
        entry.grid(row=0, column=0, columnspan=2)

        search_button = ttk.Button(del_window, text="Удалить", command=lambda: self.delete_lake(entry.get()), width=25)
        search_button.grid(row=1, column=0, pady=10)
        cancel_button = ttk.Button(del_window, text="Отмена", command=del_window.destroy, width=25)
        cancel_button.grid(row=1, column=1, pady=10)

    def delete_lake(self, name: str) -> None:
        if name == "Введите название озера..." or name == '':
            messagebox.showerror('Ошибка', 'Поле названия озера не должно быть пустым!')
            return
        if name not in self.list_of_lakes:
            messagebox.showerror('Ошибка', f'Озера с названием {name} не существует в базе')
            return
        with sq.connect("Russian's_Lakes.db") as connection:
            cur = connection.cursor()
            cur.execute("DELETE FROM lakes WHERE name = ?", (name,))
        self.list_of_lakes.remove(name)
        list_box_values = self.list_box.get(0, tk.END)
        for i, value in enumerate(list_box_values):
            if value == name:
                self.list_box.delete(i)
        messagebox.showinfo('Удаление озера', f'Удаление {name} успешно прошло!')

    def add_lake(self):
        def delete_info_about_lake() -> None:
            text_field_about_lake.delete(1.0, tk.END)
            text_field_about_lake.insert(0.1, "Введите информацию об озере...")
            text_field_about_lake.configure(foreground="#999")

        def delete_name_of_lake() -> None:
            lake_name_entry.delete(0, tk.END)
            lake_name_entry.insert(0, 'Введите название озера...')
            lake_name_entry.configure(foreground="#999")

        def delete_picture_of_lake() -> None:
            self.image_lake = None
            image = Image.open("no_image-1280x1280.png")
            image = image.resize((150, 150))
            photo = ImageTk.PhotoImage(image)
            open_file_button.configure(image=photo)
            open_file_button.image = photo

        def parse_content(content):
            soup = BeautifulSoup(content, 'html.parser')
            body_content = soup.find(id='bodyContent')
            text = body_content.get_text()
            text = re.sub(r'\n\s*\n', '\n', text)
            return text.strip()

        async def get_info_lake(session: aiohttp.ClientSession, url):
            try:
                async with session.get(url) as connection:
                    if connection.status == 200:
                        content = await connection.text()
                        loop = asyncio.get_running_loop()
                        with ThreadPoolExecutor() as pool:
                            task = loop.run_in_executor(
                                pool, parse_content, content
                            )
                            result = await task
                            if text_field_about_lake.get(0.1, tk.END).strip() == "Введите информацию об озере...":
                                text_field_about_lake.delete(1.0, tk.END)
                            text_field_about_lake.configure(foreground='black')
                            text_field_about_lake.insert(tk.END, result)
                    else:
                        tk.messagebox.showerror("Ошибка", "Информации о данном озере нет в википедии")
            except aiohttp.ClientConnectionError:
                tk.messagebox.showerror("Ошибка", "Отсутствует интернет или сайт википедии не отвечает!")

        async def get_wikipedia(topic: str):
            url = f'https://ru.wikipedia.org/wiki/{topic}'
            async with aiohttp.ClientSession() as session:
                await get_info_lake(session, url)

        def connect_to_wikipedia():
            if lake_name_entry.get() != '' and lake_name_entry.get() != "Введите название озера...":
                asyncio.run(get_wikipedia(lake_name_entry.get()))
            else:
                tk.messagebox.showerror("Ошибка", "Поле с названием озера не должно быть пустым!")

        def open_file_dialog():
            file_path = filedialog.askopenfilename(parent=add_form)
            if file_path:
                self.image_lake = file_path
                image = Image.open(file_path)
                image = image.resize((150, 150))
                photo = ImageTk.PhotoImage(image)
                open_file_button.configure(image=photo)
                open_file_button.image = photo

        def save_data():
            name_of_lake = lake_name_entry.get()
            if name_of_lake in ('', "Введите название озера..."):
                tk.messagebox.showerror("Ошибка", "Обязательные поля: картинка озера и название озера")
            else:
                with sq.connect("Russian's_Lakes.db") as con:
                    if self.image_lake_refactor is not None:
                        with open(self.image_lake_refactor, 'rb') as image_file:
                            image_data = image_file.read()
                    else:
                        with open('no_image-1280x1280.png', 'rb') as image_file:
                            image_data = image_file.read()
                    cur = con.cursor()
                    text_about_lake = text_field_about_lake.get(1.0, tk.END)
                    if text_about_lake.strip() == 'Введите информацию об озере...':
                        text_about_lake = 'Нет информации'
                    cur.execute("INSERT INTO lakes (name, picture, description) VALUES (?, ?, ?) ",
                                (name_of_lake, image_data,
                                 text_about_lake))
                self.list_of_lakes.append(name_of_lake)
                self.list_box.insert(tk.END, name_of_lake)
                messagebox.showinfo('Результат', 'Озеро успешно добавлено в базу')
                add_form.destroy()

        def cancel():
            lake_name_entry.delete(0, tk.END)
            add_form.destroy()

        def clear_entry_text(event):
            field: tk.Text = event.widget
            if field.get(0.1, tk.END).strip() == "Введите информацию об озере...":
                field.delete(1.0, tk.END)
                field.configure(foreground='black')

        def set_hint_text(event):
            field: tk.Text = event.widget
            if not field.get(1.0, tk.END).strip():
                field.insert(0.1, "Введите информацию об озере...")
                field.configure(foreground="#999")

        add_form = tk.Toplevel()
        self.settings_window(add_form)
        add_form.title("Ввод информации о озере")
        add_form.resizable(False, False)

        image = Image.open("no_image-1280x1280.png")
        image = image.resize((150, 150))
        photo = ImageTk.PhotoImage(image)

        open_file_button = ttk.Button(add_form, text="Обзор...", command=open_file_dialog, image=photo)
        open_file_button.image = photo
        open_file_button.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        delete = ttk.Button(add_form, text="\u2715", command=delete_picture_of_lake, width=2)
        delete.grid(row=0, column=1, padx=50, pady=10, sticky=tk.NW)

        lake_name_entry = ttk.Entry(add_form, width=20)
        lake_name_entry.configure(foreground="#999")
        lake_name_entry.insert(0, "Введите название озера...")
        lake_name_entry.bind("<FocusIn>", lambda event: self.hide_text_info(event.widget, "Введите название озера..."))
        lake_name_entry.bind('<FocusOut>', lambda event: self.set_text_info(event.widget, "Введите название озера..."))
        lake_name_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        delete = ttk.Button(add_form, text="\u2715", command=delete_name_of_lake, width=2)
        delete.grid(row=1, column=1, padx=5, pady=10, sticky=tk.NE)

        text_field_about_lake = tk.Text(add_form, width=45, height=5)
        text_field_about_lake.configure(foreground='#999')
        text_field_about_lake.insert(0.1, "Введите информацию об озере...")
        text_field_about_lake.bind("<Control-c>", lambda event: self.text_field.event_generate("<<Copy>>"))
        text_field_about_lake.bind("<FocusIn>", clear_entry_text)
        text_field_about_lake.bind('<FocusOut>', set_hint_text)
        text_field_about_lake.grid(row=2, column=0, columnspan=2, sticky=tk.S)
        delete = ttk.Button(add_form, text="\u2715", command=delete_info_about_lake, width=2)
        delete.grid(row=2, column=1, padx=5, pady=10, sticky=tk.NE)

        button_about_lake = ttk.Button(add_form, text="Взять информацию об озере из википедии",
                                       command=connect_to_wikipedia)
        button_about_lake.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        save_button = ttk.Button(add_form, text="Сохранить", command=save_data, width=25)
        save_button.grid(row=4, column=0, pady=10)

        cancel_button = ttk.Button(add_form, text="Отмена", command=cancel, width=25)
        cancel_button.grid(row=4, column=1, pady=10)

    def refactor_lake(self):
        def delete_info_about_lake() -> None:
            text_field_about_lake.delete(1.0, tk.END)
            text_field_about_lake.insert(0.1, "Введите информацию об озере...")
            text_field_about_lake.configure(foreground="#999")

        def delete_name_of_lake() -> None:
            lake_name_entry.delete(0, tk.END)
            lake_name_entry.insert(0, 'Введите название озера...')
            lake_name_entry.configure(foreground="#999")

        def delete_picture_of_lake() -> None:
            self.image_lake_refactor = None
            image = Image.open("no_image-1280x1280.png")
            image = image.resize((150, 150))
            photo = ImageTk.PhotoImage(image)
            open_file_button.configure(image=photo)
            open_file_button.image = photo

        def parse_content(content):
            soup = BeautifulSoup(content, 'html.parser')
            body_content = soup.find(id='bodyContent')
            text = body_content.get_text()
            text = re.sub(r'\n\s*\n', '\n', text)
            return text.strip()

        async def get_info_lake(session: aiohttp.ClientSession, url):
            try:
                async with session.get(url) as connection:
                    if connection.status == 200:
                        content = await connection.text()
                        loop = asyncio.get_running_loop()
                        with ThreadPoolExecutor() as pool:
                            task = loop.run_in_executor(
                                pool, parse_content, content
                            )
                            result = await task
                            if text_field_about_lake.get(0.1, tk.END).strip() == "Введите информацию об озере...":
                                text_field_about_lake.delete(1.0, tk.END)
                            text_field_about_lake.configure(foreground='black')
                            text_field_about_lake.insert(tk.END, result)
                    else:
                        tk.messagebox.showerror("Ошибка", "Информации о данном озере нет в википедии")
            except aiohttp.ClientConnectionError:
                tk.messagebox.showerror("Ошибка", "Отсутствует интернет или сайт википедии не отвечает!")

        async def get_wikipedia(topic: str):
            url = f'https://ru.wikipedia.org/wiki/{topic}'
            async with aiohttp.ClientSession() as session:
                await get_info_lake(session, url)

        def connect_to_wikipedia():
            if lake_name_entry.get() != '' and lake_name_entry.get() != "Введите название озера...":
                asyncio.run(get_wikipedia(lake_name_entry.get()))
            else:
                tk.messagebox.showerror("Ошибка", "Поле с названием озера не должно быть пустым!")

        def open_file_dialog():
            file_path = filedialog.askopenfilename(parent=add_form)
            if file_path:
                self.image_lake_refactor = file_path
                image = Image.open(file_path)
                image = image.resize((150, 150))
                photo = ImageTk.PhotoImage(image)
                open_file_button.configure(image=photo)
                open_file_button.image = photo

        def update_data():
            name_of_lake = lake_name_entry.get()
            if combo_box.current() == 0:
                return
            else:
                name_update = self.list_of_lakes[combo_box.current() - 1]
            if name_of_lake in ('', "Введите название озера..."):
                tk.messagebox.showerror("Ошибка", "Обязательное поле: название озера")
            else:
                with sq.connect("Russian's_Lakes.db") as con:
                    if self.image_lake_refactor is not None:
                        with open(self.image_lake_refactor, 'rb') as image_file:
                            image_data = image_file.read()
                    else:
                        with open('no_image-1280x1280.png', 'rb') as image_file:
                            image_data = image_file.read()
                    cur = con.cursor()
                    text_about_lake = text_field_about_lake.get(1.0, tk.END)
                    if text_about_lake.strip() == 'Введите информацию об озере...':
                        text_about_lake = 'Нет информации'
                    cur.execute("UPDATE lakes SET name = ?, picture = ?, description = ? WHERE name = ? ",
                                (name_of_lake, image_data,
                                 text_about_lake, name_update))
                self.list_of_lakes.remove(name_update)
                list_box_values = self.list_box.get(0, tk.END)
                for i, value in enumerate(list_box_values):
                    if value == name_update:
                        self.list_box.delete(i)
                self.list_of_lakes.append(name_of_lake)
                self.list_box.insert(tk.END, name_of_lake)
                messagebox.showinfo('Результат', 'Изменения успешно применены')
                add_form.destroy()

        def cancel():
            lake_name_entry.delete(0, tk.END)
            add_form.destroy()

        def clear_entry_text(event):
            field: tk.Text = event.widget
            if field.get(0.1, tk.END).strip() == "Введите информацию об озере...":
                field.delete(1.0, tk.END)
                field.configure(foreground='black')

        def set_hint_text(event):
            field: tk.Text = event.widget
            if not field.get(1.0, tk.END).strip():
                field.insert(0.1, "Введите информацию об озере...")
                field.configure(foreground="#999")

        def selected(event):
            if combo_box.current() == 0:
                return
            box: ttk.Combobox = event.widget
            name = box.get()
            with sq.connect(self.DB_NAME) as connection:
                cur = connection.cursor()
                image_url, description = cur.execute("SELECT picture, description FROM lakes WHERE name = ?",
                                                     (name,)).fetchone()

                photo = Image.open(io.BytesIO(image_url)).resize((150, 150), Image.BICUBIC)
                picture = ImageTk.PhotoImage(photo)
                open_file_button.configure(image=picture)
                open_file_button.image = picture
                lake_name_entry.delete(0, tk.END)
                lake_name_entry.insert(0, name)
                lake_name_entry.configure(foreground='black')
                text_field_about_lake.delete(1.0, tk.END)
                text_field_about_lake.insert(tk.END, description)
                text_field_about_lake.configure(foreground='black')

        add_form = tk.Toplevel()
        self.settings_window(add_form)
        add_form.title("Ввод информации о озере")
        add_form.resizable(False, False)

        image = Image.open("no_image-1280x1280.png")
        image = image.resize((150, 150))
        photo = ImageTk.PhotoImage(image)

        open_file_button = ttk.Button(add_form, text="Обзор...", command=open_file_dialog, image=photo)
        open_file_button.image = photo
        open_file_button.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        delete = ttk.Button(add_form, text="\u2715", command=delete_picture_of_lake, width=2)
        delete.grid(row=0, column=1, padx=50, pady=10, sticky=tk.NW)

        combo_box = ttk.Combobox(add_form, values=['Выберите озеро'] + self.list_of_lakes, state="readonly", width=10,
                                 foreground='gray')
        combo_box.current(0)
        combo_box.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NW)
        combo_box.bind("<<ComboboxSelected>>", selected)
        lake_name_entry = ttk.Entry(add_form, width=20)
        lake_name_entry.configure(foreground="#999")
        lake_name_entry.insert(0, "Введите название озера...")
        lake_name_entry.bind("<FocusIn>", lambda event: self.hide_text_info(event.widget, "Введите название озера..."))
        lake_name_entry.bind('<FocusOut>', lambda event: self.set_text_info(event.widget, "Введите название озера..."))
        lake_name_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        delete = ttk.Button(add_form, text="\u2715", command=delete_name_of_lake, width=2)
        delete.grid(row=1, column=1, padx=5, pady=10, sticky=tk.NE)

        text_field_about_lake = tk.Text(add_form, width=45, height=5)
        text_field_about_lake.configure(foreground='#999')
        text_field_about_lake.insert(0.1, "Введите информацию об озере...")
        text_field_about_lake.bind("<Control-c>", lambda event: self.text_field.event_generate("<<Copy>>"))
        text_field_about_lake.bind("<FocusIn>", clear_entry_text)
        text_field_about_lake.bind('<FocusOut>', set_hint_text)
        text_field_about_lake.grid(row=2, column=0, columnspan=2, sticky=tk.S)
        delete = ttk.Button(add_form, text="\u2715", command=delete_info_about_lake, width=2)
        delete.grid(row=2, column=1, padx=5, pady=10, sticky=tk.NE)

        button_about_lake = ttk.Button(add_form, text="Взять информацию об озере из википедии",
                                       command=connect_to_wikipedia)
        button_about_lake.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        save_button = ttk.Button(add_form, text="Сохранить", command=update_data, width=25)
        save_button.grid(row=4, column=0, pady=10)

        cancel_button = ttk.Button(add_form, text="Отмена", command=cancel, width=25)
        cancel_button.grid(row=4, column=1, pady=10)


if __name__ == '__main__':
    App()
