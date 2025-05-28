import pygame
import random
import math
import json
import subprocess
import numpy as np
from collections import defaultdict

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WORLD_WIDTH = SCREEN_WIDTH * 3
WORLD_HEIGHT = SCREEN_HEIGHT * 3
NUM_BALLS = 50
NUM_BOUNDARIES = 40
BALL_RADIUS = 10
MAX_VELOCITY = 5
FPS = 60
GRID_SIZE = 200
ASPECT_RATIO_THRESHOLD = 2.5  # avoid near-squares
DEBUG = False

SAVE_TARGET = "./footage/output.mp4"

print("Loading data from cache...")
with open("./cached_data/cache_5.json", "r") as f:
    data = json.load(f)
print("Data loaded.")
segments = data["segments"]
current_id = 0
segment_count = len(segments)

print("Recording started!")

pygame.init()
ffmpeg_cmd = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-pix_fmt", "rgb24",
    "-s", f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}",
    "-r", str(FPS),
    "-i", "-",
    "-an",
    "-vcodec", "libx264",
    "-pix_fmt", "yuv420p",
    SAVE_TARGET
]

ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("physics simulation")
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
BLACK = (0, 0, 0)
GREEN = (192, 255, 192)

def create_skewed_rect():
    for _ in range(100):
        w = random.randint(50, 150)
        h = random.randint(50, 150)
        aspect = max(w / h, h / w)
        if aspect >= ASPECT_RATIO_THRESHOLD:
            x = random.randint(0, WORLD_WIDTH - w)
            y = random.randint(0, WORLD_HEIGHT - h)
            return pygame.Rect(x, y, w, h)
    return None

boundaries = []
for _ in range(NUM_BOUNDARIES):
    for _ in range(100):
        r = create_skewed_rect()
        if r and not any(r.colliderect(b) for b in boundaries):
            boundaries.append(r)
            break

def build_spatial_grid(boundaries):
    grid = defaultdict(list)
    for b in boundaries:
        min_cell_x = b.left // GRID_SIZE
        max_cell_x = b.right // GRID_SIZE
        min_cell_y = b.top // GRID_SIZE
        max_cell_y = b.bottom // GRID_SIZE
        for i in range(min_cell_x, max_cell_x + 1):
            for j in range(min_cell_y, max_cell_y + 1):
                grid[(i, j)].append(b)
    return grid

spatial_grid = build_spatial_grid(boundaries)

def get_nearby_boundaries(rect):
    cx1 = rect.left // GRID_SIZE
    cy1 = rect.top // GRID_SIZE
    cx2 = rect.right // GRID_SIZE
    cy2 = rect.bottom // GRID_SIZE
    neighbors = []
    for i in range(cx1, cx2 + 1):
        for j in range(cy1, cy2 + 1):
            neighbors.extend(spatial_grid.get((i, j), []))
    return list({id(b): b for b in neighbors}.values())

def get_nearby_obstacles(origin, obstacles, radius=800):
    cx, cy = origin
    radius_sq = radius ** 2
    return [
        r for r in obstacles
        if (r.centerx - cx) ** 2 + (r.centery - cy) ** 2 < radius_sq
    ]

def line_intersect(p1, p2, p3, p4):
    def det(a, b):
        return a[0]*b[1] - a[1]*b[0]

    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    eps=0.01
    denom = det((x1 - x2, y1 - y2), (x3 - x4, y3 - y4))
    if denom == 0: return None
    px = det((det(p1, p2), x1 - x2), (det(p3, p4), x3 - x4)) / denom
    py = det((det(p1, p2), y1 - y2), (det(p3, p4), y3 - y4)) / denom

    if (min(x1, x2)-eps <= px <= max(x1, x2)+eps and
        min(y1, y2)-eps <= py <= max(y1, y2)+eps and
        min(x3, x4)-eps <= px <= max(x3, x4)+eps and
        min(y3, y4)-eps <= py <= max(y3, y4)+eps):
        return (px, py)

def raycast(origin, angle, segments, max_distance=1000):
    dx = math.cos(angle)
    dy = math.sin(angle)
    end = (origin[0] + dx * max_distance, origin[1] + dy * max_distance)

    closest = end
    min_dist_sq = max_distance ** 2

    for seg in segments:
        hit = line_intersect(origin, end, *seg)
        if hit:
            if DEBUG: pygame.draw.circle(screen, RED, (hit[0]-cam_x, hit[1]-cam_y), 5)
            dist_sq = (hit[0] - origin[0]) ** 2 + (hit[1] - origin[1]) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest = hit
    if DEBUG:
        pygame.draw.line(screen, RED, (origin[0] - cam_x, origin[1] - cam_y), (end[0] - cam_x, end[1] - cam_y), 1)
        pygame.draw.line(screen, WHITE, (origin[0] - cam_x, origin[1] - cam_y), (closest[0] - cam_x, closest[1] - cam_y), 3)
    return closest

def compute_visibility_polygon(origin, obstacles, ray_count=16, radius=1000):
    segments = []
    corners = []
    for r in obstacles:
        segments.extend([
            ((r.left, r.top), (r.right, r.top)),
            ((r.right, r.top), (r.right, r.bottom)),
            ((r.right, r.bottom), (r.left, r.bottom)),
            ((r.left, r.bottom), (r.left, r.top)),
        ])
        corners.extend([
            (r.left, r.top), (r.right, r.top),
            (r.right, r.bottom), (r.left, r.bottom)
        ])

    for segment in segments:
        p1, p2 = segment
        x1, y1 = p1
        x2, y2 = p2
        if DEBUG: pygame.draw.line(screen, BLUE, (x1-cam_x,y1-cam_y), (x2-cam_x,y2-cam_y), 3)

    angles = [2 * math.pi * i / ray_count for i in range(ray_count)]
    control = lambda x: (x + 2 * math.pi) % (2 * math.pi)
    for corner in corners:
        angle = math.atan2(corner[1] - origin[1], corner[0] - origin[0])
        angles.extend([control(angle-0.1), control(angle), control(angle+0.1)])
    angles.sort()
    points = [raycast(origin, angle, segments, max_distance=radius) for angle in angles]
    return points

def draw_text(text: str, size: int):
    font = pygame.font.SysFont("impact", size)
    color = WHITE
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= SCREEN_WIDTH - 40:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    line_surfaces = [font.render(line, True, color) for line in lines]
    line_height = font.get_linesize()
    total_height = line_height * len(line_surfaces)
    y = SCREEN_HEIGHT - total_height - 20

    for surface in line_surfaces:
        rect = surface.get_rect(centerx=SCREEN_WIDTH // 2, y=y)
        screen.blit(surface, rect)
        y += line_height

def handle_ball_collisions(balls):
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            a, b = balls[i], balls[j]
            dx = b.x - a.x
            dy = b.y - a.y
            dist_sq = dx**2 + dy**2
            if dist_sq < (2 * BALL_RADIUS)**2:
                dist = math.sqrt(dist_sq)
                if dist == 0:
                    continue
                nx, ny = dx / dist, dy / dist
                tx, ty = -ny, nx

                v1n = a.vx * nx + a.vy * ny
                v2n = b.vx * nx + b.vy * ny
                v1t = a.vx * tx + a.vy * ty
                v2t = b.vx * tx + b.vy * ty

                a.vx = v2n * nx + v1t * tx
                a.vy = v2n * ny + v1t * ty
                b.vx = v1n * nx + v2t * tx
                b.vy = v1n * ny + v2t * ty

                overlap = 2 * BALL_RADIUS - dist
                a.x -= nx * overlap / 2
                a.y -= ny * overlap / 2
                b.x += nx * overlap / 2
                b.y += ny * overlap / 2


class Ball:
    def __init__(self):
        while True:
            self.x = random.randint(BALL_RADIUS, WORLD_WIDTH - BALL_RADIUS)
            self.y = random.randint(BALL_RADIUS, WORLD_HEIGHT - BALL_RADIUS)
            self.vx = random.uniform(-MAX_VELOCITY, MAX_VELOCITY)
            self.vy = random.uniform(-MAX_VELOCITY, MAX_VELOCITY)
            self.rect = pygame.Rect(self.x - BALL_RADIUS, self.y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)
            if not any(self.rect.colliderect(b) for b in boundaries):
                break
        self.color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )
        self.trail = []
        self.max_trail_length = 10

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.x <= BALL_RADIUS or self.x >= WORLD_WIDTH - BALL_RADIUS:
            self.vx *= -1
        if self.y <= BALL_RADIUS or self.y >= WORLD_HEIGHT - BALL_RADIUS:
            self.vy *= -1

        self.rect.x = self.x - BALL_RADIUS
        self.rect.y = self.y - BALL_RADIUS

        for b in get_nearby_boundaries(self.rect):
            if self.rect.colliderect(b):
                dx1 = self.rect.right - b.left
                dx2 = b.right - self.rect.left
                dy1 = self.rect.bottom - b.top
                dy2 = b.bottom - self.rect.top
                overlap_x = min(dx1, dx2)
                overlap_y = min(dy1, dy2)

                if overlap_x < overlap_y:
                    if self.x < b.centerx:
                        self.x -= overlap_x
                    else:
                        self.x += overlap_x
                    self.vx *= -1
                else:
                    if self.y < b.centery:
                        self.y -= overlap_y
                    else:
                        self.y += overlap_y
                    self.vy *= -1

        self.rect.x = self.x - BALL_RADIUS
        self.rect.y = self.y - BALL_RADIUS
        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)


    def draw(self, surface, camera_offset):
        for i, (tx, ty) in enumerate(self.trail):
            screen_x = int(tx - camera_offset[0])
            screen_y = int(ty - camera_offset[1])
            alpha = int(255 * (i + 1) / self.max_trail_length)
            trail_surface = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.color, alpha), (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
            surface.blit(trail_surface, (screen_x - BALL_RADIUS, screen_y - BALL_RADIUS))

        screen_x = int(self.x - camera_offset[0])
        screen_y = int(self.y - camera_offset[1])
        pygame.draw.circle(surface, self.color, (screen_x, screen_y), BALL_RADIUS)

balls = [Ball() for _ in range(NUM_BALLS)]
smooth_camera = False
cam_x, cam_y = 0, 0
running = True
update_sim = True
total_time = 0
caption_text = ""
while running:
    total_time += 1 / FPS
    
    if segments[current_id]["end"] < total_time:
        current_id += 1
    if current_id == segment_count:
        running = False
        continue
    current_segment = segments[current_id]
    if current_segment["start"] <= total_time:
        caption_text = current_segment["text"].strip()

    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RETURN:
                update_sim = not update_sim
            elif event.key == pygame.K_SPACE:
                DEBUG = not DEBUG

    if update_sim:
        for ball in balls:
            ball.update()
        handle_ball_collisions(balls)

        target_x = max(0, min(balls[0].x - SCREEN_WIDTH // 2, WORLD_WIDTH - SCREEN_WIDTH))
        target_y = max(0, min(balls[0].y - SCREEN_HEIGHT // 2, WORLD_HEIGHT - SCREEN_HEIGHT))
        if smooth_camera:
            cam_x += (target_x - cam_x) * 0.1
            cam_y += (target_y - cam_y) * 0.1
        else:
            cam_x, cam_y = target_x, target_y
            smooth_camera = True # avoid starting off center from the ball
        camera_offset = (cam_x, cam_y)

    for b in boundaries:
        screen_rect = pygame.Rect(b.x - camera_offset[0], b.y - camera_offset[1], b.width, b.height)
        if screen_rect.colliderect(screen.get_rect()):
            pygame.draw.rect(screen, GREEN, screen_rect)

    light_origin_world = (balls[0].x, balls[0].y)
    nearby_obstacles = get_nearby_obstacles(light_origin_world, boundaries)
    visibility_polygon = compute_visibility_polygon(light_origin_world, nearby_obstacles)
    light_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(
        light_surface,
        (255, 255, 255, 40),
        [(x - cam_x, y - cam_y) for x, y in visibility_polygon]
    )

    screen.blit(light_surface, (0, 0))

    for ball in balls:
        ball.draw(screen, camera_offset)

    draw_text(caption_text, 24)
    frame = pygame.surfarray.array3d(screen)
    frame = np.transpose(frame, (1, 0, 2))
    ffmpeg_process.stdin.write(frame.astype(np.uint8).tobytes())


pygame.quit()
ffmpeg_process.stdin.close()
ffmpeg_process.wait()

print("Recording saved to {}".format(SAVE_TARGET))