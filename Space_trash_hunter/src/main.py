import arcade
import math
import random
import json
import os
import sys

# этот блок кода добавлен, чтобы Python точно знал, где искать папку src.
# Это решает проблему, когда запускаешь скрипт из другой директории, а imports ломаются.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if os.path.exists(os.path.join(project_root, "src")):
    os.chdir(project_root)

# Импортируем классы, описанные в sprites.py
from src.sprites import Player, Asteroid, Bullet, Trash, Star, ChaserEnemy, ShooterEnemy, KamikazeEnemy, \
    ExplosionParticle, RepairKit

# Константы для настройки окна и мира
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SCREEN_TITLE = "Space Scavenger: Final Animation Build"
MAP_SIZE = 2500

# Настройки сложности: сколько очков нужно набрать для прохождения уровня
LEVEL_GOALS = {
    0: 500,
    1: 1500,
    2: 2500,
    3: 4000,
    4: float('inf')  # Бесконечный уровень для проверки навыков
}

RECORDS_FILE = "records.json"


# Функции для работы с файловой системой (сохранение рекордов)
def load_records():
    # Если файла нет, возвращаем пустые рекорды
    if not os.path.exists(RECORDS_FILE):
        return {str(k): 0 for k in LEVEL_GOALS.keys()}
    with open(RECORDS_FILE, "r") as f:
        return json.load(f)


def save_record(level, score):
    # Сохраняем рекорд, только если новый счет больше старого
    data = load_records()
    str_lvl = str(level)
    if str_lvl not in data or score > data[str_lvl]:
        data[str_lvl] = score
        with open(RECORDS_FILE, "w") as f:
            json.dump(data, f)


def reset_record_lvl(level):
    # Функция для кнопки сброса рекордов в меню
    data = load_records()
    str_lvl = str(level)
    data[str_lvl] = 0
    with open(RECORDS_FILE, "w") as f:
        json.dump(data, f)


# ==========================================
#               VIEW: МЕНЮ
# ==========================================
class MenuView(arcade.View):
    """
    Класс отвечающий за главное меню игры.
    """

    def __init__(self):
        super().__init__()
        self.menu_music = None
        self.music_player = None
        # Пытаемся загрузить музыку, но используем try/except, чтобы игра не крашилась, если файлов нет
        try:
            self.menu_music = arcade.load_sound("assets/sounds/menu_ost.mp3")
        except FileNotFoundError:
            print("Предупреждение: музыка меню не найдена, продолжаем без неё.")

    def on_show_view(self):
        # Устанавливаем черный фон и запускаем музыку при открытии меню
        arcade.set_background_color(arcade.color.BLACK)
        self.records = load_records()
        if self.menu_music:
            if not self.music_player:
                self.music_player = self.menu_music.play(loop=True, volume=0.5)

    def on_draw(self):
        self.clear()
        width = self.window.width
        height = self.window.height
        cx = width / 2
        cy = height / 2

        # Отрисовка заголовка
        arcade.draw_text("SPACE SCAVENGER", cx, cy + 150,
                         arcade.color.ORANGE, font_size=50, anchor_x="center")

        arcade.draw_text("Выберите уровень:", cx, cy + 70,
                         arcade.color.WHITE, font_size=20, anchor_x="center")

        # Список уровней с описанием
        levels = [
            (0, "УРОВЕНЬ 0: Обучение (Нет врагов)"),
            (1, "УРОВЕНЬ 1: Только Астероиды и Тараны"),
            (2, "УРОВЕНЬ 2: + Стрелки + Аптечки"),
            (3, "УРОВЕНЬ 3: МАКСИМАЛЬНАЯ ОПАСНОСТЬ"),
            (4, "БЕСКОНЕЧНЫЙ РЕЖИМ: ВЫЖИВАНИЕ")
        ]

        # Цикл отрисовки кнопок уровней
        for i, (lvl, desc) in enumerate(levels):
            y_pos = cy - (i * 60)
            rec = self.records.get(str(lvl), 0)
            text = f"{desc} [Рекорд: {rec}]"

            arcade.draw_text(text, cx, y_pos,
                             arcade.color.CYAN, font_size=18, anchor_x="center")

            # Кнопка сброса рекорда
            reset_color = arcade.color.RED
            if rec == 0:
                reset_color = arcade.color.GRAY

            arcade.draw_text("[СБРОС]", cx + 380, y_pos,
                             reset_color, font_size=14, anchor_x="center", anchor_y="baseline")

        arcade.draw_text("ESC - выход  |  F11 - полноэкранный режим", cx, 50,
                         arcade.color.GRAY, font_size=14, anchor_x="center")

    def on_resize(self, width, height):
        # Важно обновлять вьюпорт при ресайзе окна, иначе картинка растянется
        self.window.ctx.viewport = (0, 0, width, height)
        super().on_resize(width, height)

    def on_mouse_press(self, x, y, button, modifiers):
        width = self.window.width
        height = self.window.height
        cx = width / 2
        cy = height / 2

        # Обработка кликов по меню
        for i in range(5):
            y_pos_button = cy - (i * 60)

            # Проверка нажатия на название уровня
            if (cx - 250 < x < cx + 250) and (y_pos_button - 20 < y < y_pos_button + 30):
                if self.music_player:
                    arcade.stop_sound(self.music_player)
                    self.music_player = None
                # Переход к игре
                game_view = GameView(level=i)
                game_view.setup()
                self.window.show_view(game_view)
                return

            # Проверка нажатия на [СБРОС]
            if (cx + 340 < x < cx + 420) and (y_pos_button - 15 < y < y_pos_button + 25):
                reset_record_lvl(i)
                self.records = load_records()

        # Кнопка выхода (неявная зона внизу)
        if cx - 100 < x < cx + 100 and 20 < y < 80:
            arcade.close_window()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)


# ==========================================
#            VIEW: КОНЕЦ ИГРЫ
# ==========================================
class GameOverView(arcade.View):
    """
    Экран, который показывается после победы или поражения.
    """

    def __init__(self, score, level, is_win):
        super().__init__()
        self.score = score
        self.level = level
        self.is_win = is_win
        # Сразу пытаемся сохранить рекорд при открытии этого экрана
        save_record(level, score)

    def on_draw(self):
        self.clear()
        cx = self.window.width / 2
        cy = self.window.height / 2
        title = "ПОБЕДА!" if self.is_win else "GAME OVER"
        color = arcade.color.GREEN if self.is_win else arcade.color.RED

        arcade.draw_text(title, cx, cy + 50,
                         color, font_size=50, anchor_x="center")
        arcade.draw_text(f"Счет: {self.score}", cx, cy,
                         arcade.color.WHITE, font_size=30, anchor_x="center")
        arcade.draw_text("Нажмите CLICK для выхода в меню", cx, cy - 80,
                         arcade.color.GRAY, font_size=20, anchor_x="center")

    def on_resize(self, width, height):
        self.window.ctx.viewport = (0, 0, width, height)
        super().on_resize(width, height)

    def on_mouse_press(self, x, y, button, modifiers):
        # Возвращаем пользователя в меню
        menu = MenuView()
        self.window.show_view(menu)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)


# ==========================================
#            VIEW: САМА ИГРА
# ==========================================
class GameView(arcade.View):
    """
    Основной класс игрового процесса.
    """

    def __init__(self, level):
        super().__init__()
        self.level = level
        self.target_score = LEVEL_GOALS.get(level, 1000)

        # Спрайт-листы для оптимизации отрисовки
        self.player_list = None
        self.asteroid_list = None
        self.bullet_list = None
        self.trash_list = None
        self.star_list = None
        self.enemy_list = None
        self.particle_list = None
        self.repair_list = None
        self.thruster_list = None

        self.player_sprite = None
        # Используем две камеры: одна для мира (двигается за игроком), другая для UI (статичная)
        self.camera_game = None
        self.camera_gui = None
        self.score = 0
        self.info_text = arcade.Text(text="", x=20, y=SCREEN_HEIGHT - 40, color=arcade.color.WHITE, font_size=16)
        self.up_pressed = False

        # Загрузка звуков (используем встроенные ресурсы arcade для тестов)
        self.sound_laser = arcade.load_sound(":resources:sounds/laser2.wav")
        self.sound_enemy_laser = arcade.load_sound(":resources:sounds/laser4.wav")
        self.sound_explosion = arcade.load_sound(":resources:sounds/explosion2.wav")
        self.sound_hit = arcade.load_sound(":resources:sounds/hit2.wav")
        self.sound_collect = arcade.load_sound(":resources:sounds/coin1.wav")
        self.sound_heal = arcade.load_sound(":resources:sounds/upgrade1.wav")

        self.level_music = None
        self.level_music_player = None
        self.sound_win = None
        self.sound_defeat = None

        # Выбор музыки в зависимости от уровня
        music_path = None
        if self.level == 0:
            music_path = "assets/sounds/level_0_ost.mp3"
        elif self.level == 1:
            music_path = "assets/sounds/level_1_ost.mp3"
        elif self.level == 2:
            music_path = "assets/sounds/level_2_ost.mp3"
        elif self.level == 3:
            music_path = "assets/sounds/level_3_ost.mp3"
        elif self.level == 4:
            music_path = "assets/sounds/level_4_ost.mp3"

        if music_path:
            try:
                self.level_music = arcade.load_sound(music_path)
            except FileNotFoundError:
                pass

        try:
            self.sound_win = arcade.load_sound("assets/sounds/win_ost.mp3")
            self.sound_defeat = arcade.load_sound("assets/sounds/defeat_ost.mp3")
        except FileNotFoundError:
            pass

    def setup(self):
        # Инициализация всех списков и объектов
        self.camera_game = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()

        self.player_list = arcade.SpriteList()
        self.asteroid_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.trash_list = arcade.SpriteList()
        self.star_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.repair_list = arcade.SpriteList()
        self.thruster_list = arcade.SpriteList()

        self.score = 0
        self.player_sprite = Player()
        self.player_list.append(self.player_sprite)
        # Важно добавить двигатель игрока в отдельный лист отрисовки
        self.thruster_list.append(self.player_sprite.thruster)

        # Создаем звездное небо
        for _ in range(300):
            star = Star()
            star.center_x = random.uniform(-MAP_SIZE, MAP_SIZE)
            star.center_y = random.uniform(-MAP_SIZE, MAP_SIZE)
            self.star_list.append(star)

        # Спавним астероиды и мусор
        for _ in range(35): self.spawn_object(Asteroid(), self.asteroid_list)
        for _ in range(20): self.spawn_object(Trash(), self.trash_list)

        # Спавним врагов в зависимости от уровня
        if self.level > 0:
            count = 4 if self.level == 4 else (4 + self.level * 2)
            for _ in range(count):
                self.spawn_random_enemy()

        # Аптечки
        repair_count = 3
        if self.level == 4:
            repair_count = 5  # В выживании даем больше шансов

        if self.level >= 2:
            for _ in range(repair_count):
                self.spawn_object(RepairKit(), self.repair_list)

        if self.level_music:
            self.level_music_player = self.level_music.play(loop=True, volume=0.5)

    def spawn_random_enemy(self):
        # тут сделана логика появления врагов.
        # Чем выше уровень (или счет в бесконечном режиме), тем опаснее враги.
        if self.level == 0: return
        rand = random.random()
        enemy = None

        if self.level == 4:
            # Прогрессия сложности для выживания
            if self.score < 500:
                enemy = ChaserEnemy(self.player_sprite, self.enemy_list)
            elif self.score < 2000:
                if rand < 0.6:
                    enemy = ChaserEnemy(self.player_sprite, self.enemy_list)
                else:
                    enemy = ShooterEnemy(self.player_sprite, self.enemy_list, self.bullet_list, self.sound_enemy_laser)
            else:
                if rand < 0.4:
                    enemy = ChaserEnemy(self.player_sprite, self.enemy_list)
                elif rand < 0.7:
                    enemy = ShooterEnemy(self.player_sprite, self.enemy_list, self.bullet_list, self.sound_enemy_laser)
                else:
                    enemy = KamikazeEnemy(self.player_sprite, self.enemy_list)
        elif self.level == 1:
            enemy = ChaserEnemy(self.player_sprite, self.enemy_list)
        elif self.level == 2:
            if rand < 0.7:
                enemy = ChaserEnemy(self.player_sprite, self.enemy_list)
            else:
                enemy = ShooterEnemy(self.player_sprite, self.enemy_list, self.bullet_list, self.sound_enemy_laser)
        elif self.level == 3:
            if rand < 0.5:
                enemy = ChaserEnemy(self.player_sprite, self.enemy_list)
            elif rand < 0.8:
                enemy = ShooterEnemy(self.player_sprite, self.enemy_list, self.bullet_list, self.sound_enemy_laser)
            else:
                enemy = KamikazeEnemy(self.player_sprite, self.enemy_list)

        if enemy:
            self.spawn_object(enemy, self.enemy_list)

    def spawn_object(self, sprite, sprite_list):
        # Функция для безопасного спавна объектов (чтобы не спавнились прямо на игроке)
        sprite.center_x = random.uniform(-MAP_SIZE, MAP_SIZE)
        sprite.center_y = random.uniform(-MAP_SIZE, MAP_SIZE)

        # Если слишком близко - пробуем еще раз (рекурсия)
        if arcade.get_distance_between_sprites(sprite, self.player_sprite) < 600:
            self.spawn_object(sprite, sprite_list)
            return

        # Если это враг, надо добавить его двигатель в список отрисовки
        if isinstance(sprite, (ChaserEnemy, ShooterEnemy, KamikazeEnemy)):
            self.thruster_list.append(sprite.thruster)

        if isinstance(sprite, Asteroid):
            sprite.change_x = random.uniform(-1.5, 1.5)
            sprite.change_y = random.uniform(-1.5, 1.5)
        sprite_list.append(sprite)

    def create_bullet_explosion(self, x, y):
        # Эффект разлета пуль во все стороны (для смерти Камикадзе)
        bullet_count = 9
        speed = 5
        for i in range(bullet_count):
            angle_deg = i * (360 / bullet_count)
            angle_rad = math.radians(angle_deg)
            bullet = Bullet(is_enemy=True)
            bullet.center_x = x
            bullet.center_y = y
            bullet.angle = angle_deg - 90
            bullet.change_x = math.cos(angle_rad) * speed
            bullet.change_y = math.sin(angle_rad) * speed
            self.bullet_list.append(bullet)

    def spawn_visual_explosion(self, x, y, color, count=10):
        # Создает группу частиц взрыва
        for _ in range(count):
            self.particle_list.append(ExplosionParticle(x, y, color))

    def on_draw(self):
        self.clear()
        width = self.window.width
        height = self.window.height

        # 1. Рисуем игровой мир (камера следит за игроком)
        if self.camera_game:
            self.camera_game.use()

        # Граница мира
        arcade.draw_rect_outline(arcade.LRBT(-MAP_SIZE, MAP_SIZE, -MAP_SIZE, MAP_SIZE), arcade.color.RED, 10)

        # Порядок отрисовки важен для слоев!
        self.star_list.draw()  # Фон
        self.trash_list.draw()
        self.repair_list.draw()
        self.particle_list.draw()
        self.thruster_list.draw()  # Двигатели ПОД кораблями
        self.asteroid_list.draw()
        self.enemy_list.draw()
        self.bullet_list.draw()
        self.player_list.draw()  # Игрок поверх всего

        # 2. Рисуем интерфейс (камера UI зафиксирована)
        if self.camera_gui:
            self.camera_gui.use()

        self.info_text.draw()

        goal_text = f"ЦЕЛЬ: {self.target_score}"
        if self.level == 4:
            goal_text = "ЦЕЛЬ: ВЫЖИТЬ"
        arcade.draw_text(goal_text, width - 150, height - 40, arcade.color.YELLOW, font_size=16)

    def on_update(self, delta_time):
        # Проверка условий проигрыша
        if self.player_sprite.hp <= 0:
            if self.level_music_player: arcade.stop_sound(self.level_music_player)
            if self.sound_defeat: arcade.play_sound(self.sound_defeat, volume=0.7)
            game_over = GameOverView(self.score, self.level, is_win=False)
            self.window.show_view(game_over)
            return

        # Проверка победы (кроме бесконечного уровня)
        if self.level != 4 and self.score >= self.target_score:
            if self.level_music_player: arcade.stop_sound(self.level_music_player)
            if self.sound_win: arcade.play_sound(self.sound_win, volume=0.7)
            game_over = GameOverView(self.score, self.level, is_win=True)
            self.window.show_view(game_over)
            return

        # --- КОНТРОЛЬ ПОПУЛЯЦИИ ВРАГОВ (УРОВЕНЬ 4) ---
        # Чтобы в бесконечном режиме враги не заканчивались и не переполняли память
        if self.level == 4:
            enemy_limit = 4
            if self.score > 500: enemy_limit = 7
            if self.score > 2000: enemy_limit = 12
            if self.score > 5000: enemy_limit = 12 + int((self.score - 5000) / 1000)

            if len(self.enemy_list) < enemy_limit:
                if random.random() < 0.05:
                    self.spawn_random_enemy()
        # -------------------------------------

        # Физика движения игрока (инерция)
        if self.up_pressed:
            rad = math.radians(-self.player_sprite.angle + 90)
            self.player_sprite.speed_x += math.cos(rad) * 0.2
            self.player_sprite.speed_y += math.sin(rad) * 0.2

        # Трение (замедление)
        self.player_sprite.speed_x *= (1 - 0.04)
        self.player_sprite.speed_y *= (1 - 0.04)

        # Обновление всех списков спрайтов
        self.player_list.update(delta_time)
        self.asteroid_list.update(delta_time)
        self.bullet_list.update(delta_time)
        self.enemy_list.update(delta_time)
        self.particle_list.update(delta_time)

        # Слежение камеры за игроком
        if self.camera_game and self.player_sprite:
            self.camera_game.position = self.player_sprite.position

        self.info_text.text = f"Счет: {self.score}  |  Корпус: {int(self.player_sprite.hp)}%  |  Уровень: {self.level}"

        # Ограничение мира (отскакивание от границ)
        if self.player_sprite.left < -MAP_SIZE:
            self.player_sprite.left = -MAP_SIZE;
            self.player_sprite.speed_x *= -0.5
        elif self.player_sprite.right > MAP_SIZE:
            self.player_sprite.right = MAP_SIZE;
            self.player_sprite.speed_x *= -0.5
        if self.player_sprite.bottom < -MAP_SIZE:
            self.player_sprite.bottom = -MAP_SIZE;
            self.player_sprite.speed_y *= -0.5
        elif self.player_sprite.top > MAP_SIZE:
            self.player_sprite.top = MAP_SIZE;
            self.player_sprite.speed_y *= -0.5

        # ================== КОЛЛИЗИИ (Столкновения) ==================

        # 1. Игрок и Аптечки
        hits = arcade.check_for_collision_with_list(self.player_sprite, self.repair_list)
        for kit in hits:
            kit.remove_from_sprite_lists()
            self.player_sprite.hp = min(100, self.player_sprite.hp + 30)
            arcade.play_sound(self.sound_heal)

            # Спавн новой аптечки
            if self.level < 4:
                if self.level >= 2: self.spawn_object(RepairKit(), self.repair_list)
            elif self.level == 4:
                # В выживании аптечки редкие
                if len(self.repair_list) < 5 and random.random() < 0.01:
                    self.spawn_object(RepairKit(), self.repair_list)

        # 2. Обработка пуль
        for bullet in self.bullet_list[:]:
            if bullet.is_enemy:
                # Вражеская пуля попала в игрока
                if arcade.check_for_collision(bullet, self.player_sprite):
                    bullet.remove_from_sprite_lists()
                    self.player_sprite.hp -= 10
                    arcade.play_sound(self.sound_hit, volume=0.5)
                    self.spawn_visual_explosion(self.player_sprite.center_x, self.player_sprite.center_y,
                                                arcade.color.ORANGE, 5)
            else:
                # Наша пуля попала во врага
                hits = arcade.check_for_collision_with_list(bullet, self.enemy_list)
                if hits:
                    bullet.remove_from_sprite_lists()
                    for enemy in hits:
                        enemy.hp -= 1
                        self.spawn_visual_explosion(bullet.center_x, bullet.center_y, arcade.color.WHITE, 3)
                        if enemy.hp <= 0:
                            # Враг уничтожен
                            arcade.play_sound(self.sound_explosion, volume=0.6)
                            exp_color = arcade.color.BLUE
                            if isinstance(enemy, ShooterEnemy):
                                exp_color = arcade.color.GREEN
                            elif isinstance(enemy, KamikazeEnemy):
                                exp_color = arcade.color.RED
                            self.spawn_visual_explosion(enemy.center_x, enemy.center_y, exp_color, 15)

                            # Камикадзе взрывается при смерти
                            if isinstance(enemy, KamikazeEnemy):
                                self.create_bullet_explosion(enemy.center_x, enemy.center_y)

                            enemy.remove_from_sprite_lists()
                            self.score += 100
                            # Спавним замену, если это не бесконечный режим (там свой спавнер)
                            if self.level != 4:
                                self.spawn_random_enemy()

            # Пуля попала в астероид
            if bullet in self.bullet_list:
                hits = arcade.check_for_collision_with_list(bullet, self.asteroid_list)
                if hits:
                    bullet.remove_from_sprite_lists()
                    for a in hits:
                        arcade.play_sound(self.sound_explosion, volume=0.4)
                        self.spawn_visual_explosion(a.center_x, a.center_y, arcade.color.GRAY, 10)
                        a.remove_from_sprite_lists()
                        self.score += 5
                        self.spawn_object(Asteroid(), self.asteroid_list)

        # 3. Сбор мусора
        hits = arcade.check_for_collision_with_list(self.player_sprite, self.trash_list)
        for t in hits:
            t.remove_from_sprite_lists()
            arcade.play_sound(self.sound_collect, volume=0.5)
            self.score += 50
            self.spawn_object(Trash(), self.trash_list)

        # 4. Столкновение с астероидами
        hits = arcade.check_for_collision_with_list(self.player_sprite, self.asteroid_list)
        for a in hits:
            a.remove_from_sprite_lists()
            arcade.play_sound(self.sound_hit, volume=1.0)
            self.spawn_visual_explosion(a.center_x, a.center_y, arcade.color.GRAY, 15)
            self.player_sprite.hp -= 20
            self.spawn_object(Asteroid(), self.asteroid_list)

        # 5. Столкновение с врагами (таран)
        hits = arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list)
        for enemy in hits:
            arcade.play_sound(self.sound_hit, volume=1.0)
            self.spawn_visual_explosion(enemy.center_x, enemy.center_y, arcade.color.RED, 20)
            if isinstance(enemy, KamikazeEnemy):
                self.player_sprite.hp -= 30
            else:
                self.player_sprite.hp -= 15
            enemy.remove_from_sprite_lists()
            if self.level != 4:
                self.spawn_random_enemy()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if self.level_music_player:
                arcade.stop_sound(self.level_music_player)
            menu_view = MenuView()
            self.window.show_view(menu_view)

        elif key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_angle = 4
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_angle = -4
        elif key == arcade.key.SPACE:
            # Стрельба с учетом текущей скорости корабля
            arcade.play_sound(self.sound_laser, volume=0.3)
            bullet = Bullet(is_enemy=False)
            bullet.angle = self.player_sprite.angle
            rad = math.radians(-self.player_sprite.angle + 90)
            bullet.center_x = self.player_sprite.center_x + (math.cos(rad) * 30)
            bullet.center_y = self.player_sprite.center_y + (math.sin(rad) * 30)
            # Пуля летит быстрее самого корабля, прибавляем скорость корабля к вектору
            bullet.change_x = self.player_sprite.speed_x + (math.cos(rad) * 12)
            bullet.change_y = self.player_sprite.speed_y + (math.sin(rad) * 12)
            self.bullet_list.append(bullet)

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W: self.up_pressed = False
        if key in [arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D]:
            self.player_sprite.change_angle = 0

    def on_resize(self, width, height):
        self.window.ctx.viewport = (0, 0, width, height)
        super().on_resize(width, height)
        # Пересоздаем камеры при изменении размера окна, чтобы не поплыли координаты
        self.camera_game = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        self.info_text.y = height - 40


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
