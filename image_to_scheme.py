import tkinter as tk
from tkinter import filedialog, ttk
import threading
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans
import colorspacious


class ImagePixelizerApp:
    '''Главный класс приложения, содержащий в себе всю его функциональность'''

    def __init__(self, root):
        self.root = root
        self.root.title("Stitch Scheme Builder")
        self.root.resizable(width=False, height=False)

        # Создание элементов управления
        self.input_label = tk.Label(root, text="Input Image:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10)

        # Кнопка выбора загружаемого изображения
        self.input_image_button = tk.Button(
            root, text="Choose Image", command=self.choose_image)
        self.input_image_button.grid(row=0, column=1, padx=10, pady=10)

        self.pixel_size_label = tk.Label(root, text="Pixel Size:")
        self.pixel_size_label.grid(row=1, column=0, padx=10, pady=10)

        self.pixel_size_entry = tk.Entry(root)
        self.pixel_size_entry.grid(row=1, column=1, padx=10, pady=10)

        self.width_label = tk.Label(root, text="Output Width:")
        self.width_label.grid(row=2, column=0, padx=10, pady=10)

        self.width_entry = tk.Entry(root)
        self.width_entry.grid(row=2, column=1, padx=10, pady=10)

        self.height_label = tk.Label(root, text="Output Height:")
        self.height_label.grid(row=3, column=0, padx=10, pady=10)

        self.height_entry = tk.Entry(root)
        self.height_entry.grid(row=3, column=1, padx=10, pady=10)

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

    def choose_image(self):
        '''Метод, открывающий диалоговое окно для выбора загружаемого изображения'''
        self.input_image_path = filedialog.askopenfilename()

    def toggle_controls(self, state):
        '''Метод для блокировки или разблокировки элементов управления'''
        for widget in [self.input_image_button, self.pixel_size_entry,
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
            print('Thread has ben started')
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
            pixel_size = int(self.pixel_size_entry.get())
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

            draw = ImageDraw.Draw(output_image)
            for x in range(0, output_width, pixel_size):
                draw.line([(x, 0), (x, output_height)], fill='black', width=1)
            for y in range(0, output_height, pixel_size):
                draw.line([(0, y), (output_width, y)], fill='black', width=1)

            # Замена цветов пикселей на ближайшие из палитры
            total_pixels = (output_width // pixel_size) * \
                (output_height // pixel_size)
            processed_pixels = 0
            for y in range(0, input_image.size[1], pixel_size):
                for x in range(0, input_image.size[0], pixel_size):
                    # Проверяем флаг отмены
                    if self.cancel_flag:
                        # Прерываем выполнение и сбрасываем флаг, если он установлен в True
                        self.cancel_flag = False
                        return
                    pixel = tuple(
                        np.mean(img_array[y:y+pixel_size, x:x+pixel_size], axis=(0, 1)).astype(int))
                    closest_color = self.find_closest_color(pixel)
                    if closest_color:
                        for i in range(pixel_size):
                            for j in range(pixel_size):
                                output_image.putpixel(
                                    (x + i, y + j), closest_color)
                    processed_pixels += 1
                    progress_percentage = (
                        processed_pixels / total_pixels) * 100
                    self.update_progress(progress_percentage)

            output_image.show()
        finally:
            # Блокировка кнопки "Cancel"
            self.cancel_button.configure(state="disabled")
            # Разблокировка элементов управления
            self.toggle_controls("normal")

            # Остановка и сброс значения прогрессбара
            self.progress_bar.stop()
            self.progress_bar["value"] = 0

            self.progress_label.config(text="")

    def find_closest_color(self, rgb_color):
        '''Метод, определяющий ближайший цвет из палитры к '''
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


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePixelizerApp(root)
    root.mainloop()
