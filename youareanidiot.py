# -*- coding: utf-8 -*-
import sys
import time
import math
import os
import random

import vlc

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QMainWindow,
)


# ============================================================
# FILES
# ============================================================

VIDEO_FILE = "you are an idiot!.mp4"
AUDIO_FILE = "you are an idiot!.mp3"

IMAGE_1 = "youareanidiot1.png"
IMAGE_2 = "youareanidiot2.png"


# ============================================================
# GENERAL SETTINGS
# ============================================================

WINDOW_TITLE = "You are an idiot!"

POPUP_WIDTH = 220
POPUP_HEIGHT = 165

UPDATE_INTERVAL_MS = 5


# ============================================================
# 184 BPM
# ============================================================

BPM = 184
BEAT_LENGTH = 60.0 / BPM

PULSE_SCALE = 1.08


# ============================================================
# GROWING WINDOWS
# ============================================================

GROW_SCALE = 1.8


# ============================================================
# MASTER TIMELINE
# ============================================================

TIMELINE_END = 119.884

REPEAT_START = 19.091
REPEAT_END = 25.000

BOUNCE_START = 25.000
BOUNCE_END = 45.100


# ============================================================
# SUBTLE SECTION
# ============================================================

AFTERMATH_START = 47.325
AFTERMATH_END = 69.237

AFTERMATH_PULSE_SCALE = 1.03


# ============================================================
# INTENSE SECTION
#
# 69.237 -> 119.884
#
# Maximum 15 ACTIVE windows.
#
# Instead of creating lots of windows, intensity comes from:
#
# - jitter
# - sudden movement
# - directional changes
# - beat jumps
# - screen-edge bouncing
# - center attacks
# - synchronized movement
# ============================================================

INTENSE_START = 69.237
INTENSE_END = 119.884

INTENSE_MAX_ACTIVE = 15

INTENSE_INITIAL_SPAWN_INTERVAL = 3.4
INTENSE_FINAL_SPAWN_INTERVAL = 2.0


# ============================================================
# AVERAGE WINDOW LIFETIME
# ============================================================

AVERAGE_WINDOW_DURATION = 0.22255


# ============================================================
# CHAOS GENERATOR
# ============================================================

def generate_chaos():

    rng = random.Random(184)

    positions = [
        "top_left",
        "top_middle",
        "top_right",
        "middle_left",
        "middle_right",
        "bottom_left",
        "bottom_middle",
        "bottom_right",
    ]

    chaos = []

    current = REPEAT_START

    while current < REPEAT_END:

        duration = rng.uniform(
            AVERAGE_WINDOW_DURATION * 0.55,
            AVERAGE_WINDOW_DURATION * 1.45
        )

        end = min(
            current + duration,
            REPEAT_END
        )

        position = rng.choice(
            positions
        )

        chaos.append(
            (
                current,
                end,
                position
            )
        )

        gap = rng.uniform(
            0.005,
            0.055
        )

        current = end + gap

    return chaos


# ============================================================
# EXACT GROWING POPUPS
# ============================================================

FIXED_GROWING_POPUPS = [

    (13.941, 14.287, "bottom_left"),

    (14.213, 14.514, "top_left"),
    (14.714, 14.798, "top_right"),

    (15.021, 15.052, "middle_left"),
    (15.099, 15.523, "middle_right"),
    (15.533, 15.784, "bottom_middle"),

    (16.113, 16.256, "bottom_right"),

    (16.435, 16.613, "top_right"),
    (16.495, 16.687, "bottom_left"),

    (16.761, 16.959, "top_middle"),

    (17.118, 17.341, "top_left"),
    (17.450, 17.675, "bottom_right"),
    (17.770, 18.074, "bottom_left"),

    (18.228, 18.372, "top_right"),
    (18.497, 18.749, "bottom_middle"),
    (18.858, 19.091, "top_middle"),
]


# ============================================================
# COMPLETE GROWING TIMELINE
# ============================================================

GROWING_POPUPS = FIXED_GROWING_POPUPS.copy()

GROWING_POPUPS.extend(
    generate_chaos()
)

GROWING_POPUPS.sort(
    key=lambda item: item[0]
)


# ============================================================
# EARLY POPUPS
# ============================================================

EARLY_POPUPS = [

    (2.903, 4.495, "top_left"),

    (3.224, 4.743, "top_middle"),

    (3.426, 5.241, "top_right"),

    (3.884, 5.430, "middle_left"),

    (4.382, 7.752, "middle_right"),
]


# ============================================================
# DVD BOUNCE
# ============================================================

BOUNCE_BPM = 40

BOUNCE_INTERVAL = (
    60.0 / BOUNCE_BPM
)

BOUNCE_WINDOW_COUNT = 15

BOUNCE_SPEED_MIN = 170.0
BOUNCE_SPEED_MAX = 290.0


# ============================================================
# POPUP WINDOW
# ============================================================

class IdiotWindow(QWidget):

    def __init__(
        self,
        popup_id,
        x,
        y,
        start_time,
        end_time,
        animation
    ):

        super().__init__()

        self.popup_id = popup_id

        self.base_x = x
        self.base_y = y

        self.start_time = start_time
        self.end_time = end_time

        self.animation = animation

        self.base_width = POPUP_WIDTH
        self.base_height = POPUP_HEIGHT

        # ----------------------------------------------------
        # BOUNCE
        # ----------------------------------------------------

        self.bounce_x = float(x)
        self.bounce_y = float(y)

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        self.last_bounce_update = None

        # ----------------------------------------------------
        # AFTERMATH
        # ----------------------------------------------------

        self.aftermath_phase_x = 0.0
        self.aftermath_phase_y = 0.0

        self.aftermath_drift_x = 0.0
        self.aftermath_drift_y = 0.0

        # ----------------------------------------------------
        # INTENSE SECTION
        # ----------------------------------------------------

        self.intense_phase = 0.0

        self.intense_phase_2 = 0.0

        self.intense_speed = 1.0

        self.intense_direction_x = 1.0
        self.intense_direction_y = 1.0

        self.intense_target_x = x
        self.intense_target_y = y

        self.intense_target_time = 0.0

        self.intense_jitter = 0.0

        self.intense_rng = random.Random(
            hash(popup_id) & 0xffffffff
        )

        # ----------------------------------------------------
        # IMAGES
        # ----------------------------------------------------

        self.image1 = QPixmap(
            IMAGE_1
        )

        self.image2 = QPixmap(
            IMAGE_2
        )

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.setWindowTitle(
            WINDOW_TITLE
        )

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose
        )

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        self.label = QLabel(
            self
        )

        self.label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.label.setScaledContents(
            True
        )

        self.resize(
            POPUP_WIDTH,
            POPUP_HEIGHT
        )

        self.move(
            x,
            y
        )

        self.set_image(
            self.image1
        )

        self.show()

    # ========================================================
    # IMAGE
    # ========================================================

    def set_image(
        self,
        pixmap
    ):

        if pixmap.isNull():
            return

        self.label.setPixmap(
            pixmap
        )

        self.label.setGeometry(
            0,
            0,
            self.width(),
            self.height()
        )

    # ========================================================
    # IMAGE ANIMATION
    # ========================================================

    def update_image(
        self,
        local_elapsed
    ):

        frame = int(
            local_elapsed
        )

        if frame % 2 == 0:

            self.set_image(
                self.image1
            )

        else:

            self.set_image(
                self.image2
            )

    # ========================================================
    # SCALED GEOMETRY
    # ========================================================

    def set_scaled_geometry(
        self,
        center_x,
        center_y,
        scale
    ):

        width = max(
            1,
            int(
                self.base_width *
                scale
            )
        )

        height = max(
            1,
            int(
                self.base_height *
                scale
            )
        )

        x = int(
            center_x -
            width / 2
        )

        y = int(
            center_y -
            height / 2
        )

        self.setGeometry(
            x,
            y,
            width,
            height
        )

        self.label.setGeometry(
            0,
            0,
            width,
            height
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            WINDOW_TITLE
        )

        self.resize(
            800,
            600
        )

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        self.video_widget = QWidget(
            self
        )

        self.video_widget.setStyleSheet(
            "background-color: black;"
        )

        self.setCentralWidget(
            self.video_widget
        )

        # ----------------------------------------------------
        # VLC
        # ----------------------------------------------------

        self.vlc_instance = vlc.Instance(
            "--no-video-title-show"
        )

        self.video_player = (
            self.vlc_instance.media_player_new()
        )

        self.audio_player = (
            self.vlc_instance.media_player_new()
        )

        # ----------------------------------------------------
        # POPUPS
        # ----------------------------------------------------

        self.popups = {}

        self.popup_counter = 0

        # ----------------------------------------------------
        # DVD
        # ----------------------------------------------------

        self.bounce_popups = []

        self.bounce_spawned = 0

        # ----------------------------------------------------
        # AFTERMATH
        # ----------------------------------------------------

        self.aftermath_rng = random.Random(
            69420
        )

        self.aftermath_next_spawn = (
            AFTERMATH_START
        )

        self.aftermath_spawned = 0

        # ----------------------------------------------------
        # INTENSE SECTION
        # ----------------------------------------------------

        self.intense_rng = random.Random(
            119884
        )

        self.intense_next_spawn = (
            INTENSE_START
        )

        self.intense_spawned = 0

        # ----------------------------------------------------
        # MASTER CLOCK
        # ----------------------------------------------------

        self.start_time = None

        self.running = False

        # ----------------------------------------------------
        # TRACKING
        # ----------------------------------------------------

        self.early_spawned = set()

        self.grow_spawned = set()

        # ----------------------------------------------------
        # TIMER
        # ----------------------------------------------------

        self.timer = QTimer(
            self
        )

        self.timer.setInterval(
            UPDATE_INTERVAL_MS
        )

        self.timer.timeout.connect(
            self.update_scene
        )

    # ========================================================
    # START
    # ========================================================

    def start(self):

        required_files = [
            VIDEO_FILE,
            AUDIO_FILE,
            IMAGE_1,
            IMAGE_2,
        ]

        for filename in required_files:

            if not os.path.exists(
                filename
            ):

                print(
                    f"Missing file: {filename}"
                )

                self.close()

                return

        self.show()

        QApplication.processEvents()

        self.video_player.set_nsobject(
            int(
                self.video_widget.winId()
            )
        )

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        video_media = (
            self.vlc_instance.media_new(
                os.path.abspath(
                    VIDEO_FILE
                )
            )
        )

        self.video_player.set_media(
            video_media
        )

        self.video_player.audio_set_mute(
            True
        )

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        audio_media = (
            self.vlc_instance.media_new(
                os.path.abspath(
                    AUDIO_FILE
                )
            )
        )

        self.audio_player.set_media(
            audio_media
        )

        # ----------------------------------------------------
        # CLOCK
        # ----------------------------------------------------

        self.start_time = time.monotonic()

        self.running = True

        self.video_player.play()
        self.audio_player.play()

        self.timer.start()

    # ========================================================
    # ELAPSED
    # ========================================================

    def elapsed(self):

        if self.start_time is None:
            return 0.0

        return (
            time.monotonic()
            -
            self.start_time
        )

    # ========================================================
    # SCREEN POSITIONS
    # ========================================================

    def positions(self):

        screen = (
            QApplication.primaryScreen()
        )

        if screen is None:
            return {}

        geometry = (
            screen.availableGeometry()
        )

        left = geometry.left()
        top = geometry.top()

        width = geometry.width()
        height = geometry.height()

        margin = 30

        center_x = (
            left +
            width // 2
        )

        center_y = (
            top +
            height // 2
        )

        return {

            "top_left": (
                left + margin,
                top + margin
            ),

            "top_middle": (
                center_x -
                POPUP_WIDTH // 2,
                top + margin
            ),

            "top_right": (
                left +
                width -
                POPUP_WIDTH -
                margin,
                top + margin
            ),

            "middle_left": (
                left + margin,
                center_y -
                POPUP_HEIGHT // 2
            ),

            "middle_right": (
                left +
                width -
                POPUP_WIDTH -
                margin,
                center_y -
                POPUP_HEIGHT // 2
            ),

            "bottom_left": (
                left + margin,
                top +
                height -
                POPUP_HEIGHT -
                margin
            ),

            "bottom_middle": (
                center_x -
                POPUP_WIDTH // 2,
                top +
                height -
                POPUP_HEIGHT -
                margin
            ),

            "bottom_right": (
                left +
                width -
                POPUP_WIDTH -
                margin,
                top +
                height -
                POPUP_HEIGHT -
                margin
            ),
        }

    # ========================================================
    # MAIN PULSE
    # ========================================================

    def pulse_scale(
        self,
        elapsed
    ):

        beat = int(
            elapsed /
            BEAT_LENGTH
        )

        if beat % 2 == 0:
            return PULSE_SCALE

        return 1.0

    # ========================================================
    # INTENSE PULSE
    # ========================================================

    def intense_pulse(
        self,
        elapsed
    ):

        progress = (
            elapsed -
            INTENSE_START
        ) / (
            INTENSE_END -
            INTENSE_START
        )

        progress = max(
            0.0,
            min(
                1.0,
                progress
            )
        )

        strength = (
            0.015 +
            progress * 0.055
        )

        beat = int(
            elapsed /
            BEAT_LENGTH
        )

        if beat % 2 == 0:
            return 1.0 + strength

        return 1.0

    # ========================================================
    # CREATE POPUP
    # ========================================================

    def create_popup(
        self,
        position_name,
        start_time,
        end_time,
        animation
    ):

        positions = self.positions()

        if position_name not in positions:
            return None

        x, y = positions[
            position_name
        ]

        self.popup_counter += 1

        popup_id = (
            f"popup_{self.popup_counter}"
        )

        popup = IdiotWindow(
            popup_id,
            x,
            y,
            start_time,
            end_time,
            animation
        )

        self.popups[
            popup_id
        ] = popup

        return popup

    # ========================================================
    # DVD POPUP
    # ========================================================

    def create_bouncing_popup(
        self,
        index,
        elapsed
    ):

        screen = (
            QApplication.primaryScreen()
        )

        if screen is None:
            return

        geometry = (
            screen.availableGeometry()
        )

        left = geometry.left()
        top = geometry.top()

        screen_width = geometry.width()
        screen_height = geometry.height()

        rng = random.Random(
            5000 + index
        )

        usable_width = max(
            1,
            screen_width -
            POPUP_WIDTH
        )

        usable_height = max(
            1,
            screen_height -
            POPUP_HEIGHT
        )

        x = (
            left +
            rng.uniform(
                0,
                usable_width
            )
        )

        y = (
            top +
            rng.uniform(
                0,
                usable_height
            )
        )

        speed = rng.uniform(
            BOUNCE_SPEED_MIN,
            BOUNCE_SPEED_MAX
        )

        angle = rng.uniform(
            math.radians(25),
            math.radians(65)
        )

        vx = (
            math.cos(angle) *
            speed *
            rng.choice(
                [-1, 1]
            )
        )

        vy = (
            math.sin(angle) *
            speed *
            rng.choice(
                [-1, 1]
            )
        )

        popup = IdiotWindow(
            f"bounce_{index + 1}",
            int(x),
            int(y),
            elapsed,
            BOUNCE_END,
            "bounce"
        )

        popup.bounce_x = x
        popup.bounce_y = y

        popup.velocity_x = vx
        popup.velocity_y = vy

        popup.last_bounce_update = (
            time.monotonic()
        )

        self.popups[
            popup.popup_id
        ] = popup

        self.bounce_popups.append(
            popup.popup_id
        )

    # ========================================================
    # AFTERMATH POPUP
    # ========================================================

    def create_aftermath_popup(
        self,
        elapsed
    ):

        screen = (
            QApplication.primaryScreen()
        )

        if screen is None:
            return

        geometry = (
            screen.availableGeometry()
        )

        left = geometry.left()
        top = geometry.top()

        width = geometry.width()
        height = geometry.height()

        margin = 40

        x = (
            left +
            margin +
            self.aftermath_rng.uniform(
                0,
                max(
                    1,
                    width -
                    POPUP_WIDTH -
                    margin * 2
                )
            )
        )

        y = (
            top +
            margin +
            self.aftermath_rng.uniform(
                0,
                max(
                    1,
                    height -
                    POPUP_HEIGHT -
                    margin * 2
                )
            )
        )

        self.popup_counter += 1

        popup_id = (
            f"aftermath_{self.popup_counter}"
        )

        lifetime = self.aftermath_rng.uniform(
            2.0,
            4.0
        )

        popup = IdiotWindow(
            popup_id,
            int(x),
            int(y),
            elapsed,
            min(
                elapsed +
                lifetime,
                AFTERMATH_END
            ),
            "aftermath"
        )

        popup.base_x = x
        popup.base_y = y

        popup.aftermath_phase_x = (
            self.aftermath_rng.uniform(
                0,
                math.pi * 2
            )
        )

        popup.aftermath_phase_y = (
            self.aftermath_rng.uniform(
                0,
                math.pi * 2
            )
        )

        popup.aftermath_drift_x = (
            self.aftermath_rng.uniform(
                5,
                15
            )
        )

        popup.aftermath_drift_y = (
            self.aftermath_rng.uniform(
                5,
                12
            )
        )

        self.popups[
            popup.popup_id
        ] = popup

    # ========================================================
    # INTENSE POPUP
    # ========================================================

    def create_intense_popup(
        self,
        elapsed
    ):

        screen = (
            QApplication.primaryScreen()
        )

        if screen is None:
            return None

        geometry = (
            screen.availableGeometry()
        )

        left = geometry.left()
        top = geometry.top()

        width = geometry.width()
        height = geometry.height()

        margin = 30

        usable_width = max(
            1,
            width -
            POPUP_WIDTH -
            margin * 2
        )

        usable_height = max(
            1,
            height -
            POPUP_HEIGHT -
            margin * 2
        )

        x = (
            left +
            margin +
            self.intense_rng.uniform(
                0,
                usable_width
            )
        )

        y = (
            top +
            margin +
            self.intense_rng.uniform(
                0,
                usable_height
            )
        )

        self.popup_counter += 1

        popup_id = (
            f"intense_{self.popup_counter}"
        )

        popup = IdiotWindow(
            popup_id,
            int(x),
            int(y),
            elapsed,
            INTENSE_END,
            "intense"
        )

        popup.base_x = x
        popup.base_y = y

        popup.intense_phase = (
            self.intense_rng.uniform(
                0,
                math.pi * 2
            )
        )

        popup.intense_phase_2 = (
            self.intense_rng.uniform(
                0,
                math.pi * 2
            )
        )

        popup.intense_speed = (
            self.intense_rng.uniform(
                0.7,
                1.3
            )
        )

        popup.intense_direction_x = (
            self.intense_rng.choice(
                [-1, 1]
            )
        )

        popup.intense_direction_y = (
            self.intense_rng.choice(
                [-1, 1]
            )
        )

        popup.intense_target_x = x
        popup.intense_target_y = y

        popup.intense_target_time = (
            elapsed +
            self.intense_rng.uniform(
                0.5,
                1.5
            )
        )

        self.popups[
            popup.popup_id
        ] = popup

        return popup

    # ========================================================
    # REMOVE
    # ========================================================

    def remove_popup(
        self,
        popup_id
    ):

        popup = self.popups.pop(
            popup_id,
            None
        )

        if popup is not None:

            if popup_id in self.bounce_popups:

                self.bounce_popups.remove(
                    popup_id
                )

            popup.close()
            popup.deleteLater()

    # ========================================================
    # SPAWN
    # ========================================================

    def spawn_due_popups(
        self,
        elapsed
    ):

        # ----------------------------------------------------
        # EARLY
        # ----------------------------------------------------

        for index, (
            start,
            end,
            position
        ) in enumerate(
            EARLY_POPUPS
        ):

            if index in self.early_spawned:
                continue

            if elapsed >= start:

                animation = "normal"

                if (
                    position ==
                    "middle_right"
                    and
                    start == 4.382
                ):

                    animation = "spiral"

                self.create_popup(
                    position,
                    start,
                    end,
                    animation
                )

                self.early_spawned.add(
                    index
                )

        # ----------------------------------------------------
        # GROWING
        # ----------------------------------------------------

        for index, (
            start,
            end,
            position
        ) in enumerate(
            GROWING_POPUPS
        ):

            if index in self.grow_spawned:
                continue

            if elapsed >= start:

                self.create_popup(
                    position,
                    start,
                    end,
                    "grow"
                )

                self.grow_spawned.add(
                    index
                )

        # ----------------------------------------------------
        # DVD
        # ----------------------------------------------------

        if (
            elapsed >= BOUNCE_START
            and
            self.bounce_spawned <
            BOUNCE_WINDOW_COUNT
        ):

            normal_index = int(
                (
                    elapsed -
                    BOUNCE_START
                ) /
                BOUNCE_INTERVAL
            )

            target_index = min(
                normal_index,
                BOUNCE_WINDOW_COUNT - 1
            )

            while (
                self.bounce_spawned <=
                target_index
                and
                self.bounce_spawned <
                BOUNCE_WINDOW_COUNT
            ):

                index = self.bounce_spawned

                if index < 14:

                    spawn_time = (
                        BOUNCE_START +
                        index *
                        BOUNCE_INTERVAL
                    )

                else:

                    spawn_time = (
                        BOUNCE_END -
                        0.001
                    )

                if elapsed >= spawn_time:

                    self.create_bouncing_popup(
                        index,
                        elapsed
                    )

                    self.bounce_spawned += 1

                else:

                    break

        # ----------------------------------------------------
        # AFTERMATH
        # ----------------------------------------------------

        if (
            elapsed >= AFTERMATH_START
            and
            elapsed < AFTERMATH_END
        ):

            progress = (
                elapsed -
                AFTERMATH_START
            ) / (
                AFTERMATH_END -
                AFTERMATH_START
            )

            progress = max(
                0.0,
                min(
                    1.0,
                    progress
                )
            )

            interval = (
                3.8 -
                1.8 *
                progress
            )

            while (
                elapsed >=
                self.aftermath_next_spawn
            ):

                self.create_aftermath_popup(
                    elapsed
                )

                self.aftermath_spawned += 1

                self.aftermath_next_spawn += (
                    interval +
                    self.aftermath_rng.uniform(
                        -0.45,
                        0.55
                    )
                )

                if (
                    self.aftermath_spawned >
                    40
                ):
                    break

        # ----------------------------------------------------
        # INTENSE SECTION
        # ----------------------------------------------------

        if (
            elapsed >= INTENSE_START
            and
            elapsed < INTENSE_END
        ):

            progress = (
                elapsed -
                INTENSE_START
            ) / (
                INTENSE_END -
                INTENSE_START
            )

            progress = max(
                0.0,
                min(
                    1.0,
                    progress
                )
            )

            interval = (
                INTENSE_INITIAL_SPAWN_INTERVAL
                -
                (
                    INTENSE_INITIAL_SPAWN_INTERVAL
                    -
                    INTENSE_FINAL_SPAWN_INTERVAL
                )
                *
                progress
            )

            active_intense = sum(
                1
                for popup in self.popups.values()
                if popup.animation == "intense"
            )

            while (
                elapsed >=
                self.intense_next_spawn
                and
                active_intense <
                INTENSE_MAX_ACTIVE
            ):

                popup = self.create_intense_popup(
                    elapsed
                )

                if popup is not None:

                    active_intense += 1

                    self.intense_spawned += 1

                self.intense_next_spawn += (
                    interval +
                    self.intense_rng.uniform(
                        -0.35,
                        0.45
                    )
                )

                if (
                    self.intense_spawned >=
                    INTENSE_MAX_ACTIVE
                ):
                    break

    # ========================================================
    # NORMAL UPDATE
    # ========================================================

    def update_normal_popup(
        self,
        popup,
        elapsed
    ):

        scale = self.pulse_scale(
            elapsed
        )

        center_x = (
            popup.base_x +
            POPUP_WIDTH / 2
        )

        center_y = (
            popup.base_y +
            POPUP_HEIGHT / 2
        )

        popup.set_scaled_geometry(
            center_x,
            center_y,
            scale
        )

    # ========================================================
    # GROW UPDATE
    # ========================================================

    def update_growing_popup(
        self,
        popup,
        elapsed
    ):

        duration = (
            popup.end_time -
            popup.start_time
        )

        progress = (
            elapsed -
            popup.start_time
        ) / duration

        progress = max(
            0.0,
            min(
                1.0,
                progress
            )
        )

        eased = (
            progress *
            progress *
            (
                3.0 -
                2.0 *
                progress
            )
        )

        scale = (
            1.0 +
            (
                GROW_SCALE -
                1.0
            ) *
            eased
        )

        scale *= self.pulse_scale(
            elapsed
        )

        center_x = (
            popup.base_x +
            POPUP_WIDTH / 2
        )

        center_y = (
            popup.base_y +
            POPUP_HEIGHT / 2
        )

        popup.set_scaled_geometry(
            center_x,
            center_y,
            scale
        )

    # ========================================================
    # SPIRAL
    # ========================================================

    def update_spiral_popup(
        self,
        popup,
        elapsed
    ):

        start = 5.491
        end = 7.752

        progress = (
            elapsed -
            start
        ) / (
            end -
            start
        )

        progress = max(
            0.0,
            min(
                1.0,
                progress
            )
        )

        eased = (
            progress *
            progress *
            (
                3.0 -
                2.0 *
                progress
            )
        )

        main_center = (
            self.geometry().center()
        )

        target_x = main_center.x()
        target_y = main_center.y()

        start_x = (
            popup.base_x +
            POPUP_WIDTH / 2
        )

        start_y = (
            popup.base_y +
            POPUP_HEIGHT / 2
        )

        radius_x = (
            abs(
                start_x -
                target_x
            ) *
            (
                1.0 -
                eased
            )
        )

        radius_y = (
            abs(
                start_y -
                target_y
            ) *
            (
                1.0 -
                eased
            )
        )

        angle = (
            eased *
            math.pi *
            4.0
        )

        center_x = (
            target_x +
            math.cos(angle) *
            radius_x
        )

        center_y = (
            target_y +
            math.sin(angle) *
            radius_y
        )

        scale = (
            1.0 -
            0.85 *
            eased
        )

        scale *= self.pulse_scale(
            elapsed
        )

        popup.set_scaled_geometry(
            center_x,
            center_y,
            scale
        )

    # ========================================================
    # DVD BOUNCE
    # ========================================================

    def update_bounce_popup(
        self,
        popup,
        elapsed
    ):

        now = time.monotonic()

        if popup.last_bounce_update is None:

            popup.last_bounce_update = now

            return

        dt = (
            now -
            popup.last_bounce_update
        )

        popup.last_bounce_update = now

        dt = min(
            dt,
            0.05
        )

        screen = (
            QApplication.primaryScreen()
        )

        if screen is None:
            return

        geometry = (
            screen.availableGeometry()
        )

        left = geometry.left()
        top = geometry.top()

        scale = self.pulse_scale(
            elapsed
        )

        width = int(
            POPUP_WIDTH *
            scale
        )

        height = int(
            POPUP_HEIGHT *
            scale
        )

        right = (
            geometry.left() +
            geometry.width() -
            width
        )

        bottom = (
            geometry.top() +
            geometry.height() -
            height
        )

        popup.bounce_x += (
            popup.velocity_x *
            dt
        )

        popup.bounce_y += (
            popup.velocity_y *
            dt
        )

        if popup.bounce_x <= left:

            popup.bounce_x = left

            popup.velocity_x = abs(
                popup.velocity_x
            )

        elif popup.bounce_x >= right:

            popup.bounce_x = right

            popup.velocity_x = -abs(
                popup.velocity_x
            )

        if popup.bounce_y <= top:

            popup.bounce_y = top

            popup.velocity_y = abs(
                popup.velocity_y
            )

        elif popup.bounce_y >= bottom:

            popup.bounce_y = bottom

            popup.velocity_y = -abs(
                popup.velocity_y
            )

        center_x = (
            popup.bounce_x +
            width / 2
        )

        center_y = (
            popup.bounce_y +
            height / 2
        )

        popup.set_scaled_geometry(
            center_x,
            center_y,
            scale
        )

    # ========================================================
    # AFTERMATH UPDATE
    # ========================================================

    def update_aftermath_popup(
        self,
        popup,
        elapsed
    ):

        local_elapsed = (
            elapsed -
            popup.start_time
        )

        drift_x = (
            math.sin(
                local_elapsed *
                0.65 +
                popup.aftermath_phase_x
            ) *
            popup.aftermath_drift_x
        )

        drift_y = (
            math.sin(
                local_elapsed *
                0.52 +
                popup.aftermath_phase_y
            ) *
            popup.aftermath_drift_y
        )

        scale = (
            1.0
            if int(
                elapsed /
                BEAT_LENGTH
            ) % 2
            else 1.03
        )

        center_x = (
            popup.base_x +
            POPUP_WIDTH / 2 +
            drift_x
        )

        center_y = (
            popup.base_y +
            POPUP_HEIGHT / 2 +
            drift_y
        )

        popup.set_scaled_geometry(
            center_x,
            center_y,
            scale
        )

    # ========================================================
    # INTENSE UPDATE
    # ========================================================

    def update_intense_popup(
        self,
        popup,
        elapsed
    ):

        screen = (
            QApplication.primaryScreen()
        )

        if screen is None:
            return

        geometry = (
            screen.availableGeometry()
        )

        left = geometry.left()
        top = geometry.top()

        width = geometry.width()
        height = geometry.height()

        screen_center_x = (
            left +
            width / 2
        )

        screen_center_y = (
            top +
            height / 2
        )

        local = (
            elapsed -
            INTENSE_START
        )

        progress = (
            elapsed -
            INTENSE_START
        ) / (
            INTENSE_END -
            INTENSE_START
        )

        progress = max(
            0.0,
            min(
                1.0,
                progress
            )
        )

        # ----------------------------------------------------
        # Increasing movement speed
        # ----------------------------------------------------

        speed_multiplier = (
            0.7 +
            progress * 2.8
        )

        # ----------------------------------------------------
        # Base chaotic movement
        # ----------------------------------------------------

        wave_x = (
            math.sin(
                local *
                1.1 *
                popup.intense_speed +
                popup.intense_phase
            )
        )

        wave_y = (
            math.cos(
                local *
                0.87 *
                popup.intense_speed +
                popup.intense_phase_2
            )
        )

        drift_x = (
            wave_x *
            80.0 *
            speed_multiplier
        )

        drift_y = (
            wave_y *
            60.0 *
            speed_multiplier
        )

        # ----------------------------------------------------
        # Faster wobble
        # ----------------------------------------------------

        wobble_x = (
            math.sin(
                local *
                5.0 *
                speed_multiplier +
                popup.intense_phase_2
            )
            *
            (
                5.0 +
                progress * 18.0
            )
        )

        wobble_y = (
            math.cos(
                local *
                4.2 *
                speed_multiplier +
                popup.intense_phase
            )
            *
            (
                5.0 +
                progress * 15.0
            )
        )

        # ----------------------------------------------------
        # Beat hit
        # ----------------------------------------------------

        beat = int(
            elapsed /
            BEAT_LENGTH
        )

        beat_time = (
            elapsed %
            BEAT_LENGTH
        )

        beat_strength = max(
            0.0,
            1.0 -
            beat_time /
            0.055
        )

        beat_jump = (
            20.0 +
            progress * 65.0
        )

        if beat % 2 == 0:

            drift_x += (
                popup.intense_direction_x *
                beat_jump *
                beat_strength
            )

            drift_y += (
                popup.intense_direction_y *
                beat_jump *
                0.55 *
                beat_strength
            )

        # ----------------------------------------------------
        # Random target repositioning
        # ----------------------------------------------------

        if elapsed >= popup.intense_target_time:

            popup.intense_target_x = (
                left +
                self.intense_rng.uniform(
                    0,
                    max(
                        1,
                        width -
                        POPUP_WIDTH
                    )
                )
            )

            popup.intense_target_y = (
                top +
                self.intense_rng.uniform(
                    0,
                    max(
                        1,
                        height -
                        POPUP_HEIGHT
                    )
                )
            )

            popup.intense_target_time = (
                elapsed +
                self.intense_rng.uniform(
                    0.25,
                    0.8
                ) /
                (
                    0.7 +
                    progress * 1.5
                )
            )

        # ----------------------------------------------------
        # Pull toward target
        # ----------------------------------------------------

        target_strength = (
            0.025 +
            progress * 0.13
        )

        target_x = (
            popup.intense_target_x +
            POPUP_WIDTH / 2
        )

        target_y = (
            popup.intense_target_y +
            POPUP_HEIGHT / 2
        )

        base_center_x = (
            popup.base_x +
            POPUP_WIDTH / 2
        )

        base_center_y = (
            popup.base_y +
            POPUP_HEIGHT / 2
        )

        target_offset_x = (
            target_x -
            base_center_x
        )

        target_offset_y = (
            target_y -
            base_center_y
        )

        center_x = (
            base_center_x
            +
            target_offset_x *
            target_strength
            +
            drift_x
            +
            wobble_x
        )

        center_y = (
            base_center_y
            +
            target_offset_y *
            target_strength
            +
            drift_y
            +
            wobble_y
        )

        # ----------------------------------------------------
        # 85-second violent synchronized movement
        # ----------------------------------------------------

        if (
            elapsed >= 85.0
            and
            elapsed < 86.0
        ):

            p = (
                elapsed -
                85.0
            )

            if p < 0.25:

                amount = p / 0.25

                center_x = (
                    base_center_x *
                    (1.0 - amount)
                    +
                    screen_center_x *
                    amount
                )

                center_y = (
                    base_center_y *
                    (1.0 - amount)
                    +
                    screen_center_y *
                    amount
                )

            elif p < 0.5:

                amount = (
                    p -
                    0.25
                ) / 0.25

                center_x = (
                    screen_center_x
                    +
                    (
                        base_center_x -
                        screen_center_x
                    )
                    *
                    amount *
                    2.2
                )

                center_y = (
                    screen_center_y
                    +
                    (
                        base_center_y -
                        screen_center_y
                    )
                    *
                    amount *
                    2.2
                )

        # ----------------------------------------------------
        # Final acceleration
        # ----------------------------------------------------

        if elapsed >= 108.0:

            final_progress = (
                elapsed -
                108.0
            ) / (
                INTENSE_END -
                108.0
            )

            final_progress = max(
                0.0,
                min(
                    1.0,
                    final_progress
                )
            )

            center_x += (
                math.sin(
                    local *
                    7.0
                )
                *
                20.0
                *
                final_progress
            )

            center_y += (
                math.cos(
                    local *
                    6.5
                )
                *
                20.0
                *
                final_progress
            )

        # ----------------------------------------------------
        # Pulse
        # ----------------------------------------------------

        scale = self.intense_pulse(
            elapsed
        )

        popup.set_scaled_geometry(
            center_x,
            center_y,
            scale
        )

    # ========================================================
    # MAIN UPDATE
    # ========================================================

    def update_scene(self):

        if not self.running:
            return

        elapsed = self.elapsed()

        # ----------------------------------------------------
        # SPAWN
        # ----------------------------------------------------

        self.spawn_due_popups(
            elapsed
        )

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        for popup_id, popup in list(
            self.popups.items()
        ):

            if elapsed >= popup.end_time:

                self.remove_popup(
                    popup_id
                )

                continue

            local_elapsed = (
                elapsed -
                popup.start_time
            )

            popup.update_image(
                local_elapsed
            )

            if popup.animation == "normal":

                self.update_normal_popup(
                    popup,
                    elapsed
                )

            elif popup.animation == "grow":

                self.update_growing_popup(
                    popup,
                    elapsed
                )

            elif popup.animation == "spiral":

                if elapsed < 5.491:

                    self.update_normal_popup(
                        popup,
                        elapsed
                    )

                else:

                    self.update_spiral_popup(
                        popup,
                        elapsed
                    )

            elif popup.animation == "bounce":

                self.update_bounce_popup(
                    popup,
                    elapsed
                )

            elif popup.animation == "aftermath":

                self.update_aftermath_popup(
                    popup,
                    elapsed
                )

            elif popup.animation == "intense":

                self.update_intense_popup(
                    popup,
                    elapsed
                )

        # ----------------------------------------------------
        # END
        # ----------------------------------------------------

        if elapsed >= TIMELINE_END:

            self.timer.stop()

            for popup_id in list(
                self.popups.keys()
            ):

                self.remove_popup(
                    popup_id
                )

            self.running = False

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        self.running = False

        if self.timer.isActive():
            self.timer.stop()

        for popup_id in list(
            self.popups.keys()
        ):

            self.remove_popup(
                popup_id
            )

        try:
            self.video_player.stop()
        except Exception:
            pass

        try:
            self.audio_player.stop()
        except Exception:
            pass

        event.accept()


# ============================================================
# RUN
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        WINDOW_TITLE
    )

    window = MainWindow()

    window.start()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()