import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../domain/workspace_controller.dart';
import '../features/startup/startup_screen.dart';
import '../features/workspace/workspace_shell.dart';
import '../services/practice_service.dart';
import '../services/workspace_service.dart';
import '../ui/glass.dart';
import 'theme.dart';

const _nativeChannel = MethodChannel('codeproof/native');

class CodeProofApp extends StatefulWidget {
  const CodeProofApp({super.key});
  @override
  State<CodeProofApp> createState() => _CodeProofAppState();
}

class _CodeProofAppState extends State<CodeProofApp> {
  bool reducedTransparency = false;
  bool reducedMotion = false;
  @override
  Widget build(BuildContext context) => GlassSettings(
    reducedTransparency: reducedTransparency,
    reducedMotion: reducedMotion,
    child: MaterialApp(
      title: 'CodeProof',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(
          disableAnimations:
              reducedMotion || MediaQuery.disableAnimationsOf(context),
        ),
        child: child!,
      ),
      home: _Home(
        onSettings: (context) => showDialog<void>(
          context: context,
          builder: (context) => StatefulBuilder(
            builder: (context, update) => AlertDialog(
              title: const Text('Make this space yours'),
              content: SizedBox(
                width: 430,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Reduce transparency'),
                      subtitle: const Text(
                        'Solid surfaces for clarity and performance',
                      ),
                      value: reducedTransparency,
                      onChanged: (value) {
                        setState(() => reducedTransparency = value);
                        update(() {});
                      },
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Reduce motion'),
                      subtitle: const Text(
                        'Keep navigation still and predictable',
                      ),
                      value: reducedMotion,
                      onChanged: (value) {
                        setState(() => reducedMotion = value);
                        update(() {});
                      },
                    ),
                    const Divider(),
                    const SizedBox(height: 12),
                    const Text(
                      'Keyboard shortcuts\nCtrl+1–5   Workspace sections\nCtrl+K      Find a file\nF1             Open engineering coach',
                      style: TextStyle(color: Palette.muted, height: 2),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Done'),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class _Home extends StatefulWidget {
  const _Home({required this.onSettings});
  final void Function(BuildContext) onSettings;
  @override
  State<_Home> createState() => _HomeState();
}

class _HomeState extends State<_Home> {
  final controller = WorkspaceController(PracticeWorkspaceService());
  final shellKey = GlobalKey<WorkspaceShellState>();
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> connect() async {
    final result = await showDialog<_Connection>(
      context: context,
      builder: (context) => const _ConnectDialog(),
    );
    if (result != null && mounted) {
      await controller.open(
        path: result.path,
        using: LocalWorkspaceService(token: result.token, port: result.port),
      );
    }
  }

  Future<void> analyze() async {
    final approved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Analyze with your AI provider?'),
        content: const SizedBox(
          width: 450,
          child: Text(
            'The backend will send selected, redacted project contents to your configured OpenRouter model for analysis and coaching. Review your project for sensitive material before continuing.\n\nYour API key stays in the backend environment.',
            style: TextStyle(color: Palette.muted),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          PrimaryButton(
            'Enable AI analysis',
            onPressed: () => Navigator.pop(context, true),
          ),
        ],
      ),
    );
    if (approved == true && mounted) {
      await controller.act('analysis', {'use_ai': true});
    }
  }

  Future<void> closeProject() async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Close this workspace?'),
        content: const Text(
          'The temporary copy and session progress will be discarded. Copy any diff or evidence you want to keep. Your original project is unchanged.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Keep working'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Close workspace'),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) await controller.close();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: controller,
    builder: (context, _) {
      final data = controller.data;
      return CallbackShortcuts(
        bindings: {
          for (final (key, tab) in [
            (LogicalKeyboardKey.digit1, WorkspaceTab.analysis),
            (LogicalKeyboardKey.digit2, WorkspaceTab.skills),
            (LogicalKeyboardKey.digit3, WorkspaceTab.code),
            (LogicalKeyboardKey.digit4, WorkspaceTab.investigation),
            (LogicalKeyboardKey.digit5, WorkspaceTab.patch),
          ])
            SingleActivator(key, control: true): () {
              if (data != null) controller.selectTab(tab);
            },
          const SingleActivator(LogicalKeyboardKey.keyK, control: true): () =>
              shellKey.currentState?.showFiles(),
          const SingleActivator(LogicalKeyboardKey.f1): () =>
              shellKey.currentState?.showCoach(),
        },
        child: Focus(
          autofocus: true,
          child: Scaffold(
            body: AmbientBackground(
              child: SafeArea(
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 12, 16, 5),
                      child: LayoutBuilder(
                        builder: (context, size) => Row(
                          children: [
                            Brand(compact: size.maxWidth < 430),
                            const SizedBox(width: 22),
                            if (data != null && size.maxWidth > 700) ...[
                              Container(
                                width: 1,
                                height: 24,
                                color: Palette.line,
                              ),
                              const SizedBox(width: 20),
                              Expanded(
                                child: Text(
                                  data.name,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: Palette.muted,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                              StatusBadge(data.mode, color: Palette.violet),
                            ] else
                              const Spacer(),
                            if (size.maxWidth > 1000) ...[
                              const SizedBox(width: 10),
                              const StatusBadge(
                                'Original protected',
                                icon: Icons.shield_outlined,
                                color: Palette.mint,
                              ),
                            ],
                            if (data != null)
                              IconButton(
                                tooltip: 'Close workspace',
                                onPressed: controller.busy
                                    ? null
                                    : closeProject,
                                icon: const Icon(
                                  Icons.logout_rounded,
                                  size: 18,
                                  color: Palette.muted,
                                ),
                              ),
                            IconButton(
                              tooltip: 'Appearance & shortcuts',
                              onPressed: () => widget.onSettings(context),
                              icon: const Icon(
                                Icons.tune_rounded,
                                size: 20,
                                color: Palette.muted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    if (controller.busy)
                      LinearProgressIndicator(
                        minHeight: 2,
                        color: Palette.cyan,
                        semanticsLabel: controller.operation,
                      )
                    else
                      const SizedBox(height: 2),
                    if (controller.error != null)
                      Container(
                        margin: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 8,
                        ),
                        padding: const EdgeInsets.fromLTRB(16, 6, 5, 6),
                        decoration: BoxDecoration(
                          color: Palette.red.withValues(alpha: .12),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.error_outline,
                              size: 18,
                              color: Palette.red,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                controller.error!,
                                style: const TextStyle(fontSize: 12),
                              ),
                            ),
                            IconButton(
                              tooltip: 'Dismiss error',
                              onPressed: controller.clearError,
                              icon: const Icon(Icons.close, size: 17),
                            ),
                          ],
                        ),
                      ),
                    Expanded(
                      child: data == null
                          ? StartupScreen(
                              busy: controller.busy,
                              onPractice: () => controller.open(
                                using: PracticeWorkspaceService(),
                              ),
                              onConnect: connect,
                            )
                          : WorkspaceShell(
                              key: shellKey,
                              controller: controller,
                              onAnalyze: analyze,
                            ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: .12),
                        border: const Border(
                          top: BorderSide(color: Palette.line),
                        ),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.circle,
                            color: Palette.mint,
                            size: 6,
                          ),
                          const SizedBox(width: 7),
                          Expanded(
                            child: Text(
                              controller.busy
                                  ? controller.operation
                                  : data == null
                                  ? 'A safe space to understand your software'
                                  : data.practice
                                  ? 'Practice mode · in-memory workspace'
                                  : 'Guardian · read-only project access',
                              style: const TextStyle(
                                color: Palette.muted,
                                fontSize: 10,
                              ),
                            ),
                          ),
                          if (MediaQuery.sizeOf(context).width > 650)
                            Text(
                              data?.hasChallenge == true
                                  ? 'Challenge copy   •   UTF-8'
                                  : 'CodeProof   /   Engineering workspace',
                              style: const TextStyle(
                                color: Palette.muted,
                                fontSize: 10,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    },
  );
}

class _Connection {
  const _Connection(this.path, this.token, this.port);
  final String path;
  final String token;
  final int port;
}

class _ConnectDialog extends StatefulWidget {
  const _ConnectDialog();
  @override
  State<_ConnectDialog> createState() => _ConnectDialogState();
}

class _ConnectDialogState extends State<_ConnectDialog> {
  final path = TextEditingController();
  final token = TextEditingController();
  final port = TextEditingController(text: '8000');
  String? error;
  @override
  void dispose() {
    path.dispose();
    token.dispose();
    port.dispose();
    super.dispose();
  }

  Future<void> browseForProject() async {
    try {
      final selected = await _nativeChannel.invokeMethod<String>(
        'pick_directory',
      );
      if (selected != null && selected.isNotEmpty && mounted) {
        setState(() {
          path.text = selected;
          error = null;
        });
      }
    } on MissingPluginException {
      if (mounted) {
        setState(
          () => error = 'Folder browsing is available in the Windows desktop build.',
        );
      }
    } on PlatformException catch (exception) {
      if (mounted) {
        setState(
          () => error = exception.message ?? 'Could not open the folder picker.',
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Connect your project'),
    content: SizedBox(
      width: 490,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Start the local service with python -m backend, then paste its pairing token. Project files stay on this computer unless you explicitly enable AI analysis.',
              style: TextStyle(color: Palette.muted),
            ),
            const SizedBox(height: 22),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: TextField(
                    controller: path,
                    decoration: const InputDecoration(
                      labelText: 'Project folder',
                      hintText: r'C:\Projects\my-app',
                      helperText:
                          'Leave empty to connect the bundled sample project.',
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: OutlinedButton.icon(
                    onPressed: browseForProject,
                    icon: const Icon(Icons.folder_open_outlined, size: 17),
                    label: const Text('Browse'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 13,
                        vertical: 15,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: token,
              obscureText: true,
              enableSuggestions: false,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Local pairing token',
                prefixIcon: Icon(Icons.key_outlined, size: 18),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: port,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Port on 127.0.0.1'),
            ),
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(error!, style: const TextStyle(color: Palette.red)),
              ),
            const SizedBox(height: 20),
            const StatusBadge(
              'Loopback connection only',
              color: Palette.mint,
              icon: Icons.lock_outline,
            ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancel'),
      ),
      PrimaryButton(
        'Open project',
        icon: Icons.folder_open_outlined,
        onPressed: () {
          final number = int.tryParse(port.text);
          if (token.text.trim().length < 32 ||
              number == null ||
              number < 1 ||
              number > 65535) {
            setState(
              () => error = 'Enter the service token (at least 32 characters) and a valid port.',
            );
            return;
          }
          Navigator.pop(
            context,
            _Connection(path.text.trim(), token.text.trim(), number),
          );
        },
      ),
    ],
  );
}
