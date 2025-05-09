from PIL import Image
from landingai.predict import SnowflakeNativeAppPredictor


def run_inference_on_images(
    image_files: list[str], predictor: SnowflakeNativeAppPredictor
):
    results = []
    for image_path in image_files:
        image = Image.open(image_path)
        predictions = predictor.predict(image)
        results.append(
            {
                "file": image_path,
                "endpoint_id": predictor._endpoint_id,
                "predictions": predictions,
            }
        )
    return results
