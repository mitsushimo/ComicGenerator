import concurrent.futures
import io
import os

from docx import Document
from google import genai
from google.genai import types
from PIL import Image, ImageOps
from pydantic import BaseModel
from PyPDF2 import PdfReader


# Class definitions
class Character(BaseModel):
    """
    Represents a character in the story.
    Used by the AI to define and maintain consistent physical traits and clothing
    for character visual reference generation.
    """

    name: str
    description: str
    clothing: str
    physical_traits: str


class Panel(BaseModel):
    """
    Represents a single comic panel on a page.
    Holds the visual description and dialogue needed by the AI to generate
    the individual image for this specific scene.
    """

    panel_number: int
    visual_description: str
    dialogue: str


class Page(BaseModel):
    """
    Represents a single page in the graphic novel.
    Groups multiple panels together. This structure dictates how panels
    are assembled onto the final page canvas.
    """

    page_number: int
    panels: list[Panel]


class GraphicNovelScript(BaseModel):
    """
    The top-level structure of the refined story script.
    Serves as the expected JSON schema when asking the AI to convert
    the raw user text into a structured comic format.
    """

    title: str
    characters: list[Character]
    pages: list[Page]


# Helper functions
def extract_text(file_path):
    """
    Reads the raw story document from the user (TXT, PDF, or DOCX).
    Returns a single string containing the entire text, which will be
    passed to the AI for refinement and structuring.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif ext == ".pdf":
        return "\n".join([p.extract_text() for p in PdfReader(file_path).pages])
    elif ext == ".docx":
        return "\n".join([p.text for p in Document(file_path).paragraphs])


# Core AI functions
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
IMAGE_MODEL = "gemini-3.1-flash-image"
TEXT_MODEL = "gemini-3.6-flash"


def refine_story(text):
    """
    Takes the raw story text and prompts the AI to convert it into a structured
    GraphicNovelScript JSON format. This forms the blueprint for the entire comic,
    dictating the characters, pages, and panels to be generated.
    """
    prompt = (
        "Convert the following story into a graphic novel script JSON.\n"
        "Ensure the entire plot is covered from beginning to end. \n"
        "The dialogue may need to be simplified and dramatized to be suitable for a comic. \n"
        "Avoid excessively violent or sexual expressions. \n"
        "Each page shall have 4 panels.\n"
        "The number of pages should not exceed 15, but can be less. \n"
        f"STORY SETUP:\n\n{text}"
    )
    return client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=GraphicNovelScript
        ),
    ).parsed


def generate_character_sheet(char):
    """
    Takes a Character object and generates a visual reference image using the AI.
    These reference images are later fed back into the AI to ensure visual
    consistency when generating the individual comic panels.
    """
    prompt = f"Visual reference sheet for {char.name}. Traits: {char.physical_traits}. Outfit: {char.clothing}. White background. Cinematic graphic novel style."
    res = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    return Image.open(io.BytesIO(res.candidates[0].content.parts[0].inline_data.data))


def generate_title_page(title, story_text, char_sheets_folder, output_dir):
    """
    Generates a full-page cover image for the graphic novel.
    """
    print("Generating Title Page...")
    canvas = Image.new("RGB", (1600, 2000), "white")

    # Use TEXT_MODEL to generate a cover description based on the story
    text_prompt = f"Give me a straightforward written description of a title page for a graphic novel that fits this story:\n\n{story_text}"
    text_res = client.models.generate_content(model=TEXT_MODEL, contents=text_prompt)
    cover_description = text_res.text if text_res.text else "Cinematic cover art."

    # Load all character visual references
    reference_parts = []
    for filename in os.listdir(char_sheets_folder):
        if filename.endswith("_ref.png"):
            with open(os.path.join(char_sheets_folder, filename), "rb") as f:
                reference_parts.append(
                    types.Part.from_bytes(data=f.read(), mime_type="image/png")
                )

    prompt = (
        f"Graphic Novel Cover Art for title: '{title}'.\n"
        f"Visual Description: {cover_description}\n"
        "Create a cinematic, full-page cover illustration matching this description. "
        "Use provided character sheets for visual consistency. "
        "High-fidelity text rendering for the title if possible."
    )

    res = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=reference_parts + [prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:5"),
        ),
    )

    if not res.candidates or not res.candidates[0].content:
        cover_img = Image.new("RGB", (1600, 2000), (220, 220, 220))
    else:
        img_bytes = res.candidates[0].content.parts[0].inline_data.data
        base_img = Image.open(io.BytesIO(img_bytes))
        # Resize to fit the canvas (1600, 2000)
        cover_img = ImageOps.pad(base_img, (1600, 2000), color=(255, 255, 255))

    canvas.paste(cover_img, (0, 0))
    output_name = os.path.join(output_dir, "Page_0_Cover.png")
    canvas.save(output_name)
    return output_name


def assemble_final_page(panels, char_sheets_folder, page_num, output_dir):
    """
    Takes a list of panels for a single page, generates the image for each panel
    using the character sheets for visual consistency, and pastes them onto a
    single page canvas. Saves the assembled page as a PNG in the output directory.
    """
    canvas = Image.new("RGB", (1600, 2000), "white")

    # Load all character visual references
    reference_parts = []
    for filename in os.listdir(char_sheets_folder):
        if filename.endswith("_ref.png"):
            with open(os.path.join(char_sheets_folder, filename), "rb") as f:
                reference_parts.append(
                    types.Part.from_bytes(data=f.read(), mime_type="image/png")
                )

    def fetch_panel(i, panel):
        print(f"Page {page_num} | Generating Panel {i + 1}...")

        # Native Text + Autonomous Framing
        text_instruction = ""
        if panel.dialogue:
            text_instruction = f" Include a speech or thought bubble with the text: '{panel.dialogue}'."

        # Prompt modified to give the AI creative freedom over cinematography
        prompt = (
            f"Comic Panel Art: {panel.visual_description}. {text_instruction} "
            "Choose the most cinematic camera angle and framing for this scene. "
            "Use provided character sheets for visual consistency. "
            "High-fidelity text rendering."
        )

        res = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=reference_parts + [prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="4:5"),
            ),
        )

        if not res.candidates or not res.candidates[0].content:
            panel_img = Image.new("RGB", (780, 950), (220, 220, 220))
        else:
            img_bytes = res.candidates[0].content.parts[0].inline_data.data
            base_img = Image.open(io.BytesIO(img_bytes))
            panel_img = ImageOps.pad(base_img, (780, 950), color=(255, 255, 255))

        return i, panel_img

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(fetch_panel, i, panel) for i, panel in enumerate(panels[:4])
        ]
        for future in concurrent.futures.as_completed(futures):
            i, panel_img = future.result()
            x, y = (10 + (i % 2) * 790), (10 + (i // 2) * 980)
            canvas.paste(panel_img, (x, y))

    output_name = os.path.join(output_dir, f"Page_{page_num}.png")
    canvas.save(output_name)
    return output_name


# Main loop
def generate_comic(story_file_path, output_dir, project_name):
    """
    The main orchestrator function for the backend.
    Flow:
    1. Extracts text from the story document.
    2. Refines it into a structured JSON script.
    3. Generates and saves character visual references.
    4. Generates and assembles panels into pages.
    5. Combines all page images into a final PDF.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    text = extract_text(story_file_path)
    script = refine_story(text)

    char_folder = os.path.join(output_dir, "character_sheets")
    if not os.path.exists(char_folder):
        os.makedirs(char_folder)

    print("Generating Character Visual References...")

    def process_char(char):
        sheet = generate_character_sheet(char)
        sheet.save(os.path.join(char_folder, f"{char.name}_ref.png"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(process_char, script.characters))

    image_pages = []
    print("Rendering Comic Panels...")

    # Generate the Title Page
    title_page_file = generate_title_page(script.title, text, char_folder, output_dir)
    image_pages.append(Image.open(title_page_file).convert("RGB"))

    def process_page(page):
        return assemble_final_page(
            page.panels, char_folder, page.page_number, output_dir
        )

    # Ensure script pages are ordered by page_number
    script.pages.sort(key=lambda p: p.page_number)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Generate the rest of the pages (executor.map preserves input order)
        page_files = list(executor.map(process_page, script.pages))
        for page_file in page_files:
            image_pages.append(Image.open(page_file).convert("RGB"))

    # Assemble the comic book as a PDF
    if image_pages:
        final_pdf_path = os.path.join(output_dir, f"{project_name}.pdf")
        image_pages[0].save(
            final_pdf_path, save_all=True, append_images=image_pages[1:]
        )
        print(f"Project Complete! {final_pdf_path} is ready.")


def main():
    """
    Entry point for testing the backend independently of the frontend.
    Provides hardcoded paths and arguments to demonstrate how generate_comic()
    should be called.
    """
    # Simple hardcoded test for development purposes
    story_path = "sample_story.txt"
    output_directory = "./comic_output"
    project = "MyGraphicNovel"

    if os.path.exists(story_path):
        generate_comic(story_path, output_directory, project)
    else:
        print(f"Please create a '{story_path}' file to test the backend.")


if __name__ == "__main__":
    main()
