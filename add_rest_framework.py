import sys

# Read the file
with open('pollr_backend/pollr_backend/settings.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with staticfiles and insert after it
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if "'django.contrib.staticfiles'," in line:
        # Add rest_framework apps after staticfiles
        new_lines.append("    'rest_framework',\n")
        new_lines.append("    'rest_framework_simplejwt',\n")

# Write back
with open('pollr_backend/pollr_backend/settings.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully added rest_framework to INSTALLED_APPS")
