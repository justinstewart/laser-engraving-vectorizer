"""Remove background from an image using fal.ai BiRefNet."""

import sys
from pathlib import Path

import fal_client
import httpx
from dotenv import load_dotenv

load_dotenv()


def remove_background(input_path: str | Path, output_path: str | Path) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Upload local file to fal storage
    url = fal_client.upload_file(input_path)

    result = fal_client.subscribe(
        "fal-ai/birefnet/v2",
        arguments={
            "image_url": url,
            "output_format": "png",
            "refine_foreground": True,
            "operating_resolution": "2048x2048",
        },
    )

    # Download the result image
    image_url = result["image"]["url"]
    response = httpx.get(image_url)
    output_path.write_bytes(response.content)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python remove_background.py input.png output.png")
        sys.exit(1)

    result = remove_background(sys.argv[1], sys.argv[2])
    print(f"Saved: {result}")
