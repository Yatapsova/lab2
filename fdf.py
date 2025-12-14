"""
FdF (Fil de Fer) - 3D Wireframe Model Viewer
This program reads FDF files and displays them as 3D wireframe models.
"""
import sys
import math
import pygame


class Point3D:
    """3D точка с координатами x, y, z"""

    def _init_(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def _str_(self):
        return f"({self.x}, {self.y}, {self.z})"


class FDFRenderer:
    """Рендерер для отображения FDF моделей"""

    def _init_(self, width=1200, height=800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("FdF - 3D Wireframe Viewer")
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Цвета
        self.bg_color = (10, 10, 30)
        self.grid_color = (100, 100, 150)
        self.high_color = (255, 100, 100)
        self.low_color = (100, 200, 255)
        self.text_color = (200, 200, 200)

        # Параметры камеры и преобразований
        self.scale = 20
        self.offset_x = width // 2
        self.offset_y = height // 2
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.auto_rotate = False
        self.show_axes = True
        self.show_grid = True

        # Данные модели
        self.points = []
        self.edges = []
        self.min_z = 0
        self.max_z = 0

        # Шрифт
        self.font = pygame.font.SysFont('Consolas', 20)

    def read_fdf_file(self, filename):
        """Чтение FDF файла и парсинг данных"""
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()

            self.points = []
            row = 0

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Разбиваем строку на значения
                values = line.split()
                col = 0
                for value in values:
                    # Разбираем значение и цвет (если есть)
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
                print(f"Error: No valid data found in {filename}")
                return False

            # Находим min и max Z для цветовой градиенты
            self.min_z = min(p[0].z for p in self.points)
            self.max_z = max(p[0].z for p in self.points)

            # Создаем ребра (соединяем точки в сетку)
            self.create_edges()
            print(f"Loaded {len(self.points)} points, {len(self.edges)} edges")
            return True

        except FileNotFoundError:
            print(f"Error: File {filename} not found")
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

    def create_edges(self):
        """Создание ребер между соседними точками"""
        self.edges = []

        # Находим размеры сетки
        max_x = max(int(p[0].x) for p in self.points)
        max_y = max(int(p[0].y) for p in self.points)

        # Создаем 2D массив индексов точек
        grid = [[-1 for _ in range(max_x + 1)] for _ in range(max_y + 1)]

        for idx, (point, _) in enumerate(self.points):
            x, y = int(point.x), int(point.y)
            if 0 <= x <= max_x and 0 <= y <= max_y:
                grid[y][x] = idx

        # Создаем горизонтальные ребра
        for y in range(max_y + 1):
            for x in range(max_x):
                if grid[y][x] != -1 and grid[y][x + 1] != -1:
                    self.edges.append((grid[y][x], grid[y][x + 1]))

        # Создаем вертикальные ребра
        for y in range(max_y):
            for x in range(max_x + 1):
                if grid[y][x] != -1 and grid[y + 1][x] != -1:
                    self.edges.append((grid[y][x], grid[y + 1][x]))

    def rotate_point(self, point, angle_x, angle_y, angle_z):
        """Вращение 3D точки по трем осям"""
        x, y, z = point.x, point.y, point.z

        # Вращение вокруг оси X
        if angle_x:
            cos_x = math.cos(angle_x)
            sin_x = math.sin(angle_x)
            y = point.y * cos_x - point.z * sin_x
            z = point.y * sin_x + point.z * cos_x

        # Вращение вокруг оси Y
        if angle_y:
            cos_y = math.cos(angle_y)
            sin_y = math.sin(angle_y)
            x = point.x * cos_y + z * sin_y
            z = -point.x * sin_y + z * cos_y

        # Вращение вокруг оси Z
        if angle_z:
            cos_z = math.cos(angle_z)
            sin_z = math.sin(angle_z)
            x = x * cos_z - y * sin_z
            y = x * sin_z + y * cos_z

        return Point3D(x, y, z)

    def project_point(self, point):
        """Проекция 3D точки на 2D плоскость (изометрическая проекция)"""
        # Изометрическая проекция
        iso_x = (point.x - point.y) * math.cos(math.radians(30))
        iso_y = point.z + (point.x + point.y) * math.sin(math.radians(30))

        # Масштабирование и смещение
        screen_x = iso_x * self.scale + self.offset_x
        screen_y = iso_y * self.scale + self.offset_y

        return (screen_x, screen_y)

    def get_color_for_height(self, z, custom_color=None):
        """Получение цвета в зависимости от высоты"""
        if custom_color:
            # Парсим hex цвет
            try:
                if custom_color.startswith('0x'):
                    hex_color = custom_color[2:]
                else:
                    hex_color = custom_color
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b)
            except (ValueError, IndexError):
                pass

        # Градиент от low_color к high_color
        if self.max_z == self.min_z:
            ratio = 0.5
        else:
            ratio = (z - self.min_z) / (self.max_z - self.min_z)

        r = int(self.low_color[0] * (1 - ratio) + self.high_color[0] * ratio)
        g = int(self.low_color[1] * (1 - ratio) + self.high_color[1] * ratio)
        b = int(self.low_color[2] * (1 - ratio) + self.high_color[2] * ratio)

        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def draw_model(self):
        """Отрисовка модели"""
        if not self.points:
            return

        # Проецируем все точки
        projected_points = []
        for point_3d, color in self.points:
            rotated = self.rotate_point(
                point_3d,
                self.angle_x,
                self.angle_y,
                self.angle_z
            )
            projected = self.project_point(rotated)
            projected_points.append((projected, point_3d.z, color))

        # Отрисовка ребер
        for edge in self.edges:
            if edge[0] < len(projected_points) and edge[1] < len(projected_points):
                p1, z1, color1 = projected_points[edge[0]]
                p2, z2, color2 = projected_points[edge[1]]

                # Используем цвет первой точки или градиент
                if color1:
                    edge_color = self.get_color_for_height(z1, color1)
                else:
                    avg_z = (z1 + z2) / 2
                    edge_color = self.get_color_for_height(avg_z)

                pygame.draw.line(self.screen, edge_color, p1, p2, 2)

        # Отрисовка осей координат (если включено)
        if self.show_axes:
            self.draw_axes()

    def draw_axes(self):
        """Отрисовка осей координат"""
        origin = Point3D(0, 0, 0)

        # Ось X (красная)
        x_end = Point3D(5, 0, 0)
        x_end_rot = self.rotate_point(x_end, self.angle_x, self.angle_y, self.angle_z)
        x_start_proj = self.project_point(self.rotate_point(
            origin, self.angle_x, self.angle_y, self.angle_z))
        x_end_proj = self.project_point(x_end_rot)
        pygame.draw.line(self.screen, (255, 50, 50), x_start_proj, x_end_proj, 3)

        # Ось Y (зеленая)
        y_end = Point3D(0, 5, 0)
        y_end_rot = self.rotate_point(y_end, self.angle_x, self.angle_y, self.angle_z)
        y_end_proj = self.project_point(y_end_rot)
        pygame.draw.line(self.screen, (50, 255, 50), x_start_proj, y_end_proj, 3)

        # Ось Z (синяя)
        z_end = Point3D(0, 0, 5)
        z_end_rot = self.rotate_point(z_end, self.angle_x, self.angle_y, self.angle_z)
        z_end_proj = self.project_point(z_end_rot)
        pygame.draw.line(self.screen, (50, 50, 255), x_start_proj, z_end_proj, 3)

        # Подписи осей
        font_small = pygame.font.SysFont('Consolas', 16)
        x_text = font_small.render('X', True, (255, 100, 100))
        y_text = font_small.render('Y', True, (100, 255, 100))
        z_text = font_small.render('Z', True, (100, 100, 255))

        self.screen.blit(x_text, (x_end_proj[0] + 5, x_end_proj[1] - 10))
        self.screen.blit(y_text, (y_end_proj[0] + 5, y_end_proj[1] - 10))
        self.screen.blit(z_text, (z_end_proj[0] + 5, z_end_proj[1] - 10))

    def draw_ui(self):
        """Отрисовка пользовательского интерфейса"""
        # Информация о модели
        info_lines = [
            f"Points: {len(self.points)}",
            f"Edges: {len(self.edges)}",
            f"Height range: {self.min_z:.1f} - {self.max_z:.1f}",
            f"Scale: {self.scale:.1f}",
            f"Rotation X: {math.degrees(self.angle_x):.1f}°",
            f"Rotation Y: {math.degrees(self.angle_y):.1f}°",
            "",
            "Controls:",
            "W/S - Rotate X axis",
            "A/D - Rotate Y axis",
            "Q/E - Rotate Z axis",
            "+/- - Zoom in/out",
            "R - Reset view",
            "T - Auto rotate",
            "G - Toggle grid",
            "X - Toggle axes",
            "ESC - Quit"
        ]

        y_offset = 10
        for line in info_lines:
            text = self.font.render(line, True, self.text_color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 25

        # Статус авто-вращения
        if self.auto_rotate:
            status = self.font.render("AUTO ROTATE: ON", True, (0, 255, 0))
            self.screen.blit(status, (self.width - 200, 10))

    def handle_keys(self):
        """Обработка нажатий клавиш"""
        keys = pygame.key.get_pressed()
        rotation_speed = 0.05
        zoom_speed = 1.0

        # Вращение
        if keys[pygame.K_w]:
            self.angle_x -= rotation_speed
        if keys[pygame.K_s]:
            self.angle_x += rotation_speed
        if keys[pygame.K_a]:
            self.angle_y -= rotation_speed
        if keys[pygame.K_d]:
            self.angle_y += rotation_speed
        if keys[pygame.K_q]:
            self.angle_z -= rotation_speed
        if keys[pygame.K_e]:
            self.angle_z += rotation_speed

        # Масштабирование
        if keys[pygame.K_PLUS] or keys[pygame.K_EQUALS]:
            self.scale += zoom_speed
        if keys[pygame.K_MINUS]:
            self.scale = max(1, self.scale - zoom_speed)

        # Смещение
        pan_speed = 5
        if keys[pygame.K_LEFT]:
            self.offset_x -= pan_speed
        if keys[pygame.K_RIGHT]:
            self.offset_x += pan_speed
        if keys[pygame.K_UP]:
            self.offset_y -= pan_speed
        if keys[pygame.K_DOWN]:
            self.offset_y += pan_speed

    def run(self, filename):
        """Основной цикл программы"""
        if not self.read_fdf_file(filename):
            print("Failed to load FDF file")
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
                        # Сброс вида
                        self.scale = 20
                        self.offset_x = self.width // 2
                        self.offset_y = self.height // 2
                        self.angle_x = 0
                        self.angle_y = 0
                        self.angle_z = 0
                    elif event.key == pygame.K_t:
                        self.auto_rotate = not self.auto_rotate
                    elif event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                    elif event.key == pygame.K_x:
                        self.show_axes = not self.show_axes

            # Автоматическое вращение
            if self.auto_rotate:
                self.angle_y += 0.01
                self.angle_x += 0.005

            # Обработка клавиш
            self.handle_keys()

            # Отрисовка
            self.screen.fill(self.bg_color)

            # Сетка (если включена)
            if self.show_grid:
                self.draw_grid()

            # Модель
            self.draw_model()

            # UI
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()
        sys.exit()

    def draw_grid(self):
        """Отрисовка сетки"""
        grid_size = 10
        half_grid = grid_size // 2

        for i in range(-half_grid, half_grid + 1):
            # Горизонтальные линии
            start_x = Point3D(-half_grid, 0, i)
            end_x = Point3D(half_grid, 0, i)
            start_proj = self.project_point(self.rotate_point(
                start_x, self.angle_x, self.angle_y, self.angle_z))
            end_proj = self.project_point(self.rotate_point(
                end_x, self.angle_x, self.angle_y, self.angle_z))
            pygame.draw.line(self.screen, (50, 50, 80), start_proj, end_proj, 1)

            # Вертикальные линии
            start_y = Point3D(i, 0, -half_grid)
            end_y = Point3D(i, 0, half_grid)
            start_proj = self.project_point(self.rotate_point(
                start_y, self.angle_x, self.angle_y, self.angle_z))
            end_proj = self.project_point(self.rotate_point(
                end_y, self.angle_x, self.angle_y, self.angle_z))
            pygame.draw.line(self.screen, (50, 50, 80), start_proj, end_proj, 1)


def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Usage: python fdf.py <filename.fdf>")
        print("Example: python fdf.py test_maps/42.fdf")
        return

    filename = sys.argv[1]
    renderer = FDFRenderer()
    renderer.run(filename)


if _name_ == "_main_":
    main()