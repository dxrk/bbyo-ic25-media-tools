# Introduction

Both crop-headshots.py and format-partners.py were created to help format headshots and partner logos for BBYO's International Convention 2025.
The outputs were used on the IC 2025 site and participant mobile app.

## crop-headshots.py

A Python script that processes headshot images from Airtable, automatically detects faces, and crops them to create standardized profile photos.

Key features and tools:

- Uses `face_recognition` library for facial detection
- Processes images from Airtable attachments
- Crops and centers detected faces with adjustable zoom
- Outputs standardized 1000x1000px JPG images
- Saves processed images locally and uploads back to Airtable

Dependencies:

- pyairtable
- Pillow (PIL)
- face_recognition
- numpy
- requests
- python-dotenv

## format-partners.py

A Python script that standardizes partner and sponsor logos into consistent, centered images with white backgrounds.

Key features and tools:

- Processes both PNG and SVG logo files
- Centers logos with consistent padding
- Converts all images to 1000x1000px PNG format
- Handles transparency and white background generation
- Saves processed logos locally and uploads back to Airtable

Dependencies:

- pyairtable
- Pillow (PIL)
- requests
- python-dotenv
- cairosvg (for SVG conversion)

## Setup

1. Create a `.env` file with your Airtable credentials:

```bash
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME=your_table_name
AIRTABLE_IMAGE_FIELD=your_image_field
AIRTABLE_HEADSHOT_FIELD=your_headshot_field
AIRTABLE_VIEW_NAME=your_view_name
```

2. Install the required Python packages:

```bash
pip install -r requirements.txt

```

3. Run the scripts:

```bash
python crop-headshots.py
```

OR

```bash
python format-partners.py
```

## Conclusion

This README provides a comprehensive overview of both scripts, their functionality, dependencies, and setup instructions. Let me know if you'd like me to add or modify anything!
