from PIL import Image
import os

def convert_ico_to_png(ico_path, png_path):
    try:
        if not os.path.exists(ico_path):
            print(f"Error: {ico_path} does not exist.")
            return

        img = Image.open(ico_path)
        # ICO files might contain multiple sizes. PIL usually loads the largest one by default or permits seeking.
        # Let's just save the current loaded image (usually the largest/first).
        print(f"Loaded ICO: {img.format}, Size: {img.size}, Mode: {img.mode}")
        
        # Ensure it's in a mode compatible with PNG (RGBA)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        img.save(png_path, format='PNG')
        print(f"Successfully converted {ico_path} to {png_path}")
        
    except Exception as e:
        print(f"Failed to convert: {e}")

if __name__ == "__main__":
    ico_file = r"c:\git\training_99\reverse_engineering_ref\resources\Icon2.ico"
    png_file = r"c:\git\training_99\doc\player.png"
    convert_ico_to_png(ico_file, png_file)
