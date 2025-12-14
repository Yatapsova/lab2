"""
FdF Bonus - Extended version with image support
Supports FDF files and various image formats (PNG, JPEG, etc.)
"""
import sys
import math
import pygame
from PIL import Image
import numpy as np


class Point3D:
    """3D точка с координатами x, y, z"""

    def _init_(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def _str_(self):
        return f"({self.x}, {self.y}, {self.z})"


class ExtendedFDFRenderer:
    """Расширенный рендерер с поддержкой изображений"""

    def _init_(self, width=1200, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("FdF Extended - 3D Wireframe Viewer")
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Цвета
        self.bg_color = (15, 15, 35)
        self.grid_color = (120, 120, 180)
        self.high_color = (255, 120, 120)
        self.low_color = (120, 220, 255)
        self.text_color = (220, 220, 220)
        self.wireframe_color = (200, 200, 255)

        # Параметры камеры
        self.scale = 20
        self.offset_x = width // 2
        self.offset_y = height // 2
        self.angle_x = math.radians(30)
        self.angle_y = math.radians(-45)
        self.angle_z = 0
        self.auto_rotate = False
        self.show_axes = True
        self.show_grid = True
        self.render_mode = 'wireframe'  # 'wireframe', 'points', 'solid'

        # Данные модели
        self.points = []
        self.edges = []
        self.faces = []
        self.colors = []
        self.min_z = 0
        self.max_z = 0
        self.image_data = None

        # Шрифты
        self.font = pygame.font.SysFont('Consolas', 20)
        self.font_large = pygame.font.SysFont('Consolas', 28)

        # Анимация
        self.animation_time = 0

    def load_file(self, filename):
        """Загрузка файла (FDF или изображение)"""
        if filename.lower().endswith('.fdf'):
            return self.load_fdf(filename)
        else:
            return self.load_image(filename)

    def load_fdf(self, filename):
        """Загрузка FDF файла"""
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()

            self.points = []
            row = 0

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                values = line.split()
                col = 0
                for value in values:
                    if ',' in value:
                        z_val, color = value.split(',')
                    else:
                        z_val = value
                        color = None

                    try:
                        z = float(z_val)
                        point = Point3D(col, row, z)
                        self.points.append((point, color))
                        col += 1
                    except ValueError:
                        continue

                row += 1

            if not self.points:
                print(f"Error: No valid data in {filename}")
                return False

            self.min_z = min(p[0].z for p in self.points)
            self.max_z = max(p[0].z for p in self.points)
            self.create_mesh()
            print(f"Loaded FDF: {len(self.points)} points, {len(self.edges)} edges")
            return True

        except Exception as e:
            print(f"Error loading FDF: {e}")
            return False

    def load_image(self, filename):
        """Загрузка изображения и преобразование в 3D модель"""
        try:
            img = Image.open(filename)
            img = img.convert('L')  # Конвертируем в grayscale
            img = img.resize((50, 50))  # Уменьшаем для производительности

            # Преобразуем в numpy массив
            img_array = np.array(img)
            self.image_data = img_array

            # Создаем точки из изображения
            self.points = []
            height, width = img_array.shape

            for y in range(height):
                for x in range(width):
                    # Яркость -> высота
                    brightness = img_array[y, x]
                    z = (255 - brightness) / 10.0  # Инвертируем для лучшего вида

                    point = Point3D(x - width/2, y - height/2, z)
                    self.points.append((point, None))

            if not self.points:
                print(f"Error: Failed to create points from image")
                return False

            self.min_z = min(p[0].z for p in self.points)
            self.max_z = max(p[0].z for p in self.points)
            self.create_mesh()
            print(f"Loaded image: {len(self.points)} points, {len(self.edges)} edges")
            return True

        except Exception as e:
            print(f"Error loading image: {e}")
            return False

    def create_mesh(self):
        """Создание сетки (ребра и грани)"""
        self.edges = []
        self.faces = []
        self.colors = []

        # Находим размеры
        points_array = [p[0] for p in self.points]
        max_x = max(int(p.x) for p in points_array)
        max_y = max(int(p.y) for p in points_array)

        # Создаем 2D сетку индексов
        grid = [[-1 for _ in range(max_x + 1)] for _ in range(max_y + 1)]
        for idx, (point, _) in enumerate(self.points):
            x, y = int(point.x), int(point.y)
            if 0 <= x <= max_x and 0 <= y <= max_y:
                grid[y][x] = idx

        # Создаем ребра и грани
        for y in range(max_y):
            for x in range(max_x):
                if (grid[y][x] != -1 and grid[y][x + 1] != -1 and
                        grid[y + 1][x] != -1 and grid[y + 1][x + 1] != -1):

                    # Ребра квадрата
                    self.edges.append((grid[y][x], grid[y][x + 1]))
                    self.edges.append((grid[y][x], grid[y + 1][x]))
                    self.edges.append((grid[y + 1][x], grid[y + 1][x + 1]))
                    self.edges.append((grid[y][x + 1], grid[y + 1][x + 1]))

                    # Две треугольные грани для квадрата
                    self.faces.append((
                        grid[y][x],
                        grid[y][x + 1],
                        grid[y + 1][x]
                    ))
                    self.faces.append((
                        grid[y + 1][x + 1],
                        grid[y][x + 1],
                        grid[y + 1][x]
                    ))

                    # Цвет грани на основе средней высоты
                    avg_z = (points_array[grid[y][x]].z +
                             points_array[grid[y][x + 1]].z +
                             points_array[grid[y + 1][x]].z +
                             points_array[grid[y + 1][x + 1]].z) / 4
                    color = self.get_color_for_height(avg_z)
                    self.colors.append(color)
                    self.colors.append(color)

    def rotate_point(self, point, angle_x, angle_y, angle_z):
        """Вращение 3D точки"""
        x, y, z = point.x, point.y, point.z

        # Вращение X
        if angle_x:
            cos_x = math.cos(angle_x)
            sin_x = math.sin(angle_x)
            y_new = y * cos_x - z * sin_x
            z_new = y * sin_x + z * cos_x
            y, z = y_new, z_new

        # Вращение Y
        if angle_y:
            cos_y = math.cos(angle_y)
            sin_y = math.sin(angle_y)
            x_new = x * cos_y + z * sin_y
            z_new = -x * sin_y + z * cos_y
            x, z = x_new, z_new

        # Вращение Z
        if angle_z:
            cos_z = math.cos(angle_z)
            sin_z = math.sin(angle_z)
            x_new = x * cos_z - y * sin_z
            y_new = x * sin_z + y * cos_z
            x, y = x_new, y_new

        return Point3D(x, y, z)

    def project_point(self, point):
        """Проекция 3D точки на 2D"""
        # Перспективная проекция
        distance = 500
        factor = distance / (distance + point.z * 2)

        screen_x = point.x * factor * self.scale + self.offset_x
        screen_y = point.y * factor * self.scale + self.offset_y

        return (screen_x, screen_y)

    def get_color_for_height(self, z, custom_color=None):
        """Получение цвета по высоте"""
        if custom_color:
            try:
                if custom_color.startswith('0x'):
                    hex_color = custom_color[2:]
                else:
                    hex_color = custom_color
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b)
            except Exception:
                pass

        if self.max_z == self.min_z:
            ratio = 0.5
        else:
            ratio = (z - self.min_z) / (self.max_z - self.min_z)

        # Плавный градиент через HSV
        hue = 0.66 * (1 - ratio)  # Синий -> Красный
        saturation = 0.8
        value = 0.8 + 0.2 * ratio

        # HSV to RGB
        h = hue * 6
        i = math.floor(h)
        f = h - i
        p = value * (1 - saturation)
        q = value * (1 - f * saturation)
        t = value * (1 - (1 - f) * saturation)

        if i == 0:
            r, g, b = value, t, p
        elif i == 1:
            r, g, b = q, value, p
        elif i == 2:
            r, g, b = p, value, t
        elif i == 3:
            r, g, b = p, q, value
        elif i == 4:
            r, g, b = t, p, value
        else:
            r, g, b = value, p, q

        return (int(r * 255), int(g * 255), int(b * 255))

    def draw_model(self):
        """Отрисовка модели в выбранном режиме"""
        if not self.points:
            return

        # Проецируем все точки
        self.animation_time += 0.01
        projected_points = []
        points_3d = []

        for i, (point_3d, color) in enumerate(self.points):
            # Добавляем небольшую анимацию
            animated_z = point_3d.z
            if self.auto_rotate:
                animated_z += math.sin(self.animation_time + i * 0.1) * 0.5

            animated_point = Point3D(point_3d.x, point_3d.y, animated_z)
            rotated = self.rotate_point(
                animated_point,
                self.angle_x,
                self.angle_y,
                self.angle_z
            )
            projected = self.project_point(rotated)
            projected_points.append(projected)
            points_3d.append(rotated)

        # Режим отрисовки
        if self.render_mode == 'solid' and self.faces:
            self.draw_solid(projected_points, points_3d)
        elif self.render_mode == 'points':
            self.draw_points(projected_points)
        else:  # wireframe
            self.draw_wireframe(projected_points)

        # Оси координат
        if self.show_axes:
            self.draw_axes()

    def draw_wireframe(self, projected_points):
        """Отрисовка каркаса"""
        for edge in self.edges:
            if edge[0] < len(projected_points) and edge[1] < len(projected_points):
                p1 = projected_points[edge[0]]
                p2 = projected_points[edge[1]]

                # Цвет на основе расстояния (затухание)
                dist = math.sqrt((p1[0] - p2[0])*2 + (p1[1] - p2[1])*2)
                alpha = max(50, min(255, 255 - dist / 5))

                color = list(self.wireframe_color)
                color.append(int(alpha))

                pygame.draw.line(self.screen, color[:3], p1, p2, 2)

    def draw_solid(self, projected_points, points_3d):
        """Отрисовка залитых граней с сортировкой по глубине"""
        # Сортируем грани по глубине (painter's algorithm)
        sorted_faces = []
        for i, face in enumerate(self.faces):
            if i < len(self.colors):
                # Средняя Z координата для сортировки
                avg_z = sum(points_3d[v].z for v in face) / 3
                sorted_faces.append((avg_z, face, self.colors[i]))

        # Сортируем по убыванию Z (дальние грани рисуем первыми)
        sorted_faces.sort(reverse=True, key=lambda x: x[0])

        # Рисуем грани
        for _, face, color in sorted_faces:
            if (face[0] < len(projected_points) and
                    face[1] < len(projected_points) and
                    face[2] < len(projected_points)):

                points = [
                    projected_points[face[0]],
                    projected_points[face[1]],
                    projected_points[face[2]]
                ]

                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, (50, 50, 80), points, 1)

    def draw_points(self, projected_points):
        """Отрисовка точек"""
        for i, (point, color) in enumerate(self.points):
            if i < len(projected_points):
                proj = projected_points[i]
                point_color = self.get_color_for_height(point.z, color)

                # Размер точки зависит от высоты
                size = max(2, int(5 + point.z))
                pygame.draw.circle(self.screen, point_color, (int(proj[0]), int(proj[1])), size)

    def draw_axes(self):
        """Отрисовка осей координат"""
        origin = Point3D(0, 0, 0)
        axes = [
            (Point3D(10, 0, 0), (255, 50, 50), 'X'),
            (Point3D(0, 10, 0), (50, 255, 50), 'Y'),
            (Point3D(0, 0, 10), (50, 50, 255), 'Z')
        ]

        for axis_end, color, label in axes:
            axis_end_rot = self.rotate_point(
                axis_end, self.angle_x, self.angle_y, self.angle_z)
            start_proj = self.project_point(self.rotate_point(
                origin, self.angle_x, self.angle_y, self.angle_z))
            end_proj = self.project_point(axis_end_rot)

            pygame.draw.line(self.screen, color, start_proj, end_proj, 3)

            # Подпись
            font_small = pygame.font.SysFont('Consolas', 18)
            text = font_small.render(label, True, color)
            self.screen.blit(text, (end_proj[0] + 5, end_proj[1] - 10))

    def draw_ui(self):
        """Отрисовка интерфейса"""
        # Информация
        info = [
            f"Points: {len(self.points)}",
            f"Edges: {len(self.edges)}",
            f"Faces: {len(self.faces)}",
            f"Height: {self.min_z:.1f} - {self.max_z:.1f}",
            f"Scale: {self.scale:.1f}",
            f"Rotation X: {math.degrees(self.angle_x):.1f}°",
            f"Rotation Y: {math.degrees(self.angle_y):.1f}°",
            f"Mode: {self.render_mode.upper()}",
            "",
            "CONTROLS:",
            "W/S - Rotate X",
            "A/D - Rotate Y",
            "Q/E - Rotate Z",
            "+/- - Zoom",
            "Arrows - Move",
            "1/2/3 - Modes",
            "R - Reset",
            "T - Auto rotate",
            "G - Grid",
            "X - Axes",
            "ESC - Quit"
        ]

        y_offset = 10
        for line in info:
            text = self.font.render(line, True, self.text_color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 24

        # Заголовок
        title = self.font_large.render("FdF EXTENDED VIEWER", True, (255, 255, 200))
        self.screen.blit(title, (self.width - 300, 10))

        # Статусы
        if self.auto_rotate:
            status = self.font.render("AUTO ROTATE: ON", True, (0, 255, 100))
            self.screen.blit(status, (self.width - 200, 50))

        if self.show_grid:
            status = self.font.render("GRID: ON", True, (100, 200, 255))
            self.screen.blit(status, (self.width - 200, 80))

    def draw_grid(self):
        """Отрисовка сетки"""
        grid_size = 12
        step = 2

        for i in range(-grid_size, grid_size + 1, step):
            for axis in ['x', 'y']:
                if axis == 'x':
                    start = Point3D(i, -grid_size, 0)
                    end = Point3D(i, grid_size, 0)
                else:
                    start = Point3D(-grid_size, i, 0)
                    end = Point3D(grid_size, i, 0)

                start_rot = self.rotate_point(
                    start, self.angle_x, self.angle_y, self.angle_z)
                end_rot = self.rotate_point(
                    end, self.angle_x, self.angle_y, self.angle_z)

                start_proj = self.project_point(start_rot)
                end_proj = self.project_point(end_rot)

                alpha = 50 if i % 4 == 0 else 30
                color = (*self.grid_color[:3], alpha)

                pygame.draw.line(self.screen, color, start_proj, end_proj, 1)

    def handle_keys(self):
        """Обработка клавиш"""
        keys = pygame.key.get_pressed()
        rot_speed = 0.03
        zoom_speed = 1.0
        pan_speed = 5

        # Вращение
        if keys[pygame.K_w]:
            self.angle_x -= rot_speed
        if keys[pygame.K_s]:
            self.angle_x += rot_speed
        if keys[pygame.K_a]:
            self.angle_y -= rot_speed
        if keys[pygame.K_d]:
            self.angle_y += rot_speed
        if keys[pygame.K_q]:
            self.angle_z -= rot_speed
        if keys[pygame.K_e]:
            self.angle_z += rot_speed

        # Масштаб
        if keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]:
            self.scale += zoom_speed
        if keys[pygame.K_MINUS]:
            self.scale = max(1, self.scale - zoom_speed)

        # Смещение
        if keys[pygame.K_LEFT]:
            self.offset_x -= pan_speed
        if keys[pygame.K_RIGHT]:
            self.offset_x += pan_speed
        if keys[pygame.K_UP]:
            self.offset_y -= pan_speed
        if keys[pygame.K_DOWN]:
            self.offset_y += pan_speed

    def run(self, filename):
        """Основной цикл"""
        if not self.load_file(filename):
            print(f"Failed to load file: {filename}")
            return

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        # Сброс
                        self.scale = 20
                        self.offset_x = self.width // 2
                        self.offset_y = self.height // 2
                        self.angle_x = math.radians(30)
                        self.angle_y = math.radians(-45)
                        self.angle_z = 0
                    elif event.key == pygame.K_t:
                        self.auto_rotate = not self.auto_rotate
                    elif event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                    elif event.key == pygame.K_x:
                        self.show_axes = not self.show_axes
                    elif event.key == pygame.K_1:
                        self.render_mode = 'wireframe'
                    elif event.key == pygame.K_2:
                        self.render_mode = 'points'
                    elif event.key == pygame.K_3:
                        self.render_mode = 'solid'

            # Авто-вращение
            if self.auto_rotate:
                self.angle_y += 0.01
                self.angle_x += 0.005

            # Обработка клавиш
            self.handle_keys()

            # Отрисовка
            self.screen.fill(self.bg_color)

            if self.show_grid:
                self.draw_grid()

            self.draw_model()
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()
        sys.exit()


def main():
    """Точка входа"""
    if len(sys.argv) != 2:
        print("Usage: python fdf_bonus.py <filename>")
        print("Supports: .fdf, .png, .jpg, .jpeg, .bmp, .tiff")
        print("Example: python fdf_bonus.py test_maps/42.fdf")
        print("Example: python fdf_bonus.py test_images/mountain.jpg")
        return

    filename = sys.argv[1]
    renderer = ExtendedFDFRenderer()
    renderer.run(filename)


if _name_ == "_main_":
    main()