import pygame
import random

# --- CONSTANTS CONFIGURATION ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BG_COLOR = (20, 20, 20)
TILE_SIZE = 32 # Size of one wall block
MAP_WIDTH = 50 # The map is 50x50 tiles
MAP_HEIGHT = 50

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Roguelike Experiments Window")
clock = pygame.time.Clock()

# --- ASSETS ---
def create_texture(color, size):
    surf = pygame.Surface((size, size))
    surf.fill(color)
    # noise added to be more realistic
    for _ in range(10):
        x, y = random.randint(0, size-1), random.randint(0, size-1)
        shade = random.randint(-20, 20)
        r, g, b = color
        new_c = (max(0, min(255, r+shade)), max(0, min(255, g+shade)), max(0, min(255, b+shade)))
        surf.set_at((x, y), new_c)
    return surf

wall_img = create_texture((100, 100, 110), TILE_SIZE)  # Grey Wall
floor_img = create_texture((40, 30, 30), TILE_SIZE)    # Dark Brown Floor

# --- MAP GENERATOR ---
class MapGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [] # 0 = Floor, 1 = Wall

    def generate(self):
        # random change to be a wall
        self.grid = [[1 if random.random() < 0.45 else 0 for _ in range(self.width)] for _ in range(self.height)]
        
        # noise smothing
        for _ in range(5):
            self.smooth_map()
            
        return self.grid

    def smooth_map(self):
        new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self.get_wall_count(x, y)
                
                # THE RULES:
                # If I have more than 4 wall neighbors, I become a wall (clumping)
                # If I have less, I become floor (opening space)
                if neighbors > 4:
                    new_grid[y][x] = 1
                elif neighbors < 4:
                    new_grid[y][x] = 0
                else:
                    new_grid[y][x] = self.grid[y][x] # no changes
        
        self.grid = new_grid

    def get_wall_count(self, x, y):
        count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0: continue
                nx, ny = x + dx, y + dy
                # Check boundaries
                if nx < 0 or ny < 0 or nx >= self.width or ny >= self.height:
                    count += 1
                elif self.grid[ny][nx] == 1:
                    count += 1
        return count

# --- SPRITE GENERATOR ---
def generate_creature_surface(color, size):
    w, h = 8, 8
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        for x in range(w // 2):
            if random.random() > 0.5:
                surface.set_at((x, y), color)
                surface.set_at((w - 1 - x, y), color)
    return pygame.transform.scale(surface, (size, size))

# --- SETUP ---
map_gen = MapGenerator(MAP_WIDTH, MAP_HEIGHT)
game_map = map_gen.generate()

# Player
player_data = {
    "x": 0, "y": 0, # initial value
    "size": 24, # smaller than tile
    "speed": 4,
    "image": generate_creature_surface((0, 255, 100), 24),
    "rect": None
}

# Basic spawn checking. WIP Sometimes fail
spawn_found = False
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        if game_map[y][x] == 0:
            player_data["x"] = x * TILE_SIZE + 4
            player_data["y"] = y * TILE_SIZE + 4
            spawn_found = True
            break
    if spawn_found: break

# --- GAME LOOP ---
running = True
camera_x, camera_y = 0, 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                game_map = map_gen.generate()
                for y in range(MAP_HEIGHT):
                    for x in range(MAP_WIDTH):
                        if game_map[y][x] == 0:
                            player_data["x"] = x * TILE_SIZE + 4
                            player_data["y"] = y * TILE_SIZE + 4
                            break
                    break

    # --- PHYSICS & MOVEMENT ---
    dx, dy = 0, 0
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  dx = -player_data["speed"]
    if keys[pygame.K_RIGHT]: dx = player_data["speed"]
    if keys[pygame.K_UP]:    dy = -player_data["speed"]
    if keys[pygame.K_DOWN]:  dy = player_data["speed"]

    # Collision Prediction
    new_x = player_data["x"] + dx
    new_y = player_data["y"] + dy
    
    player_rect = pygame.Rect(new_x, new_y, player_data["size"], player_data["size"])
    
    collision = False

    # Check nearby tiles only (optimization)
    grid_x = int(new_x // TILE_SIZE)
    grid_y = int(new_y // TILE_SIZE)
    
    for cy in range(grid_y - 1, grid_y + 2):
        for cx in range(grid_x - 1, grid_x + 2):
            if 0 <= cx < MAP_WIDTH and 0 <= cy < MAP_HEIGHT:
                if game_map[cy][cx] == 1: # Wall
                    wall_rect = pygame.Rect(cx * TILE_SIZE, cy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if player_rect.colliderect(wall_rect):
                        collision = True

    if not collision:
        player_data["x"] = new_x
        player_data["y"] = new_y

    # --- CAMERA LOGIC ---
    # Keep player in center of screen
    target_cam_x = player_data["x"] - SCREEN_WIDTH // 2
    target_cam_y = player_data["y"] - SCREEN_HEIGHT // 2
    
    camera_x += (target_cam_x - camera_x) * 0.1
    camera_y += (target_cam_y - camera_y) * 0.1

    # --- DRAW ---
    screen.fill(BG_COLOR)

    # Calculate which tiles are visible (Optimization)
    start_col = int(camera_x // TILE_SIZE)
    end_col = start_col + (SCREEN_WIDTH // TILE_SIZE) + 2
    start_row = int(camera_y // TILE_SIZE)
    end_row = start_row + (SCREEN_HEIGHT // TILE_SIZE) + 2

    for y in range(max(0, start_row), min(MAP_HEIGHT, end_row)):
        for x in range(max(0, start_col), min(MAP_WIDTH, end_col)):
            draw_x = x * TILE_SIZE - camera_x
            draw_y = y * TILE_SIZE - camera_y
            
            if game_map[y][x] == 1:
                screen.blit(wall_img, (draw_x, draw_y))
            else:
                screen.blit(floor_img, (draw_x, draw_y))

    # Draw Player
    screen.blit(player_data["image"], (player_data["x"] - camera_x, player_data["y"] - camera_y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()