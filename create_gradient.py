"""Create a pre-rendered smooth gradient PNG."""
import numpy as np
from PIL import Image

# Full export resolution
HEIGHT = 2560
WIDTH = 1440

# Example colors - change these as needed
TOP_COLOR = (40, 0, 40)
BOTTOM_COLOR = (10, 0, 20)

# Create 16-bit gradient to prevent banding
y = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32).reshape(HEIGHT, 1)

# Interpolate in 16-bit space
top_arr = np.array(TOP_COLOR, dtype=np.float32)
bottom_arr = np.array(BOTTOM_COLOR, dtype=np.float32)
grad = top_arr * (1.0 - y) + bottom_arr * y
grad = grad.astype(np.uint16)

# Add dithering
noise = np.random.normal(0, 2.0, grad.shape).astype(np.float32)
grad = grad + noise
grad = np.clip(grad, 0, 255).astype(np.uint8)

# Broadcast to full width
grad_full = np.tile(grad, (1, WIDTH))

# Save as PNG
img = Image.fromarray(grad_full, mode='RGB')
img.save('smooth_gradient.png')
print("Gradient created: smooth_gradient.png")