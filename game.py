import pygame
import random
import math
import json
import os
import wave
import struct

# ============================================================
# INITIALIZATION
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except pygame.error:
    SOUND_AVAILABLE = False

WIDTH = 800
HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("COSMIC DEFENDER - 50 LEVELS")

clock = pygame.time.Clock()

# ============================================================
# SAVE FILES
# ============================================================

SAVE_FILE = "cosmic_progress.json"
LEADERBOARD_FILE = "leaderboard.json"
MUSIC_FILE = "space_music.wav"

# ============================================================
# COLORS
# ============================================================

WHITE = (245, 250, 255)
BLACK = (0, 0, 0)

CYAN = (40, 220, 255)
BLUE = (60, 100, 255)
PURPLE = (180, 70, 255)
PINK = (255, 70, 180)

RED = (255, 65, 75)
ORANGE = (255, 150, 40)
YELLOW = (255, 230, 70)

GREEN = (60, 230, 130)
GRAY = (100, 105, 125)

MOON = (225, 225, 235)

# ============================================================
# FONTS
# ============================================================

title_font = pygame.font.SysFont(
    "arial", 56, bold=True
)

big_font = pygame.font.SysFont(
    "arial", 42, bold=True
)

button_font = pygame.font.SysFont(
    "arial", 25, bold=True
)

font = pygame.font.SysFont(
    "arial", 24, bold=True
)

small_font = pygame.font.SysFont(
    "arial", 19
)

tiny_font = pygame.font.SysFont(
    "arial", 16
)

# ============================================================
# PLAYER / SAVE DATA
# ============================================================

player_name = ""
name_input = ""

level = 1
score = 0
lives = 3

# Exactly 60 seconds of gameplay
level_time = 60.0

# ============================================================
# GAME OBJECTS
# ============================================================

player = pygame.Rect(
    WIDTH // 2 - 25,
    HEIGHT - 85,
    50,
    50
)

bullets = []

enemy = None
enemy_timer = 0

space_objects = []

# ============================================================
# GAME STATES
# ============================================================

game_state = "name"

# ============================================================
# SOUND
# ============================================================

sound_enabled = True


def create_music():

    if not SOUND_AVAILABLE:
        return False

    if os.path.exists(MUSIC_FILE):
        return True

    sample_rate = 22050
    duration = 8

    notes = [
        220,
        261,
        329,
        392,
        329,
        261,
        196,
        261
    ]

    samples = []

    for i in range(
        sample_rate * duration
    ):

        t = i / sample_rate

        note_index = int(
            t * 2
        ) % len(notes)

        frequency = notes[note_index]

        value = math.sin(
            2 * math.pi * frequency * t
        )

        value *= 0.07

        samples.append(
            struct.pack(
                "<h",
                int(value * 32767)
            )
        )

    try:

        with wave.open(
            MUSIC_FILE,
            "wb"
        ) as music:

            music.setnchannels(1)
            music.setsampwidth(2)
            music.setframerate(sample_rate)

            music.writeframes(
                b"".join(samples)
            )

        return True

    except:
        return False


music_available = create_music()

if (
    SOUND_AVAILABLE
    and music_available
):

    try:

        pygame.mixer.music.load(
            MUSIC_FILE
        )

        pygame.mixer.music.set_volume(
            0.25
        )

        pygame.mixer.music.play(
            -1
        )

    except:
        pass


# ============================================================
# SAVE SYSTEM
# ============================================================

def save_progress():

    if not player_name:
        return

    data = {
        "name": player_name,
        "level": level,
        "score": score,
        "lives": lives,
        "level_time": level_time
    }

    try:

        with open(
            SAVE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

    except:
        pass


def load_saved_data():

    if not os.path.exists(
        SAVE_FILE
    ):
        return None

    try:

        with open(
            SAVE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(
            data,
            dict
        ):
            return None

        return data

    except:

        return None


def restore_saved_game():

    global player_name
    global level
    global score
    global lives
    global level_time

    data = load_saved_data()

    if not data:
        return False

    saved_name = str(
        data.get(
            "name",
            ""
        )
    ).strip()

    if not saved_name:
        return False

    player_name = saved_name

    level = max(
        1,
        min(
            50,
            int(
                data.get(
                    "level",
                    1
                )
            )
        )
    )

    score = max(
        0,
        int(
            data.get(
                "score",
                0
            )
        )
    )

    lives = max(
        1,
        min(
            3,
            int(
                data.get(
                    "lives",
                    3
                )
            )
        )
    )

    level_time = float(
        data.get(
            "level_time",
            60
        )
    )

    if level_time <= 0:
        level_time = 60

    return True


def save_position_now():

    # --------------------------------------------------------
    # This function is called whenever the player leaves.
    # --------------------------------------------------------

    save_progress()
    update_leaderboard()


# ============================================================
# LEADERBOARD
# ============================================================

def load_leaderboard():

    if not os.path.exists(
        LEADERBOARD_FILE
    ):
        return []

    try:

        with open(
            LEADERBOARD_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(
            data,
            list
        ):
            return data

    except:
        pass

    return []


def update_leaderboard():

    if not player_name:
        return

    leaderboard = load_leaderboard()

    found = False

    for entry in leaderboard:

        if (
            str(
                entry.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            player_name.lower()
        ):

            found = True

            old_level = int(
                entry.get(
                    "level",
                    1
                )
            )

            old_score = int(
                entry.get(
                    "score",
                    0
                )
            )

            # Never reduce the player's best level.

            if level > old_level:

                entry["level"] = level

            # Keep best score.

            if score > old_score:

                entry["score"] = score

            break

    if not found:

        leaderboard.append({

            "name": player_name,

            "level": level,

            "score": score

        })

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We DO NOT delete the other players.
    # Every leaderboard record remains.
    # --------------------------------------------------------

    try:

        with open(
            LEADERBOARD_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                leaderboard,
                f,
                indent=4,
                ensure_ascii=False
            )

    except:
        pass


# ============================================================
# STAR FIELD
# ============================================================

stars = []

for _ in range(220):

    stars.append({

        "x": random.randint(
            0,
            WIDTH
        ),

        "y": random.randint(
            0,
            HEIGHT
        ),

        "speed": random.uniform(
            0.3,
            1.8
        ),

        "size": random.choice(
            [1, 1, 1, 2]
        ),

        "brightness": random.randint(
            120,
            255
        )

    })


def update_stars():

    for star in stars:

        star["y"] += star["speed"]

        if star["y"] >= HEIGHT:

            star["y"] = 0

            star["x"] = random.randint(
                0,
                WIDTH
            )


# ============================================================
# BACKGROUND THEMES
# ============================================================

background_themes = [

    (
        (2, 6, 25),
        (8, 30, 80),
        (45, 100, 200)
    ),

    (
        (25, 4, 45),
        (75, 12, 90),
        (175, 50, 190)
    ),

    (
        (2, 28, 40),
        (8, 75, 90),
        (25, 170, 170)
    ),

    (
        (40, 10, 3),
        (100, 35, 8),
        (230, 100, 30)
    ),

    (
        (5, 3, 18),
        (35, 15, 65),
        (150, 110, 220)
    ),

    (
        (2, 15, 35),
        (10, 60, 100),
        (30, 190, 230)
    )

]


def draw_background():

    index = (
        (level - 1)
        %
        len(background_themes)
    )

    top, bottom, planet_color = (
        background_themes[index]
    )

    for y in range(
        HEIGHT
    ):

        ratio = y / HEIGHT

        r = int(
            top[0]
            +
            (
                bottom[0]
                -
                top[0]
            )
            * ratio
        )

        g = int(
            top[1]
            +
            (
                bottom[1]
                -
                top[1]
            )
            * ratio
        )

        b = int(
            top[2]
            +
            (
                bottom[2]
                -
                top[2]
            )
            * ratio
        )

        pygame.draw.line(
            screen,
            (r, g, b),
            (0, y),
            (WIDTH, y)
        )

    # Background planet

    px = (
        100
        +
        ((level * 137) % 600)
    )

    py = 145

    pygame.draw.circle(
        screen,
        planet_color,
        (px, py),
        75
    )

    for star in stars:

        brightness = star[
            "brightness"
        ]

        color = (
            brightness,
            brightness,
            min(
                255,
                brightness + 20
            )
        )

        pygame.draw.circle(
            screen,
            color,
            (
                int(star["x"]),
                int(star["y"])
            ),
            star["size"]
        )


# ============================================================
# TEXT
# ============================================================

def draw_text(
    text,
    font_obj,
    color,
    x,
    y,
    center=False
):

    surface = font_obj.render(
        str(text),
        True,
        color
    )

    if center:

        rect = surface.get_rect(
            center=(
                x,
                y
            )
        )

    else:

        rect = surface.get_rect(
            topleft=(
                x,
                y
            )
        )

    screen.blit(
        surface,
        rect
    )


# ============================================================
# BUTTON
# ============================================================

def draw_button(
    rect,
    text,
    color
):

    shadow = rect.move(
        0,
        4
    )

    pygame.draw.rect(
        screen,
        (5, 5, 15),
        shadow,
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        WHITE,
        rect,
        2,
        border_radius=12
    )

    draw_text(
        text,
        button_font,
        WHITE,
        rect.centerx,
        rect.centery,
        True
    )


# ============================================================
# SPACE OBJECTS
# ============================================================

def create_space_objects():

    global space_objects

    space_objects = []

    # --------------------------------------------------------
    # More objects at higher levels.
    # --------------------------------------------------------

    object_count = min(
        4 + level,
        25
    )

    for _ in range(
        object_count
    ):

        choices = [
            "asteroid"
        ]

        if level >= 3:
            choices.append(
                "crystal"
            )

        if level >= 6:
            choices.append(
                "ring"
            )

        if level >= 10:
            choices.append(
                "star"
            )

        if level >= 15:
            choices.append(
                "satellite"
            )

        if level >= 20:
            choices.append(
                "comet"
            )

        if level >= 30:
            choices.append(
                "alien"
            )

        obj = {

            "type": random.choice(
                choices
            ),

            "x": random.randint(
                25,
                WIDTH - 25
            ),

            "y": random.randint(
                70,
                HEIGHT
            ),

            "size": random.randint(
                10,
                25
            ),

            "speed": random.uniform(
                0.25,
                0.7
                +
                level * 0.025
            )

        }

        space_objects.append(
            obj
        )


def update_space_objects():

    for obj in space_objects:

        obj["y"] += obj[
            "speed"
        ]

        if obj["y"] > HEIGHT + 40:

            obj["y"] = random.randint(
                -100,
                -20
            )

            obj["x"] = random.randint(
                25,
                WIDTH - 25
            )


def draw_space_objects():

    for obj in space_objects:

        x = int(
            obj["x"]
        )

        y = int(
            obj["y"]
        )

        s = obj["size"]

        # ----------------------------------------------------
        # ASTEROID
        # ----------------------------------------------------

        if obj["type"] == "asteroid":

            pygame.draw.circle(
                screen,
                (105, 110, 130),
                (x, y),
                s
            )

            pygame.draw.circle(
                screen,
                (65, 70, 90),
                (
                    x - s // 3,
                    y - s // 3
                ),
                max(
                    3,
                    s // 4
                )
            )

            pygame.draw.circle(
                screen,
                (80, 85, 100),
                (
                    x + s // 3,
                    y + s // 4
                ),
                max(
                    2,
                    s // 5
                )
            )

        # ----------------------------------------------------
        # CRYSTAL
        # ----------------------------------------------------

        elif obj["type"] == "crystal":

            pygame.draw.polygon(
                screen,
                PURPLE,
                [
                    (x, y - s),
                    (x + s // 2, y),
                    (x, y + s),
                    (x - s // 2, y)
                ]
            )

            pygame.draw.line(
                screen,
                WHITE,
                (
                    x,
                    y - s + 3
                ),
                (
                    x,
                    y + s - 3
                ),
                2
            )

        # ----------------------------------------------------
        # RING
        # ----------------------------------------------------

        elif obj["type"] == "ring":

            pygame.draw.circle(
                screen,
                CYAN,
                (x, y),
                s,
                3
            )

            pygame.draw.circle(
                screen,
                PINK,
                (x, y),
                max(
                    4,
                    s - 8
                ),
                2
            )

        # ----------------------------------------------------
        # STAR
        # ----------------------------------------------------

        elif obj["type"] == "star":

            points = []

            for i in range(
                10
            ):

                angle = (
                    -math.pi / 2
                    +
                    i * math.pi / 5
                )

                radius = (
                    s
                    if i % 2 == 0
                    else s // 2
                )

                points.append(
                    (
                        x
                        +
                        math.cos(angle)
                        * radius,

                        y
                        +
                        math.sin(angle)
                        * radius
                    )
                )

            pygame.draw.polygon(
                screen,
                YELLOW,
                points
            )

        # ----------------------------------------------------
        # SATELLITE
        # ----------------------------------------------------

        elif obj["type"] == "satellite":

            pygame.draw.rect(
                screen,
                GRAY,
                (
                    x - 8,
                    y - 8,
                    16,
                    16
                )
            )

            pygame.draw.rect(
                screen,
                BLUE,
                (
                    x - 22,
                    y - 6,
                    12,
                    12
                )
            )

            pygame.draw.rect(
                screen,
                BLUE,
                (
                    x + 10,
                    y - 6,
                    12,
                    12
                )
            )

            pygame.draw.line(
                screen,
                WHITE,
                (
                    x,
                    y + 8
                ),
                (
                    x,
                    y + 22
                ),
                2
            )

        # ----------------------------------------------------
        # COMET
        # ----------------------------------------------------

        elif obj["type"] == "comet":

            pygame.draw.line(
                screen,
                ORANGE,
                (
                    x - s * 2,
                    y + s * 2
                ),
                (
                    x,
                    y
                ),
                5
            )

            pygame.draw.circle(
                screen,
                YELLOW,
                (
                    x,
                    y
                ),
                s
            )

        # ----------------------------------------------------
        # ALIEN
        # ----------------------------------------------------

        elif obj["type"] == "alien":

            pygame.draw.circle(
                screen,
                GREEN,
                (
                    x,
                    y
                ),
                s
            )

            pygame.draw.circle(
                screen,
                BLACK,
                (
                    x - s // 3,
                    y - s // 5
                ),
                max(
                    3,
                    s // 5
                )
            )

            pygame.draw.circle(
                screen,
                BLACK,
                (
                    x + s // 3,
                    y - s // 5
                ),
                max(
                    3,
                    s // 5
                )
            )


# ============================================================
# PLAYER
# ============================================================

def draw_player():

    x = player.centerx
    y = player.centery

    # Engine glow

    pygame.draw.circle(
        screen,
        (15, 60, 120),
        (
            x,
            y
        ),
        35
    )

    # Main ship

    ship = [

        (
            x,
            y - 30
        ),

        (
            x - 26,
            y + 22
        ),

        (
            x - 8,
            y + 14
        ),

        (
            x,
            y + 30
        ),

        (
            x + 8,
            y + 14
        ),

        (
            x + 26,
            y + 22
        )

    ]

    pygame.draw.polygon(
        screen,
        CYAN,
        ship
    )

    # Wings

    pygame.draw.polygon(
        screen,
        PURPLE,
        [
            (
                x - 7,
                y + 4
            ),
            (
                x - 28,
                y + 22
            ),
            (
                x - 7,
                y + 16
            )
        ]
    )

    pygame.draw.polygon(
        screen,
        PURPLE,
        [
            (
                x + 7,
                y + 4
            ),
            (
                x + 28,
                y + 22
            ),
            (
                x + 7,
                y + 16
            )
        ]
    )

    # Cockpit

    pygame.draw.circle(
        screen,
        WHITE,
        (
            x,
            y - 8
        ),
        8
    )

    pygame.draw.circle(
        screen,
        BLUE,
        (
            x,
            y - 8
        ),
        5
    )

    # Engine

    pygame.draw.polygon(
        screen,
        ORANGE,
        [
            (
                x - 8,
                y + 20
            ),
            (
                x,
                y + 38
            ),
            (
                x + 8,
                y + 20
            )
        ]
    )


# ============================================================
# ENEMY
# ============================================================

def draw_enemy(rect):

    x = rect.centerx
    y = rect.centery

    # Outer glow

    pygame.draw.circle(
        screen,
        (100, 10, 65),
        (
            x,
            y
        ),
        32
    )

    # Alien enemy ship

    pygame.draw.polygon(
        screen,
        RED,
        [
            (
                x,
                y - 24
            ),
            (
                x + 24,
                y
            ),
            (
                x,
                y + 24
            ),
            (
                x - 24,
                y
            )
        ]
    )

    pygame.draw.circle(
        screen,
        ORANGE,
        (
            x,
            y
        ),
        10
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            x - 8,
            y - 4
        ),
        4
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            x + 8,
            y - 4
        ),
        4
    )


# ============================================================
# SHOOT
# ============================================================

def shoot():

    bullet = pygame.Rect(
        player.centerx - 3,
        player.top - 20,
        6,
        20
    )

    bullets.append(
        bullet
    )


def draw_bullet(rect):

    pygame.draw.circle(
        screen,
        CYAN,
        rect.center,
        8
    )

    pygame.draw.rect(
        screen,
        YELLOW,
        rect,
        border_radius=4
    )


# ============================================================
# DIFFICULTY
# ============================================================

def enemy_speed():

    return min(
        2.4
        +
        (level - 1)
        * 0.08,
        6.5
    )


def enemy_spawn_delay():

    return max(
        75
        -
        (level - 1)
        * 1.0,
        20
    )


# ============================================================
# LEVEL RESET
# ============================================================

def reset_level():

    global bullets
    global enemy
    global enemy_timer
    global level_time
    global lives

    bullets = []

    enemy = None

    enemy_timer = 0

    # Every level begins with 3 lives.

    lives = 3

    # Every level has exactly 60 seconds.

    level_time = 60.0

    player.x = WIDTH // 2 - 25
    player.y = HEIGHT - 85

    create_space_objects()

    save_progress()
    update_leaderboard()


# ============================================================
# NEW GAME
# ============================================================

def start_new_game():

    global level
    global score
    global lives
    global level_time

    level = 1
    score = 0
    lives = 3
    level_time = 60

    reset_level()


# ============================================================
# START / RESTORE
# ============================================================

def prepare_current_level():

    global bullets
    global enemy
    global enemy_timer

    bullets = []

    enemy = None

    enemy_timer = 0

    player.x = WIDTH // 2 - 25
    player.y = HEIGHT - 85

    create_space_objects()


# ============================================================
# MOON ARRIVAL
# ============================================================

moon_animation = 0.0


def draw_moon_arrival():

    global moon_animation

    # Moon

    moon_x = WIDTH // 2
    moon_y = 130

    pygame.draw.circle(
        screen,
        (70, 75, 115),
        (
            moon_x,
            moon_y
        ),
        85
    )

    pygame.draw.circle(
        screen,
        MOON,
        (
            moon_x,
            moon_y
        ),
        62
    )

    # Moon craters

    pygame.draw.circle(
        screen,
        (175, 180, 195),
        (
            moon_x - 25,
            moon_y - 20
        ),
        11
    )

    pygame.draw.circle(
        screen,
        (175, 180, 195),
        (
            moon_x + 22,
            moon_y + 18
        ),
        8
    )

    pygame.draw.circle(
        screen,
        (180, 185, 200),
        (
            moon_x + 5,
            moon_y - 30
        ),
        7
    )

    # Person waiting

    person_y = moon_y + 100

    pygame.draw.circle(
        screen,
        ORANGE,
        (
            moon_x,
            person_y
        ),
        12
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (
            moon_x - 11,
            person_y + 12,
            22,
            28
        ),
        border_radius=5
    )

    # Ship moving toward moon

    progress = min(
        1.0,
        moon_animation / 3.0
    )

    start_x = WIDTH // 2
    start_y = HEIGHT - 100

    end_x = WIDTH // 2
    end_y = moon_y + 150

    ship_x = int(
        start_x
        +
        (
            end_x
            -
            start_x
        )
        * progress
    )

    ship_y = int(
        start_y
        +
        (
            end_y
            -
            start_y
        )
        * progress
    )

    # Small ship

    pygame.draw.polygon(
        screen,
        CYAN,
        [
            (
                ship_x,
                ship_y - 20
            ),
            (
                ship_x - 17,
                ship_y + 15
            ),
            (
                ship_x,
                ship_y + 8
            ),
            (
                ship_x + 17,
                ship_y + 15
            )
        ]
    )

    pygame.draw.polygon(
        screen,
        ORANGE,
        [
            (
                ship_x - 5,
                ship_y + 10
            ),
            (
                ship_x,
                ship_y + 25
            ),
            (
                ship_x + 5,
                ship_y + 10
            )
        ]
    )

    draw_text(
        "TRAVELLING TO THE MOON...",
        font,
        CYAN,
        WIDTH // 2,
        300,
        True
    )


# ============================================================
# GAME DRAW
# ============================================================

def draw_game():

    draw_background()

    draw_space_objects()

    draw_player()

    for bullet in bullets:

        draw_bullet(
            bullet
        )

    if enemy is not None:

        draw_enemy(
            enemy
        )

    # HUD

    pygame.draw.rect(
        screen,
        (4, 6, 25),
        (
            0,
            0,
            WIDTH,
            65
        )
    )

    draw_text(
        player_name[:16],
        tiny_font,
        WHITE,
        10,
        7
    )

    draw_text(
        f"LEVEL {level}/50",
        small_font,
        CYAN,
        10,
        34
    )

    draw_text(
        f"SCORE {score}",
        small_font,
        WHITE,
        175,
        34
    )

    draw_text(
        f"TIME {max(0, int(level_time))}",
        small_font,
        YELLOW
        if level_time > 10
        else RED,
        320,
        34
    )

    draw_text(
        f"LIVES {lives}",
        small_font,
        GREEN,
        500,
        34
    )

    draw_text(
        "P = PAUSE",
        tiny_font,
        GRAY,
        710,
        38
    )


# ============================================================
# NAME SCREEN
# ============================================================

def draw_name_screen():

    draw_background()

    panel = pygame.Rect(
        75,
        40,
        650,
        520
    )

    pygame.draw.rect(
        screen,
        (5, 10, 35),
        panel,
        border_radius=25
    )

    pygame.draw.rect(
        screen,
        CYAN,
        panel,
        2,
        border_radius=25
    )

    draw_text(
        "COSMIC DEFENDER",
        title_font,
        CYAN,
        WIDTH // 2,
        100,
        True
    )

    draw_text(
        "ENTER YOUR NAME",
        font,
        WHITE,
        WIDTH // 2,
        180,
        True
    )

    box = pygame.Rect(
        WIDTH // 2 - 180,
        215,
        360,
        60
    )

    pygame.draw.rect(
        screen,
        (20, 25, 60),
        box,
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        CYAN,
        box,
        2,
        border_radius=10
    )

    draw_text(
        name_input
        if name_input
        else "Type your name...",
        font,
        WHITE
        if name_input
        else GRAY,
        box.centerx,
        box.centery,
        True
    )

    start_button = pygame.Rect(
        WIDTH // 2 - 130,
        305,
        260,
        55
    )

    leaderboard_button = pygame.Rect(
        WIDTH // 2 - 130,
        375,
        260,
        55
    )

    draw_button(
        start_button,
        "START / CONTINUE",
        GREEN
    )

    draw_button(
        leaderboard_button,
        "LEADERBOARD",
        BLUE
    )

    draw_text(
        "ENTER = Continue     ESC = Quit",
        tiny_font,
        YELLOW,
        WIDTH // 2,
        465,
        True
    )

    draw_text(
        "Your progress is automatically saved.",
        tiny_font,
        WHITE,
        WIDTH // 2,
        495,
        True
    )

    return (
        start_button,
        leaderboard_button
    )


# ============================================================
# MENU
# ============================================================

def draw_menu():

    draw_background()

    panel = pygame.Rect(
        75,
        35,
        650,
        530
    )

    pygame.draw.rect(
        screen,
        (5, 10, 35),
        panel,
        border_radius=25
    )

    pygame.draw.rect(
        screen,
        CYAN,
        panel,
        2,
        border_radius=25
    )

    draw_text(
        "COSMIC DEFENDER",
        title_font,
        CYAN,
        WIDTH // 2,
        95,
        True
    )

    draw_text(
        f"PLAYER: {player_name}",
        small_font,
        WHITE,
        WIDTH // 2,
        160,
        True
    )

    draw_text(
        f"CURRENT LEVEL: {level}/50",
        font,
        YELLOW,
        WIDTH // 2,
        195,
        True
    )

    draw_text(
        f"CURRENT SCORE: {score}",
        small_font,
        WHITE,
        WIDTH // 2,
        230,
        True
    )

    continue_button = pygame.Rect(
        WIDTH // 2 - 130,
        270,
        260,
        55
    )

    sound_button = pygame.Rect(
        WIDTH // 2 - 130,
        340,
        260,
        55
    )

    leaderboard_button = pygame.Rect(
        WIDTH // 2 - 130,
        410,
        260,
        55
    )

    quit_button = pygame.Rect(
        WIDTH // 2 - 130,
        480,
        260,
        50
    )

    draw_button(
        continue_button,
        "CONTINUE GAME",
        GREEN
    )

    draw_button(
        sound_button,
        "SOUND: ON"
        if sound_enabled
        else "SOUND: OFF",
        GREEN
        if sound_enabled
        else GRAY
    )

    draw_button(
        leaderboard_button,
        "LEADERBOARD",
        BLUE
    )

    draw_button(
        quit_button,
        "SAVE & QUIT",
        RED
    )

    return (
        continue_button,
        sound_button,
        leaderboard_button,
        quit_button
    )


# ============================================================
# LEADERBOARD
# ============================================================

def draw_leaderboard():

    draw_background()

    panel = pygame.Rect(
        55,
        25,
        690,
        550
    )

    pygame.draw.rect(
        screen,
        (5, 10, 35),
        panel,
        border_radius=25
    )

    pygame.draw.rect(
        screen,
        YELLOW,
        panel,
        2,
        border_radius=25
    )

    draw_text(
        "LEADERBOARD",
        big_font,
        YELLOW,
        WIDTH // 2,
        65,
        True
    )

    draw_text(
        "RANK",
        tiny_font,
        GRAY,
        80,
        105
    )

    draw_text(
        "PLAYER",
        tiny_font,
        GRAY,
        145,
        105
    )

    draw_text(
        "LEVEL",
        tiny_font,
        GRAY,
        510,
        105
    )

    draw_text(
        "SCORE",
        tiny_font,
        GRAY,
        640,
        105
    )

    leaderboard = load_leaderboard()

    # --------------------------------------------------------
    # Sort only for DISPLAY.
    #
    # We do not delete anything from the file.
    # --------------------------------------------------------

    display_data = sorted(
        leaderboard,
        key=lambda e: (
            int(
                e.get(
                    "level",
                    1
                )
            ),
            int(
                e.get(
                    "score",
                    0
                )
            )
        ),
        reverse=True
    )

    y = 130

    for index, entry in enumerate(
        display_data
    ):

        rank = index + 1

        name = str(
            entry.get(
                "name",
                "Unknown"
            )
        )

        entry_level = int(
            entry.get(
                "level",
                1
            )
        )

        entry_score = int(
            entry.get(
                "score",
                0
            )
        )

        if (
            name.lower()
            ==
            player_name.lower()
        ):

            color = CYAN

        elif rank == 1:

            color = YELLOW

        else:

            color = WHITE

        draw_text(
            f"{rank}.",
            small_font,
            color,
            80,
            y
        )

        draw_text(
            name[:24],
            small_font,
            color,
            145,
            y
        )

        draw_text(
            f"{entry_level}/50",
            small_font,
            color,
            510,
            y
        )

        draw_text(
            entry_score,
            small_font,
            color,
            640,
            y
        )

        y += 32

        if y > 500:
            break

    # --------------------------------------------------------
    # Show current player's position explicitly.
    # --------------------------------------------------------

    my_position = None

    for i, entry in enumerate(
        display_data
    ):

        if (
            str(
                entry.get(
                    "name",
                    ""
                )
            ).lower()
            ==
            player_name.lower()
        ):

            my_position = i + 1
            break

    if my_position:

        draw_text(
            f"YOUR POSITION: #{my_position}",
            tiny_font,
            CYAN,
            WIDTH // 2,
            515,
            True
        )

    back_button = pygame.Rect(
        WIDTH // 2 - 90,
        535,
        180,
        35
    )

    draw_button(
        back_button,
        "BACK",
        GRAY
    )

    return back_button


# ============================================================
# LEVEL COMPLETE SCREEN
# ============================================================

def draw_level_complete():

    draw_background()

    # Moon stays visible

    pygame.draw.circle(
        screen,
        (70, 75, 115),
        (
            WIDTH // 2,
            120
        ),
        85
    )

    pygame.draw.circle(
        screen,
        MOON,
        (
            WIDTH // 2,
            120
        ),
        62
    )

    # Person waiting

    pygame.draw.circle(
        screen,
        ORANGE,
        (
            WIDTH // 2,
            215
        ),
        12
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (
            WIDTH // 2 - 11,
            227,
            22,
            30
        ),
        border_radius=5
    )

    draw_text(
        "LEVEL COMPLETE!",
        big_font,
        GREEN,
        WIDTH // 2,
        290,
        True
    )

    draw_text(
        f"LEVEL {level}/50",
        font,
        CYAN,
        WIDTH // 2,
        335,
        True
    )

    draw_text(
        f"SCORE: {score}",
        font,
        WHITE,
        WIDTH // 2,
        375,
        True
    )

    draw_text(
        "★★★★★",
        big_font,
        YELLOW,
        WIDTH // 2,
        420,
        True
    )

    next_button = pygame.Rect(
        WIDTH // 2 - 130,
        475,
        260,
        55
    )

    draw_button(
        next_button,
        "NEXT LEVEL",
        BLUE
    )

    return next_button


# ============================================================
# FINAL SCREEN
# ============================================================

def draw_final():

    draw_background()

    draw_text(
        "CONGRATULATIONS!",
        big_font,
        YELLOW,
        WIDTH // 2,
        110,
        True
    )

    draw_text(
        player_name,
        title_font,
        CYAN,
        WIDTH // 2,
        175,
        True
    )

    draw_text(
        "50 / 50 LEVELS COMPLETED",
        font,
        GREEN,
        WIDTH // 2,
        240,
        True
    )

    draw_text(
        f"FINAL SCORE: {score}",
        font,
        WHITE,
        WIDTH // 2,
        285,
        True
    )

    draw_text(
        "YOUR NAME IS SAVED IN THE LEADERBOARD",
        small_font,
        YELLOW,
        WIDTH // 2,
        335,
        True
    )

    leaderboard_button = pygame.Rect(
        WIDTH // 2 - 130,
        390,
        260,
        55
    )

    menu_button = pygame.Rect(
        WIDTH // 2 - 100,
        465,
        200,
        55
    )

    draw_button(
        leaderboard_button,
        "LEADERBOARD",
        BLUE
    )

    draw_button(
        menu_button,
        "MAIN MENU",
        GRAY
    )

    return (
        leaderboard_button,
        menu_button
    )


# ============================================================
# GAME OVER
# ============================================================

def draw_game_over():

    draw_background()

    draw_text(
        "GAME OVER",
        title_font,
        RED,
        WIDTH // 2,
        125,
        True
    )

    draw_text(
        player_name,
        font,
        CYAN,
        WIDTH // 2,
        185,
        True
    )

    draw_text(
        f"YOU REACHED LEVEL {level}/50",
        font,
        WHITE,
        WIDTH // 2,
        235,
        True
    )

    draw_text(
        f"SCORE: {score}",
        font,
        WHITE,
        WIDTH // 2,
        280,
        True
    )

    draw_text(
        "ALL 3 LIVES WERE LOST",
        small_font,
        RED,
        WIDTH // 2,
        330,
        True
    )

    draw_text(
        "YOUR LEVEL HAS BEEN SAVED",
        small_font,
        YELLOW,
        WIDTH // 2,
        360,
        True
    )

    retry_button = pygame.Rect(
        WIDTH // 2 - 130,
        400,
        260,
        55
    )

    menu_button = pygame.Rect(
        WIDTH // 2 - 100,
        470,
        200,
        50
    )

    draw_button(
        retry_button,
        f"RETRY LEVEL {level}",
        GREEN
    )

    draw_button(
        menu_button,
        "MAIN MENU",
        GRAY
    )

    return (
        retry_button,
        menu_button
    )


# ============================================================
# PAUSE
# ============================================================

def draw_pause():

    draw_game()

    overlay = pygame.Surface(
        (
            WIDTH,
            HEIGHT
        ),
        pygame.SRCALPHA
    )

    overlay.fill(
        (
            0,
            0,
            20,
            190
        )
    )

    screen.blit(
        overlay,
        (
            0,
            0
        )
    )

    draw_text(
        "PAUSED",
        title_font,
        YELLOW,
        WIDTH // 2,
        145,
        True
    )

    resume_button = pygame.Rect(
        WIDTH // 2 - 120,
        240,
        240,
        55
    )

    menu_button = pygame.Rect(
        WIDTH // 2 - 120,
        320,
        240,
        55
    )

    quit_button = pygame.Rect(
        WIDTH // 2 - 120,
        400,
        240,
        55
    )

    draw_button(
        resume_button,
        "RESUME",
        GREEN
    )

    draw_button(
        menu_button,
        "SAVE & MENU",
        BLUE
    )

    draw_button(
        quit_button,
        "SAVE & QUIT",
        RED
    )

    return (
        resume_button,
        menu_button,
        quit_button
    )


# ============================================================
# STARTUP
# ============================================================

saved = load_saved_data()

if saved:

    # Automatically know the saved player's name.
    # The user can type the same name to continue.

    name_input = str(
        saved.get(
            "name",
            ""
        )
    )

# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    dt = clock.tick(
        FPS
    ) / 1000.0

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            # -----------------------------------------------
            # SAVE BEFORE APPLICATION CLOSES
            # -----------------------------------------------

            if player_name:

                save_position_now()

            running = False

        # ====================================================
        # NAME SCREEN
        # ====================================================

        elif game_state == "name":

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:

                    entered = (
                        name_input.strip()
                    )

                    if entered:

                        # ------------------------------------------------
                        # Check whether this exact player already has
                        # saved progress.
                        # ------------------------------------------------

                        saved_data = (
                            load_saved_data()
                        )

                        if (
                            saved_data
                            and
                            str(
                                saved_data.get(
                                    "name",
                                    ""
                                )
                            ).lower()
                            ==
                            entered.lower()
                        ):

                            # Restore EXACT saved position.

                            player_name = str(
                                saved_data[
                                    "name"
                                ]
                            )

                            level = int(
                                saved_data.get(
                                    "level",
                                    1
                                )
                            )

                            score = int(
                                saved_data.get(
                                    "score",
                                    0
                                )
                            )

                            lives = int(
                                saved_data.get(
                                    "lives",
                                    3
                                )
                            )

                            level_time = float(
                                saved_data.get(
                                    "level_time",
                                    60
                                )
                            )

                            prepare_current_level()

                        else:

                            # New player.

                            player_name = (
                                entered[:20]
                            )

                            start_new_game()

                        update_leaderboard()

                        game_state = "menu"

                elif event.key == pygame.K_BACKSPACE:

                    name_input = (
                        name_input[:-1]
                    )

                elif event.key == pygame.K_ESCAPE:

                    if player_name:

                        save_position_now()

                    running = False

                else:

                    if (
                        len(name_input) < 20
                        and
                        event.unicode.isprintable()
                    ):

                        name_input += (
                            event.unicode
                        )

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                start_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    305,
                    260,
                    55
                )

                leaderboard_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    375,
                    260,
                    55
                )

                if start_button.collidepoint(
                    mouse
                ):

                    entered = (
                        name_input.strip()
                    )

                    if entered:

                        saved_data = (
                            load_saved_data()
                        )

                        if (
                            saved_data
                            and
                            str(
                                saved_data.get(
                                    "name",
                                    ""
                                )
                            ).lower()
                            ==
                            entered.lower()
                        ):

                            # CONTINUE

                            player_name = str(
                                saved_data[
                                    "name"
                                ]
                            )

                            level = int(
                                saved_data.get(
                                    "level",
                                    1
                                )
                            )

                            score = int(
                                saved_data.get(
                                    "score",
                                    0
                                )
                            )

                            lives = int(
                                saved_data.get(
                                    "lives",
                                    3
                                )
                            )

                            level_time = float(
                                saved_data.get(
                                    "level_time",
                                    60
                                )
                            )

                            prepare_current_level()

                        else:

                            # NEW GAME

                            player_name = (
                                entered[:20]
                            )

                            start_new_game()

                        update_leaderboard()

                        game_state = "menu"

                elif leaderboard_button.collidepoint(
                    mouse
                ):

                    game_state = (
                        "leaderboard"
                    )

        # ====================================================
        # MENU
        # ====================================================

        elif game_state == "menu":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                continue_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    270,
                    260,
                    55
                )

                sound_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    340,
                    260,
                    55
                )

                leaderboard_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    410,
                    260,
                    55
                )

                quit_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    480,
                    260,
                    50
                )

                if continue_button.collidepoint(
                    mouse
                ):

                    prepare_current_level()

                    game_state = (
                        "playing"
                    )

                elif sound_button.collidepoint(
                    mouse
                ):

                    sound_enabled = (
                        not sound_enabled
                    )

                    if (
                        SOUND_AVAILABLE
                        and
                        music_available
                    ):

                        if sound_enabled:

                            pygame.mixer.music.unpause()

                        else:

                            pygame.mixer.music.pause()

                elif leaderboard_button.collidepoint(
                    mouse
                ):

                    game_state = (
                        "leaderboard"
                    )

                elif quit_button.collidepoint(
                    mouse
                ):

                    save_position_now()

                    running = False

        # ====================================================
        # LEADERBOARD
        # ====================================================

        elif game_state == "leaderboard":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                back_button = pygame.Rect(
                    WIDTH // 2 - 90,
                    535,
                    180,
                    35
                )

                if back_button.collidepoint(
                    mouse
                ):

                    game_state = "menu"

        # ====================================================
        # PLAYING
        # ====================================================

        elif game_state == "playing":

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:

                    shoot()

                elif event.key == pygame.K_p:

                    save_position_now()

                    game_state = "paused"

                elif event.key == pygame.K_ESCAPE:

                    save_position_now()

                    game_state = "menu"

        # ====================================================
        # PAUSED
        # ====================================================

        elif game_state == "paused":

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_p:

                    game_state = "playing"

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                resume_button = pygame.Rect(
                    WIDTH // 2 - 120,
                    240,
                    240,
                    55
                )

                menu_button = pygame.Rect(
                    WIDTH // 2 - 120,
                    320,
                    240,
                    55
                )

                quit_button = pygame.Rect(
                    WIDTH // 2 - 120,
                    400,
                    240,
                    55
                )

                if resume_button.collidepoint(
                    mouse
                ):

                    game_state = "playing"

                elif menu_button.collidepoint(
                    mouse
                ):

                    save_position_now()

                    game_state = "menu"

                elif quit_button.collidepoint(
                    mouse
                ):

                    save_position_now()

                    running = False

        # ====================================================
        # LEVEL COMPLETE
        # ====================================================

        elif game_state == "level_complete":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                next_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    475,
                    260,
                    55
                )

                if next_button.collidepoint(
                    mouse
                ):

                    if level < 50:

                        # ------------------------------------
                        # MOVE TO NEXT LEVEL PERMANENTLY
                        # ------------------------------------

                        level += 1

                        # New level gets 3 lives.

                        reset_level()

                        # Save the NEW level immediately.

                        save_progress()
                        update_leaderboard()

                        game_state = (
                            "playing"
                        )

                    else:

                        # Level 50 finished.

                        save_progress()
                        update_leaderboard()

                        game_state = (
                            "final"
                        )

        # ====================================================
        # FINAL
        # ====================================================

        elif game_state == "final":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                leaderboard_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    390,
                    260,
                    55
                )

                menu_button = pygame.Rect(
                    WIDTH // 2 - 100,
                    465,
                    200,
                    55
                )

                if leaderboard_button.collidepoint(
                    mouse
                ):

                    game_state = (
                        "leaderboard"
                    )

                elif menu_button.collidepoint(
                    mouse
                ):

                    game_state = "menu"

        # ====================================================
        # GAME OVER
        # ====================================================

        elif game_state == "gameover":

            if event.type == pygame.MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()

                retry_button = pygame.Rect(
                    WIDTH // 2 - 130,
                    400,
                    260,
                    55
                )

                menu_button = pygame.Rect(
                    WIDTH // 2 - 100,
                    470,
                    200,
                    50
                )

                if retry_button.collidepoint(
                    mouse
                ):

                    # ----------------------------------------
                    # IMPORTANT:
                    #
                    # Retry SAME LEVEL.
                    # Never return to Level 1.
                    # ----------------------------------------

                    reset_level()

                    game_state = (
                        "playing"
                    )

                elif menu_button.collidepoint(
                    mouse
                ):

                    save_position_now()

                    game_state = "menu"

    # ========================================================
    # UPDATE STARS
    # ========================================================

    update_stars()

    # ========================================================
    # PLAYING
    # ========================================================

    if game_state == "playing":

        # ----------------------------------------------------
        # LEVEL TIMER
        # ----------------------------------------------------

        level_time -= dt

        # ----------------------------------------------------
        # PLAYER MOVEMENT
        # ----------------------------------------------------

        keys = pygame.key.get_pressed()

        if (
            keys[pygame.K_LEFT]
            or
            keys[pygame.K_a]
        ):

            player.x -= 7

        if (
            keys[pygame.K_RIGHT]
            or
            keys[pygame.K_d]
        ):

            player.x += 7

        if player.left < 10:

            player.left = 10

        if player.right > WIDTH - 10:

            player.right = (
                WIDTH - 10
            )

        # ----------------------------------------------------
        # OBJECTS
        # ----------------------------------------------------

        update_space_objects()

        # ----------------------------------------------------
        # SPAWN ONLY ONE MAIN RED ENEMY
        # ----------------------------------------------------

        if enemy is None:

            enemy_timer += 1

            if (
                enemy_timer
                >=
                enemy_spawn_delay()
            ):

                size = 46

                enemy = pygame.Rect(

                    random.randint(
                        20,
                        WIDTH - size - 20
                    ),

                    -size,

                    size,
                    size
                )

                enemy_timer = 0

        # ----------------------------------------------------
        # BULLETS
        # ----------------------------------------------------

        for bullet in bullets[:]:

            bullet.y -= 12

            if bullet.bottom < 0:

                bullets.remove(
                    bullet
                )

        # ----------------------------------------------------
        # ENEMY
        # ----------------------------------------------------

        if enemy is not None:

            enemy.y += enemy_speed()

            # ------------------------------------------------
            # TOUCH RED ENEMY
            # ------------------------------------------------

            if enemy.colliderect(
                player
            ):

                enemy = None

                lives -= 1

                save_position_now()

                if lives <= 0:

                    lives = 0

                    save_position_now()

                    game_state = (
                        "gameover"
                    )

            # ------------------------------------------------
            # MISS RED ENEMY
            # ------------------------------------------------

            elif enemy.top > HEIGHT:

                enemy = None

                lives -= 1

                save_position_now()

                if lives <= 0:

                    lives = 0

                    save_position_now()

                    game_state = (
                        "gameover"
                    )

        # ----------------------------------------------------
        # SHOOT ENEMY
        # ----------------------------------------------------

        if enemy is not None:

            for bullet in bullets[:]:

                if bullet.colliderect(
                    enemy
                ):

                    if bullet in bullets:

                        bullets.remove(
                            bullet
                        )

                    enemy = None

                    score += 2

                    update_leaderboard()

                    break

        # ----------------------------------------------------
        # 60 SECOND TIMER FINISHED
        # ----------------------------------------------------

        if (
            level_time <= 0
            and
            game_state == "playing"
        ):

            level_time = 0

            # -----------------------------------------------
            # SAVE CURRENT LEVEL BEFORE MOON SEQUENCE
            # -----------------------------------------------

            save_position_now()

            # Start Moon journey.

            moon_animation = 0.0

            game_state = (
                "moon_arrival"
            )

        # ----------------------------------------------------
        # AUTO SAVE
        # ----------------------------------------------------

        save_progress()

        draw_game()

    # ========================================================
    # MOON JOURNEY
    # ========================================================

    elif game_state == "moon_arrival":

        draw_background()

        moon_animation += dt

        draw_moon_arrival()

        # ----------------------------------------------------
        # After the ship reaches the Moon:
        # ----------------------------------------------------

        if moon_animation >= 3.0:

            # Level is now officially finished.

            score += 10

            update_leaderboard()

            save_progress()

            if level >= 50:

                game_state = (
                    "final"
                )

            else:

                game_state = (
                    "level_complete"
                )

    # ========================================================
    # SCREENS
    # ========================================================

    elif game_state == "name":

        draw_name_screen()

    elif game_state == "menu":

        draw_menu()

    elif game_state == "leaderboard":

        draw_leaderboard()

    elif game_state == "level_complete":

        draw_level_complete()

    elif game_state == "final":

        draw_final()

    elif game_state == "gameover":

        draw_game_over()

    elif game_state == "paused":

        draw_pause()

    # ========================================================
    # DISPLAY
    # ========================================================

    pygame.display.flip()


# ============================================================
# FINAL SAVE
# ============================================================

if player_name:

    save_position_now()

pygame.quit()