# 桌面端构建说明

本目录使用 pnpm 12（Node.js 包管理器第 12 版）管理依赖，并通过
Vite（前端构建工具）与 electron-builder（桌面应用打包工具）生成发行文件。

## 安装依赖

```powershell
pnpm install --frozen-lockfile
```

`--frozen-lockfile`（禁止更新锁文件）用于保证本地与持续集成环境安装完全相同的版本。

## 允许依赖构建脚本

pnpm 12（Node.js 包管理器第 12 版）默认只运行仓库明确允许的依赖构建脚本。
本项目在 `pnpm-workspace.yaml`（工作区配置文件）中维护 allowBuilds（允许构建清单）：

```yaml
allowBuilds:
  electron: true
  electron-winstaller: true
  esbuild: true
```

这些依赖分别提供 Electron（桌面应用运行时）、Windows（视窗操作系统）安装器组件和
esbuild（JavaScript 构建器）。不要使用 `--all`（批准全部待处理依赖）；新增依赖被拦截时，
先核对包名、版本和构建脚本用途，再只批准明确需要的包：

```powershell
pnpm ignored-builds
pnpm approve-builds <package-name>
pnpm install --frozen-lockfile
```

执行后检查 Git（版本控制工具）差异，确认 allowBuilds（允许构建清单）只增加了预期包。

官方依据：[pnpm approve-builds（批准依赖构建脚本）](https://pnpm.io/cli/approve-builds)。
该文档的 12.x（第 12 版）说明指出，批准结果写入 allowBuilds（允许构建清单），且该配置已替代旧清单。

## 验证与打包

```powershell
pnpm exec tsx --test main/*.test.ts
pnpm check
pnpm package
```

`pnpm package`（生成发行目录）会构建渲染进程与主进程，再由
electron-builder（桌面应用打包工具）在 `release`（发行输出目录）中生成平台目录包。
