from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from typing import Any, Annotated
from pydantic import BaseModel, Field
from PIL import Image as PILImage
import cv2
import numpy as np
import io

class EnhanceImageInput(BaseModel):
    image: Any = Field(description="Input image to enhance")  # Note: Use Any, not Image
    prompt: str = Field(description="Prompt describing enhancement style")

class EnhancedImageOutput(BaseModel):
    enhanced_image: Any = Field(description="Enhanced output image")  # Use Any, not Image
    description: str = Field(description="Description of enhancement applied")

mcp = FastMCP(
    "Image Enhancer Server",
    website_url="https://github.com/modelcontextprotocol/python-sdk"
)

@mcp.tool()
def enhance_image(
    data: Annotated[EnhanceImageInput, "Image and prompt"],
    ctx: Context[ServerSession, None]
) -> EnhancedImageOutput:
    image_input = data.image
    # Image might be an object or dict, handle both
    image_bytes = getattr(image_input, "data", None) or image_input.get("data")
    img = PILImage.open(io.BytesIO(image_bytes))
    img_np = np.array(img)
    if img_np.ndim == 3 and img_np.shape[2] == 4:
        img_np = img_np[..., :3]
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    prompt = data.prompt.lower()
    if "sharpen" in prompt:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        img_cv = cv2.filter2D(img_cv, -1, kernel)
        enhancement = "Sharpened"
    elif "denoise" in prompt:
        img_cv = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)
        enhancement = "Denoised"
    else:
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl,a,b))
        img_cv = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        enhancement = "Contrast Enhanced"

    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    img_out_pil = PILImage.fromarray(img_rgb)
    out_buf = io.BytesIO()
    img_out_pil.save(out_buf, format="PNG")
    out_bytes = out_buf.getvalue()

    # Return in dict format compatible with Claude/MCP
    return EnhancedImageOutput(
        enhanced_image={"data": out_bytes, "format": "png"},
        description=f"Image enhanced: {enhancement} using prompt '{data.prompt}'"
    )

def main():
    mcp.run()

if __name__ == "__main__":
    main()
