# CodeProof Desktop

Windows desktop application for the CodeProof developer engineering environment.

## Prerequisites

- **Flutter SDK** 3.13+ (stable channel)
- **Dart SDK** 3.13+ (included with Flutter)
- **Visual Studio 2022** with "Desktop development with C++" workload
- **Windows 10/11** (for building and running)
- **Git** for version control

## Dependency Installation

```bash
cd desktop
flutter pub get
```

## Running on Windows (Development)

```bash
cd desktop
flutter run -d windows
```

## Formatting

```bash
cd desktop
dart format lib test
```

## Static Analysis

```bash
cd desktop
flutter analyze
```

## Tests

```bash
cd desktop
flutter test
```

## Windows Build (Release)

```bash
cd desktop
flutter build windows --release
```

The built executable will be at:
```
desktop/build/windows/x64/runner/Release/codeproof_desktop.exe
```

## Current Scope (Foundation Task)

This foundation implements:

- ✅ Flutter Windows project initialization
- ✅ Minimal app structure (`lib/app/`, `lib/features/startup/`)
- ✅ Custom theme (light/dark) with Material 3
- ✅ Startup screen with:
  - CodeProof title and logo
  - Application purpose description
  - "No project selected" empty state
  - Core principle footer
  - Responsive layout handling resizing
- ✅ Widget tests for startup screen and layout resilience

## Known Limitations

- **No backend integration** — Project selection, analysis, challenges, patches, sandbox, and readiness screens are not implemented
- **No project scanning** — "Select Project" button is disabled (placeholder only)
- **No navigation** — Single screen only; sidebar/routes not implemented
- **No API client** — Centralized HTTP client not yet created
- **No typed models** — Dart models matching backend contracts not yet created
- **Mock data only** — All content is static; no real data flow

## Project Structure

```
desktop/
├── lib/
│   ├── main.dart              # App entry point
│   ├── app/
│   │   ├── app.dart           # MaterialApp with theme
│   │   └── theme.dart         # Light/dark theme definitions
│   └── features/
│       └── startup/
│           └── startup_screen.dart  # Foundation startup UI
├── test/
│   └── widget_test.dart       # Startup screen tests
├── windows/                   # Windows runner (generated)
├── pubspec.yaml
├── analysis_options.yaml
└── README.md
```

## Architecture Notes

- **No direct project modification** — Following CodeProof core principle
- **Backend-first data flow** — All project data comes via FastAPI backend
- **Sandbox isolation** — Code execution happens in Docker (backend responsibility)
- **Flutter scope** — Presentation, interaction, backend API consumption only

## Next Steps (Future Tasks)

1. Application shell (sidebar, header, navigation)
2. Reusable design system components
3. Project selection & backend API integration
4. Dashboard, Analysis, Skills, Challenges, Patch Lab, Sandbox, Readiness screens
5. Centralized API client with typed models
6. State management for selected project, analysis, challenges, etc.
7. Windows installer/packaging for demo