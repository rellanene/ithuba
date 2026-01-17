import os

# Define the full folder + file structure
structure = {
    "ithuba": {
        "app": {
            "__init__.py": "",
            "config.py": "",
            "db.py": "",
            "auth": {
                "__init__.py": "",
                "routes.py": "",
            },
            "users": {
                "__init__.py": "",
                "routes.py": "",
            },
            "services": {
                "__init__.py": "",
                "routes.py": "",
                "service_logic.py": "",
            },
            "templates": {
                "base.html": "",
                "login.html": "",
                "dashboard.html": "",
                "users": {
                    "manage_users.html": "",
                    "approvals.html": "",
                },
                "services": {
                    "create_request.html": "",
                    "list_requests.html": "",
                    "request_detail.html": "",
                },
            },
        },
        "static": {
            "css": {
                "style.css": "",
            }
        },
        "run.py": "",
        "requirements.txt": "",
    }
}


def create_structure(base_path, tree):
    for name, content in tree.items():
        path = os.path.join(base_path, name)

        # If content is a dict → it's a folder
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)

        # If content is a string → it's a file
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


if __name__ == "__main__":
    create_structure(".", structure)
    print("Project structure created successfully!")