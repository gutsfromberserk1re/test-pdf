import fitz  # PyMuPDF
from PIL import Image as PILImage, ImageOps
import io

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.carousel import Carousel
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image as KivyImage
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.core.window import Window

# Set background to pitch black
Window.clearcolor = (0.06, 0.06, 0.06, 1)


class PdfPageWidget(Scatter):
    """Container allowing pinch-to-zoom and panning on individual PDF pages."""
    def __init__(self, texture, **kwargs):
        super().__init__(**kwargs)
        self.do_rotation = False
        self.auto_bring_to_front = False
        
        img = KivyImage(texture=texture, allow_stretch=True, keep_ratio=True)
        img.size = self.size
        self.add_widget(img)


class ReaderApp(App):
    def build(self):
        self.doc = None
        self.is_night_mode = True
        self.current_pdf_path = None

        self.root = FloatLayout()

        # Welcome Screen
        self.welcome_layout = BoxLayout(
            orientation='vertical',
            padding=40,
            spacing=20,
            size_hint=(0.8, 0.4),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        title = Label(
            text="📖 Pure Python E-Reader",
            font_size='24sp',
            color=(0.9, 0.9, 0.9, 1)
        )
        btn_open = Button(
            text="Choose PDF File",
            size_hint_y=None,
            height='50dp',
            background_color=(0.2, 0.4, 0.8, 1)
        )
        btn_open.bind(on_release=self.show_file_picker)

        self.welcome_layout.add_widget(title)
        self.welcome_layout.add_widget(btn_open)
        self.root.add_widget(self.welcome_layout)

        # Reader Layout (Hidden by default)
        self.reader_layout = FloatLayout()
        
        # Horizontal Page Swiping Carousel
        self.carousel = Carousel(direction='horizontal', loop=False)
        self.carousel.bind(index=self.on_page_change)
        self.reader_layout.add_widget(self.carousel)

        # Top Overlay Bar
        self.controls = BoxLayout(
            size_hint=(1, None),
            height='48dp',
            pos_hint={'top': 1},
            padding=[10, 5],
            spacing=10
        )
        
        btn_back = Button(text="Open", size_hint_x=None, width='70dp')
        btn_back.bind(on_release=self.show_file_picker)
        
        self.lbl_page = Label(text="Page 0/0", color=(1, 1, 1, 1))
        
        btn_theme = Button(text="Theme", size_hint_x=None, width='70dp')
        btn_theme.bind(on_release=self.toggle_night_mode)

        self.controls.add_widget(btn_back)
        self.controls.add_widget(self.lbl_page)
        self.controls.add_widget(btn_theme)
        
        self.reader_layout.add_widget(self.controls)
        return self.root

    def show_file_picker(self, *args):
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView(filters=['*.pdf'])
        
        popup = Popup(title="Select a PDF File", content=content, size_hint=(0.9, 0.9))
        
        def load_file(instance):
            if file_chooser.selection:
                self.load_pdf(file_chooser.selection[0])
                popup.dismiss()

        btn_select = Button(text="Open Selected", size_hint_y=None, height='45dp')
        btn_select.bind(on_release=load_file)

        content.add_widget(file_chooser)
        content.add_widget(btn_select)
        popup.open()

    def load_pdf(self, path):
        self.current_pdf_path = path
        self.doc = fitz.open(path)
        
        # Switch screen from Welcome layout to Reader layout
        self.root.clear_widgets()
        self.root.add_widget(self.reader_layout)
        
        self.render_carousel()

    def render_carousel(self):
        self.carousel.clear_widgets()
        if not self.doc:
            return

        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            
            # Render page to image at 2x resolution for crisp text reading
            pix = page.get_pixmap(dpi=150)
            img = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)

            if self.is_night_mode:
                img = ImageOps.invert(img)

            # Convert PIL image to Kivy Texture
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            data = io.BytesIO(img_byte_arr.read())
            pil_img = PILImage.open(data)
            pil_img = pil_img.convert('RGBA')
            
            texture = Texture.create(size=(pil_img.width, pil_img.height), colorfmt='rgba')
            texture.blit_buffer(pil_img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
            texture.flip_vertical()

            page_widget = PdfPageWidget(texture=texture, size=(Window.width, Window.height))
            self.carousel.add_widget(page_widget)

        self.lbl_page.text = f"Page 1/{len(self.doc)}"

    def on_page_change(self, instance, value):
        if self.doc:
            self.lbl_page.text = f"Page {value + 1}/{len(self.doc)}"

    def toggle_night_mode(self, *args):
        self.is_night_mode = not self.is_night_mode
        if self.current_pdf_path:
            current_index = self.carousel.index
            self.render_carousel()
            self.carousel.index = current_index


if __name__ == '__main__':
    ReaderApp().run()
