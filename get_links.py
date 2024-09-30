import csv
import os
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Get API token
# https://edstem.org/au/settings/api-tokens

AUTH_HEADER = {
    "Authorization": f"Bearer {os.getenv('AUTH_TOKEN')}",
    "Content-Type": "application/json",
}


# ED challange id used in api, slide id use in the url for the website

# q1
API_ID = 134120
SLIDE_ID = 414786

# # q2
# API_ID = 134120
# SLIDE_ID = 404316

# # q3
# API_ID = 134121
# SLIDE_ID = 404317

# # q4
# API_ID = 134122
# SLIDE_ID = 404318


STUDENTS_FILE = "students.txt"
# example data:
"""

ZAKA	ABBASOV	-	ZABB0738@UNI.SYDNEY.EDU.AU
KASHYAP KOUTILYA	ADIPUDI	-	KADI0215@UNI.SYDNEY.EDU.AU
AKANKSHA	AGARWAL	-	AAGA0750@UNI.SYDNEY.EDU.AU
FENDY ARDIANSYAH	ALFAN	-	FALF0810@UNI.SYDNEY.EDU.AU
MOHAMMED	ALHUSSAIN	-	MALH0057@UNI.SYDNEY.EDU.AU

"""


# Ed apt endpoints
USERS_API_URL = f"https://edstem.org/api/challenges/{API_ID}/users"
SUBMISSIONS_API_URL_TEMPLATE = (
    f"https://edstem.org/api/users/{{student_id}}/challenges/{API_ID}/submissions"
)
SUBMISSION_URL_TEMPLATE = f"https://edstem.org/au/courses/18651/lessons/61238/slides/{SLIDE_ID}/submissions?u={{student_id}}&s={{submission_id}}"

# for student with staff email
MISSING_EMAIL_URL_TEMPLATE = f"https://edstem.org/au/courses/18651/lessons/61238/slides/{SLIDE_ID}/submissions?q={{query}}"


def read_student_data(file_path):
    """
    Reads the students.txt file and extracts a list of student data.
    """
    student_data = []
    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(
                file,
                delimiter="\t",
                fieldnames=["first_name", "last_name", "preferred_name", "email"],
            )
            for row in reader:
                student_data.append(
                    {
                        "first_name": row["first_name"].strip(),
                        "last_name": row["last_name"].strip(),
                        "email": row["email"].strip().lower(),
                    }
                )
        return student_data
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return []


def fetch_users():
    """
    Fetches users from the API endpoint.
    """
    response = requests.get(USERS_API_URL, headers=AUTH_HEADER)
    if response.status_code == 200:
        return response.json().get("users", [])
    else:
        print(
            f"Failed to fetch users. Status code: {response.status_code}",
            file=sys.stderr,
        )
        return []


def fetch_submissions(student_id):
    """
    Fetches submissions for a specific student ID.
    """
    url = SUBMISSIONS_API_URL_TEMPLATE.format(student_id=student_id)
    response = requests.get(url, headers=AUTH_HEADER)
    if response.status_code == 200:
        return response.json().get("submissions", [])
    else:
        print(
            f"Failed to fetch submissions for student ID {student_id}. "
            f"Status code: {response.status_code}",
            file=sys.stderr,
        )
        return []


def parse_iso_datetime(iso_string):
    """
    Converts an ISO 8601 datetime string to a datetime object in UTC timezone.
    """
    return datetime.fromisoformat(iso_string.rstrip("Z")).replace(tzinfo=timezone.utc)


def find_accepted_submission(submissions):

    after_cutoff_submissions = [submission for submission in submissions]

    if len(after_cutoff_submissions) > 10:
        return max(submissions, key=lambda s: parse_iso_datetime(s["created_at"]))

    # 3.
    return max(submissions, key=lambda s: parse_iso_datetime(s["created_at"]))


def main():
    current_datetime = datetime.now()
    students = read_student_data(STUDENTS_FILE)
    if not students:
        print("No student data found. Exiting.")
        return

    users = fetch_users()
    if not users:
        print("No users fetched from API. Exiting.")
        return

    user_dict = {user["email"]: user["id"] for user in users}

    for student in students:
        email = student["email"]
        first_name = student["first_name"]
        last_name = student["last_name"]

        if email in user_dict:
            student_id = user_dict[email]
            submissions = fetch_submissions(student_id)
            time.sleep(0.2)
            if not submissions:
                print("No submissions found, as of", current_datetime)
                continue

            latest_submission = find_accepted_submission(submissions)
            if latest_submission:
                submission_url = SUBMISSION_URL_TEMPLATE.format(
                    student_id=student_id, submission_id=latest_submission["id"]
                )
                print(submission_url)
            else:
                print("LATE - No valid submissions before cutoff datetime")
        else:
            # student with staff email can't be found
            query = f"{first_name}%20{last_name}"
            missing_email_url = MISSING_EMAIL_URL_TEMPLATE.format(query=query)
            print(missing_email_url)


if __name__ == "__main__":
    main()
