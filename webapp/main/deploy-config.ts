export interface DeployConfig {
  Python?: {
    PythonExecutable?: string;
  };
  Backend?: {
    Host?: string;
    Port?: number;
  };
  Webapp?: {
    Lang?: string;
    Theme?: string;
    DpiScaling?: boolean;
  };
  Deploy?: {
    Python?: {
      PythonExecutable?: string;
    };
    Webui?: {
      WebuiHost?: string;
      WebuiPort?: number;
      Language?: string;
      Theme?: string;
      DpiScaling?: boolean;
    };
  };
}

const normalizeLegacyTheme = (theme: string | undefined): string | undefined => {
  return theme === "default" ? "light" : theme;
};

/**
 * Present current and legacy deploy files through one startup shape.
 *
 * Current top-level fields always take precedence when both schemas are
 * present. Legacy ALAS projects keep their single Deploy mapping on disk;
 * the Python backend owns persistence and translates preference writes back
 * to that mapping, so the Electron host only needs a read-time view here.
 */
export function normalizeDeployConfig(config: DeployConfig | null | undefined): DeployConfig {
  const source = config ?? {};
  const legacy = source.Deploy;
  const legacyWebui = legacy?.Webui;
  const theme = source.Webapp?.Theme ?? legacyWebui?.Theme;

  return {
    Python: {
      PythonExecutable: source.Python?.PythonExecutable ?? legacy?.Python?.PythonExecutable,
    },
    Backend: {
      Host: source.Backend?.Host ?? legacyWebui?.WebuiHost,
      Port: source.Backend?.Port ?? legacyWebui?.WebuiPort,
    },
    Webapp: {
      Lang: source.Webapp?.Lang ?? legacyWebui?.Language,
      Theme: source.Webapp?.Theme ?? normalizeLegacyTheme(theme),
      DpiScaling: source.Webapp?.DpiScaling ?? legacyWebui?.DpiScaling,
    },
  };
}
