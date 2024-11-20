import shutil

from fastapi import APIRouter, UploadFile

from app.tasks.tasks import resize_image

router = APIRouter(prefix="/images", tags=["Изображения отелей"])


@router.post("/")
def upload_image(file: UploadFile):
    image_path = f"/home/evalshine/backend/hotelsapi_media/{file.filename}"
    with open(image_path, "wb+") as new_file:
        shutil.copyfileobj(file.file, new_file)

    resize_image.delay(image_path)