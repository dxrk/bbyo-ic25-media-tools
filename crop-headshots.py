from pyairtable import Api
from PIL import Image
import face_recognition
import io
import base64
import numpy as np
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable API key
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
AIRTABLE_IMAGE_FIELD = os.getenv('AIRTABLE_IMAGE_FIELD')
AIRTABLE_HEADSHOT_FIELD = os.getenv('AIRTABLE_HEADSHOT_FIELD')
AIRTABLE_VIEW_NAME = os.getenv('AIRTABLE_VIEW_NAME')

# Initialize Airtable API
api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def fetch_records():
    """Fetch records from Airtable with optional view filtering"""
    try:
        return table.all(view=AIRTABLE_VIEW_NAME)
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

def detect_and_crop_face(image_buffer, zoom_out_factor=1.5):
    """Detect face in image and crop around it"""
    try:
        image = Image.open(io.BytesIO(image_buffer)).convert('RGB')
        image_array = np.array(image)

        face_locations = face_recognition.face_locations(image_array)
        if not face_locations:
            raise ValueError('No face detected')

        top, right, bottom, left = face_locations[0]
        face_width = right - left
        face_height = bottom - top

        size = max(face_width, face_height) * zoom_out_factor
        x = left - (size - face_width) // 2
        y = top - (size - face_height) // 2

        x = max(0, x)
        y = max(0, y)
        size = min(size, image.width - x, image.height - y)

        cropped_image = image.crop((x, y, x + size, y + size))
        cropped_image = cropped_image.resize((1000, 1000))

        output_buffer = io.BytesIO()
        cropped_image.save(output_buffer, format='JPEG')
        return output_buffer.getvalue()

    except Exception as e:
        print(f'Error processing image: {e}')
        raise

def upload_headshot(record_id, headshot_path):
    try:
        # Read the headshot image
        with open(headshot_path, 'rb') as f:
            headshot_buffer = f.read()

        # Encode the image as base64
        base64_headshot = base64.b64encode(headshot_buffer).decode('utf-8')

        # Prepare the Airtable API request
        url = f'https://content.airtable.com/v0/{AIRTABLE_BASE_ID}/{record_id}/{AIRTABLE_HEADSHOT_FIELD}/uploadAttachment'
        headers = {
            'Authorization': f'Bearer {AIRTABLE_API_KEY}',
            'Content-Type': 'application/json',
        }
        data = {
            'contentType': 'image/jpeg',  # Set the content type
            'file': base64_headshot,      # Base64-encoded file
            'filename': os.path.basename(headshot_path),  # Filename
        }

        # Upload the attachment
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f'Successfully uploaded headshot for record {record_id}')
        else:
            print(f'Failed to upload headshot for record {record_id}: {response.status_code} - {response.text}')

    except Exception as e:
        print(f'Error uploading headshot for record {record_id}: {e}')

def update_record(record_id, headshot_buffer):
    """Update Airtable record with new headshot"""
    try:
        base64_headshot = base64.b64encode(headshot_buffer).decode('utf-8')
        fields = {
            AIRTABLE_HEADSHOT_FIELD: [
                {
                    'url': f'data:image/jpeg;base64,{base64_headshot}',
                }
            ]
        }
        table.update(record_id, fields)
        return True
    except Exception as e:
        print(f'Error updating record: {e}')
        return False

def main():
    # Create images directory if it doesn't exist
    if not os.path.exists('./headshots'):
        os.makedirs('./headshots')

    # Fetch records from specified view
    records = fetch_records()

    for record in records:
        try:
            # check if record id already exists in images folder
            if os.path.exists(f'./headshots/{record["id"]}.jpg'):
                # print(f'Skipping record {record["id"]}: Image already processed')
                continue

            # Get image URL from record
            image_url = record['fields'].get(AIRTABLE_IMAGE_FIELD, [{}])[0].get('url')

            if not image_url:
                # print(f'Skipping record {record["id"]}: No headshot URL')
                continue

            print(f'Processing image: {image_url}')
            
            # Download and process image
            image_buffer = download_image(image_url)

            # Skip HEIC images
            if image_url.lower().endswith('.heic'):
                continue

            # Detect face and crop image
            try:
                headshot_buffer = detect_and_crop_face(image_buffer, zoom_out_factor=3)
            except Exception as e:
                print(f'Skipping record {record["id"]}: Failed to detect face')
                continue

            # Save processed image locally
            with open(f'./headshots/{record["id"]}.jpg', 'wb') as f:
                f.write(headshot_buffer)

            # Update Airtable record
            if upload_headshot(record["id"], f'./headshots/{record["id"]}.jpg'):
                print(f'Successfully processed record {record["id"]}')
            else:
                print(f'Failed to update record {record["id"]}')

        except Exception as e:
            print(f'Error processing record {record["id"]}: {e}')

if __name__ == '__main__':
    main()