"""
Filesystem Resources Adapter.
Implements IResourcePort by locating assets across source and frozen directory hierarchies.
"""

from pathlib import Path
from typing import List
from qyro_engine.application.ports.environment import IEnvironmentPort
from qyro_engine.application.ports.resources import IResourcePort
from qyro_engine.domain.entities import PlatformType, ResourceQuery, ResourceResult


class FileSystemResourceAdapter(IResourcePort):
    """Resolves assets across multi-tiered directory structures."""

    def __init__(self, env_port: IEnvironmentPort, custom_resources_dir: Path | None = None) -> None:
        self._env = env_port
        self._custom_resources_dir = custom_resources_dir

    def _get_candidate_roots(self) -> List[Path]:
        if self._custom_resources_dir and self._custom_resources_dir.exists():
            return [self._custom_resources_dir]

        platform = self._env.get_platform()
        platform_subdir_map = {
            PlatformType.WINDOWS: ["windows", "win32"],
            PlatformType.MACOS: ["mac", "darwin"],
            PlatformType.LINUX: ["linux"],
        }
        os_dirs = platform_subdir_map.get(platform, [])

        candidates: List[Path] = []

        if self._env.is_frozen():
            bundle = self._env.get_bundle_dir()
            # In PyInstaller bundles, assets might be under resources/, resources/base/, or root
            for os_sub in os_dirs:
                candidates.append(bundle / "resources" / os_sub)
                candidates.append(bundle / "src" / "main" / "resources" / os_sub)
            candidates.extend([
                bundle / "resources" / "base",
                bundle / "resources",
                bundle / "src" / "main" / "resources" / "base",
                bundle,
            ])
        else:
            root = self._env.get_root_dir()
            # Standard Qyro project structure: demo/resources/<os> and demo/resources/base
            # 1. OS-specific resources (e.g. resources/linux, resources/mac, resources/windows)
            for os_sub in os_dirs:
                candidates.append(root / "resources" / os_sub)
                candidates.append(root / "src" / "main" / "resources" / os_sub)
            # 2. Base platform-agnostic resources (e.g. resources/base/icons/Icon.ico)
            candidates.append(root / "resources" / "base")
            # 3. Direct resources root (supports get_resource("base", "icons", "Icon.ico"))
            candidates.append(root / "resources")
            # 4. Legacy/alternative maven-style paths fallback
            candidates.append(root / "src" / "main" / "resources" / "base")
            candidates.append(root / "src" / "main" / "resources")

        # Keep existing directories only, preserve order
        unique: List[Path] = []
        for c in candidates:
            if c.exists() and c not in unique:
                unique.append(c)

        return unique

    def resolve(self, query: ResourceQuery) -> ResourceResult:
        rel_path = Path(*query.relative_path_segments)
        candidates = self._get_candidate_roots()

        for root in candidates:
            target = root / rel_path
            if target.exists():
                return ResourceResult(
                    absolute_path=target.resolve(),
                    exists=True,
                    is_bundled=self._env.is_frozen(),
                    target_os=self._env.get_platform(),
                )

        # If not found, return the expected location inside the primary root
        primary_root = candidates[0] if candidates else self._env.get_root_dir()
        fallback_path = (primary_root / rel_path).resolve()
        return ResourceResult(
            absolute_path=fallback_path,
            exists=False,
            is_bundled=self._env.is_frozen(),
        )

    def list_resources(self, subdirectory: str = "") -> List[Path]:
        rel = Path(subdirectory)
        results: List[Path] = []
        for root in self._get_candidate_roots():
            target_dir = root / rel
            if target_dir.exists() and target_dir.is_dir():
                results.extend([p.resolve() for p in target_dir.iterdir()])
        return list(set(results))
