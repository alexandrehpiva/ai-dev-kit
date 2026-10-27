#!/usr/bin/env python3
"""Testes do detect_stack.py (biblioteca padrão). Rodar: python3 test_detect_stack.py"""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect_stack as ds  # noqa: E402

TODAY = dt.date(2026, 10, 27)


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def guide(gid, kind, detect, covered="", verified="2026-10-27", language="any"):
    return (f"---\nid: {gid}\ntitle: {gid}\nkind: {kind}\nlanguage: {language}\ndetect: {detect}\n"
            f'versions_covered: "{covered}"\nlast_verified: {verified}\n---\n# {gid}\n')


class DetectStackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.stacks = base / "skill" / "stacks"
        self.repo = base / "repo"
        self.repo.mkdir()
        write(self.stacks, "languages/ts.md", guide("typescript-node", "language", "lang:typescript, npm:typescript"))
        write(self.stacks, "frameworks/nest.md", guide("nestjs", "framework", "npm:@nestjs/core", "10.0 – 11.1"))
        write(self.stacks, "frameworks/fastapi.md", guide("fastapi", "framework", "pypi:fastapi", "0.100 – 0.115", "2025-01-01"))
        write(self.stacks, "frameworks/angular.md", guide("angular", "framework", "npm:@angular/core, file:angular.json", "14 – 20"))
        write(self.stacks, "data/jpa.md", guide("java-jpa", "data", "maven:org.hibernate"))
        write(self.stacks, "data/redis.md", guide("redis", "data", "npm:ioredis", "7.0 – 8.10"))
        write(self.stacks, "data/prisma.md", guide("typescript-orm", "data", "npm:prisma", "5.0 – 7.2", language="typescript"))
        write(self.stacks, "frameworks/gin.md", guide("go-http", "framework", "go:github.com/gin-gonic/gin"))
        write(self.stacks, "architecture/backend.md", guide("backend-architecture-patterns", "architecture", "always"))

    def tearDown(self):
        self.tmp.cleanup()

    def run_detect(self):
        return ds.detect(self.repo, self.stacks, TODAY)

    def ids(self, result):
        return {g["id"] for g in result["data"]["guides"]}

    def test_given_nest_project_when_detect_then_ts_nest_and_architecture_guides(self):
        write(self.repo, "package.json", json.dumps({"dependencies": {"@nestjs/core": "^11.0.1"},
                                                     "devDependencies": {"typescript": "5.9.2"}}))
        write(self.repo, "tsconfig.json", "{}")
        r = self.run_detect()
        self.assertEqual(r["status"], "ok", r)
        self.assertEqual(self.ids(r), {"typescript-node", "nestjs", "backend-architecture-patterns"})

    def test_given_old_guide_when_detect_then_stale(self):
        write(self.repo, "requirements.txt", "FastAPI[standard]==0.110.0\n")
        r = self.run_detect()
        g = next(g for g in r["data"]["guides"] if g["id"] == "fastapi")
        self.assertTrue(g["stale"])
        self.assertEqual(r["status"], "stale-guides")

    def test_given_version_outside_coverage_when_detect_then_stale(self):
        write(self.repo, "package.json", json.dumps({"dependencies": {"@nestjs/core": "^9.4.0"}}))
        r = self.run_detect()
        g = next(g for g in r["data"]["guides"] if g["id"] == "nestjs")
        self.assertTrue(g["stale"], g)

    def test_given_major_only_coverage_when_version_inside_then_not_stale(self):
        write(self.repo, "package.json", json.dumps({"dependencies": {"@angular/core": "~17.3.0"}}))
        write(self.repo, "angular.json", "{}")
        r = self.run_detect()
        g = next(g for g in r["data"]["guides"] if g["id"] == "angular")
        self.assertFalse(g["stale"], g)

    def test_given_core_package_without_guide_when_detect_then_missing(self):
        write(self.repo, "pyproject.toml", '[project]\nname="x"\ndependencies=["django>=5.0"]\n')
        r = self.run_detect()
        self.assertEqual(r["status"], "missing-guides")
        self.assertIn("pypi:django", r["data"]["missing_core"])

    def test_given_maven_and_go_prefixes_when_detect_then_matched(self):
        write(self.repo, "pom.xml", "<project xmlns='http://maven.apache.org/POM/4.0.0'><dependencies><dependency>"
                                    "<groupId>org.hibernate.orm</groupId><artifactId>hibernate-core</artifactId>"
                                    "<version>6.6.0</version></dependency></dependencies></project>")
        write(self.repo, "go.mod", "module x\n\ngo 1.24\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.10.0\n)\n")
        r = self.run_detect()
        self.assertTrue({"java-jpa", "go-http"} <= self.ids(r), r)
        self.assertEqual(r["data"]["runtimes"]["go"], "1.24")

    def test_given_database_guide_when_client_version_differs_then_not_stale(self):
        write(self.repo, "package.json", json.dumps({"dependencies": {"ioredis": "^5.4.1", "prisma": "^4.16.0"}}))
        r = self.run_detect()
        by_id = {g["id"]: g for g in r["data"]["guides"]}
        self.assertFalse(by_id["redis"]["stale"], by_id["redis"])
        self.assertTrue(by_id["typescript-orm"]["stale"], by_id["typescript-orm"])

    def test_given_multi_package_guide_when_secondary_version_differs_then_not_stale(self):
        write(self.repo, "package.json", json.dumps({"dependencies": {"drizzle-orm": "^0.45.0"}}))
        write(self.stacks, "data/prisma.md", guide("typescript-orm", "data", "npm:prisma, npm:drizzle-orm", "5.0 – 7.2", language="typescript"))
        r = self.run_detect()
        g = next(g for g in r["data"]["guides"] if g["id"] == "typescript-orm")
        self.assertFalse(g["stale"], g)

    def test_given_segmented_coverage_when_primary_inside_then_not_stale(self):
        write(self.stacks, "frameworks/node.md", guide("node-http", "framework", "npm:express, npm:koa",
                                                      "Express 4.x – 5.3 (6 em RC); Koa 2.x – 3.2"))
        write(self.repo, "package.json", json.dumps({"dependencies": {"express": "^5.1.0"}}))
        r = self.run_detect()
        g = next(g for g in r["data"]["guides"] if g["id"] == "node-http")
        self.assertFalse(g["stale"], g)

    def test_given_node_modules_when_detect_then_ignored(self):
        write(self.repo, "node_modules/x/package.json", json.dumps({"dependencies": {"@nestjs/core": "1"}}))
        r = self.run_detect()
        self.assertNotIn("nestjs", self.ids(r))

    def test_real_guides_have_valid_frontmatter(self):
        for g in ds.load_guides():
            self.assertIn(g.get("kind"), {"language", "framework", "data", "architecture"}, g["path"])
            self.assertTrue(g["detect_keys"], g["path"])
            dt.date.fromisoformat(g.get("last_verified", ""))


if __name__ == "__main__":
    unittest.main()
