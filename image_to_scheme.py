import tkinter as tk
from tkinter import filedialog, ttk
import threading
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from sklearn.cluster import KMeans
import colorspacious
from palette import rgb_to_dmc


class ImagePixelizerApp:
    '''Главный класс приложения, содержащий в себе всю его функциональность'''

    def __init__(self, root):
        self.root = root
        self.root.title("Stitch Scheme Builder")
        self.root.resizable(width=False, height=False)

        # Стандартный размер пикселя выходного изображения
        self.pixel_size = 1

        # Создание элементов управления
        self.input_label = tk.Label(root, text="Input Image:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10)

        # Кнопка выбора загружаемого изображения
        self.input_image_button = tk.Button(
            root, text="Choose Image", command=self.choose_image)
        self.input_image_button.grid(row=0, column=1, padx=10, pady=10)

        self.width_label = tk.Label(root, text="Output Width:")
        self.width_label.grid(row=1, column=0, padx=10, pady=10)

        self.width_entry = tk.Entry(root)
        self.width_entry.grid(row=1, column=1, padx=10, pady=10)
        # Привязываем функцию к событию изменения текста в поле ширины
        self.width_entry.bind('<KeyRelease>', self.update_pixel_dropdown)

        self.height_label = tk.Label(root, text="Output Height:")
        self.height_label.grid(row=2, column=0, padx=10, pady=10)

        self.height_entry = tk.Entry(root)
        self.height_entry.grid(row=2, column=1, padx=10, pady=10)
        # Привязываем функцию к событию изменения текста в поле высоты
        self.height_entry.bind('<KeyRelease>', self.update_pixel_dropdown)

        self.pixel_size_label = tk.Label(root, text="Pixel Size:")
        self.pixel_size_label.grid(row=3, column=0, padx=10, pady=10)
        # Выпадающий список для выбора размерности пикселя
        self.pixel_size_var = tk.StringVar(root)
        self.pixel_size_dropdown = ttk.Combobox(
            root, textvariable=self.pixel_size_var, state='readonly')
        self.pixel_size_dropdown.grid(row=3, column=1, padx=10, pady=10)

        self.color_count_label = tk.Label(root, text="Color Count:")
        self.color_count_label.grid(row=4, column=0, padx=10, pady=10)

        self.color_count_entry = tk.Entry(root)
        self.color_count_entry.grid(row=4, column=1, padx=10, pady=10)

        self.pixelize_button = tk.Button(
            root, text="Make a Scheme", command=self.start_pixelize_thread)
        self.pixelize_button.grid(row=5, column=0, padx=10, pady=10)

        self.cancel_button = tk.Button(
            root, text="Cancel", command=self.cancel_pixelize_thread, state="disabled")
        self.cancel_button.grid(row=5, column=1, padx=10, pady=10)

        # Индикатор прогресса
        self.progress_bar = ttk.Progressbar(
            root, orient="horizontal", mode="determinate", maximum=100, length=300)
        self.progress_bar.grid(row=6, columnspan=2, padx=10, pady=10)

        # Подпись для прогрессбара
        self.progress_label = tk.Label(root, text="")
        self.progress_label.grid(row=7, columnspan=2)

        # Переменные для хранения данных
        self.input_image_path = None
        self.palette = None
        self.cancel_flag = False  # Флаг для отмены выполнения потока

        # Обновляем выпадающий список при создании приложения
        self.update_pixel_size_dropdown()

    def update_pixel_dropdown(self, event=None):
        '''Метод для обновления выпадающего списка при изменении значений в текстовых полях'''
        self.update_pixel_size_dropdown()

    def update_pixel_size_dropdown(self):
        '''Метод для обновления выпадающего списка с размерностью пикселя'''
        # Получаем новые значения ширины и высоты изображения из текстовых полей
        output_width = self.width_entry.get()
        output_height = self.height_entry.get()

        # Проверяем, что значения ширины и высоты являются целыми числами
        try:
            output_width = int(output_width)
            output_height = int(output_height)
        except ValueError:
            # Если значения не могут быть преобразованы в целые числа, выходим из функции
            return

        # Очищаем список
        self.pixel_size_dropdown['values'] = []

        # Находим все общие делители ширины и высоты изображения
        common_divisors = []
        for i in range(1, min(output_width, output_height) + 1):
            if output_width % i == 0 and output_height % i == 0:
                common_divisors.append(i)

        # Добавляем общие делители в список размеров пикселя
        self.pixel_size_dropdown['values'] = common_divisors

        # Устанавливаем значение по умолчанию как первый общий делитель
        if common_divisors:
            self.pixel_size_dropdown.current(0)
        else:
            # Если общих делителей нет, устанавливаем пустое значение
            self.pixel_size_dropdown.set('')

    def choose_image(self):
        '''Метод, открывающий диалоговое окно для выбора загружаемого изображения'''
        self.input_image_path = filedialog.askopenfilename()

    def toggle_controls(self, state):
        '''Метод для блокировки или разблокировки элементов управления'''
        for widget in [self.input_image_button, self.pixel_size_dropdown,
                       self.width_entry, self.height_entry,
                       self.color_count_entry, self.pixelize_button]:
            widget.configure(state=state)

    def start_pixelize_thread(self):
        '''Создание потока для выполнения генерации изображения'''

        # Очищаем текст под прогрессбаром
        self.progress_label.config(text="")

        # Блокируем ввод на время выполнения потока
        self.toggle_controls("disabled")
        # Активируем кнопку отмены генерации изображения
        self.cancel_button.configure(state="normal")

        thread = threading.Thread(target=self.pixelize_image)
        thread.start()

        if thread.is_alive():
            print('Thread has been started')
            self.progress_label.config(
                text="Image generation will begin shortly")

    def cancel_pixelize_thread(self):
        '''Отмена выполнения потока генерации изображения'''
        # Устанавливаем флаг отмены в True
        self.cancel_flag = True
        # Блокировка кнопки "Cancel"
        self.cancel_button.configure(
            state="disabled")

        # Разблокировка элементов управления
        self.toggle_controls("normal")

        # Остановка прогрессбара и сброс его значения
        self.progress_bar.stop()
        self.progress_bar["value"] = 0

        # Оповещение пользователя о том, что генерация изображения отменена
        self.progress_label.config(
            text="Image generation thread has been cancelled")

    def update_progress(self, value):
        '''Метод, визуально обновляющий прогрессбар'''
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"Progress: {int(value)}%")
        self.root.update_idletasks()

    def pixelize_image(self):
        '''Метод для преобразования исходного изображения в пикселизованное'''
        try:
            output_width = int(self.width_entry.get())
            output_height = int(self.height_entry.get())
            color_count = int(self.color_count_entry.get())

            if not self.input_image_path:
                print("Please choose an input image.")
                return

            input_image = Image.open(self.input_image_path)
            input_image = input_image.resize((output_width, output_height))

            # Преобразование изображения в массив numpy
            img_array = np.array(input_image)

            # Вычисление количества линий сетки
            grid_width = output_width // self.pixel_size
            grid_height = output_height // self.pixel_size

            # Выполнение кластеризации цветов
            # Преобразование в двумерный массив
            reshaped_array = img_array.reshape((-1, 3))
            kmeans = KMeans(n_clusters=color_count,
                            random_state=0).fit(reshaped_array)

            # Получение центров кластеров (представительные цвета)
            representative_colors = kmeans.cluster_centers_.astype(int)

            # Создание палитры в формате RGB
            self.palette = [tuple(color) for color in representative_colors]

            # Создание выходного изображения
            output_image = Image.new('RGB', (output_width, output_height))

            # Замена цветов пикселей на ближайшие из палитры DMC
            total_pixels = grid_width * grid_height
            processed_pixels = 0
            for y in range(0, input_image.size[1], self.pixel_size):
                for x in range(0, input_image.size[0], self.pixel_size):
                    # Проверяем флаг отмены
                    if self.cancel_flag:
                        # Прерываем выполнение и сбрасываем флаг, если он установлен в True
                        self.cancel_flag = False
                        return
                    pixel = tuple(
                        np.mean(img_array[y:y+self.pixel_size, x:x+self.pixel_size],
                                axis=(0, 1)).astype(int))
                    closest_color = self.find_closest_color(pixel)
                    closest_color = min(rgb_to_dmc, key=lambda c: np.linalg.norm(
                        np.array(closest_color) - np.array(c)))  # Замена цвета на ближайший из палитры DMC
                    if closest_color:
                        for i in range(self.pixel_size):
                            for j in range(self.pixel_size):
                                output_image.putpixel(
                                    (x + i, y + j), closest_color)
                        self.add_color_number_to_image(
                            output_image, closest_color)  # Добавление номера цвета
                    processed_pixels += 1
                    progress_percentage = (
                        processed_pixels / total_pixels) * 100
                    self.update_progress(progress_percentage)

            draw = ImageDraw.Draw(output_image)

            for x in range(0, output_width, self.pixel_size):
                draw.line([(x, 0), (x, output_height)],
                          fill='black', width=1)
            for y in range(0, output_height, self.pixel_size):
                draw.line([(0, y), (output_width, y)],
                          fill='black', width=1)

            self.save_image(output_image)
            # output_image.show()
        finally:
            # Блокировка кнопки "Cancel"
            self.cancel_button.configure(state="disabled")
            # Разблокировка элементов управления
            self.toggle_controls("normal")

            # Остановка и сброс значения прогрессбара
            self.progress_bar.stop()
            self.progress_bar["value"] = 0

            self.progress_label.config(text="")

    def add_color_number_to_image(self, image, color):
        '''Метод для добавления номера цвета в правый верхний угол изображения'''
        draw = ImageDraw.Draw(image)
        text = rgb_to_dmc[color]  # Получаем номер цвета DMC из словаря
        font = ImageFont.truetype("arial.ttf", 12)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_size = (text_width, text_height)
        # Положение текста в углу
        draw.text(
            (image.width - text_size[0] - 10, 10), text, fill='black', font=font)

    def find_closest_color(self, rgb_color):
        '''Метод, определяющий ближайший цвет из палитры'''
        if self.palette is None:
            return None

        min_distance = float('inf')
        closest_color = None

        for color in self.palette:
            distance = self.calculate_distance(rgb_color, color)
            if distance < min_distance:
                min_distance = distance
                closest_color = color

        return closest_color

    def calculate_distance(self, rgb1, rgb2):
        '''Метод, определяющий что-то '''
        lab1 = colorspacious.cspace_convert(rgb1, "sRGB255", "CAM02-UCS")
        lab2 = colorspacious.cspace_convert(rgb2, "sRGB255", "CAM02-UCS")
        return np.linalg.norm(lab1 - lab2)

    def update_pixel_size(self):
        '''Метод для обновления переменной размерности пикселя'''
        selected_size = self.pixel_size_dropdown.get()
        if selected_size:
            self.pixel_size = int(selected_size)
        else:
            # Если размер не выбран, устанавливаем значение по умолчанию, равное 1
            self.pixel_size = 1

    def save_image(self, output_image):
        '''Метод для сохранения изображения'''
        # Запрашиваем у пользователя путь для сохранения файла
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")]
        )

        # Если пользователь выбрал файл и ввел имя, сохраняем изображение
        if file_path:
            output_image.save(file_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePixelizerApp(root)
    app.pixel_size_dropdown.bind(
        "<<ComboboxSelected>>", lambda event=None: app.update_pixel_size())
    root.mainloop()
