import tomllib

import yaml

from ccx.cli import main


def test_mcp_and_hooks_together_preserve_both_in_codex_config(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        yaml.dump({
            "hooks": {
                "SessionStart": [{"hooks": [{"command": "echo"}]}]
            }
        })
    )

    assert main(["sync"]) == 0
    config = tomllib.loads((tmp_ccx_home / ".codex" / "config.toml").read_text())
    assert "mcp_servers" in config
    assert config["mcp_servers"]["s1"]["command"] == "npx"
    assert config["features"]["codex_hooks"] is True


def test_codex_passthrough_config_merges_with_generated(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    # Passthrough codex/config.toml adds sandbox_mode.
    passthrough_dir = tmp_ccx_home / ".ccx" / "codex"
    passthrough_dir.mkdir(parents=True, exist_ok=True)
    (passthrough_dir / "config.toml").write_text(
        'sandbox_mode = "workspace-write"\n'
    )
    assert main(["sync"]) == 0

    config = tomllib.loads((tmp_ccx_home / ".codex" / "config.toml").read_text())
    assert config["sandbox_mode"] == "workspace-write"
    assert "mcp_servers" in config
