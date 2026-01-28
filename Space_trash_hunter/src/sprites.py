import arcade
import random
import math


class ShipThruster(arcade.Sprite):
    def __init__(self, owner, offset_dist=35):
        # для двигателя использована та же текстура, что и для звезд,
        # покрасил её в оранжевый цвет через свойство color.
        super().__init__(":resources:images/space_shooter/meteorGrey_tiny1.png", scale=0.8)
        self.owner = owner
        self.offset_dist = offset_dist
        self.animation_timer = 0
        self.color = arcade.color.ORANGE_PEEL

    def update(self):
        # Часть с математикой:
        # Нужно, чтобы огонь всегда был сзади корабля.
        # Так как угол в Arcade отсчитывается нестандартно, корректируем его (+90 градусов)
        # использован синус/косинус, чтобы найти точку позади корпуса.
        rad = math.radians(-self.owner.angle + 90)

        self.center_x = self.owner.center_x - math.cos(rad) * self.offset_dist
        self.center_y = self.owner.center_y - math.sin(rad) * self.offset_dist

        # Угол поворота огня должен совпадать с углом корабля
        self.angle = self.owner.angle

        # сделана простая анимацая мерцания двигателя
        # Каждые 4 кадра он меняет размер и цвет, создавая эффект пульсации.
        self.animation_timer += 1
        if self.animation_timer > 4:
            self.animation_timer = 0
            if self.color == arcade.color.ORANGE_PEEL:
                self.color = arcade.color.YELLOW
                self.scale = 0.6
            else:
                self.color = arcade.color.ORANGE_PEEL
                self.scale = 0.9


class Player(arcade.Sprite):
    def __init__(self):
        # Загружаем спрайт игрока и устанавливаем начальные характеристики
        super().__init__(":resources:images/space_shooter/playerShip2_orange.png", scale=0.5)
        self.speed_x = 0
        self.speed_y = 0
        self.hp = 100
        # Сразу при создании игрока создаем ему объект двигателя
        self.thruster = ShipThruster(self, offset_dist=35)

    def update(self, delta_time):
        # Стандартное обновление позиции на основе скорости
        self.angle += self.change_angle
        self.center_x += self.speed_x
        self.center_y += self.speed_y
        # Важно: двигатель не обновляется сам по себе через SpriteList игрока,
        # поэтому дергаем его update() вручную, чтобы он следовал за игроком без задержек.
        self.thruster.update()


class Asteroid(arcade.Sprite):
    def __init__(self):
        # Чтобы астероиды выглядели разнообразно, выбраны случайные картинки из двух вариантов
        img = random.choice([":resources:images/space_shooter/meteorGrey_big1.png",
                             ":resources:images/space_shooter/meteorGrey_med1.png"])
        super().__init__(img, scale=random.uniform(0.5, 0.8))
        # Добавляем вращение, чтобы камень не выглядел статичным
        self.rotation_speed = random.uniform(-1, 1)

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += self.rotation_speed


class Bullet(arcade.Sprite):
    def __init__(self, is_enemy=False):
        # Один класс пули используем и для игрока, и для врагов.
        # Меняем только текстуру и скорость исчезновения в зависимости от флага is_enemy.
        img = ":resources:images/space_shooter/laserRed01.png"
        scale = 0.8
        if is_enemy:
            img = ":resources:images/space_shooter/laserBlue01.png"
            scale = 0.6
        super().__init__(img, scale=scale)
        # Пуля живет ограниченное время
        self.time_to_live = 1.0 if not is_enemy else 2.0
        self.is_enemy = is_enemy

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.time_to_live -= delta_time
        # Если время жизни вышло - удаляем спрайт
        if self.time_to_live <= 0:
            self.remove_from_sprite_lists()


class Trash(arcade.Sprite):
    def __init__(self):
        # Класс для собираемых предметов (мусора)
        super().__init__(":resources:images/tiles/boxCrate_double.png", scale=0.4)


class RepairKit(arcade.Sprite):
    def __init__(self):
        # Класс аптечки
        super().__init__(":resources:images/topdown_tanks/tankBody_blue_outline.png", scale=0.6)


class Star(arcade.Sprite):
    def __init__(self):
        # Звезды на фоне. Используем прозрачность (alpha), чтобы они были разной яркости
        super().__init__(":resources:images/space_shooter/meteorGrey_tiny1.png", scale=0.4)
        self.alpha = random.randint(50, 180)


class ExplosionParticle(arcade.Sprite):
    def __init__(self, x, y, color):
        # Система частиц для взрывов.
        # Частицы разлетаются в случайных направлениях.
        super().__init__(":resources:images/space_shooter/meteorGrey_tiny1.png", scale=0.3)
        self.center_x = x
        self.center_y = y
        self.color = color
        speed = random.uniform(2, 6)
        angle = random.uniform(0, 2 * math.pi)
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.change_angle = random.uniform(-5, 5)
        # Скорость исчезновения
        self.fade_rate = random.randint(5, 10)

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += self.change_angle
        # Постепенно уменьшаем прозрачность, пока частица не исчезнет совсем
        if self.alpha > 0:
            self.alpha -= self.fade_rate
            if self.alpha < 0: self.alpha = 0
        if self.alpha <= 0:
            self.remove_from_sprite_lists()


class BaseEnemy(arcade.Sprite):
    def __init__(self, filename, scale, player_sprite, enemy_list, offset_dist=35):
        # Базовый класс для всех врагов. Здесь хранится общая логика:
        # ссылка на игрока (чтобы знать, за кем лететь) и свой двигатель.
        super().__init__(filename, scale=scale)
        self.player = player_sprite
        self.enemies = enemy_list
        self.hp = 1
        self.thruster = ShipThruster(self, offset_dist=offset_dist)

    def separate_from_friends(self):
        # Метод для избегания "слипания" врагов в одну точку.
        # Если враги слишком близко, они немного отталкиваются друг от друга.
        if self.enemies:
            for other in self.enemies:
                if other is not self:
                    dist = arcade.get_distance_between_sprites(self, other)
                    if dist < 60:
                        repel_dx = self.center_x - other.center_x
                        repel_dy = self.center_y - other.center_y
                        self.center_x += repel_dx * 0.05
                        self.center_y += repel_dy * 0.05

    def remove_from_sprite_lists(self):
        # Переопределяем метод удаления:
        # Если удаляется корабль врага, нужно удалить и его след (двигатель)
        if self.thruster:
            self.thruster.remove_from_sprite_lists()
        super().remove_from_sprite_lists()


class ChaserEnemy(BaseEnemy):
    def __init__(self, player_sprite, enemy_list):
        # Враг-преследователь. Просто летит на игрока.
        super().__init__(":resources:images/space_shooter/playerShip1_blue.png", 0.5, player_sprite, enemy_list,
                         offset_dist=35)
        self.move_speed = 3.0
        self.hp = 3

    def update(self, delta_time):
        # Вычисляем вектор до игрока
        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        angle_rad = math.atan2(dy, dx)

        # Поворачиваемся к игроку
        self.angle = -math.degrees(angle_rad) + 90

        # Движемся к игроку
        self.center_x += math.cos(angle_rad) * self.move_speed
        self.center_y += math.sin(angle_rad) * self.move_speed

        self.separate_from_friends()
        self.thruster.update()


class ShooterEnemy(BaseEnemy):
    def __init__(self, player_sprite, enemy_list, bullet_list, sound_shoot):
        # Стреляющий враг. Старается держать дистанцию.
        super().__init__(":resources:images/space_shooter/playerShip1_green.png", 0.5, player_sprite, enemy_list,
                         offset_dist=35)
        self.bullet_list = bullet_list
        self.sound_shoot = sound_shoot
        self.move_speed = 2.0
        self.hp = 2
        self.shoot_timer = random.uniform(0, 2)
        self.shoot_delay = 2.5
        self.keep_distance = 350

    def update(self, delta_time):
        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        dist = math.sqrt(dx * dx + dy * dy)
        angle_rad = math.atan2(dy, dx)
        self.angle = -math.degrees(angle_rad) + 90

        # Логика удержания дистанции:
        # Если далеко - подлетаем, если слишком близко - отлетаем назад.
        if dist > self.keep_distance + 50:
            self.center_x += math.cos(angle_rad) * self.move_speed
            self.center_y += math.sin(angle_rad) * self.move_speed
        elif dist < self.keep_distance - 50:
            self.center_x -= math.cos(angle_rad) * (self.move_speed * 0.8)
            self.center_y -= math.sin(angle_rad) * (self.move_speed * 0.8)

        self.separate_from_friends()

        # Таймер стрельбы
        self.shoot_timer -= delta_time
        if self.shoot_timer <= 0:
            self.shoot(angle_rad)
            self.shoot_timer = self.shoot_delay

        self.thruster.update()

    def shoot(self, angle_rad):
        if self.sound_shoot:
            arcade.play_sound(self.sound_shoot, volume=0.2)
        bullet = Bullet(is_enemy=True)
        bullet.angle = self.angle + 90
        # Спавним пулю немного перед кораблем
        bullet.center_x = self.center_x + (math.cos(angle_rad) * 30)
        bullet.center_y = self.center_y + (math.sin(angle_rad) * 30)
        bullet.change_x = math.cos(angle_rad) * 6
        bullet.change_y = math.sin(angle_rad) * 6
        self.bullet_list.append(bullet)


class KamikazeEnemy(BaseEnemy):
    def __init__(self, player_sprite, enemy_list):
        # Камикадзе. Быстрый, слабый, летит "пьяной" траекторией.
        super().__init__(":resources:images/space_shooter/playerShip3_orange.png", 0.4, player_sprite, enemy_list,
                         offset_dist=25)
        self.color = (255, 100, 100)  # Подкрашиваем в красный
        self.move_speed = 4.0
        self.hp = 1
        self.wobble = 0

    def update(self, delta_time):
        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        angle_rad = math.atan2(dy, dx)

        # Добавляем колебания (wobble) к углу поворота
        self.wobble += delta_time * 10
        wobble_offset = math.sin(self.wobble) * 10
        self.angle = -math.degrees(angle_rad) + 90 + wobble_offset

        self.center_x += math.cos(angle_rad) * self.move_speed
        self.center_y += math.sin(angle_rad) * self.move_speed

        self.thruster.update()