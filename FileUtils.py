from pyclamd import ClamdNetworkSocket, BufferTooLongError

from werkzeug.datastructures import FileStorage

from Utils import ActionResult

from PIL import Image, UnidentifiedImageError

class FileSafety:
    "Connects to ClamAv, provides is_safe method"
    AllowedExtensions = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}

    def __init__(self, host="localhost", port=3310):
        self.connection = ClamdNetworkSocket(host=host,port=port)

    def is_safe(self, file: FileStorage) -> ActionResult:
        "Checks if file is safe to save"
        extension = file.filename.split(".")[-1]
        if extension not in FileSafety.AllowedExtensions:
            return ActionResult(False, "Unsupported extension.")
        try:
            TestResult = self.connection.scan_stream(file.stream)
        except BufferTooLongError:
            return ActionResult(False, "File too big to scan!")
        except ConnectionError:
            return ActionResult(False, "Unable to scan file!")
        if TestResult:
            return ActionResult(False, "An unknown error occurred!")
        return ActionResult(True)
    
class ImageHandler:
    @staticmethod
    def save_as_webp(filepath: str, file: FileStorage):
        ImageFile = Image.open(file).convert("RGB")
        with open(filepath, "wb") as f:
            ImageFile.save(f,"webp")
    @staticmethod
    def verify_image(file: FileStorage) -> ActionResult:
        try:
            ImageFile = Image.open(file).convert("RGB")
        except UnidentifiedImageError:
            return ActionResult(False, "File is not an image!")
        return ActionResult(True)

