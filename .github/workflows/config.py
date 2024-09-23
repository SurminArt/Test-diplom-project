import os

UPLOAD_FOLDER = 'main/templates/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
root_dir = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(root_dir, "templates")
JS_DIRECTORY = os.path.join(TEMPLATE_FOLDER, "js")
CSS_DIRECTORY = os.path.join(TEMPLATE_FOLDER, "css")
IMAGES_DIRECTORY= os.path.join(TEMPLATE_FOLDER, "images")