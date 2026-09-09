/**
 * Unit tests for current and legacy deploy configuration normalization.
 *
 * Run with: pnpm exec tsx --test main/deploy-config.test.ts
 */
import assert from "node:assert/strict";
import { test } from "node:test";
import { normalizeDeployConfig } from "./deploy-config";

test("normalizeDeployConfig: reads current top-level sections", () => {
  assert.deepEqual(
    normalizeDeployConfig({
      Python: { PythonExecutable: "./toolkit/python.exe" },
      Backend: { Host: "127.0.0.1", Port: 22669 },
      Webapp: { Lang: "zh-CN", Theme: "dark", DpiScaling: false },
    }),
    {
      Python: { PythonExecutable: "./toolkit/python.exe" },
      Backend: { Host: "127.0.0.1", Port: 22669 },
      Webapp: { Lang: "zh-CN", Theme: "dark", DpiScaling: false },
    },
  );
});

test("normalizeDeployConfig: maps the legacy Deploy section", () => {
  assert.deepEqual(
    normalizeDeployConfig({
      Deploy: {
        Python: { PythonExecutable: "./toolkit/python.exe" },
        Webui: {
          WebuiHost: "0.0.0.0",
          WebuiPort: 22267,
          Language: "ja-JP",
          Theme: "default",
          DpiScaling: true,
        },
      },
    }),
    {
      Python: { PythonExecutable: "./toolkit/python.exe" },
      Backend: { Host: "0.0.0.0", Port: 22267 },
      Webapp: { Lang: "ja-JP", Theme: "light", DpiScaling: true },
    },
  );
});

test("normalizeDeployConfig: current fields override legacy fields", () => {
  const config = normalizeDeployConfig({
    Python: { PythonExecutable: "C:/Python/python.exe" },
    Webapp: { Theme: "system", DpiScaling: false },
    Deploy: {
      Python: { PythonExecutable: "./toolkit/python.exe" },
      Webui: { Theme: "dark", DpiScaling: true },
    },
  });

  assert.equal(config.Python?.PythonExecutable, "C:/Python/python.exe");
  assert.equal(config.Webapp?.Theme, "system");
  assert.equal(config.Webapp?.DpiScaling, false);
});
