from PIL import Image
img = Image.open("static/tmp/apple.jpg")
img.thumbnail((240, 240))
img.save('thumb.jpg')