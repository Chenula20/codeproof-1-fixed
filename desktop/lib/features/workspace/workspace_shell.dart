import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../domain/workspace_controller.dart';
import '../../ui/glass.dart';
import 'coach.dart';
import 'evidence.dart';
import 'pages.dart';

class WorkspaceShell extends StatefulWidget {
  const WorkspaceShell({
    super.key,
    required this.controller,
    required this.onAnalyze,
  });
  final WorkspaceController controller;
  final VoidCallback onAnalyze;
  @override
  State<WorkspaceShell> createState() => WorkspaceShellState();
}

class WorkspaceShellState extends State<WorkspaceShell> {
  final explanation = TextEditingController();
  bool expandedEvidence = true;
  WorkspaceController get c => widget.controller;
  @override
  void dispose() {
    explanation.dispose();
    super.dispose();
  }

  void showCoach() => showDialog<void>(
    context: context,
    builder: (context) => Dialog(
      backgroundColor: Colors.transparent,
      child: SizedBox(
        width: 430,
        height: 650,
        child: ListenableBuilder(
          listenable: c,
          builder: (context, _) => CoachPanel(
            controller: c,
            explanation: explanation,
            onClose: () => Navigator.pop(context),
          ),
        ),
      ),
    ),
  );

  void showFiles() => showDialog<void>(
    context: context,
    builder: (context) => Dialog(
      child: SizedBox(
        width: 420,
        height: 520,
        child: ProjectExplorer(
          controller: c,
          onSelected: () => Navigator.pop(context),
        ),
      ),
    ),
  );

  Future<void> startChallenge() async {
    final data = c.data!;
    final issue = TextEditingController();
    String target = c.selectedFile;
    final proceed = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, update) => AlertDialog(
          title: Text(
            data.sample
                ? 'Ready to break it, safely?'
                : 'Investigate a project issue',
          ),
          content: SizedBox(
            width: 480,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    data.sample
                        ? 'Introduce a controlled authentication failure in a temporary challenge copy. Your original project remains untouched.'
                        : 'Describe a failure you observed. CodeProof will investigate this snapshot; it will not inject a fault into your original project.',
                    style: const TextStyle(color: Palette.muted),
                  ),
                  const SizedBox(height: 20),
                  const StatusBadge(
                    'Original project protected',
                    color: Palette.mint,
                    icon: Icons.shield_outlined,
                  ),
                  if (!data.sample) ...[
                    const SizedBox(height: 20),
                    TextField(
                      controller: issue,
                      minLines: 3,
                      maxLines: 5,
                      maxLength: 4000,
                      onChanged: (_) => update(() {}),
                      decoration: const InputDecoration(
                        labelText: 'Observed issue',
                        hintText: 'What happened, and what did you expect?',
                      ),
                    ),
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      initialValue: target,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Relevant file',
                      ),
                      items: data.files.keys
                          .map(
                            (path) => DropdownMenuItem(
                              value: path,
                              child: Text(
                                path,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontSize: 12),
                              ),
                            ),
                          )
                          .toList(),
                      onChanged: (value) => target = value!,
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Coaching and patch generation require AI analysis to be enabled first.',
                      style: TextStyle(fontSize: 11, color: Palette.muted),
                    ),
                  ],
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            PrimaryButton(
              'Start challenge',
              onPressed: !data.sample && issue.text.trim().isEmpty
                  ? null
                  : () => Navigator.pop(context, true),
            ),
          ],
        ),
      ),
    );
    final issueText = issue.text;
    // Dialog exit animations may still reference the controller for one frame.
    if (proceed == true && mounted) {
      explanation.clear();
      await c.act('challenge', {'issue': issueText, 'target_file': target});
    }
  }

  Future<void> validate() async {
    c.selectEvidence(EvidenceTab.sandbox);
    setState(() => expandedEvidence = true);
    String? runner = 'python-unittest';
    if (!c.data!.practice) {
      runner = await showDialog<String>(
        context: context,
        builder: (context) => SimpleDialog(
          title: const Text('Run tests in Docker'),
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(24, 0, 24, 16),
              child: Text(
                'Uses a prepared local image, without network access. No packages are installed during a run.',
                style: TextStyle(color: Palette.muted, fontSize: 12),
              ),
            ),
            for (final (value, title, description) in const [
              (
                'python-unittest',
                'Python · unittest',
                'Discover tests in tests/',
              ),
              (
                'python-pytest',
                'Python · pytest',
                'Run the project test suite',
              ),
              ('node-test', 'Node.js · built-in tests', 'Run node --test'),
            ])
              ListTile(
                title: Text(title),
                subtitle: Text(description),
                trailing: const Icon(Icons.arrow_forward, size: 18),
                onTap: () => Navigator.pop(context, value),
              ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
          ],
        ),
      );
    }
    if (runner != null && mounted) {
      await c.act('validation', {'runner': runner});
    }
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, size) {
      final wide = size.maxWidth >= 1180;
      final showExplorer = size.maxWidth >= 820;
      final data = c.data!;
      final evidenceHeight = expandedEvidence
          ? (size.maxHeight * .29).clamp(155.0, 245.0)
          : 45.0;
      return Padding(
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 10),
        child: Column(
          children: [
            SizedBox(
              height: 62,
              child: Row(
                children: [
                  if (!showExplorer)
                    IconButton(
                      tooltip: 'Project explorer',
                      onPressed: showFiles,
                      icon: const Icon(Icons.folder_open_outlined, size: 19),
                    ),
                  Expanded(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          for (final (tab, label, icon) in const [
                            (
                              WorkspaceTab.analysis,
                              'Analysis',
                              Icons.grid_view_rounded,
                            ),
                            (
                              WorkspaceTab.skills,
                              'Skill Map',
                              Icons.hub_outlined,
                            ),
                            (WorkspaceTab.code, 'Code', Icons.code_rounded),
                            (
                              WorkspaceTab.investigation,
                              'Investigation',
                              Icons.search_rounded,
                            ),
                            (
                              WorkspaceTab.patch,
                              'Patch Review',
                              Icons.difference_outlined,
                            ),
                          ])
                            Padding(
                              padding: const EdgeInsets.only(right: 5),
                              child: _nav(tab, label, icon),
                            ),
                        ],
                      ),
                    ),
                  ),
                  if (!wide)
                    IconButton(
                      tooltip: 'Open engineering coach',
                      onPressed: showCoach,
                      icon: const Icon(
                        Icons.auto_awesome_outlined,
                        color: Palette.violet,
                        size: 19,
                      ),
                    ),
                  if (size.maxWidth >= 700 && !data.hasChallenge)
                    Padding(
                      padding: const EdgeInsets.only(left: 12),
                      child: PrimaryButton(
                        data.sample ? 'Break My App' : 'Investigate',
                        icon: Icons.bolt_rounded,
                        onPressed: c.busy ? null : startChallenge,
                      ),
                    ),
                ],
              ),
            ),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (showExplorer) ...[
                    SizedBox(
                      width: 200,
                      child: GlassPanel(
                        padding: EdgeInsets.zero,
                        child: ProjectExplorer(controller: c),
                      ),
                    ),
                    const SizedBox(width: 12),
                  ],
                  Expanded(
                    child: GlassPanel(
                      padding: EdgeInsets.zero,
                      child: WorkspacePage(
                        controller: c,
                        onChallenge: startChallenge,
                        onAnalyze: widget.onAnalyze,
                        onValidate: validate,
                        onCoach: showCoach,
                      ),
                    ),
                  ),
                  if (wide) ...[
                    const SizedBox(width: 12),
                    SizedBox(
                      width: 300,
                      child: CoachPanel(
                        controller: c,
                        explanation: explanation,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              height: evidenceHeight,
              child: EvidencePanel(
                controller: c,
                expanded: expandedEvidence,
                onToggle: () =>
                    setState(() => expandedEvidence = !expandedEvidence),
                onValidate: validate,
              ),
            ),
          ],
        ),
      );
    },
  );

  Widget _nav(WorkspaceTab tab, String label, IconData icon) {
    final locked =
        tab == WorkspaceTab.investigation && !c.data!.hasChallenge ||
        tab == WorkspaceTab.patch && !c.data!.canReview;
    return Tooltip(
      message: locked
          ? 'Complete the previous step to unlock'
          : '$label · Ctrl+${tab.index + 1}',
      child: AnimatedContainer(
        duration: GlassSettings.of(context).reducedMotion
            ? Duration.zero
            : const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(13),
          color: c.tab == tab
              ? Palette.cyan.withValues(alpha: .10)
              : Colors.transparent,
          border: Border.all(
            color: c.tab == tab
                ? Palette.cyan.withValues(alpha: .30)
                : Colors.transparent,
          ),
        ),
        child: TextButton.icon(
          onPressed: locked ? null : () => c.selectTab(tab),
          icon: Icon(locked ? Icons.lock_outline : icon, size: 15),
          label: Text(label),
          style: TextButton.styleFrom(
            foregroundColor: c.tab == tab ? Palette.cyan : Palette.muted,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            textStyle: const TextStyle(fontFamily: 'Segoe UI', fontSize: 12),
          ),
        ),
      ),
    );
  }
}

class ProjectExplorer extends StatefulWidget {
  const ProjectExplorer({super.key, required this.controller, this.onSelected});
  final WorkspaceController controller;
  final VoidCallback? onSelected;
  @override
  State<ProjectExplorer> createState() => _ProjectExplorerState();
}

class _ProjectExplorerState extends State<ProjectExplorer> {
  String filter = '';
  @override
  Widget build(BuildContext context) {
    final c = widget.controller;
    final files =
        c.data!.files.keys
            .where((path) => path.toLowerCase().contains(filter.toLowerCase()))
            .toList()
          ..sort();
    String previous = '';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(17, 20, 17, 12),
          child: Text(
            'PROJECT EXPLORER',
            style: TextStyle(
              color: Palette.muted,
              letterSpacing: 1.4,
              fontSize: 9,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: TextField(
            decoration: const InputDecoration(
              hintText: 'Find a file…',
              prefixIcon: Icon(Icons.search, size: 17),
              isDense: true,
              contentPadding: EdgeInsets.all(11),
            ),
            onChanged: (value) => setState(() => filter = value),
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            children: [
              if (files.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text(
                    'No matching files',
                    style: TextStyle(color: Palette.muted, fontSize: 12),
                  ),
                ),
              for (final path in files) ...[
                if (path.contains('/') &&
                    path.substring(0, path.lastIndexOf('/')) != previous)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(9, 15, 5, 6),
                    child: Text(
                      previous = path.substring(0, path.lastIndexOf('/')),
                      style: const TextStyle(
                        color: Palette.muted,
                        fontSize: 10,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                Tooltip(
                  message: path,
                  child: ListTile(
                    dense: true,
                    visualDensity: const VisualDensity(vertical: -2),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 10),
                    minLeadingWidth: 14,
                    selected: c.selectedFile == path,
                    selectedTileColor: Palette.cyan.withValues(alpha: .08),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    leading: Icon(
                      path.endsWith('.js')
                          ? Icons.javascript_rounded
                          : path.endsWith('.py')
                          ? Icons.code_rounded
                          : Icons.description_outlined,
                      size: 15,
                      color: path.endsWith('.js')
                          ? Palette.amber
                          : Palette.mint,
                    ),
                    title: Text(
                      path.split('/').last,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12),
                    ),
                    onTap: () {
                      c.selectFile(path);
                      widget.onSelected?.call();
                    },
                  ),
                ),
              ],
            ],
          ),
        ),
        const Padding(
          padding: EdgeInsets.all(15),
          child: StatusBadge(
            'READ-ONLY',
            color: Palette.mint,
            icon: Icons.lock_outline,
          ),
        ),
      ],
    );
  }
}
