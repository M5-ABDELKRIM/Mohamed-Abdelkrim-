import os

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_data(modules_file, marks_file):
    modules_df = pd.read_csv(modules_file, header=None, names=["Module_Code", "Module_Name"])
    marks_df = pd.read_csv(marks_file, header=None)

    modules_df["Credits"] = modules_df["Module_Code"].apply(lambda code: 30 if "-30-" in code else 15)

    structured_data = []
    for _, row in marks_df.iterrows():
        student_id = row[0]
        row_data = row[1:].values

        for i in range(0, len(row_data), 2):
            if i + 1 < len(row_data):
                module_code = row_data[i]
                mark = row_data[i + 1]
                structured_data.append([student_id, module_code, mark])

    marks_df = pd.DataFrame(structured_data, columns=["Student_ID", "Module_Code", "Mark"])
    marks_df["Mark"] = pd.to_numeric(marks_df["Mark"], errors="coerce")
    return modules_df, marks_df.merge(modules_df, on="Module_Code", how="left")


def calculate_weighted_average(marks_df, level):
    level_df = marks_df[marks_df["Module_Code"].astype(str).str.endswith(f"-{level}")].copy()

    if level_df.empty:
        return 0

    if level == "2":
        level_df = level_df.sort_values(by="Mark", ascending=False)
        level_df = level_df[level_df["Credits"].cumsum() <= 100]

    level_df["Weighted_Mark"] = level_df["Mark"] * level_df["Credits"]
    total_credits = level_df["Credits"].sum()

    if total_credits == 0:
        return 0

    return level_df["Weighted_Mark"].sum() / total_credits


def calculate_final_degree(marks_df):
    degree_results = []

    for student_id in marks_df["Student_ID"].unique():
        student_marks = marks_df[marks_df["Student_ID"] == student_id]

        avg_level5 = calculate_weighted_average(student_marks, "2")
        avg_level6 = calculate_weighted_average(student_marks, "3")
        final_mark = ((avg_level6 * 3) + avg_level5) / 4

        if final_mark >= 70:
            classification = "First Class"
        elif final_mark >= 60:
            classification = "Upper Second (2.1)"
        elif final_mark >= 50:
            classification = "Lower Second (2.2)"
        elif final_mark >= 40:
            classification = "Third Class"
        else:
            classification = "Fail"

        degree_results.append([student_id, avg_level5, avg_level6, final_mark, classification])

    return pd.DataFrame(
        degree_results,
        columns=["Student_ID", "Avg_Level5", "Avg_Level6", "Final_Mark", "Classification"],
    )


def main():
    modules_file = os.path.join(BASE_DIR, "cs_modules.csv")
    marks_file = os.path.join(BASE_DIR, "task1_1_marks.csv")
    _, marks_df = load_data(modules_file, marks_file)

    degree_results = calculate_final_degree(marks_df)
    output_path = os.path.join(BASE_DIR, "degree_results_fixed.csv")
    degree_results.to_csv(output_path, index=False)
    print(f"Degree results saved to: {output_path}")


if __name__ == "__main__":
    main()
