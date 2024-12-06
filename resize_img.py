from PIL import Image

# Input image path
input_image_path = "/Users/yuta/property_proj/static/Screenshot 2024-11-17 at 14.34.24.png"
output_image_path = "/Users/yuta/property_proj/static/resized_image.png"

# Target dimensions
target_width = 516
target_height = 430

def resize_and_crop(input_path, output_path, target_width, target_height):
    with Image.open(input_path) as img:
        # Calculate aspect ratio
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        # Determine if we need to crop by width or height
        if img_ratio > target_ratio:
            # Crop the width
            new_width = int(target_ratio * img.height)
            new_height = img.height
            crop_box = ((img.width - new_width) // 2, 0, (img.width + new_width) // 2, new_height)
        else:
            # Crop the height
            new_width = img.width
            new_height = int(img.width / target_ratio)
            crop_box = (0, (img.height - new_height) // 2, new_width, (img.height + new_height) // 2)

        # Crop and resize
        img = img.crop(crop_box)
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        img.save(output_path)
        print(f"Image cropped and resized to {target_width}x{target_height}, saved to {output_path}")

# Call the function
resize_and_crop(input_image_path, output_image_path, target_width, target_height)
