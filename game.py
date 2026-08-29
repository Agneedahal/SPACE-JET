import pygame
import random
import json
import os
import sys
import math

# ============================================================
# COSMIC DEFENDER
# Complete Windows + Android-friendly Pygame game
# ============================================================

# ------------------------------------------------------------
# AUDIO MUST BE INITIALIZED BEFORE pygame.init()
# ------------------------------------------------------------
pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=512
)

pygame.init()

# ------------------------------------------------------------
# FILE PATHS
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAVE_FILE = os.path.join(
    BASE_DIR,
    "cosmic_progress.json"
)

LEADERBOARD_FILE = os.path.join(
    BASE_DIR,
    "leaderboard.json"
)
MUSIC_FILE = os.path.join(
    BASE_DIR,
    "background_music.wav"
)

# ------------------------------------------------------------
# AUDIO
# ------------------------------------------------------------
# The game can use an external music file if one exists, but it
# also creates a small built-in music track in memory. This means
# the game DOES NOT depend on a missing MP3/WAV file.
MUSIC_OK = False
music_channel = None
music_sound = None

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(
            frequency=44100,
            size=-16,
            channels=2,
            buffer=512
        )
    MUSIC_OK = True
except Exception as e:
    print("Audio initialization error:", e)


def make_builtin_music():
    """Create a simple looping space-style background track in memory."""
    if not MUSIC_OK:
        return None

    try:
        import array

        sample_rate = 44100
        seconds = 12.0
        total = int(sample_rate * seconds)
        samples = array.array("h")

        # A calm repeating melody. No external audio file is required.
        notes = [
            220.00, 261.63, 329.63, 293.66,
            246.94, 293.66, 349.23, 329.63,
            196.00, 246.94, 293.66, 261.63,
            220.00, 293.66, 329.63, 392.00
        ]
        note_len = seconds / len(notes)

        for i in range(total):
            t = i / sample_rate
            n = int(t / note_len) % len(notes)
            local_t = t - int(t / note_len) * note_len

            freq = notes[n]

            # Main melody + quiet harmony + low bass.
            melody = math.sin(2.0 * math.pi * freq * t)
            harmony = 0.35 * math.sin(
                2.0 * math.pi * (freq * 1.5) * t
            )
            bass = 0.18 * math.sin(
                2.0 * math.pi * (freq / 2.0) * t
            )

            # Smooth note envelope to avoid clicks.
            attack = min(1.0, local_t / 0.08)
            release = min(
                1.0,
                max(0.0, (note_len - local_t) / 0.12)
            )
            envelope = min(attack, release)

            value = (
                melody * 0.42
                + harmony * 0.20
                + bass * 0.16
            ) * envelope

            value = int(max(-1.0, min(1.0, value)) * 9000)

            # Stereo sample.
            samples.append(value)
            samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    except Exception as e:
        print("Built-in music creation error:", e)
        return None


def start_background_music():
    """Start background music. Uses an external file when available,
    otherwise uses the built-in music generated above."""

    global music_channel
    global music_sound

    if not MUSIC_OK:
        print("Music system unavailable. Game will continue silently.")
        return

    try:
        # First try a user-supplied music file.
        candidates = [
            os.path.join(BASE_DIR, "background_music.ogg"),
            os.path.join(BASE_DIR, "background_music.wav"),
            os.path.join(BASE_DIR, "background_music.mp3"),
        ]

        external_file = None
        for candidate in candidates:
            if os.path.isfile(candidate):
                external_file = candidate
                break

        if external_file:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(external_file)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(loops=-1)
            print("Background music: ON")
            print("Using:", external_file)
            return

        # No external file: use built-in music.
        music_sound = make_builtin_music()

        if music_sound is not None:
            music_sound.set_volume(1.0)
            music_channel = pygame.mixer.Channel(0)
            music_channel.play(music_sound, loops=-1)
            print("Background music: ON (built-in)")
        else:
            print("Could not create background music.")

    except Exception as e:
        print("Could not play background music:")
        print(e)


def stop_background_music():
    global music_channel

    if not MUSIC_OK:
        return

    try:
        pygame.mixer.music.stop()

        if music_channel is not None:
            music_channel.stop()

    except Exception:
        pass


# Start music immediately.
start_background_music()


# ============================================================
# SCREEN
# ============================================================

WIDTH = 900
HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.RESIZABLE | pygame.SCALED
)

pygame.display.set_caption(
    "COSMIC DEFENDER"
)

clock = pygame.time.Clock()


# ============================================================
# COLORS
# ============================================================

WHITE = (245, 245, 255)
BLACK = (5, 5, 15)

CYAN = (40, 220, 255)
BLUE = (60, 110, 255)
PURPLE = (175, 70, 255)
PINK = (255, 70, 180)

RED = (255, 55, 65)
ORANGE = (255, 145, 35)
YELLOW = (255, 225, 50)

GREEN = (60, 230, 125)
GRAY = (120, 125, 145)

DARK_PANEL = (8, 10, 30)


# ============================================================
# FONTS
# ============================================================

title_font = pygame.font.SysFont(
    "arial",
    55,
    bold=True
)

big_font = pygame.font.SysFont(
    "arial",
    39,
    bold=True
)

button_font = pygame.font.SysFont(
    "arial",
    26,
    bold=True
)

font = pygame.font.SysFont(
    "arial",
    22,
    bold=True
)

small_font = pygame.font.SysFont(
    "arial",
    18
)


# ============================================================
# GAME STATE
# ============================================================

game_state = "name"

player_name = ""
name_text = ""

level = 1
score = 0
lives = 3

LEVEL_DURATION = 30.0
level_time = LEVEL_DURATION

# ------------------------------------------------------------
# Player
# ------------------------------------------------------------

player = pygame.Rect(
    WIDTH // 2 - 30,
    HEIGHT - 105,
    60,
    45
)

PLAYER_SPEED = 450


# ============================================================
# OBJECT LISTS
# ============================================================

bullets = []
monsters = []
particles = []


# ============================================================
# TOUCH BUTTONS
# ============================================================

left_button = pygame.Rect(
    25,
    HEIGHT - 75,
    100,
    55
)

right_button = pygame.Rect(
    140,
    HEIGHT - 75,
    100,
    55
)

fire_button = pygame.Rect(
    WIDTH - 175,
    HEIGHT - 85,
    150,
    65
)

pause_button = pygame.Rect(
    WIDTH - 95,
    12,
    75,
    45
)

touch_left = False
touch_right = False


# ============================================================
# LOCATIONS
# ============================================================

LOCATIONS = [
    "DEEP SPACE",
    "ASTEROID FIELD",
    "BLUE NEBULA",
    "CRYSTAL WORLD",
    "RED PLANET",
    "ICE PLANET",
    "DARK GALAXY",
    "SPACE STATION",
    "MOON REGION",
    "FINAL GALAXY"
]

LOCATION_COLORS = [
    (5, 8, 35),
    (20, 8, 30),
    (5, 20, 50),
    (25, 5, 45),
    (45, 10, 10),
    (8, 25, 45),
    (8, 5, 25),
    (20, 20, 32),
    (25, 25, 38),
    (35, 5, 40)
]


def current_location():
    return LOCATIONS[
        (level - 1) % len(LOCATIONS)
    ]


def current_background_color():
    return LOCATION_COLORS[
        (level - 1) % len(LOCATION_COLORS)
    ]


# ============================================================
# STARS
# ============================================================

stars = []

for _ in range(180):

    stars.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "speed": random.randint(15, 75),
        "size": random.choice([1, 1, 1, 2])
    })


def update_stars(dt):

    for star in stars:

        star["y"] += (
            star["speed"] * dt
        )

        if star["y"] > HEIGHT:

            star["y"] = 0

            star["x"] = random.randint(
                0,
                WIDTH
            )


# ============================================================
# BACKGROUND
# ============================================================

def draw_background():

    bg = current_background_color()

    # Background
    screen.fill(bg)

    # Slight vertical gradient
    for y in range(
        0,
        HEIGHT,
        6
    ):

        ratio = y / HEIGHT

        r = min(
            255,
            int(bg[0] + ratio * 8)
        )

        g = min(
            255,
            int(bg[1] + ratio * 8)
        )

        b = min(
            255,
            int(bg[2] + ratio * 18)
        )

        pygame.draw.rect(
            screen,
            (r, g, b),
            (0, y, WIDTH, 6)
        )

    # Stars
    for star in stars:

        pygame.draw.circle(
            screen,
            (190, 215, 255),
            (
                int(star["x"]),
                int(star["y"])
            ),
            star["size"]
        )

    location = current_location()

    # --------------------------------------------------------
    # ASTEROID FIELD
    # --------------------------------------------------------

    if location == "ASTEROID FIELD":

        for i in range(8):

            x = 50 + i * 120
            y = 100 + (i % 3) * 115

            pygame.draw.circle(
                screen,
                (75, 75, 90),
                (x, y),
                21
            )

    # --------------------------------------------------------
    # BLUE NEBULA
    # --------------------------------------------------------

    elif location == "BLUE NEBULA":

        for i in range(5):

            pygame.draw.circle(
                screen,
                (25, 70, 130),
                (
                    100 + i * 190,
                    145 + (i % 2) * 140
                ),
                65
            )

    # --------------------------------------------------------
    # CRYSTAL WORLD
    # --------------------------------------------------------

    elif location == "CRYSTAL WORLD":

        for i in range(7):

            x = 40 + i * 135

            pygame.draw.polygon(
                screen,
                (90, 40, 150),
                [
                    (x, 500),
                    (x + 24, 350),
                    (x + 50, 500)
                ]
            )

    # --------------------------------------------------------
    # RED PLANET
    # --------------------------------------------------------

    elif location == "RED PLANET":

        pygame.draw.circle(
            screen,
            (120, 40, 40),
            (
                WIDTH - 115,
                145
            ),
            80
        )

        pygame.draw.circle(
            screen,
            (80, 25, 25),
            (
                WIDTH - 145,
                120
            ),
            12
        )

        pygame.draw.circle(
            screen,
            (85, 28, 28),
            (
                WIDTH - 90,
                165
            ),
            17
        )

    # --------------------------------------------------------
    # ICE PLANET
    # --------------------------------------------------------

    elif location == "ICE PLANET":

        pygame.draw.circle(
            screen,
            (90, 175, 225),
            (
                105,
                145
            ),
            78
        )

    # --------------------------------------------------------
    # DARK GALAXY
    # --------------------------------------------------------

    elif location == "DARK GALAXY":

        pygame.draw.circle(
            screen,
            (100, 35, 130),
            (
                WIDTH // 2,
                180
            ),
            105
        )

        pygame.draw.circle(
            screen,
            (20, 5, 35),
            (
                WIDTH // 2,
                180
            ),
            55
        )

    # --------------------------------------------------------
    # SPACE STATION
    # --------------------------------------------------------

    elif location == "SPACE STATION":

        pygame.draw.rect(
            screen,
            (70, 75, 100),
            (
                WIDTH - 190,
                105,
                130,
                45
            )
        )

        pygame.draw.line(
            screen,
            CYAN,
            (
                WIDTH - 125,
                75
            ),
            (
                WIDTH - 125,
                185
            ),
            5
        )

    # --------------------------------------------------------
    # MOON
    # --------------------------------------------------------

    elif location == "MOON REGION":

        pygame.draw.circle(
            screen,
            (200, 200, 210),
            (
                WIDTH - 110,
                135
            ),
            75
        )

        pygame.draw.circle(
            screen,
            (160, 160, 170),
            (
                WIDTH - 140,
                110
            ),
            12
        )

        pygame.draw.circle(
            screen,
            (160, 160, 170),
            (
                WIDTH - 85,
                155
            ),
            9
        )

    # --------------------------------------------------------
    # FINAL GALAXY
    # --------------------------------------------------------

    elif location == "FINAL GALAXY":

        pygame.draw.circle(
            screen,
            (145, 50, 170),
            (
                WIDTH // 2,
                180
            ),
            110
        )

        pygame.draw.circle(
            screen,
            (80, 25, 100),
            (
                WIDTH // 2,
                180
            ),
            55
        )


# ============================================================
# TEXT
# ============================================================

def draw_text(
    text,
    font_object,
    color,
    x,
    y,
    center=False
):

    surface = font_object.render(
        str(text),
        True,
        color
    )

    if center:

        rect = surface.get_rect(
            center=(x, y)
        )

    else:

        rect = surface.get_rect(
            topleft=(x, y)
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
        (2, 2, 10),
        shadow,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        WHITE,
        rect,
        2,
        border_radius=14
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
# SAVE
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
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    except Exception as e:

        print(
            "Save error:",
            e
        )


# ============================================================
# LOAD
# ============================================================

def load_progress():

    if not os.path.exists(
        SAVE_FILE
    ):
        return None

    try:

        with open(
            SAVE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print(
            "Load error:",
            e
        )

        return None


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
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


def update_leaderboard():

    if not player_name:
        return

    board = load_leaderboard()

    found = False

    for item in board:

        if item.get(
            "name",
            ""
        ).lower() == player_name.lower():

            found = True

            item["level"] = max(
                int(
                    item.get(
                        "level",
                        1
                    )
                ),
                level
            )

            item["score"] = max(
                int(
                    item.get(
                        "score",
                        0
                    )
                ),
                score
            )

            break

    if not found:

        board.append({
            "name": player_name,
            "level": level,
            "score": score
        })

    # Highest level first.
    # If levels are equal, highest score first.
    board.sort(
        key=lambda item: (
            int(
                item.get(
                    "level",
                    1
                )
            ),
            int(
                item.get(
                    "score",
                    0
                )
            )
        ),
        reverse=True
    )

    try:

        with open(
            LEADERBOARD_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                board,
                file,
                indent=4
            )

    except Exception as e:

        print(
            "Leaderboard error:",
            e
        )


# ============================================================
# NAME SCREEN
# ============================================================

def draw_name_screen():

    draw_background()

    draw_text(
        "COSMIC DEFENDER",
        title_font,
        CYAN,
        WIDTH // 2,
        105,
        True
    )

    draw_text(
        "ENTER YOUR NAME",
        big_font,
        WHITE,
        WIDTH // 2,
        190,
        True
    )

    name_box = pygame.Rect(
        WIDTH // 2 - 220,
        240,
        440,
        65
    )

    pygame.draw.rect(
        screen,
        DARK_PANEL,
        name_box,
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        CYAN,
        name_box,
        3,
        border_radius=12
    )

    if name_text:

        draw_text(
            name_text,
            font,
            WHITE,
            name_box.x + 20,
            name_box.y + 20
        )

    else:

        draw_text(
            "Type your name...",
            small_font,
            GRAY,
            name_box.x + 20,
            name_box.y + 22
        )

    continue_button = pygame.Rect(
        WIDTH // 2 - 135,
        340,
        270,
        62
    )

    draw_button(
        continue_button,
        "CONTINUE",
        GREEN
    )

    draw_text(
        "Press ENTER after typing your name",
        small_font,
        WHITE,
        WIDTH // 2,
        440,
        True
    )


# ============================================================
# MENU
# ============================================================

def draw_menu():

    draw_background()

    draw_text(
        "COSMIC DEFENDER",
        title_font,
        CYAN,
        WIDTH // 2,
        65,
        True
    )

    draw_text(
        "WELCOME " +
        player_name.upper(),
        font,
        WHITE,
        WIDTH // 2,
        130,
        True
    )

    draw_text(
        "CURRENT LEVEL " +
        str(level),
        big_font,
        YELLOW,
        WIDTH // 2,
        180,
        True
    )

    draw_text(
        current_location(),
        font,
        PINK,
        WIDTH // 2,
        225,
        True
    )

    start_button = pygame.Rect(
        WIDTH // 2 - 145,
        275,
        290,
        60
    )

    leaderboard_button = pygame.Rect(
        WIDTH // 2 - 145,
        355,
        290,
        60
    )

    exit_button = pygame.Rect(
        WIDTH // 2 - 145,
        435,
        290,
        60
    )

    draw_button(
        start_button,
        "START MISSION",
        GREEN
    )

    draw_button(
        leaderboard_button,
        "LEADERBOARD",
        PURPLE
    )

    draw_button(
        exit_button,
        "EXIT",
        RED
    )


# ============================================================
# PLAYER DRAWING
# ============================================================

def draw_player():

    x = player.centerx

    # Engine
    pygame.draw.polygon(
        screen,
        ORANGE,
        [
            (
                x - 8,
                player.bottom
            ),
            (
                x + 8,
                player.bottom
            ),
            (
                x,
                player.bottom + 20
            )
        ]
    )

    pygame.draw.polygon(
        screen,
        YELLOW,
        [
            (
                x - 5,
                player.bottom
            ),
            (
                x + 5,
                player.bottom
            ),
            (
                x,
                player.bottom + 12
            )
        ]
    )

    # Ship
    pygame.draw.polygon(
        screen,
        CYAN,
        [
            (
                x,
                player.top
            ),
            (
                player.right,
                player.bottom
            ),
            (
                x,
                player.bottom - 13
            ),
            (
                player.left,
                player.bottom
            )
        ]
    )

    # Cockpit
    pygame.draw.circle(
        screen,
        WHITE,
        (
            x,
            player.top + 21
        ),
        7
    )


# ============================================================
# DIFFICULTY
# ============================================================

def monster_speed():

    # Very easy levels
    if level <= 10:

        return random.uniform(
            38,
            62
        )

    # Easy-average
    if level <= 20:

        return random.uniform(
            50,
            75
        )

    # Average
    if level <= 30:

        return random.uniform(
            60,
            88
        )

    # Average / challenging
    if level <= 40:

        return random.uniform(
            70,
            98
        )

    # Still beatable
    return random.uniform(
        78,
        105
    )


def monster_delay():

    if level <= 10:
        return 2.8

    if level <= 20:
        return 2.4

    if level <= 30:
        return 2.1

    if level <= 40:
        return 1.9

    return 1.8


def maximum_monsters():

    if level <= 10:
        return 2

    if level <= 20:
        return 3

    if level <= 30:
        return 4

    return 5


# ============================================================
# SPAWN MONSTER
# ============================================================

def spawn_monster():

    size = random.randint(
        17,
        24
    )

    if level <= 10:

        monster_types = [
            "circle",
            "square"
        ]

    elif level <= 20:

        monster_types = [
            "circle",
            "square",
            "diamond"
        ]

    else:

        monster_types = [
            "circle",
            "square",
            "diamond",
            "triangle",
            "alien"
        ]

    monster = {
        "x": random.randint(
            30,
            WIDTH - 30
        ),
        "y": -35,
        "size": size,
        "speed": monster_speed(),
        "type": random.choice(
            monster_types
        ),
        "hp": 1
    }

    # Occasional 2-hit monster later
    if level >= 25:

        if random.random() < 0.10:

            monster["hp"] = 2

    monsters.append(
        monster
    )


# ============================================================
# DRAW MONSTER
# ============================================================

def draw_monster(monster):

    x = int(monster["x"])
    y = int(monster["y"])
    s = monster["size"]

    monster_type = monster["type"]

    if monster_type == "circle":

        pygame.draw.circle(
            screen,
            RED,
            (x, y),
            s
        )

        pygame.draw.circle(
            screen,
            YELLOW,
            (
                x - s // 3,
                y - s // 4
            ),
            3
        )

        pygame.draw.circle(
            screen,
            YELLOW,
            (
                x + s // 3,
                y - s // 4
            ),
            3
        )

    elif monster_type == "square":

        pygame.draw.rect(
            screen,
            ORANGE,
            (
                x - s,
                y - s,
                s * 2,
                s * 2
            ),
            border_radius=5
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (
                x - 5,
                y - 3
            ),
            3
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (
                x + 5,
                y - 3
            ),
            3
        )

    elif monster_type == "diamond":

        pygame.draw.polygon(
            screen,
            PURPLE,
            [
                (x, y - s),
                (x + s, y),
                (x, y + s),
                (x - s, y)
            ]
        )

    elif monster_type == "triangle":

        pygame.draw.polygon(
            screen,
            PINK,
            [
                (x, y - s),
                (x - s, y + s),
                (x + s, y + s)
            ]
        )

    else:

        pygame.draw.ellipse(
            screen,
            GREEN,
            (
                x - s,
                y - s,
                s * 2,
                s * 2
            )
        )

        pygame.draw.circle(
            screen,
            BLACK,
            (
                x - 5,
                y - 2
            ),
            3
        )

        pygame.draw.circle(
            screen,
            BLACK,
            (
                x + 5,
                y - 2
            ),
            3
        )


# ============================================================
# SHOOT THREE BULLETS
# ============================================================

def shoot():

    x = player.centerx
    y = player.top

    # EXACTLY THREE BULLETS
    bullets.append({
        "x": x - 16,
        "y": y,
        "dx": -80
    })

    bullets.append({
        "x": x,
        "y": y,
        "dx": 0
    })

    bullets.append({
        "x": x + 16,
        "y": y,
        "dx": 80
    })


def draw_bullets():

    for bullet in bullets:

        pygame.draw.rect(
            screen,
            YELLOW,
            (
                int(bullet["x"] - 3),
                int(bullet["y"]),
                6,
                18
            ),
            border_radius=3
        )


# ============================================================
# PARTICLES
# ============================================================

def create_explosion(x, y):

    for _ in range(8):

        particles.append({
            "x": x,
            "y": y,
            "dx": random.uniform(-80, 80),
            "dy": random.uniform(-80, 80),
            "life": 0.35
        })


def update_particles(dt):

    for particle in particles[:]:

        particle["x"] += (
            particle["dx"] * dt
        )

        particle["y"] += (
            particle["dy"] * dt
        )

        particle["life"] -= dt

        if particle["life"] <= 0:

            if particle in particles:
                particles.remove(
                    particle
                )


def draw_particles():

    for particle in particles:

        pygame.draw.circle(
            screen,
            YELLOW,
            (
                int(particle["x"]),
                int(particle["y"])
            ),
            3
        )


# ============================================================
# HUD
# ============================================================

def draw_hud():

    pygame.draw.rect(
        screen,
        (5, 5, 25),
        (
            0,
            0,
            WIDTH,
            65
        )
    )

    draw_text(
        "LEVEL " + str(level),
        font,
        WHITE,
        15,
        18
    )

    draw_text(
        "SCORE " + str(score),
        font,
        YELLOW,
        165,
        18
    )

    draw_text(
        "LIVES " + str(lives),
        font,
        GREEN,
        340,
        18
    )

    draw_text(
        "TIME " +
        str(
            max(
                0,
                int(level_time)
            )
        ),
        font,
        CYAN,
        500,
        18
    )

    draw_text(
        current_location(),
        small_font,
        PINK,
        630,
        22
    )

    draw_button(
        pause_button,
        "II",
        PURPLE
    )


# ============================================================
# TOUCH CONTROLS
# ============================================================

def draw_touch_controls():

    draw_button(
        left_button,
        "<",
        BLUE
    )

    draw_button(
        right_button,
        ">",
        BLUE
    )

    draw_button(
        fire_button,
        "FIRE x3",
        RED
    )


# ============================================================
# RESET LEVEL
# ============================================================

def reset_level():

    global level_time

    level_time = LEVEL_DURATION

    bullets.clear()
    monsters.clear()
    particles.clear()

    player.centerx = WIDTH // 2
    player.bottom = HEIGHT - 95


# ============================================================
# NEW GAME
# ============================================================

def start_new_game():

    global level
    global score
    global lives

    level = 1
    score = 0
    lives = 3

    reset_level()

    save_progress()
    update_leaderboard()


# ============================================================
# CONTINUE SAVED GAME
# ============================================================

def continue_saved_game():

    global player_name
    global level
    global score
    global lives
    global level_time

    data = load_progress()

    if not data:

        start_new_game()
        return

    try:

        player_name = data.get(
            "name",
            player_name
        )

        level = int(
            data.get(
                "level",
                1
            )
        )

        score = int(
            data.get(
                "score",
                0
            )
        )

        lives = int(
            data.get(
                "lives",
                3
            )
        )

        level_time = float(
            data.get(
                "level_time",
                LEVEL_DURATION
            )
        )

        # Safety
        level = max(
            1,
            min(
                50,
                level
            )
        )

        lives = max(
            1,
            min(
                3,
                lives
            )
        )

        bullets.clear()
        monsters.clear()
        particles.clear()

        player.centerx = WIDTH // 2
        player.bottom = HEIGHT - 95

    except Exception:

        start_new_game()


# ============================================================
# LEADERBOARD SCREEN
# ============================================================

def draw_leaderboard():

    draw_background()

    draw_text(
        "LEADERBOARD",
        title_font,
        YELLOW,
        WIDTH // 2,
        60,
        True
    )

    draw_text(
        "RANK",
        small_font,
        GRAY,
        115,
        115
    )

    draw_text(
        "PLAYER",
        small_font,
        GRAY,
        200,
        115
    )

    draw_text(
        "LEVEL",
        small_font,
        GRAY,
        500,
        115
    )

    draw_text(
        "SCORE",
        small_font,
        GRAY,
        680,
        115
    )

    board = load_leaderboard()

    y = 150

    if not board:

        draw_text(
            "No scores yet",
            font,
            WHITE,
            WIDTH // 2,
            220,
            True
        )

    for index, item in enumerate(
        board[:10]
    ):

        draw_text(
            str(index + 1),
            font,
            YELLOW,
            120,
            y
        )

        draw_text(
            item.get(
                "name",
                "PLAYER"
            ),
            font,
            WHITE,
            200,
            y
        )

        draw_text(
            str(
                item.get(
                    "level",
                    1
                )
            ),
            font,
            CYAN,
            510,
            y
        )

        draw_text(
            str(
                item.get(
                    "score",
                    0
                )
            ),
            font,
            GREEN,
            685,
            y
        )

        y += 38

    back_button = pygame.Rect(
        WIDTH // 2 - 110,
        520,
        220,
        55
    )

    draw_button(
        back_button,
        "BACK",
        BLUE
    )


# ============================================================
# PAUSE SCREEN
# ============================================================

def draw_pause():

    draw_background()

    draw_text(
        "PAUSED",
        title_font,
        WHITE,
        WIDTH // 2,
        135,
        True
    )

    draw_text(
        "Your progress is saved.",
        font,
        CYAN,
        WIDTH // 2,
        195,
        True
    )

    resume_button = pygame.Rect(
        WIDTH // 2 - 140,
        245,
        280,
        60
    )

    menu_button = pygame.Rect(
        WIDTH // 2 - 140,
        325,
        280,
        60
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


# ============================================================
# LEVEL COMPLETE
# ============================================================

def draw_level_complete():

    draw_background()

    draw_text(
        "LEVEL COMPLETE!",
        title_font,
        GREEN,
        WIDTH // 2,
        100,
        True
    )

    draw_text(
        "LEVEL " + str(level),
        big_font,
        YELLOW,
        WIDTH // 2,
        175,
        True
    )

    draw_text(
        "LOCATION COMPLETED",
        font,
        WHITE,
        WIDTH // 2,
        230,
        True
    )

    draw_text(
        current_location(),
        big_font,
        PINK,
        WIDTH // 2,
        280,
        True
    )

    if level < 50:

        draw_text(
            "Next level = new location",
            small_font,
            CYAN,
            WIDTH // 2,
            335,
            True
        )

        next_button = pygame.Rect(
            WIDTH // 2 - 150,
            385,
            300,
            65
        )

        draw_button(
            next_button,
            "NEXT LEVEL",
            CYAN
        )

    else:

        draw_text(
            "YOU BEAT ALL 50 LEVELS!",
            font,
            YELLOW,
            WIDTH // 2,
            365,
            True
        )

        leaderboard_button = pygame.Rect(
            WIDTH // 2 - 150,
            430,
            300,
            60
        )

        draw_button(
            leaderboard_button,
            "LEADERBOARD",
            PURPLE
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
        140,
        True
    )

    draw_text(
        "LEVEL " + str(level),
        big_font,
        WHITE,
        WIDTH // 2,
        215,
        True
    )

    draw_text(
        "SCORE " + str(score),
        font,
        YELLOW,
        WIDTH // 2,
        260,
        True
    )

    retry_button = pygame.Rect(
        WIDTH // 2 - 140,
        320,
        280,
        60
    )

    menu_button = pygame.Rect(
        WIDTH // 2 - 140,
        400,
        280,
        60
    )

    draw_button(
        retry_button,
        "RETRY LEVEL",
        GREEN
    )

    draw_button(
        menu_button,
        "SAVE & MENU",
        BLUE
    )


# ============================================================
# MOUSE POSITION
# ============================================================

def get_game_mouse_position():

    mx, my = pygame.mouse.get_pos()

    current_width, current_height = (
        screen.get_size()
    )

    if current_width <= 0:
        current_width = WIDTH

    if current_height <= 0:
        current_height = HEIGHT

    mx = int(
        mx * WIDTH / current_width
    )

    my = int(
        my * HEIGHT / current_height
    )

    return mx, my


# ============================================================
# MAIN LOOP
# ============================================================

running = True

while running:

    dt = clock.tick(FPS) / 1000.0

    # Prevent huge jumps after lag
    dt = min(
        dt,
        0.05
    )

    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():

        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if event.type == pygame.QUIT:

            save_progress()
            update_leaderboard()

            running = False

        # ----------------------------------------------------
        # KEYBOARD
        # ----------------------------------------------------

        elif event.type == pygame.KEYDOWN:

            # NAME SCREEN
            if game_state == "name":

                if event.key == pygame.K_BACKSPACE:

                    name_text = name_text[:-1]

                elif event.key == pygame.K_RETURN:

                    if name_text.strip():

                        player_name = (
                            name_text.strip()
                        )

                        saved = load_progress()

                        # Continue if same player
                        if (
                            saved
                            and
                            saved.get(
                                "name",
                                ""
                            ).lower()
                            ==
                            player_name.lower()
                        ):

                            continue_saved_game()

                        else:

                            level = 1
                            score = 0
                            lives = 3

                            reset_level()

                            save_progress()

                        update_leaderboard()

                        game_state = "menu"

                else:

                    if len(name_text) < 18:

                        if event.unicode.isprintable():

                            name_text += (
                                event.unicode
                            )

            # PLAYING
            elif game_state == "playing":

                if event.key == pygame.K_SPACE:

                    shoot()

                elif event.key in (
                    pygame.K_p,
                    pygame.K_ESCAPE
                ):

                    save_progress()
                    update_leaderboard()

                    game_state = "paused"

            # PAUSED
            elif game_state == "paused":

                if event.key in (
                    pygame.K_p,
                    pygame.K_ESCAPE
                ):

                    game_state = "playing"

        # ----------------------------------------------------
        # MOUSE DOWN
        # ----------------------------------------------------

        elif event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = (
                get_game_mouse_position()
            )

            # =================================================
            # NAME
            # =================================================

            if game_state == "name":

                continue_button = pygame.Rect(
                    WIDTH // 2 - 135,
                    340,
                    270,
                    62
                )

                if continue_button.collidepoint(
                    mx,
                    my
                ):

                    if name_text.strip():

                        player_name = (
                            name_text.strip()
                        )

                        saved = load_progress()

                        if (
                            saved
                            and
                            saved.get(
                                "name",
                                ""
                            ).lower()
                            ==
                            player_name.lower()
                        ):

                            continue_saved_game()

                        else:

                            level = 1
                            score = 0
                            lives = 3

                            reset_level()

                            save_progress()

                        update_leaderboard()

                        game_state = "menu"

            # =================================================
            # MENU
            # =================================================

            elif game_state == "menu":

                start_button = pygame.Rect(
                    WIDTH // 2 - 145,
                    275,
                    290,
                    60
                )

                leaderboard_button = pygame.Rect(
                    WIDTH // 2 - 145,
                    355,
                    290,
                    60
                )

                exit_button = pygame.Rect(
                    WIDTH // 2 - 145,
                    435,
                    290,
                    60
                )

                if start_button.collidepoint(
                    mx,
                    my
                ):

                    reset_level()

                    game_state = "playing"

                elif leaderboard_button.collidepoint(
                    mx,
                    my
                ):

                    game_state = "leaderboard"

                elif exit_button.collidepoint(
                    mx,
                    my
                ):

                    save_progress()
                    update_leaderboard()

                    running = False

            # =================================================
            # PLAYING
            # =================================================

            elif game_state == "playing":

                if left_button.collidepoint(
                    mx,
                    my
                ):

                    touch_left = True

                elif right_button.collidepoint(
                    mx,
                    my
                ):

                    touch_right = True

                elif fire_button.collidepoint(
                    mx,
                    my
                ):

                    shoot()

                elif pause_button.collidepoint(
                    mx,
                    my
                ):

                    save_progress()
                    update_leaderboard()

                    game_state = "paused"

            # =================================================
            # PAUSED
            # =================================================

            elif game_state == "paused":

                resume_button = pygame.Rect(
                    WIDTH // 2 - 140,
                    245,
                    280,
                    60
                )

                menu_button = pygame.Rect(
                    WIDTH // 2 - 140,
                    325,
                    280,
                    60
                )

                if resume_button.collidepoint(
                    mx,
                    my
                ):

                    game_state = "playing"

                elif menu_button.collidepoint(
                    mx,
                    my
                ):

                    save_progress()
                    update_leaderboard()

                    game_state = "menu"

            # =================================================
            # LEADERBOARD
            # =================================================

            elif game_state == "leaderboard":

                back_button = pygame.Rect(
                    WIDTH // 2 - 110,
                    520,
                    220,
                    55
                )

                if back_button.collidepoint(
                    mx,
                    my
                ):

                    game_state = "menu"

            # =================================================
            # LEVEL COMPLETE
            # =================================================

            elif game_state == "level_complete":

                if level < 50:

                    next_button = pygame.Rect(
                        WIDTH // 2 - 150,
                        385,
                        300,
                        65
                    )

                    if next_button.collidepoint(
                        mx,
                        my
                    ):

                        level += 1

                        lives = 3

                        reset_level()

                        save_progress()
                        update_leaderboard()

                        game_state = "playing"

                else:

                    leaderboard_button = pygame.Rect(
                        WIDTH // 2 - 150,
                        430,
                        300,
                        60
                    )

                    if leaderboard_button.collidepoint(
                        mx,
                        my
                    ):

                        game_state = "leaderboard"

            # =================================================
            # GAME OVER
            # =================================================

            elif game_state == "gameover":

                retry_button = pygame.Rect(
                    WIDTH // 2 - 140,
                    320,
                    280,
                    60
                )

                menu_button = pygame.Rect(
                    WIDTH // 2 - 140,
                    400,
                    280,
                    60
                )

                if retry_button.collidepoint(
                    mx,
                    my
                ):

                    lives = 3

                    reset_level()

                    game_state = "playing"

                elif menu_button.collidepoint(
                    mx,
                    my
                ):

                    save_progress()
                    update_leaderboard()

                    game_state = "menu"

        # ----------------------------------------------------
        # MOUSE UP
        # ----------------------------------------------------

        elif event.type == pygame.MOUSEBUTTONUP:

            touch_left = False
            touch_right = False

    # ========================================================
    # STAR MOVEMENT
    # ========================================================

    update_stars(dt)

    # ========================================================
    # PARTICLES
    # ========================================================

    update_particles(dt)

    # ========================================================
    # GAMEPLAY
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

        moving_left = (
            keys[pygame.K_LEFT]
            or
            keys[pygame.K_a]
            or
            touch_left
        )

        moving_right = (
            keys[pygame.K_RIGHT]
            or
            keys[pygame.K_d]
            or
            touch_right
        )

        if moving_left:

            player.x -= int(
                PLAYER_SPEED * dt
            )

        if moving_right:

            player.x += int(
                PLAYER_SPEED * dt
            )

        # Screen boundaries
        if player.left < 10:

            player.left = 10

        if player.right > WIDTH - 10:

            player.right = WIDTH - 10

        # ----------------------------------------------------
        # MONSTER SPAWN
        # ----------------------------------------------------

        if not hasattr(
            pygame,
            "_monster_spawn_timer"
        ):

            pygame._monster_spawn_timer = 0.0

        pygame._monster_spawn_timer += dt

        if (
            pygame._monster_spawn_timer
            >=
            monster_delay()
            and
            len(monsters)
            <
            maximum_monsters()
        ):

            spawn_monster()

            pygame._monster_spawn_timer = 0.0

        # ----------------------------------------------------
        # BULLETS
        # ----------------------------------------------------

        for bullet in bullets[:]:

            bullet["y"] -= (
                650 * dt
            )

            bullet["x"] += (
                bullet["dx"] * dt
            )

            if (
                bullet["y"] < -30
                or
                bullet["x"] < -50
                or
                bullet["x"] > WIDTH + 50
            ):

                if bullet in bullets:

                    bullets.remove(
                        bullet
                    )

        # ----------------------------------------------------
        # MONSTERS
        # ----------------------------------------------------

        for monster in monsters[:]:

            monster["y"] += (
                monster["speed"] * dt
            )

            size = monster["size"]

            monster_rect = pygame.Rect(
                int(
                    monster["x"] - size
                ),
                int(
                    monster["y"] - size
                ),
                size * 2,
                size * 2
            )

            # Monster hits ship
            if monster_rect.colliderect(
                player
            ):

                if monster in monsters:

                    monsters.remove(
                        monster
                    )

                lives -= 1

                create_explosion(
                    player.centerx,
                    player.centery
                )

                if lives <= 0:

                    lives = 0

                    save_progress()
                    update_leaderboard()

                    game_state = "gameover"

                continue

            # Monster reaches bottom
            if monster["y"] > HEIGHT + 40:

                if monster in monsters:

                    monsters.remove(
                        monster
                    )

                lives -= 1

                if lives <= 0:

                    lives = 0

                    save_progress()
                    update_leaderboard()

                    game_state = "gameover"

        # ----------------------------------------------------
        # BULLET COLLISION
        # ----------------------------------------------------

        for bullet in bullets[:]:

            bullet_rect = pygame.Rect(
                int(
                    bullet["x"] - 3
                ),
                int(
                    bullet["y"]
                ),
                6,
                18
            )

            hit_something = False

            for monster in monsters[:]:

                size = monster["size"]

                monster_rect = pygame.Rect(
                    int(
                        monster["x"] - size
                    ),
                    int(
                        monster["y"] - size
                    ),
                    size * 2,
                    size * 2
                )

                if bullet_rect.colliderect(
                    monster_rect
                ):

                    if bullet in bullets:

                        bullets.remove(
                            bullet
                        )

                    monster["hp"] -= 1

                    score += 5

                    if monster["hp"] <= 0:

                        create_explosion(
                            monster["x"],
                            monster["y"]
                        )

                        if monster in monsters:

                            monsters.remove(
                                monster
                            )

                        score += 5

                    hit_something = True

                    break

            if hit_something:
                continue

        # ----------------------------------------------------
        # SAVE PROGRESS
        # ----------------------------------------------------

        save_progress()
        update_leaderboard()

        # ----------------------------------------------------
        # LEVEL COMPLETE
        # ----------------------------------------------------

        if (
            level_time <= 0
            and
            game_state == "playing"
        ):

            level_time = 0

            bullets.clear()
            monsters.clear()

            # Level completion bonus
            score += 20

            save_progress()
            update_leaderboard()

            game_state = "level_complete"

        # ----------------------------------------------------
        # DRAW GAME
        # ----------------------------------------------------

        draw_background()

        for monster in monsters:

            draw_monster(
                monster
            )

        draw_bullets()

        draw_particles()

        draw_player()

        draw_hud()

        draw_touch_controls()

    # ========================================================
    # NAME
    # ========================================================

    elif game_state == "name":

        draw_name_screen()

    # ========================================================
    # MENU
    # ========================================================

    elif game_state == "menu":

        draw_menu()

    # ========================================================
    # LEADERBOARD
    # ========================================================

    elif game_state == "leaderboard":

        draw_leaderboard()

    # ========================================================
    # PAUSE
    # ========================================================

    elif game_state == "paused":

        draw_pause()

    # ========================================================
    # LEVEL COMPLETE
    # ========================================================

    elif game_state == "level_complete":

        draw_level_complete()

    # ========================================================
    # GAME OVER
    # ========================================================

    elif game_state == "gameover":

        draw_game_over()

    # ========================================================
    # DISPLAY
    # ========================================================

    pygame.display.flip()


# ============================================================
# CLEAN EXIT
# ============================================================

save_progress()
update_leaderboard()
stop_background_music()

pygame.quit()
sys.exit() 