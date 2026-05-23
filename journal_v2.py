import os
import requests
import json
import csv
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Initialize Rich console
console = Console()

# Configuration paths
DIARY_DIR = "entries"
OLLAMA_URL = "http://localhost:11434/api/generate"
CSV_FILE = "history.csv"

if not os.path.exists(DIARY_DIR):
    os.makedirs(DIARY_DIR)

def query_local_ai(user_raw_text, quick_stats):
    """Uses Qwen2.5:1.5b to generate a contextual, supportive peer-coach response."""
    system_instruction = (
        "You are an encouraging personal health and routine coach for an embedded systems engineer.\n"
        "Review the user's raw daily notes and their metrics. Provide a supportive 3-4 sentence summary.\n"
        "Praise their consistency (like badminton or core work) and gently highlight potential calorie traps."
    )
    
    # UPGRADED: Now passing the explicit diet score into the local LLM context
    contextual_prompt = (
        f"Metrics Today -> Badminton: {quick_stats['badminton']} mins, "
        f"Plank Sets: {quick_stats['planks']}, Squats: {quick_stats['squats']}, "
        f"Diet Discipline Score: {quick_stats['diet_score']}/100.\n"
        f"Notes: {user_raw_text}"
    )
    
    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": f"{system_instruction}\n\nUser Data:\n{contextual_prompt}",
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "Keep pushing forward!")
        return "Excellent effort today! Keep sticking to your routine."
    except Exception:
        return "Ollama server offline, but your data has been successfully saved locally!"

def log_to_csv(date_str, stats):
    """Appends strict, mathematically accurate data to a local spreadsheet database."""
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # UPGRADED: Added Diet_Score to tracking metrics
        if not file_exists:
            writer.writerow(["Date", "Badminton_Mins", "Plank_Sets", "Squat_Reps", "Diet_Score"])
        writer.writerow([date_str, stats["badminton"], stats["planks"], stats["squats"], stats["diet_score"]])

def generate_trend_chart():
    """Reads the local CSV data and generates a clean habit tracking visualization."""
    try:
        import matplotlib.pyplot as plt
        dates, badminton, planks = [], [], []
        
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dates.append(row["Date"][-5:]) # Just keep MM-DD
                badminton.append(float(row["Badminton_Mins"]))
                planks.append(int(row["Plank_Sets"]))
        
        fig, ax1 = plt.subplots(figsize=(10, 4))
        
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Badminton (Mins)", color="tab:blue")
        ax1.plot(dates, badminton, color="tab:blue", marker="o", linewidth=2)
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        
        ax2 = ax1.twinx()
        ax2.set_ylabel("Plank (Sets)", color="tab:orange")
        ax2.step(dates, planks, color="tab:orange", where="mid", linestyle="--")
        ax2.tick_params(axis="y", labelcolor="tab:orange")
        
        plt.title("Habit & Activity Consistency Trends")
        fig.tight_layout()
        plt.savefig("progress_chart.png")
        plt.close()
        console.print("[bold green]📈 Progress chart automatically updated: progress_chart.png[/bold green]")
    except Exception:
        pass # Handle if matplotlib faces headless display issues inside basic WSL profiles

def main():
    console.clear()
    console.print(Panel("[bold cyan]Personal Habit Monitor & Interactive Diary v2.0[/bold cyan]\n[dim]Hybrid Engineering Architecture[/dim]", expand=False))
    
    date_str = datetime.now().strftime("%Y-%m-%d")
   
    # 1. Gather 100% Accurate Metrics First
    console.print("\n[bold yellow]Step 1: Log Your Core Engineering Metrics[/bold yellow]")
    badminton_mins = Prompt.ask("Badminton play time today (in minutes)", default="0")
    plank_sets = Prompt.ask("How many 1-minute plank sets completed", default="0")
    squat_reps = Prompt.ask("Total bodyweight squats completed", default="0")
    
    # Interactive Diet Scoring Checklist
    console.print("\n[bold green]🥗 Daily Diet Checklist (Enter 'y' for Yes, 'n' for No):[/bold green]")
    rule1 = Prompt.ask("Avoided the 'Double Carb' trap (Rice + Chapati together)?", choices=["y", "n"], default="y")
    rule2 = Prompt.ask("Kept liquid sugar low (Cut excess tea/coffee or drank buttermilk)?", choices=["y", "n"], default="y")
    rule3 = Prompt.ask("Avoided processed evening junk food (No Kurkure/Lays/Biscuits)?", choices=["y", "n"], default="y")
    rule4 = Prompt.ask("Kept dinner portion disciplined (Light carbs/no heavy late curd)?", choices=["y", "n"], default="y")
    
    # Calculate explicit compliance score
    followed_rules = [rule1, rule2, rule3, rule4].count("y")
    diet_score_pct = followed_rules * 25
    
    stats = {
        "badminton": float(badminton_mins if badminton_mins.isdigit() else 0),
        "planks": int(plank_sets if plank_sets.isdigit() else 0),
        "squats": int(squat_reps if squat_reps.isdigit() else 0),
        "diet_score": diet_score_pct
    }
    
    # 2. Log unstructured reflections
    console.print("\n[bold yellow]Step 2: Free Flow Diary[/bold yellow] (What did you eat? Special events?)")
    user_input = Prompt.ask("[bold green]>>>[/bold green]")
    
    # UPGRADED: Python-level localized string scan for keyword carb traps
    high_carb_keywords = ["dosa", "idli", "rice", "biryani", "parotta", "chapati"]
    found_carbs = [item for item in high_carb_keywords if item in user_input.lower()]
    if found_carbs:
        console.print(f"[bold yellow]⚠️  Python Scanner: High-carb indicators noted locally: {found_carbs}[/bold yellow]")
    
    # 3. Process database entries and visualization
    log_to_csv(date_str, stats)
    generate_trend_chart()
    
    # 4. Generate AI feedback based on hybrid inputs
    console.print("\n[bold magenta]Generating peer coach analysis...[/bold magenta]")
    ai_response = query_local_ai(user_input, stats)
    
    # 5. Build Final Markdown Structure cleanly inside Python
    markdown_output = (
        f"## 🕒 Activity Dashboard\n"
        f"- **Badminton Cardio**: {stats['badminton']} minutes\n"
        f"- **Core Planks**: {stats['planks']} sets\n"
        f"- **Leg Squats**: {stats['squats']} reps\n"
        f"- **Diet Discipline Score**: {stats['diet_score']}/100\n\n"
        f"## 📝 Raw Journal Entry\n"
        f"{user_input}\n\n"
        f"## 🤖 Coach Feedback\n"
        f"{ai_response}\n"
    )
    
    print("\n" + "="*50 + "\n")
    console.print(markdown_output)
    print("="*50 + "\n")
    
    # Save file
    file_path = os.path.join(DIARY_DIR, f"diary_{date_str}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Journal Entry - {date_str}\n\n{markdown_output}")
        
    console.print(f"[bold green]✓ Log complete![/bold green] Saved to [cyan]{file_path}[/cyan]")

if __name__ == "__main__":
    main()