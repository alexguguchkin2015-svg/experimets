#!/usr/bin/env python3
"""
Script to create a simple icon for the game
"""
import pygame

# Create a 64x64 icon surface
icon = pygame.Surface((64, 64), pygame.SRCALPHA)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (10, 20, 50)

# Draw a simplified version of the character head
# Head circle
pygame.draw.circle(icon, WHITE, (32, 32), 25)

# Horns
pygame.draw.polygon(icon, WHITE, [
    (22, 22),
    (15, 12),
    (18, 8),
    (24, 18)
])
pygame.draw.polygon(icon, WHITE, [
    (42, 22),
    (49, 12),
    (46, 8),
    (40, 18)
])

# Eyes (black voids)
pygame.draw.circle(icon, BLACK, (27, 30), 5)
pygame.draw.circle(icon, BLACK, (37, 30), 5)

# Save as PNG (can be converted to ICO later)
pygame.image.save(icon, "icon.png")
print("Icon saved as icon.png")
print("To convert to .ico format, use an online converter or:")
print("  pip install pillow")
print("  python -c \"from PIL import Image; img=Image.open('icon.png'); img.save('icon.ico', format='ICO')\"")
