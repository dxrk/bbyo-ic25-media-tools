import os
from pyairtable import Api
from PIL import Image
import io
import base64
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable API key
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = 'Partners, Sponsor & Pop-Ups'
AIRTABLE_LOGO_FIELD = 'Logo'
AIRTABLE_REFORMATTED_FIELD = 'Logo (Reformatted)'
AIRTABLE_VIEW_NAME = 'IC 2025 Full Partner List'

# Create a directory to store logos
os.makedirs('logos', exist_ok=True)

# Initialize Airtable API
api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def fetch_records():
    """Fetch records from Airtable with logo"""
    try:
        records = table.all(view=AIRTABLE_VIEW_NAME)
        return [
            record for record in records 
            if AIRTABLE_LOGO_FIELD in record['fields'] and record['fields'][AIRTABLE_LOGO_FIELD]
        ]
    except Exception as e:
        print(f'Error fetching records: {e}')
        return []
    
def download_image(image_url):
    """Download an image from a URL"""
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f'Error downloading image from {image_url}: {e}')
        raise

# convert svg to png
def convert_svg_to_png(svg_buffer, target_size=1000, padding_percent=0.1):
    """
    Robust SVG to PNG conversion with centering and background
    """
    try:
        # Convert SVG to PNG using cairosvg with high resolution
        png_buffer = cairosvg.svg2png(
            bytestring=svg_buffer, 
            output_width=target_size, 
            output_height=target_size
        )
        
        # Open the converted image
        img = Image.open(io.BytesIO(png_buffer))
        
        # Convert to RGBA
        img = img.convert('RGBA')
        
        # Create white background
        background = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 255))
        
        # Calculate centering offset
        offset = ((target_size - img.width) // 2, (target_size - img.height) // 2)
        
        # Paste image
        background.paste(img, offset, img)
        
        # Convert to bytes
        output = io.BytesIO()
        background.save(output, format='PNG')
        return output.getvalue()
    
    except Exception as e:
        print(f'Error converting SVG to PNG: {e}')
        raise

def center_logo_in_square(image_data, target_size=1000, padding_percent=0.1):
    """Center logo in a square image with optional padding and trim whitespace"""
    try:
        # Open the image
        img = Image.open(io.BytesIO(image_data))

        # Trim whitespace (transparent pixels)
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

        # Calculate padding
        padding = int(target_size * padding_percent)
        logo_size = target_size - 2 * padding

        # Resize while maintaining aspect ratio
        img.thumbnail((logo_size, logo_size), Image.LANCZOS)

        # Create a new white square image
        background = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 255))

        # Calculate position to center the logo
        offset = ((target_size - img.width) // 2, (target_size - img.height) // 2)

        # Paste the logo onto the white background
        background.paste(img, offset, img if img.mode == 'RGBA' else None)

        # Convert to bytes
        output = io.BytesIO()
        background.save(output, format='PNG')
        return output.getvalue()
    except Exception as e:
        print(f'Error processing image: {e}')
        raise

def upload_logo(record_id, logo_path):
    try:
        # Read the logo image
        with open(logo_path, 'rb') as f:
            logo_buffer = f.read()

        # Encode the image as base64
        base64_logo = base64.b64encode(logo_buffer).decode('utf-8')

        # Prepare the Airtable API request
        url = f'https://content.airtable.com/v0/{AIRTABLE_BASE_ID}/{record_id}/{AIRTABLE_REFORMATTED_FIELD}/uploadAttachment'
        headers = {
            'Authorization': f'Bearer {AIRTABLE_API_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'contentType': 'image/jpeg',  # Set the content type
            'file': base64_logo,      # Base64-encoded file
            'filename': os.path.basename(logo_path),  # Filename
        }

        # Upload the attachment
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            print(f'Successfully uploaded logo for record {record_id}')
        else:
            print(f'Failed to upload logo for record {record_id}: {response.status_code} - {response.text}')

    except Exception as e:
        print(f'Error uploading logo for record {record_id}: {e}')

def main():
    # Fetch records from Airtable
    records = fetch_records()

    # Iterate over the records
    for record in records:
        try:
            # check if logo exists in logos folder by record id
            if os.path.exists(f'./logos/{record["id"]}.png'):
                print(f"Logo already exists for record {record['id']}")
                continue

            # Get the logo URL from the record
            logo_url = record['fields'][AIRTABLE_LOGO_FIELD][0]['url']
            print(f"Processing logo: {logo_url}")

            # Download the logo image
            logo_image = download_image(logo_url)

            # Convert SVG to PNG
            if logo_url.endswith('.svg'):
                logo_image = convert_svg_to_png(logo_image)

            # Center logo in 1000x1000 square
            centered_logo = center_logo_in_square(logo_image)

            # Generate a filename based on the record ID
            logo_filename = os.path.join('./logos', f"{record['id']}.png")

            # Save the centered logo to the logos directory
            with open(logo_filename, 'wb') as f:
                f.write(centered_logo)

            # Upload the centered logo to Airtable
            upload_logo(record['id'], logo_filename)
        except Exception as e:
            print(f"Error processing record {record['id']}: {e}")

if __name__ == '__main__':
    main()