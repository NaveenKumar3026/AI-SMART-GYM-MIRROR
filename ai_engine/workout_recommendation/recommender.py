from typing import List, Dict, Any, Optional

class WorkoutRecommender:
    # Repository of exercises and their descriptions/muscles
    EXERCISES_DB = {
        "Squat": {"category": "Lower Body", "muscles": ["quadriceps", "gluteus_maximus", "hamstrings"]},
        "Push-up": {"category": "Upper Body Press", "muscles": ["chest", "triceps", "front_deltoids"]},
        "Bench Press": {"category": "Upper Body Press", "muscles": ["chest", "triceps", "front_deltoids"]},
        "Pull-up": {"category": "Upper Body Pull", "muscles": ["lats", "biceps", "upper_back"]},
        "Deadlift": {"category": "Full Body / Posterior", "muscles": ["hamstrings", "gluteus_maximus", "lower_back"]},
        "Shoulder Press": {"category": "Upper Body Press", "muscles": ["shoulders", "triceps"]},
        "Bicep Curl": {"category": "Arms", "muscles": ["biceps", "forearms"]},
        "Lunges": {"category": "Lower Body", "muscles": ["quadriceps", "gluteus_maximus", "calves"]}
    }

    def recommend(self, goal: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recommends a custom workout plan based on fitness goal and historical exercises.
        Fitness Goals: "Muscle Gain", "Weight Loss", "Strength", "Endurance"
        """
        # Determine sets and reps scheme based on goal
        if goal == "Strength":
            sets, reps = 4, 6
            description = "High sets, low reps focus on compound exercises to maximize mechanical tension and neurological adaptation."
        elif goal == "Weight Loss":
            sets, reps = 3, 15
            description = "High reps, low rest scheme to keep heart rate elevated, maximize caloric burn, and improve aerobic efficiency."
        elif goal == "Endurance":
            sets, reps = 3, 20
            description = "High volume endurance training focusing on local muscle endurance and stamina."
        else: # "Muscle Gain" (Hypertrophy)
            sets, reps = 3, 10
            description = "Classic hypertrophy volume (3-4 sets of 8-12 reps) to stimulate muscle protein synthesis."

        # Count frequencies of exercises in history to find under-trained exercises
        exercise_counts = {}
        for session in history:
            ex_name = session.get("exercise_name")
            if ex_name:
                exercise_counts[ex_name] = exercise_counts.get(ex_name, 0) + 1

        # Select exercises based on goal and variety
        # Let's order exercises to ensure a balanced full-body or split routine
        all_exercises = list(self.EXERCISES_DB.keys())
        
        # Sort exercises: prioritize ones that have been performed LESS in the history
        sorted_exercises = sorted(all_exercises, key=lambda x: exercise_counts.get(x, 0))

        # Build a plan
        # We select 4-5 exercises to form a balanced routine (incorporating at least one Lower Body, Upper Body Press, Upper Body Pull)
        selected = []
        has_lower = False
        has_press = False
        has_pull = False

        for ex in sorted_exercises:
            ex_info = self.EXERCISES_DB[ex]
            cat = ex_info["category"]
            
            # Select logic to ensure balance
            if cat == "Lower Body" and not has_lower:
                selected.append(ex)
                has_lower = True
            elif cat == "Upper Body Press" and not has_press:
                selected.append(ex)
                has_press = True
            elif cat == "Upper Body Pull" and not has_pull:
                selected.append(ex)
                has_pull = True
            elif len(selected) < 4:
                selected.append(ex)

        # Ensure we have at least 4 exercises
        for ex in sorted_exercises:
            if ex not in selected and len(selected) < 5:
                selected.append(ex)

        # Formulate items
        workout_items = []
        estimated_calories = 0
        
        for idx, ex in enumerate(selected):
            # Calculate dynamic calorie burn baseline
            # Squats/Deadlifts burn more than Curls
            cal_multiplier = 0.15 if ex in ["Squat", "Deadlift"] else 0.08
            ex_calories = int(sets * reps * cal_multiplier * 75) # baseline weight of 75kg
            estimated_calories += ex_calories

            workout_items.append({
                "exercise_name": ex,
                "sets": sets,
                "reps": reps,
                "target_rest_seconds": 90 if goal == "Strength" else 60,
                "muscles_targeted": self.EXERCISES_DB[ex]["muscles"],
                "estimated_calories": ex_calories
            })

        return {
            "name": f"{goal} Optimizer Routine",
            "goal": goal,
            "description": description,
            "estimated_duration_minutes": len(selected) * 8,
            "estimated_calories_burned": estimated_calories,
            "exercises": workout_items
        }
