import json
from vibe_agent.generator.build_plan import BuildPlan

def render_static(plan: BuildPlan) -> str:
    return f"""FROM caddy:2-alpine
COPY . /usr/share/caddy
EXPOSE {plan.port}
"""

def node_base_image(plan: BuildPlan) -> str:
    # Bun apps run on Bun, not Node
    if plan.package_manager == "bun":
        return f"oven/bun:{plan.runtime_version}-alpine"
    return f"node:{plan.runtime_version}-alpine"

def node_setup_line(plan: BuildPlan) -> str:
    # node:alpine only ships npm; corepack switches on pnpm and yarn
    if plan.package_manager in ["pnpm", "yarn"]:
        return "RUN corepack enable\n"
    return ""

def render_node(plan: BuildPlan) -> str:
 # build step is optional (plain-JS Express needs none: Node runs .js files directly)
    build_line = ""
    if plan.build_command: 
        build_line = f"RUN {plan.build_command}\n"
    
    # "npm run start" -> ["npm", "run", "start"],
    # uses the start command given from the planner to create the actual docker command to start the container 
    cmd = json.dumps(plan.start_command.split())

    return f"""FROM {node_base_image(plan)}
WORKDIR /app
COPY . .
{node_setup_line(plan)}RUN {plan.install_command}
{build_line}ENV NODE_ENV=production
ENV PORT={plan.port}
EXPOSE {plan.port}
CMD {cmd}
"""

def render_vite(plan: BuildPlan) -> str:
    # stage 1 builds with Node; sstage 2 ships only the built files with Caddy
    return f"""FROM {node_base_image(plan)} AS build
WORKDIR /app
COPY . .
{node_setup_line(plan)}RUN {plan.install_command}
RUN {plan.build_command}

FROM caddy:2-alpine
COPY --from=build /app/{plan.output_dir} /usr/share/caddy
EXPOSE {plan.port}
"""

def render_fastapi(plan: BuildPlan) -> str:

    #because python slim doesn not have uv installed and only has pip
    #if the package manager for a python app is uv there will be an error 
    #uv and poetry build using a venv where all the files exist so they need to be handled different 
    #in order to handle a successful build
    #pip is already in python:slim, so no setup by default
    setup_line = ""
    if plan.package_manager == "uv":
       setup_line = (
            "COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv\n"
            'ENV PATH="/app/.venv/bin:$PATH"\n'
        )

    if plan.package_manager == "poetry":
        setup_line = (
            "RUN pip install --no-cache-dir poetry\n"
            "RUN poetry config virtualenvs.create false\n"
        )
    # "uvicorn main:app --host 0.0.0.0 --port 8000" -> ["uvicorn", "main:app", ...] 
    # this is what the start command looks like from the planner 
    cmd = json.dumps(plan.start_command.split())

    return f"""FROM python:{plan.runtime_version}-slim
WORKDIR /app
COPY . .
{setup_line}RUN {plan.install_command}
ENV PYTHONUNBUFFERED=1
EXPOSE {plan.port}
CMD {cmd}
"""

DOCKERIGNORE = [
    # secrets
    "**/.env", "**/.env.*", "!**/.env.example",
    "**/*.pem", "**/*.key", "**/*.p12", "**/*.pfx", "**/id_rsa*",
    # databases and dumps
    "**/*.sql", "**/*.sqlite", "**/*.sqlite3", "**/*.db", "**/*.dump",
    # installed packages (reinstalled inside the image)
    "**/node_modules", "**/.venv", "**/venv", "**/__pycache__", "**/*.pyc",
    # build output (rebuilt inside the image)
    "**/.next",
    # junk
    "**/.git", "**/.DS_Store", "**/*.log", "**/.vscode", "**/.idea", "**/coverage",
    # the build files themselves
    "Dockerfile", ".dockerignore",
]


RENDERERS = {
    "static": render_static,
    "vite": render_vite,
    "next": render_node,
    "node-server": render_node,
    "fastapi": render_fastapi,
}

def render_dockerfile(plan: BuildPlan) -> str:
    renderer = RENDERERS.get(plan.framework)
    if renderer is None:
        raise ValueError(f"No Dockerfile template for framework: {plan.framework}")
    return renderer(plan)

def render_dockerignore() -> str:
    # one pattern per line
    return "\n".join(DOCKERIGNORE) + "\n"  