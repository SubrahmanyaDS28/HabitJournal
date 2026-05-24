import os
import requests
import json
import csv
import argparse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Initialize Rich console
console = Console()

# Configuration default fallbacks
DIARY_DIR = "entries"
CSV_FILE = "history.csv"

def load_env_config():
    """Loads settings from a local .env file manually without external dependencies."""
    config = {
        "OLLAMA_URL": "http://localhost:11434/api/generate",
        "AI_MODEL": "qwen2.5:1.5b",
        "TIMEOUT_SEC": 60
    }
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config

# Load settings from the clean config layer
ENV = load_env_config()

if not os.path.exists(DIARY_DIR):
    os.makedirs(DIARY_DIR)

def analyze_historical_weaknesses():
    """Reads history.csv to evaluate the last 7 entries for routines and traps."""
    if not os.path.exists(CSV_FILE):
        return None
        
    try:
        with open(CSV_FILE, "r") as f:
            reader = list(csv.DictReader(f))
            
        # Grab up to the last 7 entries
        recent_history = reader[-7:]
        if not recent_history:
            return None
            
        total_days = len(recent_history)
        badminton_days = 0
        total_planks = 0
        total_diet_score = 0.0
        
        for row in recent_history:
            if float(row.get("Badminton_Mins", 0) or 0) > 0:
                badminton_days += 1
            total_planks += int(row.get("Plank_Sets", 0) or 0)
            total_diet_score += float(row.get("Diet_Score", 100) or 100)
            
        avg_diet = total_diet_score / total_days
        
        # Compile targeted warning flags
        warnings = []
        if badminton_days < 3 and total_days >= 4:
            warnings.append(f"🔴 Low Cardio: Played badminton only {badminton_days}/{total_days} days.")
        if total_planks < (total_days * 1):
            warnings.append(f"🟠 Core Slippage: Averaging less than 1 plank set per day ({total_planks} total).")
        if avg_diet < 75.0:
            warnings.append(f"⚠️  Nutritional Risk: 7-day diet discipline dropped to {avg_diet:.1f}%. Watch out for carb traps!")
            
        return {
            "days": total_days,
            "badminton_frequency": f"{badminton_days}/{total_days}",
            "total_planks": total_planks,
            "avg_diet": round(avg_diet, 1),
            "warnings": warnings
        }
    except Exception:
        return None

def query_local_ai(user_raw_text, quick_stats, historical_summary):
    """Uses the local model to generate coach responses, factoring in historical trends."""
    system_instruction = (
        "You are an encouraging personal health and routine coach for an embedded systems engineer.\n"
        "Review the user's raw daily notes, current metrics, and historical warnings. Provide a supportive 3-4 sentence summary.\n"
        "Praise their consistency and address any lingering multi-day weaknesses mentioned in the data."
    )
    
    history_context = "No historical warnings."
    if historical_summary and historical_summary["warnings"]:
        history_context = " ".join(historical_summary["warnings"])
        
    contextual_prompt = (
        f"--- HISTORICAL TRENDS (LAST 7 DAYS) ---\n{history_context}\n\n"
        f"--- TODAY'S DATA ---\n"
        f"Badminton: {quick_stats['badminton']} mins, Plank Sets: {quick_stats['planks']}, "
        f"Squats: {quick_stats['squats']}, Diet Discipline Score: {quick_stats['diet_score']}/100.\n"
        f"Notes: {user_raw_text}"
    )
    
    payload = {
        "model": ENV["AI_MODEL"],
        "prompt": f"{system_instruction}\n\nUser Data:\n{contextual_prompt}",
        "stream": False
    }
    
    try:
        response = requests.post(ENV["OLLAMA_URL"], json=payload, timeout=int(ENV["TIMEOUT_SEC"]))
        if response.status_code == 200:
            return response.json().get("response", "Keep pushing forward!")
        return "Excellent effort today! Keep sticking to your routine."
    except Exception:
        return f"Ollama server offline or timed out, but your data has been successfully saved locally!"

def log_to_csv(date_str, stats):
    """Appends data to a local spreadsheet database."""
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Badminton_Mins", "Plank_Sets", "Squat_Reps", "Diet_Score"])
        writer.writerow([date_str, stats["badminton"], stats["planks"], stats["squats"], stats["diet_score"]])

def generate_trend_chart():
    """Reads the local CSV data and generates a clean habit tracking visualization."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        dates, badminton, planks = [], [], []
        if not os.path.exists(CSV_FILE):
            return

        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dates.append(row.get("Date", "")[-5:])
                badminton.append(float(row.get("Badminton_Mins", 0) or 0))
                planks.append(int(row.get("Plank_Sets", 0) or 0))
        
        if not dates:
            return

        fig, ax1 = plt.subplots(figsize=(10, 4))
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Badminton (Mins)", color="tab:blue")
        ax1.plot(dates, badminton, color="tab:blue", marker="o", linewidth=2, label="Badminton")
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        
        ax2 = ax1.twinx()
        ax2.set_ylabel("Plank (Sets)", color="tab:orange")
        ax2.step(dates, planks, color="tab:orange", where="mid", linestyle="--", label="Planks")
        ax2.tick_params(axis="y", labelcolor="tab:orange")
        
        plt.title("Habit & Activity Consistency Trends")
        fig.tight_layout()
        plt.savefig("progress_chart.png")
        plt.close()
        console.print("[bold green]📈 Progress chart automatically updated: progress_chart.png[/bold green]")
    except Exception:
        pass 

def parse_arguments():
    """Defines flexible command line flags for swift automation logging."""
    parser = argparse.ArgumentParser(description="HabitJournal CLI Automation Driver")
    parser.add_argument("-b", "--badminton", type=float, help="Badminton playtime in minutes")
    parser.add_argument("-p", "--planks", type=int, help="Completed 1-minute plank sets")
    parser.add_argument("-s", "--squats", type=int, help="Total bodyweight squats completed")
    parser.add_argument("-m", "--notes", type=str, help="Free flow daily log/notes")
    return parser.parse_args()

def main():
    args = parse_arguments()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Run the Historical Analysis Engine FIRST
    history_report = analyze_historical_weaknesses()
    
    cli_mode = any(v is not None for v in [args.badminton, args.planks, args.squats, args.notes])
    
    if not cli_mode:
        console.clear()
        console.print(Panel("[bold cyan]Personal Habit Monitor & Interactive Diary v2.2[/bold cyan]\n[dim]Historical Trend Analytics Engine Enabled[/dim]", expand=False))
        
        # Display the Historical Report explicitly if data exists
        if history_report:
            table = Table(title="📊 Weekly Health & Routine Status Report", title_justify="left")
            table.add_column("Metric Description", style="cyan")
            table.add_column("7-Day Standing", style="magenta")
            
            table.add_row("Badminton Consistency", f"{history_report['badminton_frequency']} days active")
            table.add_row("Core Strength (Planks)", f"{history_report['total_planks']} sets executed")
            table.add_row("Diet Discipline Average", f"{history_report['avg_diet']}% adherence")
            console.print(table)
            
            if history_report["warnings"]:
                console.print("[bold yellow]🚨 System Diagnosis / Weakness Signals Detected:[/bold yellow]")
                for warn in history_report["warnings"]:
                    console.print(f"  {warn}")
                console.print("")
        
        console.print("[bold yellow]Step 1: Log Your Core Engineering Metrics[/bold yellow]")
        badminton_mins = float(Prompt.ask("Badminton play time today (in minutes)", default="0"))
        plank_sets = int(Prompt.ask("How many 1-minute plank sets completed", default="0"))
        squat_reps = int(Prompt.ask("Total bodyweight squats completed", default="0"))
        
        console.print("\n[bold green]🥗 Daily Diet Checklist (Enter 'y' for Yes, 'n' for No):[/bold green]")
        rule1 = Prompt.ask("Avoided the 'Double Carb' trap (Rice + Chapati together)?", choices=["y", "n"], default="y")
        rule2 = Prompt.ask("Kept liquid sugar low (Cut excess tea/coffee)?", choices=["y", "n"], default="y")
        rule3 = Prompt.ask("Avoided processed evening junk food?", choices=["y", "n"], default="y")
        rule4 = Prompt.ask("Kept dinner portion disciplined?", choices=["y", "n"], default="y")
        
        followed_rules = [rule1, rule2, rule3, rule4].count("y")
        diet_score_pct = followed_rules * 25
        
        console.print("\n[bold yellow]Step 2: Free Flow Diary[/bold yellow]")
        user_input = Prompt.ask("[bold green]>>>[/bold green]")
    else:
        console.print("[bold green]🚀 Running in automated CLI mode...[/bold green]")
        badminton_mins = args.badminton if args.badminton is not None else 0.0
        plank_sets = args.planks if args.planks is not None else 0
        squat_reps = args.squats if args.squats is not None else 0
        user_input = args.notes if args.notes is not None else "No journal entry notes provided."
        diet_score_pct = 100

    stats = {
        "badminton": badminton_mins,
        "planks": plank_sets,
        "squats": squat_reps,
        "diet_score": diet_score_pct
    }
    
    # Scan for localized carb traps
    high_carb_keywords = ["dosa", "idli", "rice", "biryani", "parotta", "chapati"]
    found_carbs = [item for item in high_carb_keywords if item in user_input.lower()]
    if found_carbs:
        console.print(f"[bold yellow]⚠️  Python Scanner: High-carb indicators noted locally: {found_carbs}[/bold yellow]")
    
    # Process updates
    log_to_csv(date_str, stats)
    generate_trend_chart()
    
    console.print("\n[bold magenta]Generating peer coach analysis via local AI...[/bold magenta]")
    ai_response = query_local_ai(user_input, stats, history_report)
    
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
    
    file_path = os.path.join(DIARY_DIR, f"diary_{date_str}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Journal Entry - {date_str}\n\n{markdown_output}")
        
    console.print(f"[bold green]✓ Log complete![/bold green] Saved to [cyan]{file_path}[/cyan]")

if __name__ == "__main__":
    main()