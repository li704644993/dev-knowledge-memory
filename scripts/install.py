#!/usr/bin/env python3
"""Install the configured local development-memory workflow into Codex."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "development-memory"
MCP_SERVER = "development_memory"
MEMORY_PROJECT = "work-development"
BEGIN = "# BEGIN dev-knowledge-memory"
END = "# END dev-knowledge-memory"
REQUIRED_SETTINGS = {
    "work_roots", "knowledge_dir", "codex_home", "skills_dir",
    "memory_state_dir", "basic_memory_command", "embedding_model",
    "embedding_dimensions", "semantic_min_similarity",
}
PATH_SETTINGS = {"knowledge_dir", "codex_home", "skills_dir", "memory_state_dir", "basic_memory_command"}
STARTUP_TIMEOUT_SECONDS = 60
TOOL_TIMEOUT_SECONDS = 120
ENABLED_TOOLS = [
    "search_notes", "read_note", "read_content", "build_context",
    "list_directory", "write_note", "edit_note",
]
NOTE_DIRECTORIES = ("concepts", "topics", "changes")


def configured_path(value):
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"Configuration paths must be absolute or start with ~: {value}")
    return path.resolve()


def load_settings(config_path):
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if set(raw) != REQUIRED_SETTINGS:
        raise ValueError(f"Configuration must contain exactly: {sorted(REQUIRED_SETTINGS)}")
    roots = raw["work_roots"]
    if not isinstance(roots, list) or not roots:
        raise ValueError("work_roots must be a nonempty list of directory paths")
    settings = raw.copy()
    settings.update({key: configured_path(raw[key]) for key in PATH_SETTINGS})
    settings["work_roots"] = [configured_path(root) for root in roots]
    if not isinstance(settings["embedding_model"], str) or not settings["embedding_model"]:
        raise ValueError("embedding_model must be a FastEmbed model name")
    if type(settings["embedding_dimensions"]) is not int or settings["embedding_dimensions"] <= 0:
        raise ValueError("embedding_dimensions must be a positive integer")
    if type(settings["semantic_min_similarity"]) not in (int, float) or not 0 <= settings["semantic_min_similarity"] <= 1:
        raise ValueError("semantic_min_similarity must be between 0 and 1")
    for root in settings["work_roots"]:
        if not root.is_dir():
            raise FileNotFoundError(f"Work root does not exist: {root}")
    if not settings["basic_memory_command"].is_file():
        raise FileNotFoundError(f"Install Basic Memory first: {settings['basic_memory_command']}")
    for key in ("knowledge_dir", "codex_home", "skills_dir", "memory_state_dir"):
        path = settings[key]
        if path.exists() and not path.is_dir():
            raise ValueError(f"{key} must be a directory: {path}")
    return settings


def read_existing(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def replace_managed_block(text, block):
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ValueError("Invalid dev-knowledge-memory markers; review the file before installing")
    if BEGIN not in text:
        separator = "\n" if text.endswith("\n") else "\n\n" if text else ""
        return text + separator + block + "\n"
    prefix, rest = text.split(BEGIN, 1)
    managed, suffix = rest.split(END, 1)
    if BEGIN in managed or END in prefix:
        raise ValueError("Invalid dev-knowledge-memory marker order")
    return prefix + block + suffix


def expected_server(settings):
    return {
        "command": str(settings["basic_memory_command"]),
        "args": ["mcp", "--project", MEMORY_PROJECT],
        "cwd": str(settings["knowledge_dir"]),
        "startup_timeout_sec": STARTUP_TIMEOUT_SECONDS,
        "tool_timeout_sec": TOOL_TIMEOUT_SECONDS,
        "enabled_tools": ENABLED_TOOLS,
        "env": {
            "BASIC_MEMORY_CONFIG_DIR": str(settings["memory_state_dir"]),
            "BASIC_MEMORY_MCP_PROJECT": MEMORY_PROJECT,
            "BASIC_MEMORY_FORCE_LOCAL": "true",
            "BASIC_MEMORY_NO_PROMOS": "1",
        },
    }


def render_mcp(server):
    lines = [BEGIN, f"[mcp_servers.{MCP_SERVER}]"]
    for key, value in server.items():
        if key != "env":
            lines.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["", f"[mcp_servers.{MCP_SERVER}.env]"])
    lines.extend(f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in server["env"].items())
    lines.append(END)
    return "\n".join(lines)


def render_guidance(settings, skill_path):
    roots = ", ".join(f"`{root}`" for root in settings["work_roots"])
    return f"""{BEGIN}
## Development Knowledge Workflow

For development, business-code investigation, bug fixes, review or business-data tasks in {roots}, and their confirmed Git worktrees, use the `{SKILL_NAME}` skill at `{skill_path / 'SKILL.md'}` before choosing an implementation or data-write path and at completion.

Use `{MCP_SERVER}` MCP with project `{MEMORY_PROJECT}`. The only Obsidian knowledge root for this workflow is `{settings['knowledge_dir']}`. Search by relevant terms, read the matching notes and verify the necessary live code; do not preload the library or inspect Research/other vault folders unless explicitly requested. Repository source/configuration/docs remain readable as needed. General external research follows its own workflow.

At completion, without a separate reminder, update affected canonical topics and save materially reusable decisions. Confirm writes and report actual note paths and verification status. If no new knowledge emerged, no note is needed. Do not treat a pending or failed save as complete. Capture remains part of the active task, not a background agent.

Never infer a business-write procedure from a table name; do not execute direct database writes unless explicitly requested. If the knowledge service is unavailable, report it and do not silently switch to a whole-vault search. Current user requests and repository instructions remain authoritative.
{END}"""


def build_plan(settings):
    skill_path = settings["skills_dir"] / SKILL_NAME
    server = expected_server(settings)
    config_path = settings["codex_home"] / "config.toml"
    original_config = read_existing(config_path)
    parsed = tomllib.loads(original_config)
    existing_server = parsed.get("mcp_servers", {}).get(MCP_SERVER)
    if existing_server is not None and BEGIN not in original_config:
        if existing_server != server:
            raise ValueError(f"Unmanaged MCP {MCP_SERVER} conflicts; review {config_path} manually")
        config_content = original_config
    else:
        config_content = replace_managed_block(original_config, render_mcp(server))
    if tomllib.loads(config_content)["mcp_servers"][MCP_SERVER] != server:
        raise ValueError("Rendered MCP configuration does not match the requested settings")

    override = settings["codex_home"] / "AGENTS.override.md"
    if override.exists() and override.read_text(encoding="utf-8").strip():
        raise ValueError(f"Global instructions are shadowed by {override}; integrate manually")
    agents_path = settings["codex_home"] / "AGENTS.md"
    agents_content = replace_managed_block(read_existing(agents_path), render_guidance(settings, skill_path))
    memory_config_path = settings["memory_state_dir"] / "config.json"
    memory_config = {
        "projects": {MEMORY_PROJECT: {"path": str(settings["knowledge_dir"]), "mode": "local"}},
        "default_project": MEMORY_PROJECT,
        "database_backend": "sqlite",
        "semantic_embedding_provider": "fastembed",
        "semantic_embedding_model": settings["embedding_model"],
        "semantic_embedding_dimensions": settings["embedding_dimensions"],
        "semantic_min_similarity": settings["semantic_min_similarity"],
        "reranker_enabled": False,
        "auto_update": False,
        "cloud_promo_opt_out": True,
    }
    if memory_config_path.exists():
        existing_memory = json.loads(memory_config_path.read_text(encoding="utf-8"))
        if existing_memory != memory_config:
            raise ValueError(f"Existing Basic Memory configuration differs; review {memory_config_path}")

    plan = {
        config_path: config_content,
        agents_path: agents_content,
        memory_config_path: json.dumps(memory_config, ensure_ascii=False, indent=2) + "\n",
    }
    source_skill = REPOSITORY_ROOT / "skills" / SKILL_NAME
    for source in sorted(source_skill.rglob("*")):
        if source.is_file():
            target = skill_path / source.relative_to(source_skill)
            if target.exists() and BEGIN not in read_existing(agents_path):
                if target.read_text(encoding="utf-8") != source.read_text(encoding="utf-8"):
                    raise ValueError(f"Unmanaged installed skill differs: {target}")
            plan[target] = source.read_text(encoding="utf-8")
    runtime_settings = {
        key: [str(root) for root in value] if key == "work_roots" else str(value) if key in PATH_SETTINGS else value
        for key, value in settings.items()
    }
    runtime_settings.update({"mcp_server": MCP_SERVER, "memory_project": MEMORY_PROJECT})
    runtime_path = skill_path / "settings.json"
    if runtime_path.exists() and BEGIN not in read_existing(agents_path):
        if json.loads(runtime_path.read_text(encoding="utf-8")) != runtime_settings:
            raise ValueError(f"Unmanaged installed skill settings differ: {runtime_path}")
    plan[runtime_path] = json.dumps(runtime_settings, ensure_ascii=False, indent=2) + "\n"

    index_path = settings["knowledge_dir"] / "README.md"
    if not index_path.exists():
        index = (REPOSITORY_ROOT / "templates" / "knowledge-index.md").read_text(encoding="utf-8")
        for key, value in {
            "KNOWLEDGE_DIR": settings["knowledge_dir"],
            "MEMORY_PROJECT": MEMORY_PROJECT,
            "MCP_SERVER": MCP_SERVER,
        }.items():
            index = index.replace("{{" + key + "}}", str(value))
        plan[index_path] = index
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=REPOSITORY_ROOT / "config.json")
    parser.add_argument("--dry-run", action="store_true", help="Print the install plan without writing or indexing")
    parser.add_argument("--initialize-index", action="store_true", help="Run Basic Memory reindex after configuration installation")
    args = parser.parse_args()
    if args.dry_run and args.initialize_index:
        parser.error("--dry-run and --initialize-index cannot be combined")
    settings = load_settings(args.config.expanduser().resolve())
    plan = build_plan(settings)
    directories = [settings["knowledge_dir"] / name for name in NOTE_DIRECTORIES]
    for directory in directories:
        if directory.exists() and not directory.is_dir():
            raise ValueError(f"Expected a note directory: {directory}")

    print("Dry run" if args.dry_run else "Install")
    for directory in directories:
        print(f"  {'keep' if directory.exists() else 'mkdir'} {directory}")
    for path, content in plan.items():
        action = "unchanged" if path.exists() and read_existing(path) == content else "write"
        print(f"  {action} {path}")
    if args.dry_run:
        return

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    for path, content in plan.items():
        if path.exists() and read_existing(path) == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if args.initialize_index:
        env = os.environ.copy()
        env.update(expected_server(settings)["env"])
        sys.stdout.flush()
        subprocess.run(
            [str(settings["basic_memory_command"]), "reindex", "--project", MEMORY_PROJECT],
            env=env,
            check=True,
        )
        print("Configuration and initial index ready. Restart Codex.")
    else:
        print("Configuration installed. Run again with --initialize-index, then restart Codex.")
    print("Business notes were not imported. Existing research notes were not changed.")


if __name__ == "__main__":
    main()
