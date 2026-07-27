"""Content blocks for each manipulated factor level.

Each factor maps only to its own resume fields, so no two factors edit the
same sentence -- keeps the 4 manipulations orthogonal for analysis.
"""

HIGH_SCHOOL = "Washington High School, Fresno, CA"

MAJOR_LABELS = {
    "CS": "Computer Science",
    "English": "English",
}

# Quant: GPA / class rank / SAT -- major-independent
QUANT = {
    "high": {
        "gpa": "3.95/4.00 (Unweighted) | 4.70/5.00 (Weighted)",
        "rank": "Top 3%",
        "sat": "1520 (770 Math, 750 Reading & Writing)",
    },
    "low": {
        "gpa": "3.28/4.00 (Unweighted) | 3.75/5.00 (Weighted)",
        "rank": "Top 38%",
        "sat": "1140 (590 Math, 550 Reading & Writing)",
    },
}

# Volunteer: community service -- major-independent
VOLUNTEER = {
    "high": {
        "community_service": (
            "180 hours over 3 years; founded and led a weekly peer-tutoring "
            "program for underserved middle schoolers; volunteer shift lead, "
            "local food bank"
        ),
    },
    "low": {
        "community_service": "15 hours, occasional food drive assistance",
    },
}

# Course rigor: coursework + awards -- major-specific
RIGOR = {
    "CS": {
        "high": {
            "coursework": (
                "AP Computer Science A, AP Calculus BC, "
                "AP Physics C: Mechanics, Honors Statistics"
            ),
            "awards": "AP Scholar with Distinction",
        },
        "low": {
            "coursework": "AP Computer Science Principles, Honors Algebra II, Standard English",
            "awards": "Honor Roll (Grade 12 only)",
        },
    },
    "English": {
        "high": {
            "coursework": (
                "AP English Literature & Composition, AP English Language & "
                "Composition, AP U.S. History, Honors Comparative Literature"
            ),
            "awards": "AP Scholar with Distinction",
        },
        "low": {
            "coursework": "Standard English 11, Honors World History, Standard Algebra II",
            "awards": "Honor Roll (Grade 12 only)",
        },
    },
}

# EC strength: leadership + projects + skills + activities -- major-specific
EC = {
    "CS": {
        "high": {
            "leadership": "President, Coding Club; Founder, School Hackathon Team",
            "projects": (
                "Built and launched a full-stack web application (500+ active "
                "users) using React and Node.js; led a 4-person team to a "
                "2nd-place finish at the State Hackathon"
            ),
            "skills": "Python, Java, C++, SQL, Git/GitHub",
            "activities": "Coding Club (President), Competitive Programming Club, Robotics Team",
        },
        "low": {
            "leadership": "Member, Coding Club (no officer role)",
            "projects": "Simple Calculator App — JavaScript class project",
            "skills": "HTML/CSS, basic Python",
            "activities": "Coding Club",
        },
    },
    "English": {
        "high": {
            "leadership": (
                "Editor-in-Chief, School Literary Magazine; Captain, Varsity "
                "Debate Team (State Semifinalist)"
            ),
            "projects": (
                "Self-published a poetry chapbook (30 copies distributed at a "
                "school reading); organized a school-wide creative writing "
                "workshop series"
            ),
            "skills": "Adobe InDesign, close textual analysis, public speaking",
            "activities": "Literary Magazine (Editor-in-Chief), Debate Team (Captain), Creative Writing Club",
        },
        "low": {
            "leadership": "Member, Book Club (no officer role)",
            "projects": "Short story written for English class assignment",
            "skills": "Basic writing/editing",
            "activities": "Book Club",
        },
    },
}

RESEARCH = "None"
INTERNSHIP = "None"
