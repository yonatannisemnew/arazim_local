#!/usr/bin/env python3
import pygame
import sys
import os
import subprocess
import signal
import platform

PARENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MANAGER_PATH = os.path.join(PARENT_DIR, "manager", "manager.py")
sys.path.append(PARENT_DIR)
from utils import manager_utils, premissions_stats
import dashboard_utils

if sys.platform != "win32":
    # Tell the OS to automatically reap dead children (Prevent Zombies)
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)


# --- CONFIGURATION ---
class Config:
    SCREEN_SIZE = (600, 300)
    BG_COLOR = (30, 30, 30)
    # Colors
    GREEN = (0, 200, 0)
    RED = (200, 0, 0)
    YELLOW = (255, 200, 0)
    WHITE = (255, 255, 255)
    GRAY = (50, 50, 50)


# --- MODEL: The Business Logic ---
class AppManager:
    def __init__(self):
        self._autorun = False

    def get_status(self):
        running = manager_utils.is_manager_running()
        if not running:
            return "STOPPED"
        is_connected = manager_utils.load_is_connected()
        return "RUNNING" if is_connected else "SLEEPING"

    def open_manager(self):
        manager_dir = os.path.dirname(MANAGER_PATH)

        if sys.platform == "win32":
            kwargs = {"creationflags": subprocess.CREATE_NEW_CONSOLE}
        else:
            kwargs = {"start_new_session": True}

        subprocess.Popen([sys.executable, MANAGER_PATH], cwd=manager_dir, **kwargs)

    def close_manager(self):
        manager_utils.kill_manager()

    def set_autorun(self, active):
        self._autorun = active
        if active:
            dashboard_utils.add_scheduling()
        else:
            dashboard_utils.remove_scheduling()


# --- VIEW: UI Components ---
class Button:
    def __init__(self, text, x, y, w=120, h=80):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = False
        self.font = pygame.font.Font(None, 36)
        self.sub_font = pygame.font.Font(None, 24)

    def draw(self, screen):
        color = Config.GREEN if self.active else Config.RED
        status_text = "ON" if self.active else "OFF"

        # Draw Body and Border
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, Config.WHITE, self.rect, 2, border_radius=12)

        # Draw Label
        lbl_surf = self.font.render(self.text, True, Config.WHITE)
        screen.blit(lbl_surf, lbl_surf.get_rect(center=self.rect.center))

        # Draw Status (On/Off)
        stat_surf = self.sub_font.render(status_text, True, (200, 200, 200))
        screen.blit(
            stat_surf,
            stat_surf.get_rect(midtop=(self.rect.centerx, self.rect.bottom + 5)),
        )

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class StatusDisplay:
    def __init__(self, x, y, w=200, h=80):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = pygame.font.Font(None, 48)
        self.lbl_font = pygame.font.Font(None, 24)

    def draw(self, screen, status_text):
        # Draw Box
        pygame.draw.rect(screen, Config.GRAY, self.rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2, border_radius=8)

        # Determine Text Color
        if status_text == "RUNNING":
            color = Config.GREEN
        elif status_text == "SLEEPING":
            color = Config.YELLOW
        else:
            color = (255, 80, 80)  # Light Red

        # Render Status Text
        text_surf = self.font.render(status_text, True, color)
        screen.blit(text_surf, text_surf.get_rect(center=self.rect.center))

        # Render Label
        lbl_surf = self.lbl_font.render("STATUS", True, (150, 150, 150))
        screen.blit(
            lbl_surf,
            lbl_surf.get_rect(midbottom=(self.rect.centerx, self.rect.top - 5)),
        )


# --- CONTROLLER: The Main App ---
class DashboardApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(Config.SCREEN_SIZE)
        pygame.display.set_caption("Modular Dashboard")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize Components
        self.manager = AppManager()
        self.btn_power = Button("POWER", 50, 100)
        # self.btn_autorun = Button("AUTORUN", 430, 100)
        self.display = StatusDisplay(200, 100)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # 1. Power Logic: Call functions based on intent
                if self.btn_power.is_clicked(event.pos):
                    if self.btn_power.active:
                        self.manager.close_manager()
                    else:
                        self.manager.open_manager()

                # 2. Autorun Logic: Toggle immediately
                """if self.btn_autorun.is_clicked(event.pos):
                    self.btn_autorun.active = not self.btn_autorun.active
                    self.manager.set_autorun(self.btn_autorun.active)"""

    def sync_state(self):
        """Checks Manager state and forces Buttons to match."""
        status = self.manager.get_status()

        # Logic: If stopped, Button is OFF. If Running/Sleeping, Button is ON.
        if status == "STOPPED":
            self.btn_power.active = False
        else:
            self.btn_power.active = True

    def draw(self):
        self.screen.fill(Config.BG_COLOR)

        self.btn_power.draw(self.screen)
        # self.btn_autorun.draw(self.screen)
        self.display.draw(self.screen, self.manager.get_status())

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.sync_state()
            self.draw()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()


# --- ENTRY POINT ---
if __name__ == "__main__":
    premissions_stats.root_check()
    app = DashboardApp()
    app.run()
