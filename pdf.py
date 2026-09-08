import os
import sys
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

dirname, _ = os.path.split(os.path.abspath(__file__))
THIS_DIRECTORY = f'{dirname}{os.sep}'

PAGE_W, PAGE_H = A4
IMAGE_W = PAGE_W / 4
IMAGE_H = IMAGE_W * 1024 / 733
COLUMNS = 4
ROWS = 4
PER_PAGE = COLUMNS * ROWS

def create(images, save_as):
    pdf = canvas.Canvas(save_as, pagesize=A4)
    for i, filename in enumerate(images):
        position = i % PER_PAGE
        column = position % COLUMNS
        row = position // COLUMNS

        x = column * IMAGE_W
        y = PAGE_H - (row + 1) * IMAGE_H

        image = Image.open(filename)
        image = ImageOps.exif_transpose(image)

        temp_file = f'{THIS_DIRECTORY}temp/image_{i}.jpg'
        image.convert('RGB').save(
            temp_file,
            'JPEG',
            quality=90,
            optimize=True,
        )

        pdf.drawImage(
            temp_file,
            x,
            y,
            width=IMAGE_W,
            height=IMAGE_H,
        )

        if position == PER_PAGE - 1 or i == len(images) - 1:
            pdf.showPage()
    pdf.save()
