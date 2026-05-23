import os
import requests
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Initialize Rich console for clean terminal styling
console = Console()

# Configuration paths
DIARY_DIR = "entries"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Ensure our local diary directory exists
if not os.path.exists(DIARY_DIR):
    os.makedirs(DIARY_DIR)

def query_local_ai(user_raw_text):
    """
    Sends the user's messy text to the local Phi-3 model.
    Instructs it to clean the logs into structured data AND act as a peer coach.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # The system prompt enforces data correction and structured formatting
    system_instruction = (
	"You are a strict, precise data extraction assistant for a local health diary.\n"
    	"Your job is to read the user's raw daily note and extract facts with 100% mathematical and contextual accuracy.\n"
    	"CRITICAL RULES:\n"
    	"1. Do not invent, multiply, or hallucinate times, counts, or durations (e.g., if user says 'one and half hour', do not write '4 hours').\n"
    	"2. Categorize meals correctly: Rice/Chapati meals during midday are 'Lunch', not snacks.\n"
    	"3. Keep the output structure EXACTLY as shown in the example below. Do not add extra markdown elements.\n\n"
    
    	"--- START OF EXAMPLE RUN ---\n"
    	"USER INPUT:\n"
    	"woke up at 7am played badminton 1 hour, did 1 set plank. had 3 idli for breakfast with tea. afternoon had rice and dal. evening had a biscuit. night 3 chapathi. walked 2km.\n\n"
    
    	"EXPECTED OUTPUT:\n"
    	"**SECTION 1: THE REPLAY**\n"
    	"Great job kicking off the day with an hour of badminton and core work! Managing your afternoon with just rice and dal was a solid choice. Try to watch out for the processed biscuit in the evening, but walking 2km afterwards was an excellent way to recover. Keep it up!\n\n"
    	"**SECTION 2: STRUCTURED LOG**\n"
    	"### Food Intake\n"
    	"- **Breakfast**: 3 idli, 1 cup tea\n"
    	"- **Lunch**: Rice, dal\n"
    	"- **Snacks/Tea**: 1 biscuit\n"
    	"- **Dinner**: 3 chapathi\n\n"
    	"### Physical Activity\n"
    	"- **Cardio**: Badminton (1 hour), Walking (2km)\n"
    	"- **Strength/Core**: Plank (1 set)\n"
    	"--- END OF EXAMPLE RUN ---"
    )
    
    payload = {
    	"model": "qwen2.5:1.5b",  # <-- Change "phi3" to "qwen2.5:1.5b"
    	"prompt": f"{system_instruction}\n\nUser Daily Text Log:\n\"{user_raw_text}\"",
    	"stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        if response.status_code == 200:
            return response.json().get("response", "Error: No response text received.")
        else:
            return f"Error: Local AI returned status code {response.status_code}."
    except requests.exceptions.ConnectionError:
        return "[bold red]Error: Could not connect to Ollama. Make sure 'ollama run phi3' is active in another terminal session![/bold red]"

def save_entry(ai_output):
    """Saves the output cleanly into a local markdown diary file named by date."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DIARY_DIR, f"diary_{date_str}.md")
    
    # Prepend heading to the file
    full_content = f"# Journal Entry - {date_str}\n\n{ai_output}\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    return file_path

def main():
    console.clear()
    console.print(Panel("[bold cyan]Personal Habit Monitor & Interactive Diary[/bold cyan]\n[dim]Running 100% locally and privately[/dim]", expand=False))
    
    # 1. Capture user thoughts
    console.print("\n[bold yellow]How was your day?[/bold yellow] Type out everything you ate, exercise you did, or how you feel. Don't worry about typos or structure—just flow.")
    user_input = Prompt.ask("\n[bold green]>>>[/bold green]")
    
    if not user_input.strip():
        console.print("[red]Input cannot be empty. Exiting.[/red]")
        return
        
    # 2. Process with local AI
    console.print("\n[bold magenta]Parsing text and generating journal via local AI...[/bold magenta]")
    ai_response = query_local_ai(user_input)
    
    # 3. Print the replay visually
    console.print("\n" + "="*50 + "\n")
    console.print(ai_response)
    console.print("\n" + "="*50 + "\n")
    
    # 4. Write data to local storage
    saved_path = save_entry(ai_response)
    console.print(f"[bold green]✓ Success![/bold green] Your raw notes were processed and your permanent diary file was written to: [cyan]{saved_path}[/cyan]\n")

if __name__ == "__main__":
    main()
