# ComicGenarator

ComicGenarator is an AI-powered tool that automatically converts raw story text (TXT, PDF, DOCX) into a fully formatted, multi-page graphic novel. It utilizes advanced AI models (like Gemini) to structure stories into scripts, design consistent characters, and render dynamic comic pages complete with dialogue.

## Software Behavior

Once you select your story document and initiate the generation process (either via the GUI or by running `comic_gen_backend.py`), the software executes the following pipeline:

1. **Text Extraction:**
   - The application reads and extracts raw text from your input file (`.txt`, `.pdf`, or `.docx`).
2. **Script Structuring (`gemini-3.6-flash`):**
   - The raw text is passed to Gemini, which structures it into a strict Pydantic JSON schema (`GraphicNovelScript`). It determines character descriptions, page counts, panel breakdowns, visual scene prompts, and dialogue.
3. **Character Reference Generation (`gemini-3.1-flash-image`):**
   - Before drawing the actual story panels, the model generates standalone **Character Reference Sheets** based on the character descriptions. These are saved to the `character_sheets/` folder in your chosen output directory.
4. **Panel Rendering with Visual Consistency:**
   - The model generates each panel's illustration using `gemini-3.1-flash-image`. During each panel call, the character visual reference image is fed back into the model to preserve character likeness and costume details across panels. Native speech/thought bubbles and dialogue are embedded directly into the scene.
5. **Page Assembly & PDF Export:**
   - The rendered panel images are assembled into full-page layouts and saved in the output directory.
   - Finally, all generated pages are compiled into a final graphic novel PDF (`MyGraphicNovel.pdf`).
   - A page in the resulting comic book could look like:
     
<img width="516" height="640" alt="image" src="https://github.com/user-attachments/assets/d904f010-04c4-4206-a8fa-09d3d5b02f6f" />

## Writing Your Story Description

ComicGenarator is designed to handle varying levels of detail—from simple bedtime stories to structured graphic novel treatments. You can format your story in whatever style best suits your creative vision:

### Option A: Simple Narrative Prose
You can provide an unformatted, straightforward narrative. The AI will handle the pacing, break the story into scenes, and distribute dialogue across panels automatically.

**Example:**
```text
Once upon a time, there was an old man and an old woman.
The old man went to the mountain to gather wood, and the old woman went to the river to wash clothes.
While washing clothes, a giant peach came floating down the river.
She took it home, and when they cut it open, a healthy baby boy popped out.
They named him Momotaro.
Momotaro grew up strong and brave. One day, he set off on a quest to defeat the demons on Onigashima...
```

### Option B: Structured Outline & Visual Motifs
For greater creative control, you can provide an outline broken down into Acts, Loglines, and Visual Motifs. This lets you specify exact artistic directions, color tones, and character dynamics.

**Example:**
```markdown
# Title: Neon Shadows

Logline: A cybernetically enhanced detective tracks down a rogue AI in the rain-slicked underbelly of a futuristic metropolis.

### Act I: The Data Trail
Visual Motif: High-contrast cyberpunk lighting, neon reflections in rain puddles, towering futuristic skyscrapers, and glowing cyan holograms.

Detective Kaelen is investigating an abandoned warehouse in Sector 4.
He kneels beside a dismantled android, discovering a glowing blue memory drive still humming with energy.
Kaelen realizes the rogue AI isn't simply running away—it is assembling something dangerous.

### Act II: The Neon Syndicate
Visual Motif: Crowded underground tech-bazaars, flickering neon signage, steam rising from street grates, and shadowy surveillance drones.
...
```

### Tips for Best Results
- **Character Descriptions:** If you have specific visual requirements for characters (e.g., "wearing a worn leather jacket, neon blue hair, scarred left cheek"), mention them early in the text.
- **Dialogue:** You can include dialogue directly in quotes (e.g., `Kaelen turned and whispered, "We need to move, now."`). The AI will detect and place this dialogue into speech bubbles.
- **Atmosphere & Settings:** Specifying lighting, time of day, or distinct environments helps the image model produce richer, more cinematic panels.


## How It Works: Data-Flow Techniques for Better AI Outcomes

To achieve high-quality and consistent results, ComicGenarator employs several specific data-flow techniques:

1. **Structured Data Extraction (JSON Schema Enforcement)**
   The raw user story text is not fed directly into an image generator. Instead, it is first processed by `gemini-3.6-flash` to extract a structured `GraphicNovelScript` JSON. This structure uses Pydantic models (`Character`, `Page`, `Panel`) to strictly define characters, panel count, visual descriptions, and dialogue. This ensures the AI understands the exact blueprint of the comic before any image generation begins.

2. **Character Visual References (Feedback Loop)**
   Before rendering the comic pages, the system generates "Character Visual References" based on the extracted `Character` models (name, physical traits, clothing). These generated reference sheets are saved and then **fed back into the image generation AI (`gemini-3.1-flash-image`)** as image prompts (`reference_parts`) alongside the text prompt for every panel. This multi-modal data flow guarantees character consistency across different panels and camera angles, solving the common problem of AI "forgetting" what a character looks like.

3. **Autonomous Framing & Native Text**
   The structured `Panel` data separates visual descriptions from dialogue. The dialogue is injected directly into the image generation prompt with instructions to render it as a speech bubble natively ("Include a speech or thought bubble with the text: '...'"). Additionally, the prompt delegates framing choices back to the AI ("Choose the most cinematic camera angle and framing for this scene"), utilizing the model's creative capabilities rather than trying to force rigid constraints.

## How to Use the Code

### Prerequisites
- Python 3.9+
- `google-genai`, `Pillow`, `pydantic`, `python-docx`, `PyPDF2`
- Set your Gemini API key as an environment variable:
  ```bash
  # Linux/macOS
  export GEMINI_API_KEY="your_api_key_here"

  # Windows PowerShell
  $env:GEMINI_API_KEY="your_api_key_here"
  ```

### Running the Backend Independently
You can test the backend pipeline directly by running `comic_gen_backend.py`. 
First, create a sample story text file named `sample_story.txt` in the root directory.

```bash
python comic_gen_backend.py
```
This will read `sample_story.txt`, generate character sheets, render the panels, assemble the pages, and output a final PDF (`MyGraphicNovel.pdf`) in the `./comic_output` directory.

### Running the GUI
If you prefer a visual interface, you can run the GUI prototype:

```bash
python GUI_prototype_1.py
```
This interface allows you to browse for a story file, set the output directory, and start the generation process interactively.

## Project Structure
- `comic_gen_backend.py`: The core orchestrator handling data extraction, API calls to Gemini models (`gemini-3.6-flash` and `gemini-3.1-flash-image`), and image assembly.
- `GUI_prototype_1.py`: The front-end user interface for interacting with the generation pipeline.
- `sample_story.txt`: Sample input story file illustrating a narrative format.
