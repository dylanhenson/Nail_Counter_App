import PySimpleGUI as sg
import ctypes
import platform
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO #converts image to bytes

def make_dpi_aware():
    if int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

make_dpi_aware()

sg.theme("DarkBlue")

def fs_dither(image):
    # Convert the image to grayscale
    grayscale = image.convert('L')

    # Create a new image to store the dithered version
    dithered = Image.new('L', image.size, color=0)

    # Define the Floyd-Steinberg dithering matrix
    dither_matrix = [
        [0, 0, 0],
        [0, 0, 7],
        [3, 5, 1]
    ]

    # Iterate over each pixel in the grayscale image
    for y in range(1, image.height - 1):
        for x in range(1, image.width - 1):
            old_pixel = grayscale.getpixel((x, y))
            new_pixel = 255 if old_pixel > 127 else 0
            dithered.putpixel((x, y), new_pixel)
            quant_error = old_pixel - new_pixel

            # Distribute the quantization error to neighboring pixels
            for dy, dx in [(0, 1), (1, -1), (1, 0), (1, 1)]:
                neighbor_x, neighbor_y = x + dx, y + dy
                neighbor_pixel = grayscale.getpixel((neighbor_x, neighbor_y))
                neighbor_pixel += quant_error * dither_matrix[dy][dx] // 16
                grayscale.putpixel((neighbor_x, neighbor_y), neighbor_pixel)

    return dithered


def update_image(original, brightness, dither, resize_factor, contrast):
    global image

    # change brightness
    image = ImageEnhance.Brightness(original).enhance(brightness) # add image changes here

    # change contrast
    image = image.filter(ImageFilter.UnsharpMask(contrast))

    # change size
    w, h = original.size
    new_w = int(w * resize_factor)
    new_h = int(h * resize_factor)

    image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if dither:
        image = fs_dither(image)

    nail_count = 0

    # update nail count
    for pixel in image.getdata():
        if pixel < (255/2):
            nail_count += 1

    # increase size to match the original image 
    image = image.resize((w*3, h*3), Image.Resampling.NEAREST)

    # convert image to bytes
    bio = BytesIO()
    image.save(bio, format='PNG')

    window['-IMAGE-'].update(data=bio.getvalue())
    window['-NAILCOUNTTEXT-'].update(f'Nail count: {str(nail_count)}')


#image_path = 'C:/Users/Dylan/Desktop/DH Projects/Dad/'s Art/Floyd Steinberg Dithering/Jerry final test 2 for dylan.jpg'

control_col = sg.Column([
    [sg.Checkbox('Floyd-Steinberg Dither', key='-DITHER-')],
    [sg.Frame('Brightness', layout=[[sg.Slider(range=(0,5), orientation='h', 
                                    default_value=1, resolution=.1,
                                    key='-BRIGHT-')]])],
    [sg.Frame('Scale size', layout=[[sg.Slider(range=(0.01,1), orientation='h', 
                                    default_value=1, resolution=.01, 
                                    key='-SIZE-')]])],
    [sg.Frame('Contrast', layout=[[sg.Slider(range=(0,10), orientation='h', 
                                    default_value=0, resolution=.1, 
                                    key='-CONTRAST-')]])],
    [
        sg.Text('Image file'),
        sg.Input(size=(25, 1), key='-FILE-'),
        sg.FileBrowse(key='-BROWSE-'),
        sg.Button('Load image', key='-LOAD-')
    ],
    [sg.Button('Save image as', key='-SAVE-')],
])

image_col = sg.Column([[sg.Image(expand_x=True, 
                        expand_y=True, key='-IMAGE-')]], expand_x=True, 
                        expand_y=True, size=(800, 500))

layout = [[sg.Text('Pixel Counter', font='Courier 70')],
            [control_col, image_col],
            [sg.Text('Nail count: ', expand_x=True, 
                        expand_y=True, font='Arial 30', 
                        key='-NAILCOUNTTEXT-')]]


window = sg.Window('window1', layout, location=(0,0), resizable=True,
    font='Arial 12', 
    size=(1800,1400))


original = Image.open("C:/Users/Dylan/Desktop/test.png").convert('L')

while True:
    event, values = window.read(timeout=50)
    if event == sg.WIN_CLOSED:
        break

    update_image(original, values['-BRIGHT-'], values['-DITHER-'], 
                    values['-SIZE-'], values['-CONTRAST-'])
    
    if event == '-SAVE-':
        save_path = sg.popup_get_file('Save', save_as=True, no_window=True) + '.png'
        image.save(save_path, 'PNG')

    if event == '-LOAD-':
        print(values['-FILE-'])
        original = Image.open(values['-FILE-']).convert('L')

window.close()


#NOTES:
# Current issue deals with uploading image. replace loaded 
    # image with static filepath string to make it work
# Make sure window doesn't cut off image (happens with window1)
# add flag warning when image is too large to dither quickly
# Implement chache-ing or move around code to not run fs dithering each loop